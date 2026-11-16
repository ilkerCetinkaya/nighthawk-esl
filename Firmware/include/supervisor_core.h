#pragma once
#include <stdbool.h>
#include <stdint.h>

#define SUP_SAMPLE_MAX_AGE_MS 400
#define SUP_ARM_SAMPLE_MAX_AGE_MS 250
#define SUP_PRECHECK_SAMPLES 3
#define SUP_PRECHECK_TIMEOUT_MS 700
#define SUP_ARMING_SAMPLES 2
#define SUP_ARM_SETTLE_MS 60
#define SUP_ARM_TIMEOUT_MS 500
#define SUP_BAD_STREAK_FAULT 3
#define SUP_GOOD_STREAK_RECOVER 3

typedef enum {
    SUP_DISARMED,
    SUP_PRECHECK,
    SUP_ARMING,
    SUP_ARMED,
    SUP_OPEN,
    SUP_FAULT
} sup_state_t;

typedef enum {
    SUP_REASON_NONE,
    SUP_REASON_TASK_STALL,
    SUP_REASON_I2C,
    SUP_REASON_STALE_SAMPLE,
    SUP_REASON_INTERLOCK_OPEN,
    SUP_REASON_ARM_TIMEOUT,
    SUP_REASON_ENABLES_HIGH,
    SUP_REASON_OUTPUT_MISMATCH,
    SUP_REASON_ARM_ABORTED,
    SUP_REASON_BOOT
} sup_reason_t;

typedef struct {
    bool valid;
    bool interlock_ok;
    bool enables_low;
    bool outputs_match;
    bool loops_observable;
    bool loops_closed;
    uint8_t good_streak;
    uint8_t bad_streak;
    uint32_t seq;
    uint32_t time_ms;
} sup_sample_t;

typedef struct {
    bool tasks_healthy;
    sup_sample_t sample;
    bool arm_request;
    bool disarm_request;
} sup_in_t;

typedef struct {
    bool service_wdi;
    bool arm_level;
    bool clear_enables;
    bool enables_permitted;
    bool arm_refused;
} sup_out_t;

typedef struct {
    sup_state_t state;
    sup_reason_t reason;
    uint32_t request_ms;
    uint32_t request_seq;
    uint32_t last_seq;
    uint32_t arming_start_ms;
    uint32_t arming_seq;
    uint8_t counted;
} sup_t;

void sup_init(sup_t *s, bool boot_ok);
void sup_step(sup_t *s, const sup_in_t *in, sup_out_t *out, uint32_t now_ms);
const char *sup_state_name(sup_state_t state);
const char *sup_reason_name(sup_reason_t reason);
