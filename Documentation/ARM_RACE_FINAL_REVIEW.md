# ARM_RACE_FINAL_REVIEW

Evidence labels: [SRC] source, [SIM] host simulation (a model, not hardware), [DS] datasheet, [CALC] calculation. No hardware measurement exists.

## Revision note (audit6): PRECHECK acceptance corrected
An independent review found that `step_precheck()` counted a sample after checking only `valid`, `enables_low` and age. The interlock reading and the output-register/shadow match were first checked in ARMING, i.e. after ARM had risen. Corrected in supervisor_core.c (`precheck_sample_ok`). Every one of the three PRECHECK samples must now satisfy: (1) valid acquisition; (2) acquired after the request (`time_ms >= request_ms`; earlier samples are ignored, not counted); (3) age `0 <= age <= 250 ms` (negative age = timestamp in the future is rejected, 32-bit wraparound preserved); (4) interlock condition, see below; (5) both enable output-register bits low and (6) both physical enable pins low (`enables_low`, computed from the output register and the input port); (7) output register equals the shadow register. Any failing post-request sample aborts arming (state DISARMED, reason ARM_ABORTED); ARM does not rise.
Deviation from the requested condition 4 ("interlock input confirmed HIGH") and why: on REV A, INTERLOCK_OK = ARM AND EN AND LOOP_OK AND ENCL_OK ([N] design.py U8/U9/U10). In PRECHECK ARM is low, so INTERLOCK_OK is LOW by construction whatever the state of the loops, and LOOP_OK / ENCL_OK are not wired to anything the MCU can read (only to U9, J6 and their pull-downs). Requiring HIGH would make arming impossible. What is implemented instead: (a) INTERLOCK_OK must read LOW with ARM low (a HIGH reading means a stuck/shorted gate chain or ARM unexpectedly high -> abort); (b) a `loops_observable` / `loops_closed` pair in the sample: where the hardware exposes the loop inputs (REV B proposal) PRECHECK requires them closed; on REV A `loops_observable` is false. On REV A an open loop is therefore found in ARMING (the first qualifying sample after ARM rises and settles reads INTERLOCK_OK low -> OPEN). This is safe because with the loop open the AND chain keeps the module rails off: raising ARM cannot power a module. The safety-relevant PRECHECK property (enables verified low before ARM rises) is unchanged. The sampler also now takes the supervisor timestamp inside the same critical section as the sample copy; otherwise a sample published after the supervisor's earlier clock read could legitimately look "from the future" and be rejected by the new age check.

## Path traced
CLI `interlock arm` -> `interlock_request_arm()` (api mutex, then under the spinlock: refuse if disarm pending or state != DISARMED, else set `arm_request`) -> supervisor pass (50 ms) -> `sup_step`: DISARMED -> PRECHECK (ARM stays low) -> sampler acquisitions (100 ms) with sequence numbers -> after 3 distinct valid post-request samples whose enable output bits AND enable pins read low -> ARMING (ARM high) -> after 60 ms settle, 2 distinct qualifying samples (valid, fresh, enables low, output register equals shadow, INTERLOCK_OK high) -> ARMED -> enable permit granted.
Typical duration [SIM]: about 0.6 s. CLI waits up to 1.5 s.

