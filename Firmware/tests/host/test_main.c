#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "health_core.h"
#include "supervisor_core.h"

#define EN1 0x01
#define EN2 0x02
#define SAMPLER_DEADLINE 500
#define CLI_DEADLINE 5000

static int failures;
static int checks;

#define CHECK(cond, ...) do { checks++; if (!(cond)) { failures++; printf("  FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

typedef struct {
    bool mcu_in_reset;
    bool button_reset;
    bool wd_reset;
    bool arm_driven;
    bool loop_ok;
    bool encl_ok;
    uint8_t tca_out;
    uint32_t ttout;
    uint32_t td;
    uint32_t last_wdi_fall;
    bool wdi_level;
    uint32_t wd_reset_until;
    int resets;
    int wdi_falls;
    uint32_t last_fall_time;
} hw_t;

typedef struct {
    sup_t sup;
    hc_t hc;
    sup_sample_t sample;
    bool arm_req;
    bool disarm_req;
    bool clear_flag;
    bool stall_sampler;
    bool stall_supervisor;
    bool stall_cli;
    bool i2c_fail;
    bool output_mismatch;
    bool en_pin_high;
    uint8_t good;
    uint8_t bad;
    uint32_t seq;
    bool skip_boot_clear;
    bool cli_ready;
    uint32_t boot_time;
    bool booted;
    int wdi_toggle;
    sup_out_t last_out;
} fw_t;

static hw_t hw;
static fw_t fw;
static uint32_t now;

static bool arm_pin(void) { return !hw.mcu_in_reset && hw.arm_driven; }
static bool en_pin(void) { return !hw.mcu_in_reset; }
static bool interlock_ok(void) { return arm_pin() && en_pin() && hw.loop_ok && hw.encl_ok; }
static bool rail(int i) { return interlock_ok() && (hw.tca_out & (i == 1 ? EN1 : EN2)); }

static void fw_boot(void)
{
    uint8_t keep_tca = hw.tca_out;
    bool skip = fw.skip_boot_clear;
    memset(&fw, 0, sizeof fw);
    fw.skip_boot_clear = skip;
    hw.tca_out = keep_tca;
    hw.arm_driven = false;
    sup_init(&fw.sup, true);
    hc_init(&fw.hc);
    hc_register(&fw.hc, "sampler", SAMPLER_DEADLINE, now);
    hc_register(&fw.hc, "cli", 10000, now);
    fw.boot_time = now;
    fw.booted = true;
}

static void hw_set_reset(bool reset)
{
    bool before = hw.mcu_in_reset;
    hw.mcu_in_reset = hw.button_reset || hw.wd_reset;
    if (!before && hw.mcu_in_reset) {
        hw.resets++;
        fw.booted = false;
        hw.arm_driven = false;
    }
    if (before && !hw.mcu_in_reset) {
        fw_boot();
        hw.last_wdi_fall = now;
    }
    (void)reset;
}

static void hw_tick(void)
{
    if (hw.wd_reset && now >= hw.wd_reset_until) {
        hw.wd_reset = false;
        hw_set_reset(false);
    }
    if (!hw.mcu_in_reset && (uint32_t)(now - hw.last_wdi_fall) >= hw.ttout) {
        hw.wd_reset = true;
        hw.wd_reset_until = now + hw.td;
        hw_set_reset(true);
    }
}

static void hw_wdi(bool level)
{
    if (hw.wdi_level && !level) {
        hw.last_wdi_fall = now;
        hw.wdi_falls++;
        hw.last_fall_time = now;
    }
    hw.wdi_level = level;
}

static void fw_tick(void)
{
    if (!fw.booted) {
        return;
    }
    if (!fw.cli_ready && now - fw.boot_time >= 200) {
        fw.cli_ready = true;
        if (!fw.skip_boot_clear) {
            hw.tca_out &= (uint8_t)~(EN1 | EN2);
        }
        hc_progress(&fw.hc, 1, now);
        hc_set_idle(&fw.hc, 1);
    }
    if (!fw.stall_sampler && (now - fw.boot_time) % 100 == 0) {
        bool ok = !fw.i2c_fail;
        if (ok) {
            fw.good = fw.good < 255 ? fw.good + 1 : fw.good;
            fw.bad = 0;
        } else {
            fw.bad = fw.bad < 255 ? fw.bad + 1 : fw.bad;
            fw.good = 0;
        }
        fw.sample.valid = ok;
        fw.sample.interlock_ok = ok && interlock_ok();
        fw.sample.enables_low = ok && (hw.tca_out & (EN1 | EN2)) == 0 && !fw.en_pin_high;
        fw.sample.outputs_match = ok && !fw.output_mismatch;
        fw.sample.good_streak = fw.good;
        fw.sample.bad_streak = fw.bad;
        fw.sample.time_ms = now;
        fw.sample.seq = ++fw.seq;
        if (fw.clear_flag && ok && !fw.skip_boot_clear) {
            hw.tca_out &= (uint8_t)~(EN1 | EN2);
        }
        hc_progress(&fw.hc, 0, now);
    }
    if (!fw.stall_supervisor && (now - fw.boot_time) % 50 == 0) {
        sup_in_t in;
        in.tasks_healthy = hc_evaluate(&fw.hc, now, 2, NULL);
        in.sample = fw.sample;
        in.arm_request = fw.arm_req;
        in.disarm_request = fw.disarm_req;
        fw.arm_req = false;
        sup_step(&fw.sup, &in, &fw.last_out, now);
        fw.clear_flag = fw.last_out.clear_enables;
        hw.arm_driven = fw.last_out.arm_level;
        if (fw.last_out.service_wdi) {
            hw_wdi(true);
            hw_wdi(false);
            hw_wdi(true);
        }
    }
}

