#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
runtime_root="$project_root/.eval-runtime"
mkdir -p "$runtime_root/workspaces" "$runtime_root/fixtures" "$runtime_root/docker" "$runtime_root/home"

auth_file="${SPECSPINE_EVAL_AUTH_FILE:-${CODEX_HOME:-$HOME/.codex}/auth.json}"
auth_file="$(cd "$(dirname "$auth_file")" && pwd)/$(basename "$auth_file")"
if [[ ! -f "$auth_file" ]]; then
  echo "Codex authentication file is missing: $auth_file" >&2
  exit 2
fi

docker_host="${DOCKER_HOST:-$(docker context inspect --format '{{.Endpoints.docker.Host}}')}"
if [[ "$docker_host" != unix://* ]]; then
  echo "The controller currently requires a local Unix Docker socket, got: $docker_host" >&2
  exit 2
fi
docker_socket="${docker_host#unix://}"
if [[ ! -S "$docker_socket" ]]; then
  echo "Docker socket is unavailable: $docker_socket" >&2
  exit 2
fi

controller_hash="$({ shasum -a 256 "$project_root/tests/eval/docker/controller.Dockerfile" 2>/dev/null || sha256sum "$project_root/tests/eval/docker/controller.Dockerfile"; } | awk '{print substr($1,1,16)}')"
controller_image="specspine-eval-controller:$controller_hash"
if ! docker image inspect "$controller_image" >/dev/null 2>&1; then
  docker build \
    --file "$project_root/tests/eval/docker/controller.Dockerfile" \
    --tag "$controller_image" \
    "$project_root"
fi

socket_gid=""
if socket_gid="$(stat -f '%g' "$docker_socket" 2>/dev/null)"; then
  :
elif socket_gid="$(stat -c '%g' "$docker_socket" 2>/dev/null)"; then
  :
fi

agent_model="${SPECSPINE_EVAL_AGENT_MODEL:-gpt-5.6-luna}"
agent_reasoning="${SPECSPINE_EVAL_AGENT_REASONING:-medium}"
judge_model="${SPECSPINE_EVAL_JUDGE_MODEL:-gpt-5.6-terra}"
judge_reasoning="${SPECSPINE_EVAL_JUDGE_REASONING:-medium}"
agent_command="python3 $project_root/tests/eval/adapters/docker.py --model $agent_model --reasoning-effort $agent_reasoning"
judge_command="python3 $project_root/tests/eval/adapters/docker.py --model $judge_model --reasoning-effort $judge_reasoning"

has_agent_command=false
has_judge_command=false
run_requested=false
for argument in "$@"; do
  [[ "$argument" == "--agent-command" ]] && has_agent_command=true
  [[ "$argument" == "--judge-command" ]] && has_judge_command=true
  [[ "$argument" == "--all" || "$argument" == "--experiment" || "$argument" == "--comparison" ]] && run_requested=true
done

docker_args=(
  run --rm --interactive
  --user "$(id -u):$(id -g)"
  --read-only
  --cap-drop=ALL
  --security-opt=no-new-privileges
  --tmpfs /tmp:rw,nosuid,nodev,size=256m
  --volume "$project_root:$project_root"
  --volume "$auth_file:$auth_file:ro"
  --volume "$docker_socket:$docker_socket"
  --workdir "$project_root"
  --env "HOME=$runtime_root/home"
  --env "DOCKER_HOST=unix://$docker_socket"
  --env "SPECSPINE_EVAL_AUTH_FILE=$auth_file"
  --env "SPECSPINE_EVAL_WORKSPACES_DIR=$runtime_root/workspaces"
  --env "SPECSPINE_EVAL_FIXTURES_DIR=$runtime_root/fixtures"
  --env "SPECSPINE_EVAL_DOCKER_CACHE_DIR=$runtime_root/docker"
  --env PYTHONDONTWRITEBYTECODE=1
)
if [[ -n "$socket_gid" ]]; then
  docker_args+=(--group-add "$socket_gid")
fi
# Docker Desktop exposes a bind-mounted user socket as root:root inside Linux
# containers, regardless of its host ownership. The controller is trusted and
# receives the socket by design; keep its host UID for correctly owned results.
docker_args+=(--group-add 0)

compare_args=("$@")
if [[ "$#" -eq 1 && "$1" == "--preflight" ]]; then
  exec docker "${docker_args[@]}" \
    --entrypoint python3 \
    "$controller_image" \
    "$project_root/tests/eval/adapters/docker.py" --preflight
fi
if [[ "$run_requested" == true && "$has_agent_command" == false ]]; then
  compare_args+=(--agent-command "$agent_command")
fi
if [[ "$run_requested" == true && "$has_judge_command" == false && "${SPECSPINE_EVAL_NO_JUDGE:-0}" != "1" ]]; then
  compare_args+=(--judge-command "$judge_command")
fi

exec docker "${docker_args[@]}" "$controller_image" "${compare_args[@]}"
