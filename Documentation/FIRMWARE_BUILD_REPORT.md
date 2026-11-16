# FIRMWARE_BUILD_REPORT

Date: 2026-11-07. Host: macOS (Darwin 23.0.0, arm64).

## Result
`idf.py build` exited 0 for target esp32c3. Output: nighthawk.bin 0x57490 bytes (357,520), smallest app partition 0x100000, 66 % free; bootloader.bin 0x6560 bytes. Compiler warnings in the log: 0 (`grep -c "warning:"` = 0). Full log: Documentation/Validation/audit2/firmware_build_full_log.txt. Not flashed, not run on hardware, no runtime test.

## Exact command
```
cd NIGHTHAWK_ESL/Firmware
export PATH=$HOME/.espressif/python_env/idf5.4_py3.11_env/bin:$PATH
. $HOME/esp/esp-idf/export.sh
export PATH=<dir containing a complete riscv32-esp-elf/bin>:$PATH
idf.py -B <out> -D SDKCONFIG=<out>/sdkconfig -D IDF_TARGET=esp32c3 build
```
Wrapper: Firmware/build_idf.sh (takes NH_TOOLCHAIN_BIN, NH_BUILD_DIR). Build output was written outside the project tree.

## Versions
ESP-IDF v5.4 (git describe in ~/esp/esp-idf), riscv32-esp-elf gcc 14.2.0 (esp-14.2.0_20241119), CMake 3.30.2, Python 3.11.5 (IDF venv). PlatformIO was not used; platformio.ini was not built.

## Environment problems found (not hardware, not firmware)
1. The ESP-IDF python venv `idf5.4_py3.11_env` had setuptools 75.8.0; IDF's constraints file requires `setuptools<71.0.1`, so `export.sh` aborted. I ran `pip install "setuptools<71.0.1"` inside that venv (the user-level IDF venv, not the system Python). This is the one change made to the existing environment; revert with `pip install setuptools==75.8.0` in that venv.
2. The installed `~/.espressif/tools/riscv32-esp-elf/esp-14.2.0_20241119` had no inner `riscv32-esp-elf/riscv32-esp-elf/bin` directory (assembler, linker), so gcc fell back to Apple `as` and failed ("clang: error: unsupported option '--traditional-format'"). Not modified; I extracted the cached tarball `~/.espressif/dist/riscv32-esp-elf-14.2.0_20241119-aarch64-apple-darwin.tar.xz` into a scratch directory and put its bin first on PATH. A test compile there succeeded. Reinstalling the tool with `~/esp/esp-idf/install.sh esp32c3` would fix the original.
3. An earlier set-target attempt used the broken toolchain and left an esp32 (Xtensa) configuration; the files were removed and not used for the result.

## Firmware defects found by the build
- src/ was not an ESP-IDF component of the project (no main component) -> `undefined reference to app_main`. Fix: Firmware/CMakeLists.txt now sets EXTRA_COMPONENT_DIRS to src/.
- src/cli.c used EXP_RF1_IRQ / EXP_RF2_IRQ without including pins.h -> compile error. Fix: include added.
So the firmware delivered in the previous turn did not compile; the earlier statement "not compiled" was accurate, and it would have failed.

## Observations
- sdkconfig.defaults sets CONFIG_ESP_WIFI_ENABLED=n, but the generated sdkconfig has CONFIG_ESP_WIFI_ENABLED=y (the option is not user-settable in IDF 5.4). Wi-Fi code is linked but no esp_wifi/esp_bt call exists in src/ or include/ (grep), so the radio is not initialised. Bluetooth is off in sdkconfig. Radio-off behaviour was not measured.
- Interlock firmware changes are in CRITICAL_AUDIT.md (corrections C3-C6).

## Rebuild after supervisor rework (2026-11-07)
Same command and toolchain. `idf.py build` exit 0, 0 errors, 0 warnings; nighthawk.bin 0x57d70 bytes, 66 % of the app partition free. Log: Documentation/Validation/audit2/firmware_build_full_log_rev2.txt. New sources compiled: health_core.c, supervisor_core.c, health.c; interlock.c, expander.c, cli.c, storage.c, main.c changed. Host tests: FIRMWARE_TEST_REPORT.md (113 checks, 0 failures). Not flashed or run on hardware.

## Rebuild after hardware-shutdown review (2026-11-07)
`idf.py build` exit 0, 0 errors, 0 warnings; nighthawk.bin 0x57ea0 bytes (66 % free). Log: Documentation/Validation/audit2/firmware_build_full_log_rev3.txt. Changes: sample timestamp at cycle start, enable pin-level read-back, good/bad streak counters, output-register mismatch check under the expander mutex. Host tests: 122 checks, 0 failures. Not flashed or run on hardware.

## Rebuild after PRECHECK / concurrency / init rework (2026-11-07)
`idf.py build` exit 0, 0 errors, 0 warnings; nighthawk.bin 0x584f0 bytes (66 % free); log Validation/audit2/firmware_build_full_log_rev4.txt. Host tests 720 checks, 0 failures (UPDATED_FIRMWARE_TEST_REPORT.md). Not flashed.

## Rebuild after PRECHECK validation fix (audit6)
`idf.py build` exit 0, 0 errors, 0 warnings; nighthawk.bin 0x58530 bytes (65 % free); log Validation/audit2/firmware_build_full_log_rev5.txt. Host tests 750 checks, 0 failures. Not flashed.