static void step(uint32_t ms)
{
    for (uint32_t i = 0; i < ms; i++) {
        now++;
        hw_tick();
        fw_tick();
    }
}

static void reset_world(uint32_t ttout)
{
    memset(&hw, 0, sizeof hw);
    memset(&fw, 0, sizeof fw);
    now = 1000;
    hw.loop_ok = true;
    hw.encl_ok = true;
    hw.ttout = ttout;
    hw.td = 200;
    hw.last_wdi_fall = now;
    fw_boot();
}

static void button(bool pressed)
{
    hw.button_reset = pressed;
    hw_set_reset(pressed);
}

static bool fw_write_enable(uint8_t bits)
{
    if (!fw.last_out.enables_permitted) {
        return false;
    }
    hw.tca_out |= bits;
    return true;
}

static bool arm_and_enable(void)
{
    hw.tca_out &= (uint8_t)~(EN1 | EN2);
    step(300);
    fw.arm_req = true;
    step(1000);
    if (fw.sup.state != SUP_ARMED) {
        return false;
    }
    bool wrote = fw_write_enable(EN1 | EN2);
    step(10);
    return wrote;
}

static void test_health_core(void)
{
    printf("T0 health_core unit checks\n");
    hc_t h;
    hc_init(&h);
    int a = hc_register(&h, "a", 100, 0);
    int b = hc_register(&h, "b", 200, 0);
    int failed = -1;
    CHECK(hc_evaluate(&h, 100, 2, &failed), "within deadline must pass");
    CHECK(!hc_evaluate(&h, 101, 2, &failed) && failed == a, "a must fail at 101 ms");
    hc_progress(&h, a, 101);
    CHECK(hc_evaluate(&h, 150, 2, &failed), "a progressed");
    CHECK(!hc_evaluate(&h, 201, 2, &failed) && failed == b, "b must fail at 201 ms");
    hc_set_idle(&h, b);
    hc_progress(&h, a, 400);
    CHECK(hc_evaluate(&h, 450, 2, &failed), "idle task never fails");
    CHECK(!hc_evaluate(&h, 450, 3, &failed), "missing registered task fails");
    hc_set_busy(&h, b, 50, 450);
    hc_progress(&h, a, 480);
    CHECK(!hc_evaluate(&h, 501, 2, &failed) && failed == b, "busy again with new deadline");
    hc_t w;
    hc_init(&w);
    int c = hc_register(&w, "c", 100, 0xFFFFFF80u);
    CHECK(hc_evaluate(&w, 0xFFFFFFC0u, 1, NULL), "wrap-around: 64 ms elapsed within 100 ms deadline");
    CHECK(!hc_evaluate(&w, 0x20u, 1, NULL), "wrap-around elapsed 160 ms must fail");
    hc_progress(&w, c, 0x10u);
    CHECK(hc_evaluate(&w, 0x20u, 1, NULL), "wrap-around after progress passes");
}

static void test_all_healthy(void)
{
    printf("T1 all tasks healthy\n");
    reset_world(1600);
    step(500);
    CHECK(arm_and_enable(), "arming must succeed");
    int falls_before = hw.wdi_falls;
    step(20000);
    CHECK(hw.resets == 0, "no reset, got %d", hw.resets);
    CHECK(fw.sup.state == SUP_ARMED, "stays armed, state %s", sup_state_name(fw.sup.state));
    CHECK(rail(1) && rail(2), "both rails on while armed and enabled");
    CHECK(hw.wdi_falls - falls_before > 150, "WDI keeps toggling, falls %d", hw.wdi_falls - falls_before);
    printf("  armed 20 s, resets=%d, WDI falling edges=%d\n", hw.resets, hw.wdi_falls - falls_before);
}

static uint32_t first_time(bool (*cond)(void), uint32_t limit)
{
    uint32_t t0 = now;
    while ((uint32_t)(now - t0) < limit) {
        if (cond()) {
            return now - t0;
        }
        step(1);
    }
    return 0xFFFFFFFFu;
}

static bool cond_arm_low(void) { return !arm_pin(); }
static bool cond_rails_off(void) { return !rail(1) && !rail(2); }
static bool cond_reset(void) { return hw.mcu_in_reset; }
static bool cond_booted(void) { return !hw.mcu_in_reset && fw.booted; }

