#include "supervisor_core.h"
#include <string.h>

static int32_t diff_u32(uint32_t a, uint32_t b)
{
    return (int32_t)(a - b);
}

static bool age_ok(const sup_sample_t *smp, uint32_t now_ms, int32_t max_age)
{
    int32_t age = diff_u32(now_ms, smp->time_ms);
    return age >= 0 && age <= max_age;
}

static bool precheck_sample_ok(const sup_sample_t *smp, uint32_t now_ms)
{
    if (!smp->valid) {
        return false;
    }
    if (!age_ok(smp, now_ms, SUP_ARM_SAMPLE_MAX_AGE_MS)) {
        return false;
    }
    if (!smp->enables_low || !smp->outputs_match) {
        return false;
    }
    if (smp->interlock_ok) {
        return false;
    }
    if (smp->loops_observable && !smp->loops_closed) {
        return false;
    }
    return true;
}

static void latch(sup_t *s, sup_state_t state, sup_reason_t reason)
{
    s->state = state;
    s->reason = reason;
}

void sup_init(sup_t *s, bool boot_ok)
{
    memset(s, 0, sizeof *s);
    s->state = boot_ok ? SUP_DISARMED : SUP_FAULT;
    s->reason = boot_ok ? SUP_REASON_NONE : SUP_REASON_BOOT;
}

static void abort_arming(sup_t *s, sup_out_t *out)
{
    latch(s, SUP_DISARMED, SUP_REASON_ARM_ABORTED);
    out->arm_level = false;
    out->arm_refused = true;
}

static void step_precheck(sup_t *s, const sup_in_t *in, sup_out_t *out, uint32_t now_ms)
{
    const sup_sample_t *smp = &in->sample;
    if (smp->seq != s->last_seq) {
        s->last_seq = smp->seq;
        bool acquired_after_request = diff_u32(smp->time_ms, s->request_ms) >= 0;
        if (acquired_after_request) {
            if (precheck_sample_ok(smp, now_ms)) {
                s->counted++;
            } else {
                abort_arming(s, out);
                return;
            }
        }
    } else if (diff_u32(now_ms, s->request_ms) > SUP_PRECHECK_TIMEOUT_MS) {
        abort_arming(s, out);
        return;
    }
    if (diff_u32(now_ms, s->request_ms) > SUP_PRECHECK_TIMEOUT_MS && s->counted < SUP_PRECHECK_SAMPLES) {
        abort_arming(s, out);
        return;
    }
    if (s->counted >= SUP_PRECHECK_SAMPLES) {
        s->state = SUP_ARMING;
        s->arming_start_ms = now_ms;
        s->arming_seq = smp->seq;
        s->counted = 0;
        out->arm_level = true;
    }
}

static void step_arming(sup_t *s, const sup_in_t *in, sup_out_t *out, uint32_t now_ms)
{
    const sup_sample_t *smp = &in->sample;
    out->arm_level = true;
    if (smp->seq != s->last_seq) {
        s->last_seq = smp->seq;
        bool after_settle = diff_u32(smp->time_ms, s->arming_start_ms + SUP_ARM_SETTLE_MS) >= 0;
        if (after_settle) {
            if (!smp->valid) {
                latch(s, SUP_FAULT, SUP_REASON_I2C);
            } else if (!age_ok(smp, now_ms, SUP_ARM_SAMPLE_MAX_AGE_MS)) {
                latch(s, SUP_FAULT, SUP_REASON_STALE_SAMPLE);
            } else if (!smp->enables_low) {
                latch(s, SUP_FAULT, SUP_REASON_ENABLES_HIGH);
            } else if (!smp->outputs_match) {
                latch(s, SUP_FAULT, SUP_REASON_OUTPUT_MISMATCH);
            } else if (!smp->interlock_ok) {
                latch(s, SUP_OPEN, SUP_REASON_INTERLOCK_OPEN);
            } else {
                s->counted++;
            }
            if (s->state != SUP_ARMING) {
                out->arm_level = false;
                return;
            }
        }
    }
    if (s->counted >= SUP_ARMING_SAMPLES) {
        s->state = SUP_ARMED;
        return;
    }
    if (diff_u32(now_ms, s->arming_start_ms) > SUP_ARM_TIMEOUT_MS) {
        latch(s, SUP_FAULT, SUP_REASON_ARM_TIMEOUT);
        out->arm_level = false;
    }
}

