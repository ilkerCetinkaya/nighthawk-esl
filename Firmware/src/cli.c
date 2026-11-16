#include "cli.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "devdb.h"
#include "driver/usb_serial_jtag.h"
#include "esp_console.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "expander.h"
#include "health.h"
#include "interlock.h"
#include "linenoise/linenoise.h"
#include "measure.h"
#include "pins.h"
#include "storage.h"

static bool session_active = false;
static int64_t session_start_us = 0;
static char session_id[24] = "";

static int cmd_help(int argc, char **argv)
{
    puts("device list | device add <mfr> <model> <gateway> <rev> <freq> <mod> <bw> <antenna> <range_m> <rssi_dbm> <doc> <security> <confidence>");
    puts("device info | rf status | rf monitor [n] | rf measure | rf modules");
    puts("test status | test start | test stop | log export | config show | interlock arm|disarm");
    printf("manufacturers: %s\n", devdb_manufacturers());
    puts("This firmware does not generate ESL commands or transmit RF.");
    return 0;
}

static int cmd_device(int argc, char **argv)
{
    if (argc >= 2 && strcmp(argv[1], "list") == 0) {
        esp_err_t err = devdb_list();
        if (err != ESP_OK) {
            printf("device list failed: %s\n", esp_err_to_name(err));
        }
        return 0;
    }
    if (argc >= 2 && strcmp(argv[1], "info") == 0) {
        printf("fields: manufacturer,model,gateway,revision,frequency,modulation,bandwidth,antenna,range_m,rssi_dbm,documentation,security,confidence\n");
        printf("unknown values must be entered as 'unknown'\n");
        return 0;
    }
    if (argc == 15 && strcmp(argv[1], "add") == 0) {
        if (!devdb_valid_manufacturer(argv[2])) {
            printf("manufacturer must be one of: %s\n", devdb_manufacturers());
            return 1;
        }
        device_record_t r = {0};
        strlcpy(r.manufacturer, argv[2], sizeof r.manufacturer);
        strlcpy(r.model, argv[3], sizeof r.model);
        strlcpy(r.gateway, argv[4], sizeof r.gateway);
        strlcpy(r.revision, argv[5], sizeof r.revision);
        strlcpy(r.frequency, argv[6], sizeof r.frequency);
        strlcpy(r.modulation, argv[7], sizeof r.modulation);
        strlcpy(r.bandwidth, argv[8], sizeof r.bandwidth);
        strlcpy(r.antenna, argv[9], sizeof r.antenna);
        strlcpy(r.range_m, argv[10], sizeof r.range_m);
        strlcpy(r.rssi_dbm, argv[11], sizeof r.rssi_dbm);
        strlcpy(r.documentation, argv[12], sizeof r.documentation);
        strlcpy(r.security, argv[13], sizeof r.security);
        strlcpy(r.confidence, argv[14], sizeof r.confidence);
        esp_err_t err = devdb_add(&r);
        printf(err == ESP_OK ? "ok\n" : "error: %s\n", esp_err_to_name(err));
        return err == ESP_OK ? 0 : 1;
    }
    puts("usage: device list | device info | device add <14 fields, see help>");
    return 1;
}

static int cmd_rf(int argc, char **argv)
{
    if (argc < 2) {
        puts("usage: rf status|monitor|measure|modules");
        return 1;
    }
    if (strcmp(argv[1], "status") == 0) {
        printf("interlock=%s hardware_ok=%d wifi=disabled ble=disabled\n", interlock_state_name(interlock_state()), interlock_hardware_ok());
        return 0;
    }
    if (strcmp(argv[1], "measure") == 0) {
        printf("rssi_input_mv=%d\n", measure_rssi_mv());
        return 0;
    }
    if (strcmp(argv[1], "monitor") == 0) {
        int n = argc > 2 ? atoi(argv[2]) : 20;
        for (int i = 0; i < n; i++) {
            printf("%lld,%d\n", (long long)(esp_timer_get_time() / 1000), measure_rssi_mv());
            health_progress(HEALTH_CLI);
            vTaskDelay(pdMS_TO_TICKS(100));
        }
        return 0;
    }
    if (strcmp(argv[1], "modules") == 0) {
        bool irq1 = false;
        bool irq2 = false;
        expander_read(EXP_RF1_IRQ, &irq1);
        expander_read(EXP_RF2_IRQ, &irq2);
        printf("slot1 irq=%d slot2 irq=%d module identification EEPROM read not implemented\n", irq1, irq2);
        return 0;
    }
    puts("unknown rf command");
    return 1;
}

