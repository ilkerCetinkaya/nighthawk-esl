#pragma once
#include <stdbool.h>
#include <stdint.h>
#include "health_core.h"

typedef enum {
    HEALTH_SAMPLER = 0,
    HEALTH_CLI = 1,
    HEALTH_TASK_COUNT
} health_id_t;

#define HEALTH_SAMPLER_DEADLINE_MS 500
#define HEALTH_BOOT_DEADLINE_MS 10000
#define HEALTH_COMMAND_DEADLINE_MS 5000

void health_init(void);
void health_progress(health_id_t id);
void health_set_idle(health_id_t id);
void health_set_busy(health_id_t id, uint32_t deadline_ms);
bool health_all_ok(int *failed_id);
void health_snapshot(hc_t *out);
