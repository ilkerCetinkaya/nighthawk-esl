#pragma once
#include "esp_err.h"

typedef struct {
    char manufacturer[16];
    char model[32];
    char gateway[32];
    char revision[16];
    char frequency[24];
    char modulation[24];
    char bandwidth[16];
    char antenna[24];
    char range_m[8];
    char rssi_dbm[8];
    char documentation[48];
    char security[48];
    char confidence[16];
} device_record_t;

esp_err_t devdb_add(const device_record_t *record);
esp_err_t devdb_list(void);
const char *devdb_manufacturers(void);
int devdb_valid_manufacturer(const char *name);