static int cmd_test(int argc, char **argv)
{
    if (argc < 2) {
        puts("usage: test status|start|stop");
        return 1;
    }
    if (strcmp(argv[1], "status") == 0) {
        printf("session=%s id=%s interlock=%s\n", session_active ? "active" : "idle", session_id, interlock_state_name(interlock_state()));
        return 0;
    }
    if (strcmp(argv[1], "start") == 0) {
        if (!interlock_request_arm()) {
            puts("refused: hardware interlock is open");
            return 1;
        }
        session_active = true;
        session_start_us = esp_timer_get_time();
        snprintf(session_id, sizeof session_id, "S%lld", (long long)(session_start_us / 1000000));
        storage_append_line("sessions.csv", session_id);
        puts("session started; only passive RSSI logging is available");
        return 0;
    }
    if (strcmp(argv[1], "stop") == 0) {
        session_active = false;
        interlock_disarm();
        puts("session stopped, interlock disarmed");
        return 0;
    }
    puts("unknown test command");
    return 1;
}

static int cmd_interlock(int argc, char **argv)
{
    if (argc == 2 && strcmp(argv[1], "arm") == 0) {
        puts(interlock_request_arm() ? "armed" : "refused: loop or enclosure open, or supervisor not ready");
        return 0;
    }
    if (argc == 2 && strcmp(argv[1], "disarm") == 0) {
        interlock_disarm();
        puts("disarmed");
        return 0;
    }
    if (argc == 2 && strcmp(argv[1], "status") == 0) {
        hc_t snap;
        health_snapshot(&snap);
        printf("state=%s reason=%s hardware_ok=%d\n", interlock_state_name(interlock_state()), sup_reason_name(interlock_reason()), interlock_hardware_ok());
        for (int i = 0; i < snap.count; i++) {
            printf("task %s mode=%s progress=%lu\n", snap.task[i].name, snap.task[i].mode == HC_BUSY ? "busy" : "idle", (unsigned long)snap.task[i].progress_count);
        }
        return 0;
    }
    puts("usage: interlock arm|disarm|status");
    return 1;
}

static int cmd_log(int argc, char **argv)
{
    if (argc == 2 && strcmp(argv[1], "export") == 0) {
        esp_err_t err = storage_cat("devices.csv");
        if (err != ESP_OK) {
            printf("log export failed: %s\n", esp_err_to_name(err));
        }
        return 0;
    }
    puts("usage: log export");
    return 1;
}

static int cmd_config(int argc, char **argv)
{
    printf("hardware=NIGHTHAWK REV A\nstorage=%s\nwifi=disabled\nble=disabled\n", storage_ready() ? "mounted" : "not mounted");
    return 0;
}

static void register_commands(void)
{
    const esp_console_cmd_t cmds[] = {
        {.command = "help", .help = "List commands", .func = cmd_help},
        {.command = "device", .help = "Device database", .func = cmd_device},
        {.command = "rf", .help = "RF monitor, passive", .func = cmd_rf},
        {.command = "test", .help = "Test sessions", .func = cmd_test},
        {.command = "interlock", .help = "Hardware interlock", .func = cmd_interlock},
        {.command = "log", .help = "Log export", .func = cmd_log},
        {.command = "config", .help = "Show configuration", .func = cmd_config},
    };
    for (size_t i = 0; i < sizeof cmds / sizeof cmds[0]; i++) {
        esp_console_cmd_register(&cmds[i]);
    }
}

void cli_start(void)
{
    esp_console_config_t cfg = {.max_cmdline_length = 256, .max_cmdline_args = 20};
    esp_console_init(&cfg);
    register_commands();
    linenoiseSetMultiLine(0);
    for (;;) {
        health_set_idle(HEALTH_CLI);
        char *line = linenoise("nighthawk> ");
        if (!line) {
            vTaskDelay(pdMS_TO_TICKS(10));
            continue;
        }
        health_set_busy(HEALTH_CLI, HEALTH_COMMAND_DEADLINE_MS);
        linenoiseHistoryAdd(line);
        int ret = 0;
        esp_err_t err = esp_console_run(line, &ret);
        if (err == ESP_ERR_NOT_FOUND) {
            puts("unknown command, try help");
        }
        linenoiseFree(line);
    }
}