static void test_sampler_stall(void)
{
    printf("T2a critical task stalled: sampler (I2C hang) while armed\n");
    static const uint32_t tt[3] = {900, 1600, 2500};
    for (int k = 0; k < 3; k++) {
        reset_world(tt[k]);
        step(500);
        CHECK(arm_and_enable(), "arm");
        step(1000);
        fw.stall_sampler = true;
        uint32_t t_arm = first_time(cond_arm_low, 3000);
        CHECK(t_arm <= SUP_SAMPLE_MAX_AGE_MS + 100, "ARM low %u ms after stall (limit 500)", t_arm);
        CHECK(!rail(1) && !rail(2), "rails off when ARM low");
        step(150);
        int fallsA = hw.wdi_falls;
        step(100);
        CHECK(hw.wdi_falls == fallsA, "WDI serviced after stall detected: %d vs %d state=%s healthy=%d", hw.wdi_falls, fallsA, sup_state_name(fw.sup.state), fw.last_out.service_wdi);
        uint32_t t_rst = first_time(cond_reset, 4000);
        CHECK(t_rst != 0xFFFFFFFFu, "watchdog reset must follow");
        printf("  ttout=%u ms: ARM low %u ms after stall, hardware reset %u ms after that\n", tt[k], t_arm, t_rst);
        first_time(cond_booted, 1000);
        step(300);
        CHECK(fw.sup.state == SUP_DISARMED && !arm_pin(), "after reset: DISARMED, ARM low");
        CHECK(!rail(1) && !rail(2), "after reset rails off");
        step(2000);
        CHECK(!rail(1) && !rail(2), "rails stay off until explicit arm");
    }
}

static void test_cli_stall(void)
{
    printf("T2b critical task stalled: CLI command blocked (e.g. SD write) while armed\n");
    reset_world(1600);
    step(500);
    CHECK(arm_and_enable(), "arm");
    hc_set_busy(&fw.hc, 1, CLI_DEADLINE, now);
    uint32_t t = first_time(cond_arm_low, 8000);
    CHECK(t >= CLI_DEADLINE && t <= CLI_DEADLINE + 100, "ARM low %u ms after command start (expect 5000..5100)", t);
    CHECK(!rail(1) && !rail(2), "rails off");
    printf("  CLI blocked: ARM low after %u ms (deadline %d ms)\n", t, CLI_DEADLINE);
    hc_t copy = fw.hc;
    (void)copy;
    reset_world(1600);
    step(500);
    CHECK(arm_and_enable(), "arm");
    hc_set_busy(&fw.hc, 1, CLI_DEADLINE, now);
    for (int i = 0; i < 80; i++) {
        step(100);
        hc_progress(&fw.hc, 1, now);
    }
    CHECK(fw.sup.state == SUP_ARMED, "long command with progress is not a fault");
    printf("  8 s command reporting progress every 100 ms: still ARMED\n");
}

static void test_supervisor_stall(void)
{
    printf("T3 health supervisor stalled while armed (ARM latched high, no reset yet)\n");
    static const uint32_t tt[3] = {900, 1600, 2500};
    for (int level = 0; level < 2; level++) {
        for (int k = 0; k < 3; k++) {
            reset_world(tt[k]);
            step(500);
            CHECK(arm_and_enable(), "arm");
            step(200);
            step(5);
            fw.stall_supervisor = true;
            if (level == 0) {
                hw_wdi(false);
            }
            uint32_t t_rail = first_time(cond_rails_off, 4000);
            CHECK(t_rail != 0xFFFFFFFFu, "hardware watchdog must cut the rails");
            CHECK(t_rail <= tt[k] + 60, "exposure %u ms exceeds ttout %u + 60", t_rail, tt[k]);
            printf("  WDI stuck %s, ttout=%u ms: rails on for %u ms after supervisor stall\n", level ? "high (idle)" : "low (stalled mid-pulse)", tt[k], t_rail);
            first_time(cond_booted, 1000);
            step(300);
            CHECK(!arm_pin() && fw.sup.state == SUP_DISARMED, "after watchdog reset: ARM low, DISARMED");
        }
    }
    printf("  exposure is bounded by the TPS3823 time-out (0.9 / 1.6 / 2.5 s min/typ/max); it is not zero\n");
}

