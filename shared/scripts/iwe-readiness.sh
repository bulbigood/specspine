#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname "$0")" && pwd -P)
bundled_root=$(dirname "$script_dir")/assets/iwe

printf 'iwe=%s\n' "$(command -v iwe 2>/dev/null || true)"
printf 'bundled_config=%s\n' "$bundled_root/config.toml"
printf 'bundled_schema=%s\n' "$bundled_root/schemas/specification.yaml"

probe=$PWD
nearest=
while [ "$probe" != / ]; do
    if [ -f "$probe/.iwe/config.toml" ]; then
        nearest=$probe/.iwe/config.toml
        break
    fi
    probe=$(dirname "$probe")
done
printf 'nearest_config=%s\n' "${nearest:-none}"

if [ "${1:-}" = "--descendants" ]; then
    find . \
        -path './.git' -prune -o \
        -path '*/node_modules' -prune -o \
        -path '*/.iwe/config.toml' -type f -print \
        | sort
fi
