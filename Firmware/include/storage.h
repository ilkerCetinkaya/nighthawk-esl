#pragma once
#include <stdbool.h>
#include "esp_err.h"

esp_err_t storage_init(void);
bool storage_ready(void);
esp_err_t storage_append_line(const char *file, const char *line);
esp_err_t storage_cat(const char *file);