static void test_i2c_failure(void)
{
    printf("T4 I2C failure during arm / disarm\n");
    reset_world(1600);
    step(500);
    CHECK(arm_and_enable(), "arm");
    uint32_t resets = hw.resets;
    fw.i2c_fail = true;
    uint32_t t = first_time(cond_arm_low, 1000);
    CHECK(t <= 150, "ARM low %u ms after I2C failure (limit 150)", t);
    CHECK(!rail(1) && !rail(2), "rails off");
    CHECK(fw.sup.state == SUP_FAULT && fw.sup.reason == SUP_REASON_I2C, "FAULT/I2C, got %s/%s", sup_state_name(fw.sup.state), sup_reason_name(fw.sup.reason));
    step(3000);
    CHECK(hw.resets == (int)resets, "no watchdog reset: system alive and safe");
    fw.arm_req = true;
    step(500);
    CHECK(fw.sup.state == SUP_FAULT && !arm_pin(), "arm refused while latched");
    fw.disarm_req = true;
    step(500);
    CHECK(fw.sup.state == SUP_FAULT, "disarm cannot clear fault while I2C is down");
    CHECK(!arm_pin() && !rail(1) && !rail(2), "still safe");
    fw.i2c_fail = false;
    step(500);
    CHECK(fw.sup.state == SUP_DISARMED, "disarm completes after I2C returns, state %s", sup_state_name(fw.sup.state));
    CHECK((hw.tca_out & (EN1 | EN2)) == 0, "enables cleared and verified");
    fw.disarm_req = false;
    fw.arm_req = true;
    step(1200);
    CHECK(fw.sup.state == SUP_ARMED, "re-arm after recovery");
    printf("  I2C failure: ARM low in %u ms, latched FAULT, recovery only via disarm\n", t);
}

static void test_mcu_reset(void)
{
    printf("T5 MCU reset (reset button) while armed\n");
    reset_world(1600);
    step(500);
    CHECK(arm_and_enable(), "arm");
    CHECK(rail(1), "rail on before reset");
    button(true);
    CHECK(!rail(1) && !rail(2), "rails off in the same instant (hardware, 0 ms)");
    step(300);
    button(false);
    step(5);
    CHECK(hw.tca_out & EN1, "TCA9555 output register retained across MCU reset (datasheet: no reset pin)");
    CHECK(!rail(1), "rail stays off after reset release because ARM low");
    step(2000);
    CHECK(!rail(1) && fw.sup.state == SUP_DISARMED, "stays off and DISARMED");
    CHECK((hw.tca_out & (EN1 | EN2)) == 0, "boot sequence cleared retained enables");
    printf("  rails off at reset edge; retained TCA bits cleared by boot sequence; no re-arm without request\n");
    reset_world(1600);
    fw.skip_boot_clear = true;
    hw.tca_out = EN1 | EN2;
    step(500);
    fw.arm_req = true;
    bool arm_ever_high = false;
    for (int i = 0; i < 1500; i++) {
        step(1);
        arm_ever_high = arm_ever_high || arm_pin();
    }
    CHECK(!arm_ever_high, "ARM must never rise while enables cannot be cleared");
    CHECK(fw.sup.state == SUP_DISARMED && fw.sup.reason == SUP_REASON_ARM_ABORTED, "arming aborted, got %s/%s", sup_state_name(fw.sup.state), sup_reason_name(fw.sup.reason));
    CHECK(!rail(1) && !rail(2), "rails off");
    printf("  arming aborted in PRECHECK, ARM never rose, when enables could not be cleared\n");
}

static void test_enable_race(void)
{
    printf("T5b enable raised by a NON-firmware cause (bit flip, ESD) around the ARM transition\n");
    uint32_t worst = 0;
    int detected = 0;
    for (uint32_t offset = 0; offset <= 800; offset += 7) {
        reset_world(1600);
        step(500);
        fw.arm_req = true;
        step(offset);
        bool armed_at_raise = fw.sup.state == SUP_ARMED;
        hw.tca_out |= EN1;
        uint32_t on_ms = 0;
        for (int i = 0; i < 1500; i++) {
            step(1);
            if (rail(1)) {
                on_ms++;
            }
        }
        if (fw.sup.state == SUP_FAULT || fw.sup.state == SUP_DISARMED) {
            detected++;
        }
        if (!armed_at_raise) {
            CHECK(fw.sup.state != SUP_ARMED, "raised before ARMED: must not end ARMED (offset %u)", offset);
            if (on_ms > worst) {
                worst = on_ms;
            }
        }
    }
    CHECK(worst <= 260, "worst rail exposure %u ms", worst);
    printf("  swept offsets 0..800 ms after the request; raised before ARMED -> never ended ARMED; worst module power exposure %u ms (non-firmware source cannot be prevented by firmware)\n", worst);
    (void)detected;
}

static void test_firmware_enable_permit(void)
{
    printf("T5c firmware enable path is refused unless ARMED\n");
    reset_world(1600);
    step(500);
    CHECK(!fw_write_enable(EN1), "write refused in DISARMED");
    fw.arm_req = true;
    for (int i = 0; i < 1500; i++) {
        step(1);
        if (fw.sup.state != SUP_ARMED) {
            CHECK(!fw.last_out.enables_permitted, "no permit in %s", sup_state_name(fw.sup.state));
        }
    }
    CHECK(fw.sup.state == SUP_ARMED, "armed");
    CHECK(fw_write_enable(EN1) && rail(1), "write accepted and rail on in ARMED");
    hw.loop_ok = false;
    step(120);
    CHECK(!fw.last_out.enables_permitted && !fw_write_enable(EN2), "permit revoked after interlock opened");
    hw.loop_ok = true;
    step(300);
    CHECK((hw.tca_out & (EN1 | EN2)) == 0, "stale enable cleared while not ARMED");
    printf("  permit only in ARMED; revoked on OPEN; enables cleared\n");
}

