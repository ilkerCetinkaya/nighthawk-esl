#pragma once
#include <stdbool.h>
#include "supervisor_core.h"

typedef sup_state_t interlock_state_t;

typedef struct {
    sup_state_t state;
    sup_reason_t reason;
    sup_sample_t sample;
} interlock_snapshot_t;

void interlock_safe_gpio_init(void);
void interlock_start(bool expander_ready);
bool interlock_request_arm(void);
void interlock_disarm(void);
void interlock_snapshot(interlock_snapshot_t *out);
interlock_state_t interlock_state(void);
sup_reason_t interlock_reason(void);
bool interlock_hardware_ok(void);
const char *interlock_state_name(interlock_state_t state);
