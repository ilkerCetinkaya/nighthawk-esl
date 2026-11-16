from datetime import datetime


def build_report(db, session_id, device):
    rows = db.measurements(session_id)
    values = [v for _, v in rows]
    lines = [f"# NIGHTHAWK test report", f"Generated: {datetime.now().isoformat(timespec='seconds')}", ""]
    lines.append(f"Device: {device.get('manufacturer', 'unknown')} {device.get('model', 'unknown')}")
    lines.append(f"Measurement confidence: {device.get('confidence', 'unknown')}")
    lines.append("")
    if values:
        lines.append(f"Samples: {len(values)}  min {min(values):.1f} mV  max {max(values):.1f} mV  mean {sum(values) / len(values):.1f} mV")
    else:
        lines.append("No measurements recorded.")
    lines.append("")
    lines.append("Values are raw detector-input millivolts. They are not calibrated dBm.")
    return "\n".join(lines)
