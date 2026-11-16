# INITIALIZATION_SEQUENCE_REVIEW

Evidence: [SRC] source (main.c, interlock.c, expander.c), [DS] datasheet, [BUILD] build only. Not run on hardware.

## Sequence after this revision
| Step | Code | Safe state if it fails |
|---|---|---|
| 0 | Before app_main: bootloader / startup. GPIO10 (ARM) is a hi-Z input (IE only, [DS] ESP32-C3 datasheet Table 2-1); external 10 k pull-down holds ARM low | n/a, hardware default |
| 1 | `interlock_safe_gpio_init()`: writes output level 0, configures GPIO10 as output, writes 0 again; `ESP_ERROR_CHECK` -> reboot loop on failure (ARM stays low) | ARM low / reboot |
| 2 | `nvs_flash_init()` (can erase flash; non-safety) | ARM low |
| 3 | `expander_init()`: creates the mutex, installs the I2C driver, `expander_configure` writes output register = 0x0000 first and then the configuration register, then `expander_boot_verify()` reads back configuration, output and input registers and requires: config = shadow, output = shadow, both enable bits low in the output register, low on the input-port pins, and configured as outputs | returns an error |
| 4 | `interlock_start(expander_ready)`: creates the API mutex, configures the WDI pin, `sup_init`: state DISARMED if verify passed, otherwise FAULT with reason BOOT (latched), `health_init`, then creates the sampler and supervisor tasks (return values checked, `abort()` with ARM low on failure) | FAULT/BOOT or reboot loop |
| 5 | `measure_init`, `storage_init`: non-safety; failures only light the fault LED | unchanged |
| 6 | `cli_start()`: the only entry point for arm requests; first reached after steps 1-4 | n/a |

## What changed from audit4
- Audit4 started the sampler and supervisor before `expander_init()`; the sampler could take a NULL mutex (see CURRENT_SOURCE_VS_REPORT.md). Now no task exists until the expander has been initialised and verified.
- Expander mutex creation is now the first thing in `expander_init` and every expander function that uses the mutex returns an error on a NULL mutex.
- A failed verify no longer aborts the boot (a reboot loop would hide the reason): the system comes up in FAULT/BOOT, the CLI works and `interlock status` shows `boot verification failed`; `sup_step` never raises ARM from FAULT. Recovery needs a disarm with fresh valid samples showing enables low.
- Task creation failures abort with ARM low instead of continuing without a supervisor.
- The WDI pin is not driven before the supervisor exists (hi-Z). The TPS3823 treats a floating WDI as "no watchdog" [DS], which is acceptable here because ARM is low and the CLI cannot arm yet; it also means a hang between steps 1 and 4 is not reset by the hardware watchdog. ARM stays low in that case.

## Requirements check
| Requirement | Result |
|---|---|
| Safe GPIO init before anything else | yes (step 1); the only earlier window is hardware default (step 0) |
| I2C init, TCA9555 init, output clearing, readback verification complete before task startup | yes (step 3 precedes step 4) |
| All completed before ARM acceptance | yes: arm requests come only from the CLI, started last; `interlock_request_arm` also returns false if `started` is not set |
| Every failure leaves the system disarmed | yes by construction: ARM low (GPIO + pull-down) in all failure branches; FAULT/BOOT latches; reboot loops end with ARM low |
| Residual | the retained TCA9555 enables from before an MCU reset stay high until step 3 (outputs written 0); ARM is low during that time, so rails are off |

## Not verified
Real boot timing, `i2c_driver_install` failure paths, behaviour on a missing TCA9555 (expected: step 3 returns a timeout error -> FAULT/BOOT) were not run on hardware. A host test covers only `sup_init(boot_ok=false)` (T10).