static void test_sampler_semantics(void)
{
    printf("T9 sampler: execution progress vs acquisition success vs peripheral health\n");
    reset_world(1600);
    step(500);
    fw.i2c_fail = true;
    step(250);
    CHECK(fw.sup.state == SUP_DISARMED, "two failed cycles tolerated while DISARMED, got %s", sup_state_name(fw.sup.state));
    step(100);
    CHECK(fw.sup.state == SUP_FAULT && fw.sup.reason == SUP_REASON_I2C, "3 consecutive failures latch FAULT/I2C while DISARMED, got %s/%s", sup_state_name(fw.sup.state), sup_reason_name(fw.sup.reason));
    int resets = hw.resets;
    step(3000);
    CHECK(hw.resets == resets, "task alive: no watchdog reset (execution progress is healthy, peripheral is not)");
    fw.arm_req = true;
    step(300);
    CHECK(fw.sup.state == SUP_FAULT && !arm_pin(), "arm refused while peripheral unhealthy");
    fw.i2c_fail = false;
    fw.disarm_req = true;
    step(150);
    CHECK(fw.sup.state == SUP_FAULT, "recovery needs %d consecutive good samples, still FAULT after 1-2", SUP_GOOD_STREAK_RECOVER);
    step(300);
    CHECK(fw.sup.state == SUP_DISARMED, "recovered after good streak + disarm, got %s", sup_state_name(fw.sup.state));
    fw.disarm_req = false;
    printf("  repeated I2C failure is a peripheral fault (latched), never reported as healthy operation\n");

    reset_world(1600);
    step(500);
    CHECK(arm_and_enable(), "arm");
    fw.output_mismatch = true;
    uint32_t t = first_time(cond_arm_low, 1000);
    CHECK(t <= 150 && fw.sup.state == SUP_FAULT && fw.sup.reason == SUP_REASON_OUTPUT_MISMATCH, "output register mismatch while armed: ARM low in %u ms, %s/%s", t, sup_state_name(fw.sup.state), sup_reason_name(fw.sup.reason));
    printf("  output register mismatch: ARM low in %u ms\n", t);

    reset_world(1600);
    step(500);
    fw.en_pin_high = true;
    step(150);
    fw.arm_req = true;
    step(500);
    CHECK(fw.sup.state == SUP_DISARMED && !arm_pin(), "arm refused when an enable PIN reads high although output register is low");
    printf("  enable pin read high with output low: arm refused\n");
}

static sup_in_t mk_in(uint32_t seq, uint32_t time_ms, bool valid, bool enables_low)
{
    sup_in_t in;
    memset(&in, 0, sizeof in);
    in.tasks_healthy = true;
    in.sample.valid = valid;
    in.sample.enables_low = enables_low;
    in.sample.outputs_match = true;
    in.sample.interlock_ok = false;
    in.sample.good_streak = 9;
    in.sample.seq = seq;
    in.sample.time_ms = time_ms;
    return in;
}

