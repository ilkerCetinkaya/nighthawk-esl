#include "health_core.h"
#include <string.h>

void hc_init(hc_t *h)
{
    memset(h, 0, sizeof *h);
}

int hc_register(hc_t *h, const char *name, uint32_t deadline_ms, uint32_t now_ms)
{
    if (h->count >= HC_MAX_TASKS) {
        return -1;
    }
    int id = h->count++;
    h->task[id].name = name;
    h->task[id].mode = HC_BUSY;
    h->task[id].deadline_ms = deadline_ms;
    h->task[id].last_progress_ms = now_ms;
    h->task[id].progress_count = 0;
    return id;
}

void hc_progress(hc_t *h, int id, uint32_t now_ms)
{
    if (id < 0 || id >= h->count) {
        return;
    }
    h->task[id].last_progress_ms = now_ms;
    h->task[id].progress_count++;
}

void hc_set_idle(hc_t *h, int id)
{
    if (id < 0 || id >= h->count) {
        return;
    }
    h->task[id].mode = HC_IDLE;
}

void hc_set_busy(hc_t *h, int id, uint32_t deadline_ms, uint32_t now_ms)
{
    if (id < 0 || id >= h->count) {
        return;
    }
    h->task[id].deadline_ms = deadline_ms;
    h->task[id].last_progress_ms = now_ms;
    h->task[id].mode = HC_BUSY;
}

bool hc_evaluate(const hc_t *h, uint32_t now_ms, int expected_tasks, int *failed_id)
{
    if (h->count < expected_tasks) {
        if (failed_id) {
            *failed_id = h->count;
        }
        return false;
    }
    for (int i = 0; i < h->count; i++) {
        const hc_task_t *t = &h->task[i];
        if (t->mode == HC_BUSY && (uint32_t)(now_ms - t->last_progress_ms) > t->deadline_ms) {
            if (failed_id) {
                *failed_id = i;
            }
            return false;
        }
    }
    return true;
}
