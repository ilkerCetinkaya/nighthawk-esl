#include "health.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"

static hc_t core;
static portMUX_TYPE guard = portMUX_INITIALIZER_UNLOCKED;

static uint32_t now_ms(void)
{
    return (uint32_t)(esp_timer_get_time() / 1000);
}

void health_init(void)
{
    uint32_t now = now_ms();
    portENTER_CRITICAL(&guard);
    hc_init(&core);
    hc_register(&core, "sampler", HEALTH_SAMPLER_DEADLINE_MS, now);
    hc_register(&core, "cli", HEALTH_BOOT_DEADLINE_MS, now);
    portEXIT_CRITICAL(&guard);
}

void health_progress(health_id_t id)
{
    uint32_t now = now_ms();
    portENTER_CRITICAL(&guard);
    hc_progress(&core, id, now);
    portEXIT_CRITICAL(&guard);
}

void health_set_idle(health_id_t id)
{
    portENTER_CRITICAL(&guard);
    hc_set_idle(&core, id);
    portEXIT_CRITICAL(&guard);
}

void health_set_busy(health_id_t id, uint32_t deadline_ms)
{
    uint32_t now = now_ms();
    portENTER_CRITICAL(&guard);
    hc_set_busy(&core, id, deadline_ms, now);
    portEXIT_CRITICAL(&guard);
}

bool health_all_ok(int *failed_id)
{
    uint32_t now = now_ms();
    portENTER_CRITICAL(&guard);
    bool ok = hc_evaluate(&core, now, HEALTH_TASK_COUNT, failed_id);
    portEXIT_CRITICAL(&guard);
    return ok;
}

void health_snapshot(hc_t *out)
{
    portENTER_CRITICAL(&guard);
    *out = core;
    portEXIT_CRITICAL(&guard);
}