static void test_stale_sample_rules(void)
{
    printf("T10 stale / reused / inconsistent samples can never reach ARMED (supervisor_core, synthetic samples)\n");
    sup_t s;
    sup_out_t out;
    sup_in_t in;
    sup_init(&s, true);
    in = mk_in(10, 900, true, true);
    in.arm_request = true;
    sup_step(&s, &in, &out, 1000);
    CHECK(s.state == SUP_PRECHECK && !out.arm_level, "request enters PRECHECK with ARM low, no sample reused");
    bool arm_high = false;
    for (uint32_t t = 1050; t <= 2000; t += 50) {
        in = mk_in(10, 900, true, true);
        sup_step(&s, &in, &out, t);
        arm_high = arm_high || out.arm_level;
    }
    CHECK(!arm_high && s.state == SUP_DISARMED && s.reason == SUP_REASON_ARM_ABORTED, "same old sample forever: aborted, ARM never high (%s)", sup_state_name(s.state));

    sup_init(&s, true);
    in = mk_in(10, 900, true, true);
    in.arm_request = true;
    sup_step(&s, &in, &out, 1000);
    in = mk_in(11, 950, true, true);
    sup_step(&s, &in, &out, 1050);
    CHECK(s.counted == 0 && s.state == SUP_PRECHECK, "sample acquired before the request is ignored, not counted");
    in = mk_in(12, 1040, true, true);
    sup_step(&s, &in, &out, 1100);
    in = mk_in(12, 1040, true, true);
    sup_step(&s, &in, &out, 1150);
    CHECK(s.counted == 1, "same acquisition seen twice counts once, counted=%u", s.counted);
    in = mk_in(13, 1140, true, true);
    sup_step(&s, &in, &out, 1200);
    in = mk_in(14, 1240, true, true);
    sup_step(&s, &in, &out, 1250);
    CHECK(s.state == SUP_ARMING && out.arm_level, "three distinct post-request samples -> ARMING, state %s", sup_state_name(s.state));
    in = mk_in(15, 1250, true, true);
    in.sample.interlock_ok = true;
    sup_step(&s, &in, &out, 1300);
    CHECK(s.state == SUP_ARMING && s.counted == 0, "sample acquired before settle time is ignored");
    in = mk_in(16, 1320, true, true);
    in.sample.interlock_ok = true;
    sup_step(&s, &in, &out, 1350);
    CHECK(s.state == SUP_ARMING && s.counted == 1, "one qualifying sample is not enough");
    in = mk_in(16, 1320, true, true);
    in.sample.interlock_ok = true;
    sup_step(&s, &in, &out, 1400);
    CHECK(s.state == SUP_ARMING && s.counted == 1, "same qualifying sample cannot be reused");
    in = mk_in(17, 1400, true, true);
    in.sample.interlock_ok = true;
    sup_step(&s, &in, &out, 1410);
    CHECK(s.state == SUP_ARMED && out.enables_permitted, "two distinct qualifying samples -> ARMED");

    sup_init(&s, true);
    in = mk_in(1, 0, true, true);
    in.arm_request = true;
    sup_step(&s, &in, &out, 100);
    in = mk_in(2, 120, false, false);
    sup_step(&s, &in, &out, 150);
    CHECK(s.state == SUP_DISARMED && s.reason == SUP_REASON_ARM_ABORTED && !out.arm_level, "invalid sample during PRECHECK aborts");
    sup_init(&s, true);
    in = mk_in(1, 0, true, true);
    in.arm_request = true;
    sup_step(&s, &in, &out, 100);
    in = mk_in(2, 120, true, false);
    sup_step(&s, &in, &out, 150);
    CHECK(s.state == SUP_DISARMED && !out.arm_level, "enable high during PRECHECK aborts");
    sup_init(&s, true);
    in = mk_in(1, 0, true, true);
    in.arm_request = true;
    sup_step(&s, &in, &out, 100);
    in = mk_in(2, 120, true, true);
    sup_step(&s, &in, &out, 1000);
    CHECK(s.state == SUP_DISARMED && !out.arm_level, "sample older than the age limit aborts");

    sup_init(&s, true);
    in = mk_in(1, 0, true, true);
    in.arm_request = true;
    in.disarm_request = true;
    sup_step(&s, &in, &out, 100);
    CHECK(s.state == SUP_DISARMED && out.arm_refused && !out.arm_level, "simultaneous arm and disarm: disarm wins, arm refused");
    sup_state_t states[5] = {SUP_PRECHECK, SUP_ARMING, SUP_ARMED, SUP_OPEN, SUP_FAULT};
    for (int i = 0; i < 5; i++) {
        sup_init(&s, true);
        s.state = states[i];
        s.last_seq = 5;
        in = mk_in(5, 90, true, true);
        in.arm_request = true;
        sup_step(&s, &in, &out, 100);
        CHECK(out.arm_refused, "arm request refused in %s", sup_state_name(states[i]));
    }
    sup_init(&s, false);
    CHECK(s.state == SUP_FAULT && s.reason == SUP_REASON_BOOT, "failed boot verification starts in FAULT");
    in = mk_in(1, 0, true, true);
    in.arm_request = true;
    sup_step(&s, &in, &out, 100);
    CHECK(s.state == SUP_FAULT && !out.arm_level, "arm impossible after failed boot verification");
}


typedef enum {
    MUT_NONE,
    MUT_INVALID,
    MUT_ENABLES_HIGH,
    MUT_OUTPUT_MISMATCH,
    MUT_INTERLOCK_HIGH,
    MUT_LOOP_OPEN,
    MUT_STALE,
    MUT_FUTURE,
    MUT_COUNT
} mutation_t;

static const char *mutation_name(mutation_t m)
{
    switch (m) {
    case MUT_NONE: return "none";
    case MUT_INVALID: return "invalid acquisition";
    case MUT_ENABLES_HIGH: return "enable output/pin high";
    case MUT_OUTPUT_MISMATCH: return "output register mismatch";
    case MUT_INTERLOCK_HIGH: return "interlock reads HIGH while ARM is low";
    case MUT_LOOP_OPEN: return "loop input observable and open";
    case MUT_STALE: return "stale timestamp";
    default: return "future timestamp";
    }
}

static sup_in_t precheck_sample(uint32_t seq, uint32_t t, uint32_t now, mutation_t m, bool loops_observable)
{
    sup_in_t in = mk_in(seq, t, true, true);
    in.sample.loops_observable = loops_observable;
    in.sample.loops_closed = true;
    switch (m) {
    case MUT_INVALID: in.sample.valid = false; break;
    case MUT_ENABLES_HIGH: in.sample.enables_low = false; break;
    case MUT_OUTPUT_MISMATCH: in.sample.outputs_match = false; break;
    case MUT_INTERLOCK_HIGH: in.sample.interlock_ok = true; break;
    case MUT_LOOP_OPEN: in.sample.loops_observable = true; in.sample.loops_closed = false; break;
    case MUT_STALE: break;
    case MUT_FUTURE: in.sample.time_ms = now + 5; break;
    default: break;
    }
    return in;
}

