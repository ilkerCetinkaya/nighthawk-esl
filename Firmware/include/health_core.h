#pragma once
#include <stdbool.h>
#include <stdint.h>

#define HC_MAX_TASKS 4

typedef enum {
    HC_FREE,
    HC_IDLE,
    HC_BUSY
} hc_mode_t;

typedef struct {
    const char *name;
    hc_mode_t mode;
    uint32_t deadline_ms;
    uint32_t last_progress_ms;
    uint32_t progress_count;
} hc_task_t;

typedef struct {
    hc_task_t task[HC_MAX_TASKS];
    int count;
} hc_t;

void hc_init(hc_t *h);
int hc_register(hc_t *h, const char *name, uint32_t deadline_ms, uint32_t now_ms);
void hc_progress(hc_t *h, int id, uint32_t now_ms);
void hc_set_idle(hc_t *h, int id);
void hc_set_busy(hc_t *h, int id, uint32_t deadline_ms, uint32_t now_ms);
bool hc_evaluate(const hc_t *h, uint32_t now_ms, int expected_tasks, int *failed_id);
