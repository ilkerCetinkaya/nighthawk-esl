#include "expander.h"
#include "driver/i2c.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "pins.h"

#define PORT I2C_NUM_0
#define REG_INPUT0 0x00
#define REG_OUTPUT0 0x02
#define REG_CONFIG0 0x06

static uint16_t output_shadow = 0x0000;
static uint16_t config_shadow = 0xFFFF;
static SemaphoreHandle_t lock;
static portMUX_TYPE permit_guard = portMUX_INITIALIZER_UNLOCKED;
static bool enable_permit;

#define ENABLE_MASK ((uint16_t)((1u << EXP_RF1_EN) | (1u << EXP_RF2_EN)))

static esp_err_t read_reg16(uint8_t reg, uint16_t *value)
{
    uint8_t buf[2] = {0, 0};
    esp_err_t err = i2c_master_write_read_device(PORT, EXP_I2C_ADDR, &reg, 1, buf, 2, pdMS_TO_TICKS(50));
    if (err == ESP_OK) {
        *value = (uint16_t)(buf[0] | (buf[1] << 8));
    }
    return err;
}

static bool permit_read(void)
{
    portENTER_CRITICAL(&permit_guard);
    bool value = enable_permit;
    portEXIT_CRITICAL(&permit_guard);
    return value;
}

void expander_set_enable_permit(bool permitted)
{
    portENTER_CRITICAL(&permit_guard);
    enable_permit = permitted;
    portEXIT_CRITICAL(&permit_guard);
}

static esp_err_t write_reg16(uint8_t reg, uint16_t value)
{
    uint8_t buf[3] = {reg, (uint8_t)(value & 0xFF), (uint8_t)(value >> 8)};
    return i2c_master_write_to_device(PORT, EXP_I2C_ADDR, buf, sizeof buf, pdMS_TO_TICKS(50));
}

esp_err_t expander_init(void)
{
    if (lock == NULL) {
        lock = xSemaphoreCreateMutex();
    }
    if (lock == NULL) {
        return ESP_ERR_NO_MEM;
    }
    i2c_config_t cfg = {
        .mode = I2C_MODE_MASTER,
        .sda_io_num = PIN_I2C_SDA,
        .scl_io_num = PIN_I2C_SCL,
        .sda_pullup_en = GPIO_PULLUP_DISABLE,
        .scl_pullup_en = GPIO_PULLUP_DISABLE,
        .master.clk_speed = 400000,
    };
    esp_err_t err = i2c_param_config(PORT, &cfg);
    if (err != ESP_OK) {
        return err;
    }
    err = i2c_driver_install(PORT, cfg.mode, 0, 0, 0);
    if (err != ESP_OK) {
        return err;
    }
    err = expander_configure(1u << EXP_RF1_IRQ | 1u << EXP_RF2_IRQ | 1u << EXP_SD_CD | 1u << EXP_INTERLOCK_OK | 1u << EXP_RF1_IO1 | 1u << EXP_RF2_IO1 | 1u << EXP_SPARE);
    if (err != ESP_OK) {
        return err;
    }
    return expander_boot_verify();
}

esp_err_t expander_boot_verify(void)
{
    uint16_t config = 0;
    uint16_t outputs = 0;
    uint16_t inputs = 0;
    esp_err_t err = read_reg16(REG_CONFIG0, &config);
    if (err != ESP_OK) {
        return err;
    }
    err = read_reg16(REG_OUTPUT0, &outputs);
    if (err != ESP_OK) {
        return err;
    }
    err = read_reg16(REG_INPUT0, &inputs);
    if (err != ESP_OK) {
        return err;
    }
    if (config != config_shadow || outputs != output_shadow) {
        return ESP_ERR_INVALID_RESPONSE;
    }
    if ((outputs & ENABLE_MASK) != 0 || (inputs & ENABLE_MASK) != 0 || (config & ENABLE_MASK) != 0) {
        return ESP_ERR_INVALID_STATE;
    }
    return ESP_OK;
}

esp_err_t expander_configure(uint16_t input_mask)
{
    config_shadow = input_mask;
    esp_err_t err = write_reg16(REG_OUTPUT0, output_shadow);
    if (err != ESP_OK) {
        return err;
    }
    return write_reg16(REG_CONFIG0, config_shadow);
}

esp_err_t expander_write(int bit, bool level)
{
    if (lock == NULL) {
        return ESP_ERR_INVALID_STATE;
    }
    xSemaphoreTake(lock, portMAX_DELAY);
    if (level && ((ENABLE_MASK >> bit) & 1u) && !permit_read()) {
        xSemaphoreGive(lock);
        return ESP_ERR_INVALID_STATE;
    }
    uint16_t previous = output_shadow;
    if (level) {
        output_shadow |= (uint16_t)(1u << bit);
    } else {
        output_shadow &= (uint16_t)~(1u << bit);
    }
    esp_err_t err = write_reg16(REG_OUTPUT0, output_shadow);
    if (err != ESP_OK) {
        output_shadow = previous;
    }
    xSemaphoreGive(lock);
    return err;
}

esp_err_t expander_read_all(uint16_t *value)
{
    uint8_t reg = REG_INPUT0;
    uint8_t buf[2] = {0, 0};
    esp_err_t err = i2c_master_write_read_device(PORT, EXP_I2C_ADDR, &reg, 1, buf, 2, pdMS_TO_TICKS(50));
    if (err == ESP_OK) {
        *value = (uint16_t)(buf[0] | (buf[1] << 8));
    }
    return err;
}

esp_err_t expander_read(int bit, bool *level)
{
    uint16_t value = 0;
    esp_err_t err = expander_read_all(&value);
    if (err == ESP_OK) {
        *level = (value >> bit) & 1u;
    }
    return err;
}

esp_err_t expander_read_outputs(uint16_t *value, bool *matches_shadow)
{
    if (lock == NULL) {
        return ESP_ERR_INVALID_STATE;
    }
    xSemaphoreTake(lock, portMAX_DELAY);
    esp_err_t err = read_reg16(REG_OUTPUT0, value);
    if (err == ESP_OK) {
        *matches_shadow = (*value == output_shadow);
    }
    xSemaphoreGive(lock);
    return err;
}
