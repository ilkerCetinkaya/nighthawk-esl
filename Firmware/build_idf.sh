#!/bin/zsh
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="${NH_BUILD_DIR:-$HERE/../.build_fw}"
export PATH="$HOME/.espressif/python_env/idf5.4_py3.11_env/bin:$PATH"
. "$HOME/esp/esp-idf/export.sh" >/dev/null
[ -n "$NH_TOOLCHAIN_BIN" ] && export PATH="$NH_TOOLCHAIN_BIN:$PATH"
cd "$HERE"
idf.py -B "$OUT" -D SDKCONFIG="$OUT/sdkconfig" -D IDF_TARGET=esp32c3 build
