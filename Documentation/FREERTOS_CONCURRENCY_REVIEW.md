# FREERTOS_CONCURRENCY_REVIEW

Source-level review of Firmware/src (interlock.c, expander.c, health.c, cli.c, main.c) after this revision. Host tests are single-threaded models and do not establish FreeRTOS correctness; they are not used as evidence here. ESP32-C3 is single-core, so spinlock critical sections reduce to interrupt masking. FreeRTOS/IDF internals (driver mutex) are cited from the IDF source on this machine.

## Tasks and priorities
supervisor (6), sampler (5), CLI = app_main main task (default priority 1), IDF system tasks. The supervisor never blocks on a mutex, I2C, SD, or the API lock.

## Shared state inventory and protection
| Object | Writers | Readers | Protection | Notes |
|---|---|---|---|---|
| `shared.sup` (state, reason, counters) | supervisor (inside `guard`), `interlock_start` (before tasks exist) | CLI snapshot, supervisor | `guard` (spinlock) | CLI reads state+reason together in `interlock_snapshot` so they are consistent |
| `shared.sample` | sampler | supervisor, CLI snapshot | `guard` | copied by value under the lock; sequence number inside |
| `shared.arm_request` | CLI (`interlock_request_arm`, under `guard` together with the busy check) | supervisor | `guard` | consumed and cleared by the supervisor each pass |
| `shared.disarm_pending` | CLI | supervisor | `guard` | level, cleared by the CLI after the wait |
| `shared.clear_enables` | supervisor | sampler | `guard` | |
| `shared.refused_count` | supervisor | CLI | `guard` | a counter instead of a flag: the CLI compares with the value before its request, so a refusal of an earlier request cannot be mistaken for its own |
| Request serialisation | `api_lock` mutex (CLI/API callers only) | | mutex | held while waiting up to 1.5 s; the supervisor does not take it |
| `enable_permit` (expander.c) | supervisor via `expander_set_enable_permit` | `expander_write` | own spinlock `permit_guard` | |
| `output_shadow` | `expander_write`, `expander_configure` | `expander_read_outputs`, `expander_boot_verify` | `lock` mutex (configure/verify run during init, before tasks) | |
| health table | CLI, sampler (progress), supervisor (evaluate) | | spinlock in health.c | |
| `started`, `api_lock` handle | `interlock_start` once, before any API caller (cli_start is last in main) | CLI | write-once before concurrency | not protected, single writer, happens-before by task creation order |
`volatile` is not used anywhere in src/ or include/ (grep).

## Specific items asked about
- arm_request_flag, disarm_request_flag, clear_enables_flag, arm_refused_flag: replaced by fields of `shared` under `guard` (see table). The old unlocked accesses are removed.
- sup.state / sup.reason: only modified by the supervisor under `guard`; read as a pair under `guard`.
- sample: written and read under `guard` as a whole struct.

## Critical sections
Contents: copying structs, `sup_step` (pure arithmetic, no loops over unbounded data), `gpio_set_level`. No blocking calls, no logging, no I2C inside any critical section. The supervisor does not call `health_all_ok` while holding `guard` (it takes the health spinlock separately); no nested spinlocks.

## Ordering and TOCTOU on the enable path
`expander_write(enable bit, high)`: takes `lock`, then checks the permit, then writes. The sampler clears the enables (also under `lock`) in every non-ARMED state after its read. Sequence "writer checks permit true, supervisor leaves ARMED and drops ARM, writer completes the write" ends with the enable cleared by the next sampler cycle (<= ~100 ms) while ARM is already low, so the rails are off throughout. Not a leak of power; a short interval where the shadow and register show high while not ARMED, which the sampler also flags (`enables_low` false) and the next ARM request would abort on.

## I2C driver concurrency
`i2c_master_cmd_begin` takes the port's `cmd_mux` with the caller's timeout (read in components/driver/i2c/i2c.c). Concurrent transactions are serialised; a caller may time out after 50 ms if another holds the bus. A false failure is possible when the CLI and sampler collide; consequences are fail-safe (sample invalid), see ARM_RACE_FINAL_REVIEW.md.

## Priority inversion / deadlock
- Locks: `guard` (short), `permit_guard` (short), `lock` (expander, held during I2C <= 50 ms per transaction), `api_lock` (CLI only). The supervisor takes only spinlocks. The sampler takes `lock` but never `api_lock`. The CLI takes `api_lock` then (via `interlock_*` helpers) only spinlocks; its `expander_write` takes `lock` outside `api_lock`-protected waits. No cycle.
- Priority inversion on `lock`: sampler (5) can wait for a CLI (1) holder of `lock` during an I2C transaction; FreeRTOS mutexes use priority inheritance. The supervisor (6) is unaffected.

## What this review does not establish
No formal proof, no race detector, no run on target. Interrupt contexts in IDF drivers were not reviewed. Stack sizes (3072) and task starvation under load were not measured. If any other task starts touching `expander_write` for enable bits, it is subject to the permit but not to `api_lock`.
