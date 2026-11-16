#include "interlock.h"
#include "driver/gpio.h"
#include "esp_err.h"
#include "esp_rom_sys.h"
#include "esp_system.h"
#include "esp_timer.h"
#include "expander.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "freertos/task.h"
#include "health.h"
#include "pins.h"

#define SAMPLER_PERIOD_MS 100
#define SUPERVISOR_PERIOD_MS 50
#define WDI_PULSE_US 5
#define ARM_WAIT_MS 1500
#define DISARM_WAIT_MS 1500

typedef struct {
    sup_t sup;
    sup_sample_t sample;
    bool arm_request;
    bool disarm_pending;
    bool clear_enables;
    uint32_t refused_count;
} shared_t;

static portMUX_TYPE guard = portMUX_INITIALIZER_UNLOCKED;
static shared_t shared;
static SemaphoreHandle_t api_lock;
static bool started;

static uint32_t now_ms(void)
{
    return (uint32_t)(esp_timer_get_time() / 1000);
}

static void sampler_task(void *arg)
{
    const uint16_t enable_mask = (uint16_t)((1u << EXP_RF1_EN) | (1u << EXP_RF2_EN));
    uint8_t good = 0;
    uint8_t bad = 0;
    uint32_t seq = 0;
    for (;;) {
        uint32_t cycle_start = now_ms();
        uint16_t inputs = 0;
        uint16_t outputs = 0;
        bool match = false;
        bool ok = expander_read_all(&inputs) == ESP_OK && expander_read_outputs(&outputs, &match) == ESP_OK;
        if (ok) {
            good = good < 255 ? good + 1 : good;
            bad = 0;
        } else {
            bad = bad < 255 ? bad + 1 : bad;
            good = 0;
        }
        sup_sample_t fresh = {
            .valid = ok,
            .interlock_ok = ok && ((inputs >> EXP_INTERLOCK_OK) & 1u),
            .enables_low = ok && (outputs & enable_mask) == 0 && (inputs & enable_mask) == 0,
            .outputs_match = ok && match,
            .loops_observable = false,
            .loops_closed = false,
            .good_streak = good,
            .bad_streak = bad,
            .seq = ++seq,
            .time_ms = cycle_start,
        };
        portENTER_CRITICAL(&guard);
        shared.sample = fresh;
        bool want_clear = shared.clear_enables;
        portEXIT_CRITICAL(&guard);
        if (want_clear) {
            expander_write(EXP_RF1_EN, false);
            expander_write(EXP_RF2_EN, false);
        }
        health_progress(HEALTH_SAMPLER);
        vTaskDelay(pdMS_TO_TICKS(SAMPLER_PERIOD_MS));
    }
}

static void supervisor_task(void *arg)
{
    for (;;) {
        sup_in_t in;
        sup_out_t out;
        in.tasks_healthy = health_all_ok(NULL);
        portENTER_CRITICAL(&guard);
        in.sample = shared.sample;
        uint32_t now = now_ms();
        in.arm_request = shared.arm_request;
        in.disarm_request = shared.disarm_pending;
        shared.arm_request = false;
        sup_step(&shared.sup, &in, &out, now);
        shared.clear_enables = out.clear_enables;
        if (out.arm_refused) {
            shared.refused_count++;
        }
        gpio_set_level(PIN_ARM, out.arm_level ? 1 : 0);
        portEXIT_CRITICAL(&guard);
        expander_set_enable_permit(out.enables_permitted);
        if (out.service_wdi) {
            gpio_set_level(PIN_WDI, 0);
            esp_rom_delay_us(WDI_PULSE_US);
            gpio_set_level(PIN_WDI, 1);
        }
        vTaskDelay(pdMS_TO_TICKS(SUPERVISOR_PERIOD_MS));
    }
}

void interlock_safe_gpio_init(void)
{
    gpio_set_level(PIN_ARM, 0);
    gpio_config_t arm = {
        .pin_bit_mask = 1ULL << PIN_ARM,
        .mode = GPIO_MODE_OUTPUT,
    };
    ESP_ERROR_CHECK(gpio_config(&arm));
    gpio_set_level(PIN_ARM, 0);
}

