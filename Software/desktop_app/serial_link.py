import serial
from serial.tools import list_ports


def find_port():
    for p in list_ports.comports():
        if p.vid == 0x303A:
            return p.device
    return None


class Link:
    def __init__(self, port, baud=115200):
        self.ser = serial.Serial(port, baud, timeout=0.5)

    def command(self, text):
        self.ser.reset_input_buffer()
        self.ser.write((text + "\n").encode())
        lines = []
        while True:
            line = self.ser.readline().decode(errors="replace").strip()
            if not line:
                break
            lines.append(line)
        return [l for l in lines if l != text and not l.startswith("nighthawk>")]

    def interlock_status(self):
        out = " ".join(self.command("rf status"))
        return out

    def monitor(self, n=50):
        rows = []
        for line in self.command(f"rf monitor {n}"):
            parts = line.split(",")
            if len(parts) == 2 and parts[0].isdigit():
                rows.append((int(parts[0]), float(parts[1])))
        return rows

    def close(self):
        self.ser.close()
