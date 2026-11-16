#pragma once
#include <stdbool.h>
#include <stdint.h>
#include "esp_err.h"

esp_err_t expander_init(void);
esp_err_t expander_configure(uint16_t input_mask);
esp_err_t expander_write(int bit, bool level);
esp_err_t expander_read(int bit, bool *level);
esp_err_t expander_read_all(uint16_t *value);
esp_err_t expander_read_outputs(uint16_t *value, bool *matches_shadow);
esp_err_t expander_boot_verify(void);
void expander_set_enable_permit(bool permitted);
