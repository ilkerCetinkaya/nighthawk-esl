import json
import sqlite3

MANUFACTURERS = ["SoluM", "Hanshow", "Pricer", "TagTurk"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    manufacturer TEXT NOT NULL,
    model TEXT, gateway TEXT, revision TEXT, frequency TEXT, modulation TEXT, bandwidth TEXT,
    antenna TEXT, range_m TEXT, rssi_dbm TEXT, documentation TEXT, security TEXT, confidence TEXT
);
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT, started TEXT, ended TEXT, device_id INTEGER, notes TEXT,
    interlock_state TEXT
);
CREATE TABLE IF NOT EXISTS measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER, t_ms INTEGER, rssi_mv REAL
);
"""

FIELDS = ["manufacturer", "model", "gateway", "revision", "frequency", "modulation", "bandwidth", "antenna",
          "range_m", "rssi_dbm", "documentation", "security", "confidence"]


class Database:
    def __init__(self, path="nighthawk.sqlite"):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def add_device(self, record):
        values = [record.get(f, "unknown") or "unknown" for f in FIELDS]
        cur = self.conn.execute(f"INSERT INTO devices ({','.join(FIELDS)}) VALUES ({','.join('?' * len(FIELDS))})", values)
        self.conn.commit()
        return cur.lastrowid

    def devices(self, manufacturer=None):
        if manufacturer:
            rows = self.conn.execute("SELECT * FROM devices WHERE manufacturer=?", (manufacturer,))
        else:
            rows = self.conn.execute("SELECT * FROM devices")
        return [dict(r) for r in rows]

    def start_session(self, started, device_id, interlock_state, notes=""):
        cur = self.conn.execute("INSERT INTO sessions (started, device_id, interlock_state, notes) VALUES (?,?,?,?)", (started, device_id, interlock_state, notes))
        self.conn.commit()
        return cur.lastrowid

    def end_session(self, session_id, ended):
        self.conn.execute("UPDATE sessions SET ended=? WHERE id=?", (ended, session_id))
        self.conn.commit()

    def add_measurement(self, session_id, t_ms, rssi_mv):
        self.conn.execute("INSERT INTO measurements (session_id, t_ms, rssi_mv) VALUES (?,?,?)", (session_id, t_ms, rssi_mv))

    def commit(self):
        self.conn.commit()

    def measurements(self, session_id):
        return [(r["t_ms"], r["rssi_mv"]) for r in self.conn.execute("SELECT t_ms, rssi_mv FROM measurements WHERE session_id=? ORDER BY t_ms", (session_id,))]

    def export_json(self, path):
        data = {"devices": self.devices(), "sessions": [dict(r) for r in self.conn.execute("SELECT * FROM sessions")]}
        with open(path, "w") as handle:
            json.dump(data, handle, indent=2)

    def export_csv(self, path):
        import csv
        rows = self.devices()
        with open(path, "w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["id"] + FIELDS)
            writer.writeheader()
            writer.writerows(rows)