void interlock_start(bool expander_ready)
{
    if (started) {
        return;
    }
    api_lock = xSemaphoreCreateMutex();
    if (api_lock == NULL) {
        gpio_set_level(PIN_ARM, 0);
        abort();
    }
    gpio_config_t wdi = {
        .pin_bit_mask = 1ULL << PIN_WDI,
        .mode = GPIO_MODE_OUTPUT,
    };
    ESP_ERROR_CHECK(gpio_config(&wdi));
    gpio_set_level(PIN_WDI, 1);
    sup_init(&shared.sup, expander_ready);
    health_init();
    if (xTaskCreate(sampler_task, "sampler", 3072, NULL, 5, NULL) != pdPASS ||
        xTaskCreate(supervisor_task, "supervisor", 3072, NULL, 6, NULL) != pdPASS) {
        gpio_set_level(PIN_ARM, 0);
        abort();
    }
    started = true;
}

void interlock_snapshot(interlock_snapshot_t *out)
{
    portENTER_CRITICAL(&guard);
    out->state = shared.sup.state;
    out->reason = shared.sup.reason;
    out->sample = shared.sample;
    portEXIT_CRITICAL(&guard);
}

interlock_state_t interlock_state(void)
{
    interlock_snapshot_t snap;
    interlock_snapshot(&snap);
    return snap.state;
}

sup_reason_t interlock_reason(void)
{
    interlock_snapshot_t snap;
    interlock_snapshot(&snap);
    return snap.reason;
}

bool interlock_hardware_ok(void)
{
    interlock_snapshot_t snap;
    interlock_snapshot(&snap);
    return snap.sample.valid && snap.sample.interlock_ok;
}

bool interlock_request_arm(void)
{
    if (!started) {
        return false;
    }
    xSemaphoreTake(api_lock, portMAX_DELAY);
    bool armed = false;
    portENTER_CRITICAL(&guard);
    bool busy = shared.disarm_pending || shared.sup.state != SUP_DISARMED;
    uint32_t refused_before = shared.refused_count;
    if (!busy) {
        shared.arm_request = true;
    }
    portEXIT_CRITICAL(&guard);
    if (!busy) {
        for (int waited = 0; waited < ARM_WAIT_MS; waited += SUPERVISOR_PERIOD_MS) {
            vTaskDelay(pdMS_TO_TICKS(SUPERVISOR_PERIOD_MS));
            health_progress(HEALTH_CLI);
            interlock_snapshot_t snap;
            interlock_snapshot(&snap);
            portENTER_CRITICAL(&guard);
            bool refused = shared.refused_count != refused_before;
            portEXIT_CRITICAL(&guard);
            if (snap.state == SUP_ARMED) {
                armed = true;
                break;
            }
            if (refused || snap.state == SUP_OPEN || snap.state == SUP_FAULT) {
                break;
            }
        }
    }
    xSemaphoreGive(api_lock);
    return armed;
}

void interlock_disarm(void)
{
    if (!started) {
        return;
    }
    xSemaphoreTake(api_lock, portMAX_DELAY);
    portENTER_CRITICAL(&guard);
    shared.disarm_pending = true;
    portEXIT_CRITICAL(&guard);
    for (int waited = 0; waited < DISARM_WAIT_MS; waited += SUPERVISOR_PERIOD_MS) {
        vTaskDelay(pdMS_TO_TICKS(SUPERVISOR_PERIOD_MS));
        health_progress(HEALTH_CLI);
        if (interlock_state() == SUP_DISARMED) {
            break;
        }
    }
    portENTER_CRITICAL(&guard);
    shared.disarm_pending = false;
    portEXIT_CRITICAL(&guard);
    xSemaphoreGive(api_lock);
}

const char *interlock_state_name(interlock_state_t state)
{
    return sup_state_name(state);
}
