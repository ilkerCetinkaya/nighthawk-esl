#include "measure.h"
#include "esp_adc/adc_oneshot.h"
#include "pins.h"

static adc_oneshot_unit_handle_t unit;

esp_err_t measure_init(void)
{
    adc_oneshot_unit_init_cfg_t init = {.unit_id = ADC_UNIT_1};
    esp_err_t err = adc_oneshot_new_unit(&init, &unit);
    if (err != ESP_OK) {
        return err;
    }
    adc_oneshot_chan_cfg_t cfg = {.atten = ADC_ATTEN_DB_12, .bitwidth = ADC_BITWIDTH_12};
    err = adc_oneshot_config_channel(unit, ADC_CH_RSSI, &cfg);
    return err;
}

static int sample_mv(int channel)
{
    int sum = 0;
    int raw = 0;
    for (int i = 0; i < 16; i++) {
        if (adc_oneshot_read(unit, channel, &raw) != ESP_OK) {
            return -1;
        }
        sum += raw;
    }
    return (sum / 16) * 3100 / 4095;
}

int measure_rssi_mv(void)
{
    return sample_mv(ADC_CH_RSSI);
}
