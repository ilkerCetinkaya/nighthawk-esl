#include <stdio.h>
#include "cli.h"
#include "driver/gpio.h"
#include "driver/usb_serial_jtag.h"
#include "esp_log.h"
#include "expander.h"
#include "health.h"
#include "interlock.h"
#include "measure.h"
#include "nvs_flash.h"
#include "pins.h"
#include "storage.h"

static const char *TAG = "nighthawk";

void app_main(void)
{
    interlock_safe_gpio_init();
    nvs_flash_init();
    esp_err_t expander_err = expander_init();
    bool expander_ready = expander_err == ESP_OK;
    if (!expander_ready) {
        ESP_LOGE(TAG, "expander init/verify failed: %s, system stays disarmed in FAULT", esp_err_to_name(expander_err));
    }
    interlock_start(expander_ready);
    health_progress(HEALTH_CLI);
    if (expander_ready) {
        expander_write(EXP_RF1_RST, false);
        expander_write(EXP_RF2_RST, false);
        expander_write(EXP_LED_FAULT, false);
    }
    if (measure_init() != ESP_OK) {
        ESP_LOGE(TAG, "RSSI ADC init failed");
    }
    health_progress(HEALTH_CLI);
    esp_err_t err = storage_init();
    if (err != ESP_OK) {
        ESP_LOGW(TAG, "storage not mounted: %s", esp_err_to_name(err));
        expander_write(EXP_LED_FAULT, true);
    }
    health_progress(HEALTH_CLI);
    expander_write(EXP_LED_STATUS, expander_ready);
    cli_start();
}
