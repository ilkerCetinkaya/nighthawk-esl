#include "devdb.h"
#include <stdio.h>
#include <string.h>
#include <strings.h>
#include "storage.h"

#define DB_FILE "devices.csv"

static const char *const ALLOWED[] = {"SoluM", "Hanshow", "Pricer", "TagTurk"};

const char *devdb_manufacturers(void)
{
    return "SoluM, Hanshow, Pricer, TagTurk";
}

int devdb_valid_manufacturer(const char *name)
{
    for (size_t i = 0; i < sizeof ALLOWED / sizeof ALLOWED[0]; i++) {
        if (strcasecmp(name, ALLOWED[i]) == 0) {
            return 1;
        }
    }
    return 0;
}

esp_err_t devdb_add(const device_record_t *r)
{
    char line[512];
    snprintf(line, sizeof line, "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s", r->manufacturer, r->model, r->gateway, r->revision, r->frequency,
             r->modulation, r->bandwidth, r->antenna, r->range_m, r->rssi_dbm, r->documentation, r->security, r->confidence);
    return storage_append_line(DB_FILE, line);
}

esp_err_t devdb_list(void)
{
    return storage_cat(DB_FILE);
}
