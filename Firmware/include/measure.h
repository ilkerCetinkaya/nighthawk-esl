#pragma once
#include <stdint.h>
#include "esp_err.h"

esp_err_t measure_init(void);
int measure_rssi_mv(void);
