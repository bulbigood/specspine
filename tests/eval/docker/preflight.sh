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
printf 'module.exports = true;\n' >/workspace/preflight.js
rg 'module.exports' /workspace/preflight.js >/dev/null
rm /workspace/preflight.js
