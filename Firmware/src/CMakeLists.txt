idf_component_register(
    SRCS "main.c" "expander.c" "health_core.c" "supervisor_core.c" "health.c" "interlock.c" "measure.c" "storage.c" "devdb.c" "cli.c"
    INCLUDE_DIRS "../include"
    REQUIRES driver esp_adc esp_driver_gpio esp_driver_i2c esp_driver_spi esp_driver_sdspi esp_driver_usb_serial_jtag console fatfs sdmmc nvs_flash esp_timer vfs
)
