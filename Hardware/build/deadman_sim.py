import itertools

class Deadman:
    def __init__(self, twd_ms, trst_ms, power_up_ms):
        self.twd = twd_ms
        self.trst = trst_ms
        self.t = 0
        self.last_wdi_fall = 0
        self.wdi = 0
        self.wdo_low_until = None
        self.enout_low_until = power_up_ms + trst_ms
        self.arm = 0
        self.q = None
        self.powered = False
        self.power_up_ms = power_up_ms

    def tick(self, wdi, arm):
        self.t += 1
        if not self.powered and self.t >= self.power_up_ms:
            self.powered = True
            self.last_wdi_fall = self.t
        if self.powered:
            wdo_low = self.wdo_low_until is not None and self.t < self.wdo_low_until
            if self.wdi and not wdi and not wdo_low:
                self.last_wdi_fall = self.t
            if not wdo_low and self.t - self.last_wdi_fall >= self.twd:
                self.wdo_low_until = self.t + self.trst
                self.last_wdi_fall = self.t + self.trst
                wdo_low = True
            enout_low = self.t < self.enout_low_until
            clr_active = wdo_low or enout_low
            if clr_active:
                self.q = 0
            elif arm and not self.arm:
                self.q = 1
        self.wdi = wdi
        self.arm = arm
        return self.q

def run(twd):
    results = {}
    d = Deadman(twd, 200, 5)
    wdi = 1
    q = None
    arm = 0
    log = []
    def step(n, toggle=True, arm_val=None):
        nonlocal wdi, q, arm
        for _ in range(n):
            if arm_val is not None:
                arm = arm_val
            wdi = 0 if (toggle and d.t % 50 == 0) else 1
            q = d.tick(wdi, arm)
    step(10, toggle=True, arm_val=0)
    step(5, toggle=True, arm_val=1)
    results["ARM rises 15 ms after power-up (inside power-up hold) -> permit"] = q
    step(10, toggle=True, arm_val=0)
    step(400, toggle=True, arm_val=0)
    step(5, toggle=True, arm_val=1)
    results["ARM rises after hold, WDI toggling -> permit"] = q
    step(400, toggle=True, arm_val=1)
    results["stays set while WDI toggles"] = q
    t0 = d.t
    step(1, toggle=False)
    cleared = None
    for i in range(1200):
        step(1, toggle=False)
        if q == 0:
            cleared = d.t - t0
            break
    results["supervisor stalls (ARM high): permit cleared after ms"] = cleared
    step(1500, toggle=False)
    results["still stalled, ARM high, long after WDO pulses: permit"] = q
    step(300, toggle=True)
    results["WDI toggling resumes, no ARM edge: permit"] = q
    step(10, toggle=True, arm_val=0)
    step(300, toggle=True, arm_val=0)
    step(5, toggle=True, arm_val=1)
    results["ARM low then high with WDI healthy -> permit"] = q
    return results

for name, twd in (("tWD min 170 ms", 170), ("tWD typ 200 ms", 200), ("tWD max 230 ms", 230)):
    print("==", name)
    for k, v in run(twd).items():
        print(f"  {k}: {v}")
