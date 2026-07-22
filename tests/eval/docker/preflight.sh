#!/bin/sh
set -eu

test "$(id -u)" != "0"
test -w /workspace
test -w /runtime
node --version
rg --version | sed -n '1p'
git --version
python3 --version
codex --version
node -e 'process.stdout.write("node-ok\n")'
mkdir -p /runtime/tmp
mkdir -p /runtime/.git /runtime/.agents /runtime/.codex
mkdir -p /workspace/.git /workspace/.agents /workspace/.codex
bwrap_path="$(find /usr/local/lib/node_modules/@openai/codex -path '*/codex-resources/bwrap' -type f | head -n 1)"
test -x "$bwrap_path"
"$bwrap_path" \
  --unshare-user \
  --uid "$(id -u)" \
  --gid "$(id -g)" \
  --ro-bind / / \
  --proc /proc \
  --dev /dev \
  -- /bin/true
printf 'module.exports = true;\n' >/workspace/preflight.js
# Exercise concurrent sandbox construction: real agents can issue parallel
# shell tools, which is where missing protected mountpoints used to fail.
pids=""
index=1
while [ "$index" -le 12 ]; do
  HOME=/home/eval TMPDIR=/runtime/tmp codex sandbox \
    -C /workspace \
    -c 'permissions.specspine_eval.workspace_roots={"."=true,"/runtime"=true}' \
    -c 'permissions.specspine_eval.filesystem={":minimal"="read",":workspace_roots"={"."="write",".git"="read"}}' \
    -c 'permissions.specspine_eval.network.enabled=false' \
    -P specspine_eval \
    /bin/sh -c "test -r preflight.js && printf sandbox-ok >preflight-sandbox-output-$index" &
  pids="$pids $!"
  index=$((index + 1))
done
for pid in $pids; do
  wait "$pid"
done
index=1
while [ "$index" -le 12 ]; do
  test "$(cat "/workspace/preflight-sandbox-output-$index")" = "sandbox-ok"
  rm "/workspace/preflight-sandbox-output-$index"
  index=$((index + 1))
done
rg 'module.exports' /workspace/preflight.js >/dev/null
rm /workspace/preflight.js
