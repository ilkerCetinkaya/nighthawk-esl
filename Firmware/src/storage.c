#include "storage.h"
#include "health.h"
#include <stdio.h>
#include "driver/sdspi_host.h"
#include "driver/spi_common.h"
#include "esp_vfs_fat.h"
#include "expander.h"
#include "pins.h"
#include "sdmmc_cmd.h"

#define MOUNT_POINT "/sdcard"

static bool mounted = false;

esp_err_t storage_init(void)
{
    spi_bus_config_t bus = {
        .mosi_io_num = PIN_SPI_MOSI,
        .miso_io_num = PIN_SPI_MISO,
        .sclk_io_num = PIN_SPI_SCK,
        .quadwp_io_num = -1,
        .quadhd_io_num = -1,
        .max_transfer_sz = 4096,
    };
    esp_err_t err = spi_bus_initialize(SPI2_HOST, &bus, SPI_DMA_CH_AUTO);
    if (err != ESP_OK) {
        return err;
    }
    bool card_detect_level = true;
    expander_read(EXP_SD_CD, &card_detect_level);
    if (card_detect_level) {
        return ESP_ERR_NOT_FOUND;
    }
    sdmmc_host_t host = SDSPI_HOST_DEFAULT();
    host.slot = SPI2_HOST;
    sdspi_device_config_t slot = SDSPI_DEVICE_CONFIG_DEFAULT();
    slot.host_id = SPI2_HOST;
    slot.gpio_cs = PIN_SD_CS;
    esp_vfs_fat_sdmmc_mount_config_t cfg = {.format_if_mount_failed = false, .max_files = 4, .allocation_unit_size = 16 * 1024};
    sdmmc_card_t *card = NULL;
    err = esp_vfs_fat_sdspi_mount(MOUNT_POINT, &host, &slot, &cfg, &card);
    mounted = (err == ESP_OK);
    return err;
}

bool storage_ready(void)
{
    return mounted;
}

esp_err_t storage_append_line(const char *file, const char *line)
{
    if (!mounted) {
        return ESP_ERR_INVALID_STATE;
    }
    char path[96];
    snprintf(path, sizeof path, MOUNT_POINT "/%s", file);
    FILE *f = fopen(path, "a");
    if (!f) {
        return ESP_FAIL;
    }
    fprintf(f, "%s\n", line);
    fclose(f);
    return ESP_OK;
}

esp_err_t storage_cat(const char *file)
{
    if (!mounted) {
        return ESP_ERR_INVALID_STATE;
    }
    char path[96];
    snprintf(path, sizeof path, MOUNT_POINT "/%s", file);
    FILE *f = fopen(path, "r");
    if (!f) {
        return ESP_ERR_NOT_FOUND;
    }
    char buf[160];
    while (fgets(buf, sizeof buf, f)) {
        fputs(buf, stdout);
        health_progress(HEALTH_CLI);
    }
    fclose(f);
    return ESP_OK;
}
