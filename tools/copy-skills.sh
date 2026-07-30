#!/usr/bin/env bash

set -euo pipefail

usage() {
  echo "Usage: $(basename "$0") <project-directory>" >&2
}

if [[ $# -ne 1 ]]; then
  usage
  exit 2
fi

project_dir=$1
if [[ ! -d "$project_dir" ]]; then
  echo "Error: project directory does not exist: $project_dir" >&2
  exit 1
fi

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source_dir=$(cd -- "$script_dir/../skills" && pwd)
destination_dir="$project_dir/.agents/skills"

mkdir -p -- "$destination_dir"

# Dereference repository-relative symlinks so every installed skill remains
# self-contained after it is copied outside this repository.
cp -RL -- "$source_dir/." "$destination_dir/"

echo "Copied skills to $destination_dir"