static void test_precheck_conditions(void)
{
    printf("T12 PRECHECK counts a sample only if ALL conditions hold; any failing sample aborts before ARM rises\n");
    for (int mutation = MUT_INVALID; mutation < MUT_COUNT; mutation++) {
        for (int position = 0; position < 3; position++) {
            sup_t s;
            sup_out_t out;
            sup_init(&s, true);
            sup_in_t in = mk_in(1, 0, true, true);
            in.arm_request = true;
            uint32_t now = 1000;
            sup_step(&s, &in, &out, now);
            bool arm_high = false;
            for (int k = 0; k < 3; k++) {
                now += 100;
                mutation_t m = (k == position) ? (mutation_t)mutation : MUT_NONE;
                uint32_t acquired = now - 10;
                uint32_t consumed = (m == MUT_STALE) ? acquired + SUP_ARM_SAMPLE_MAX_AGE_MS + 1 : now;
                in = precheck_sample((uint32_t)(2 + k), acquired, consumed, m, false);
                sup_step(&s, &in, &out, consumed);
                arm_high = arm_high || out.arm_level;
                if (s.state != SUP_PRECHECK) {
                    break;
                }
            }
            CHECK(!arm_high && s.state == SUP_DISARMED && s.reason == SUP_REASON_ARM_ABORTED,
                  "%s in sample %d must abort with ARM never high (state %s, ARM %d)", mutation_name((mutation_t)mutation), position + 1, sup_state_name(s.state), arm_high);
        }
    }
    printf("  7 conditions x 3 sample positions: every failing sample aborted, ARM never rose\n");

    sup_t s;
    sup_out_t out;
    sup_init(&s, true);
    sup_in_t in = mk_in(1, 0, true, true);
    in.arm_request = true;
    uint32_t now = 1000;
    sup_step(&s, &in, &out, now);
    for (int k = 0; k < 3; k++) {
        now += 100;
        in = precheck_sample((uint32_t)(2 + k), now - 10, now, MUT_NONE, true);
        sup_step(&s, &in, &out, now);
    }
    CHECK(s.state == SUP_ARMING && out.arm_level, "three consecutive fully valid samples (loops observable and closed) reach ARMING, got %s", sup_state_name(s.state));
    printf("  three consecutive fully valid samples -> ARMING\n");

    sup_init(&s, true);
    now = 0xFFFFFF9Cu;
    in = mk_in(1, now - 5, true, true);
    in.arm_request = true;
    sup_step(&s, &in, &out, now);
    bool arm_high = false;
    for (int k = 0; k < 3; k++) {
        now += 100;
        in = precheck_sample((uint32_t)(2 + k), now - 10, now, MUT_NONE, false);
        sup_step(&s, &in, &out, now);
        arm_high = arm_high || out.arm_level;
    }
    CHECK(s.state == SUP_ARMING, "time wraps from 0xFFFFFF9C through 0 during PRECHECK: still ARMING, got %s (now=%u)", sup_state_name(s.state), now);
    sup_init(&s, true);
    now = 0xFFFFFFF0u;
    in = mk_in(1, now - 5, true, true);
    in.arm_request = true;
    sup_step(&s, &in, &out, now);
    now += 100;
    in = precheck_sample(2, 0xFFFFFFF8u, now, MUT_NONE, false);
    sup_step(&s, &in, &out, now);
    CHECK(s.state == SUP_PRECHECK && s.counted == 1, "sample timestamped before the wrap, now after it: age 108 ms counts, counted=%u", s.counted);
    now += 400;
    in = precheck_sample(3, 0xFFFFFFF8u, now, MUT_NONE, false);
    sup_step(&s, &in, &out, now);
    CHECK(s.state == SUP_DISARMED, "wrapped timestamp older than the limit aborts");
    printf("  wraparound: valid across 2^32 boundary, stale across boundary rejected\n");

    sup_init(&s, true);
    s.state = SUP_ARMED;
    in = mk_in(5, 1005, true, true);
    in.sample.interlock_ok = true;
    sup_step(&s, &in, &out, 1000);
    CHECK(s.state == SUP_FAULT && s.reason == SUP_REASON_STALE_SAMPLE, "future timestamp while ARMED -> FAULT, got %s", sup_state_name(s.state));
    sup_init(&s, true);
    s.state = SUP_ARMING;
    s.arming_start_ms = 900;
    s.last_seq = 1;
    in = mk_in(2, 1005, true, true);
    in.sample.interlock_ok = true;
    sup_step(&s, &in, &out, 1000);
    CHECK(s.state == SUP_FAULT && !out.arm_level, "future timestamp while ARMING -> FAULT, ARM low, got %s", sup_state_name(s.state));
    printf("  future timestamps rejected in PRECHECK, ARMING and ARMED\n");
}