static void step_armed(sup_t *s, const sup_in_t *in, sup_out_t *out, uint32_t now_ms)
{
    const sup_sample_t *smp = &in->sample;
    out->arm_level = true;
    if (!smp->valid) {
        latch(s, SUP_FAULT, SUP_REASON_I2C);
    } else if (!age_ok(smp, now_ms, SUP_SAMPLE_MAX_AGE_MS)) {
        latch(s, SUP_FAULT, SUP_REASON_STALE_SAMPLE);
    } else if (!smp->outputs_match) {
        latch(s, SUP_FAULT, SUP_REASON_OUTPUT_MISMATCH);
    } else if (!smp->interlock_ok) {
        latch(s, SUP_OPEN, SUP_REASON_INTERLOCK_OPEN);
    }
    if (s->state != SUP_ARMED) {
        out->arm_level = false;
    }
}

void sup_step(sup_t *s, const sup_in_t *in, sup_out_t *out, uint32_t now_ms)
{
    out->service_wdi = in->tasks_healthy;
    out->arm_level = false;
    out->clear_enables = false;
    out->enables_permitted = false;
    out->arm_refused = false;

    if (!in->tasks_healthy && s->state != SUP_FAULT) {
        latch(s, SUP_FAULT, SUP_REASON_TASK_STALL);
    }
    if (in->sample.bad_streak >= SUP_BAD_STREAK_FAULT && s->state != SUP_FAULT) {
        latch(s, SUP_FAULT, SUP_REASON_I2C);
    }

    if (in->disarm_request) {
        if (s->state == SUP_PRECHECK || s->state == SUP_ARMING || s->state == SUP_ARMED) {
            latch(s, SUP_DISARMED, SUP_REASON_NONE);
        }
    }

    if (in->arm_request) {
        if (s->state == SUP_DISARMED && !in->disarm_request) {
            s->state = SUP_PRECHECK;
            s->reason = SUP_REASON_NONE;
            s->request_ms = now_ms;
            s->request_seq = in->sample.seq;
            s->last_seq = in->sample.seq;
            s->counted = 0;
            goto done;
        }
        out->arm_refused = true;
    }

    switch (s->state) {
    case SUP_PRECHECK:
        step_precheck(s, in, out, now_ms);
        break;
    case SUP_ARMING:
        step_arming(s, in, out, now_ms);
        break;
    case SUP_ARMED:
        step_armed(s, in, out, now_ms);
        break;
    default:
        break;
    }

    if ((s->state == SUP_OPEN || s->state == SUP_FAULT) && in->disarm_request && in->tasks_healthy &&
        in->sample.valid && age_ok(&in->sample, now_ms, SUP_ARM_SAMPLE_MAX_AGE_MS) && in->sample.enables_low &&
        in->sample.good_streak >= SUP_GOOD_STREAK_RECOVER) {
        latch(s, SUP_DISARMED, SUP_REASON_NONE);
    }

done:
    out->enables_permitted = (s->state == SUP_ARMED);
    out->arm_level = out->arm_level && (s->state == SUP_ARMING || s->state == SUP_ARMED);
    out->clear_enables = (s->state != SUP_ARMED);
}

const char *sup_state_name(sup_state_t state)
{
    switch (state) {
    case SUP_DISARMED: return "DISARMED";
    case SUP_PRECHECK: return "PRECHECK";
    case SUP_ARMING: return "ARMING";
    case SUP_ARMED: return "ARMED";
    case SUP_OPEN: return "OPEN";
    default: return "FAULT";
    }
}

const char *sup_reason_name(sup_reason_t reason)
{
    switch (reason) {
    case SUP_REASON_NONE: return "none";
    case SUP_REASON_TASK_STALL: return "critical task stalled";
    case SUP_REASON_I2C: return "expander I2C failure";
    case SUP_REASON_STALE_SAMPLE: return "sample stale";
    case SUP_REASON_INTERLOCK_OPEN: return "interlock open";
    case SUP_REASON_ARM_TIMEOUT: return "arming timeout";
    case SUP_REASON_ENABLES_HIGH: return "module enables not low";
    case SUP_REASON_OUTPUT_MISMATCH: return "expander output register mismatch";
    case SUP_REASON_ARM_ABORTED: return "arming aborted: stale or inconsistent sample";
    default: return "boot verification failed";
    }
}