## Requirement-by-requirement
| Requirement | Mechanism | Evidence |
|---|---|---|
| Samples acquired after the current ARM request | `sample.time_ms` = start of the sampler cycle; PRECHECK counts only samples with `time_ms >= request_ms` and `seq` different from the last one seen; earlier samples are ignored, not counted | [SRC] supervisor_core.c step_precheck; [SIM] T10 |
| Defined maximum age on every sample | 250 ms at PRECHECK and ARMING consumption, 400 ms while ARMED, and age must not be negative (future timestamp rejected, wraparound-safe); failing -> abort (PRECHECK), FAULT (ARMING/ARMED) | [SRC]; [SIM] T10 |
| Three successful readings are distinct acquisitions | `seq` increments once per sampler cycle; a repeated `seq` is not counted (test: same sample twice counts once) | [SIM] T10 |
| No previous sample reused | request records `request_seq`/`request_ms`; ARMING records `arming_seq` and requires `time_ms >= arming_start + 60 ms` | [SIM] T10 |
| Interlock/outputs consistent before ARM rises (PRECHECK) | `precheck_sample_ok`: INTERLOCK_OK must be LOW with ARM low (REV A), loops closed if observable, `outputs_match` required | [SRC]; [SIM] T12, T13 |
| Enable outputs verified LOW before ARMED | `enables_low` requires output-register bits = 0 AND input-port (pin) bits = 0, in PRECHECK samples and again in ARMING samples | [SRC]; [SIM] T5, T5b, T9, T10 |
| Physical enable pins checked | input port read (pin level), not only output register | [SRC] interlock.c sampler |
| Concurrent ARM/DISARM cannot bypass | callers serialised by a mutex; all request state under one spinlock; in `sup_step` a pending disarm refuses arm and wins; arm refused in every state except DISARMED | [SRC]; [SIM] T10 (arm+disarm same pass; arm in PRECHECK/ARMING/ARMED/OPEN/FAULT) |
| Stale or inconsistent sample aborts arming | PRECHECK: invalid, enable high or too old -> state DISARMED, reason ARM_ABORTED, refused counter incremented; ARMING: any bad qualifying sample -> FAULT/OPEN with ARM low | [SIM] T10, T11 |

## Where ARM can rise
Only from PRECHECK after three qualifying samples, i.e. only with enables verified low at three distinct instants after the request. Tests: ARM never rises with a stalled sampler or a frozen sample (T10, T11), nor when enables cannot be cleared (T5).

## The 150 ms exposure: what is eliminated and what is not
- Eliminated (firmware causes): the firmware enable path is refused unless the state is ARMED (permit in expander.c; T5c). Nothing in the firmware can raise an enable while ARM is rising or high but unverified. The earlier stale-sample window is gone because ARM does not rise until fresh samples exist.
- Not eliminated (non-firmware causes): an enable bit raised by a bit flip, ESD or hardware fault between the last PRECHECK sample and the first ARMING sample. The sampler reads first, then clears. [SIM] T5b sweeps the raise time from 0 to 800 ms after the request in 7 ms steps: in no case did the state end ARMED when the bit was raised before ARMED; the worst module power exposure was 98 ms (rail on while ARM high until the ARMING sample / clear). Firmware cannot prevent that case; it needs hardware (REV_B_DEADMAN_DESIGN.md: independent permit, LDO enable gating, rail sensing).

## Remaining risks
1. The 98 ms figure is a model result; real timing depends on I2C transaction time and task scheduling.
2. A raised enable bit while ARM is already high and the state is ARMED is a legitimate configuration; it is not an error.
3. `INTERLOCK_OK` is read through the same expander; if the TCA9555 returned wrong-but-plausible data both would be wrong. REV B adds a second observation path.

## Tests for the audit6 correction [SIM]
T12 mutates, in each of the three PRECHECK sample positions, each of: invalid acquisition, enable high, output mismatch, interlock reading HIGH with ARM low, loop observable and open, stale timestamp, future timestamp: 21 cases, each aborted with ARM never high. Three fully valid samples (loops observable and closed) reach ARMING. Wraparound: a PRECHECK that crosses 2^32 succeeds; a stale sample across the boundary is rejected. Future timestamps are rejected in ARMING and ARMED. T13 (model with the REV A interlock behaviour): enable pin HIGH and output mismatch during PRECHECK keep ARM low; an open loop on REV A is caught in ARMING (state OPEN, rails off). Check of test value: with the old acceptance condition substituted, the new tests fail (13 failures); with the correction they pass (750 checks, 0 failures).