static void test_integrated_precheck(void)
{
    printf("T13 integrated PRECHECK (model): physical enable pin high, output mismatch, REV A interlock behaviour\n");
    reset_world(1600);
    step(500);
    fw.en_pin_high = true;
    step(150);
    fw.arm_req = true;
    bool arm_high = false;
    for (int i = 0; i < 1500; i++) {
        step(1);
        arm_high = arm_high || arm_pin();
    }
    CHECK(!arm_high && fw.sup.state == SUP_DISARMED, "enable pin HIGH during PRECHECK: ARM never rose");
    reset_world(1600);
    step(500);
    fw.output_mismatch = true;
    step(150);
    fw.arm_req = true;
    arm_high = false;
    for (int i = 0; i < 1500; i++) {
        step(1);
        arm_high = arm_high || arm_pin();
    }
    CHECK(!arm_high && fw.sup.state == SUP_DISARMED, "output register mismatch during PRECHECK: ARM never rose");
    reset_world(1600);
    step(500);
    hw.loop_ok = false;
    fw.arm_req = true;
    step(1500);
    CHECK(fw.sup.state == SUP_OPEN && !rail(1) && !rail(2), "REV A: loops are not observable before ARM; ARM rises, the first ARMING sample finds INTERLOCK_OK low -> OPEN, rails stay off (state %s)", sup_state_name(fw.sup.state));
    printf("  pin high / mismatch abort before ARM; REV A open loop is detected in ARMING (rails off throughout)\n");
}

static void test_integrated_stale(void)
{
    printf("T11 integrated: sampler frozen / stalled before arm request\n");
    reset_world(1600);
    step(500);
    fw.stall_sampler = true;
    step(600);
    fw.arm_req = true;
    bool arm_high = false;
    for (int i = 0; i < 2500; i++) {
        step(1);
        arm_high = arm_high || arm_pin();
    }
    CHECK(!arm_high, "ARM must never rise with a stalled sampler");
    printf("  stalled sampler: ARM never rose (state %s)\n", sup_state_name(fw.sup.state));
    reset_world(1600);
    step(500);
    fw.arm_req = true;
    step(150);
    fw.stall_sampler = true;
    step(1500);
    CHECK(fw.sup.state != SUP_ARMED, "sampler dying mid-PRECHECK must not produce ARMED, got %s", sup_state_name(fw.sup.state));
}

static void test_watchdog_timeout(void)
{
    printf("T6 watchdog timeout path (WDI stops, e.g. MCU halted) at ttout min/typ/max\n");
    static const uint32_t tt[3] = {900, 1600, 2500};
    for (int k = 0; k < 3; k++) {
        reset_world(tt[k]);
        step(500);
        CHECK(arm_and_enable(), "arm");
        uint32_t last = hw.last_wdi_fall;
        fw.stall_supervisor = true;
        fw.stall_sampler = true;
        step(tt[k] + 100);
        CHECK(hw.resets == 1, "exactly one watchdog reset, got %d", hw.resets);
        CHECK(!rail(1) && !rail(2), "rails off");
        printf("  ttout=%u ms: reset asserted %u ms after last WDI falling edge\n", tt[k], (uint32_t)(hw.wd_reset_until - hw.td - last));
    }
}

static void test_interlock_open(void)
{
    printf("T7 interlock loop / enclosure open while armed\n");
    for (int which = 0; which < 2; which++) {
        reset_world(1600);
        step(500);
        CHECK(arm_and_enable(), "arm");
        if (which == 0) {
            hw.loop_ok = false;
        } else {
            hw.encl_ok = false;
        }
        CHECK(!rail(1) && !rail(2), "rails off immediately (combinational hardware)");
        step(150);
        CHECK(fw.sup.state == SUP_OPEN && !arm_pin(), "supervisor latches OPEN and drives ARM low, state %s", sup_state_name(fw.sup.state));
        hw.loop_ok = true;
        hw.encl_ok = true;
        step(500);
        CHECK(fw.sup.state == SUP_OPEN && !rail(1), "closing the loop does not re-arm");
        fw.arm_req = true;
        step(300);
        CHECK(fw.sup.state == SUP_OPEN, "arm request refused from OPEN");
        fw.disarm_req = true;
        step(400);
        CHECK(fw.sup.state == SUP_DISARMED, "disarm clears OPEN");
        fw.disarm_req = false;
        fw.arm_req = true;
        step(1200);
        CHECK(fw.sup.state == SUP_ARMED, "arm possible again after disarm");
        printf("  %s open: rails off at 0 ms (hardware), supervisor state OPEN, recovery needs disarm\n", which ? "enclosure" : "loop");
    }
}

int main(void)
{
    test_health_core();
    test_all_healthy();
    test_sampler_stall();
    test_cli_stall();
    test_supervisor_stall();
    test_i2c_failure();
    test_mcu_reset();
    test_enable_race();
    test_firmware_enable_permit();
    test_sampler_semantics();
    test_stale_sample_rules();
    test_integrated_stale();
    test_precheck_conditions();
    test_integrated_precheck();
    test_watchdog_timeout();
    test_interlock_open();
    printf("\nchecks=%d failures=%d\n", checks, failures);
    return failures ? 1 : 0;
}
