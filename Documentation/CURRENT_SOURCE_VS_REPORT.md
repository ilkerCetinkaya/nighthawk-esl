# CURRENT_SOURCE_VS_REPORT

Method: the source files as they were at the start of this task (audit4 state) were read line by line (interlock.c, supervisor_core.c, expander.c, main.c) and compared with what the earlier reports claimed. Labels: [SRC] read in source, [SIM] host simulation, [BUILD] `idf.py build`, [DS] datasheet. Nothing was measured on hardware.

## The three reviewed issues in the audit4 source
| Issue | State in audit4 source | Verdict |
|---|---|---|
| 1. ARMING sample freshness | `sup_step` accepted arm in DISARMED from any `fw.sample` that was <= 400 ms old with `good_streak >= 3`. The streak could consist of samples taken before the request; samples were not required to be distinct acquisitions after the request; there was no sequence number. | NOT fixed. The ARM_TRANSITION_RACE_ANALYSIS.md statement "narrowed, not removed" was accurate but the residual was larger than described: the first ARM rise could be based entirely on pre-request data |
| 2. FreeRTOS shared state | `arm_request_flag`, `disarm_request_flag`, `clear_enables_flag`, `arm_refused_flag` were `static volatile bool`; the CLI wrote `arm_request_flag`, `disarm_request_flag` and read `arm_refused_flag` outside any critical section; the sampler read `clear_enables_flag` unlocked; `sup.state`/`sup.reason` were read unlocked by the CLI (state and reason could be seen from different passes); only `sample` was under the spinlock | NOT fixed. `volatile` was used as a substitute for synchronisation. Concurrent arm and disarm callers were not arbitrated (arm and disarm both pending would take the arm path). The refused flag could be consumed from an earlier request |
| 3. Initialisation order | `app_main`: `interlock_init()` (which created the sampler and supervisor tasks) ran BEFORE `expander_init()`. The sampler calls `expander_read_outputs()`, which in audit4 took the expander mutex `lock`; `lock` was created inside `expander_init()`. | NOT fixed, and worse than the report assumed: a sampler cycle before `expander_init()` would call `xSemaphoreTake(NULL)` (null handle). This defect was introduced in the previous turn when the mutex was added to `expander_read_outputs` |

## Report statements that did not match the source
| Report | Statement | Source reality |
|---|---|---|
| FIRMWARE_BUILD_REPORT / CRITICAL_AUDIT C6 | "interlock_init() (ARM low) now runs before expander init in app_main" presented as a fix | true, but it also started the tasks early (issue 3). The statement was incomplete |
| ARM_TRANSITION_RACE_ANALYSIS R2/R5/R7 | R5 "closed", R7 "acceptable" | R5 (read-back vs shadow under mutex) was correct. R7 ignored that the request flags were unsynchronised |
| WATCHDOG_TASK_HEALTH_MATRIX | "sampler cycle worst case 250 ms" | with two writes now added after the reads it is 100 ms period + up to 4 x 50 ms transactions = 300 ms; deadline 500 ms still holds |
| FAILURE_MODE_MATRIX row 6 and FIRMWARE_TEST_REPORT | counts "122 checks" | superseded: 720 checks after this revision (the T5b sweep contributes ~115 of them) |
| Previous reports | "no volatile as synchronisation" not claimed, but not met | now met: no `volatile` remains in src/ or include/ (grep) |

## Additional discrepancy found while reviewing
WDI was toggled as a level (`level ^= 1`) every 50 ms, i.e. one falling edge per 100 ms, while the review documents reasoned with a 50 ms edge period. Fixed: a 5 us low pulse per pass.

## What changed in this revision (details in the other five documents)
- supervisor_core.c rewritten: new state PRECHECK, sample sequence numbers, three distinct post-request samples before ARM can rise, two distinct post-settle samples before ARMED, ages checked at every consumption, arm refused in every state except DISARMED, disarm priority, failed boot verification starts in FAULT.
- interlock.c rewritten: all cross-task state in one structure guarded by one spinlock; request/response through that structure; callers serialised by a mutex; consistent snapshots; no `volatile`.
- expander.c: enable-high writes refused unless the supervisor grants a permit (ARMED only); boot verification of config/output/pin registers; null-mutex guards.
- main.c / interlock.c: ordering fixed; failures leave ARM low (see INITIALIZATION_SEQUENCE_REVIEW.md).

## Older documents now superseded
ARM_TRANSITION_RACE_ANALYSIS.md -> ARM_RACE_FINAL_REVIEW.md; FIRMWARE_TEST_REPORT.md -> UPDATED_FIRMWARE_TEST_REPORT.md. WATCHDOG_TASK_HEALTH_MATRIX.md remains valid except the states list gained PRECHECK and the sampler cycle time (above).
