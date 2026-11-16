import sys
from datetime import datetime

from PySide6.QtWidgets import (QApplication, QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton,
                               QTableWidget, QTableWidgetItem, QTabWidget, QTextEdit, QVBoxLayout, QWidget)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from db import FIELDS, MANUFACTURERS, Database
from report import build_report
from serial_link import Link, find_port


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NIGHTHAWK ESL Security Research")
        self.db = Database()
        self.link = None
        self.session_id = None
        tabs = QTabWidget()
        tabs.addTab(self.build_connection(), "Hardware")
        tabs.addTab(self.build_inventory(), "Inventory")
        tabs.addTab(self.build_monitor(), "RF monitor")
        tabs.addTab(self.build_report_tab(), "Report")
        self.setCentralWidget(tabs)
        self.refresh_devices()

    def build_connection(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        self.status = QLabel("Not connected")
        self.interlock = QLabel("Interlock: unknown")
        button = QPushButton("Connect")
        button.clicked.connect(self.connect)
        refresh = QPushButton("Refresh interlock status")
        refresh.clicked.connect(self.refresh_interlock)
        for item in (self.status, self.interlock, button, refresh):
            layout.addWidget(item)
        layout.addStretch()
        return w

    def build_inventory(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        form = QFormLayout()
        self.inputs = {}
        for field in FIELDS:
            if field == "manufacturer":
                box = QComboBox()
                box.addItems(MANUFACTURERS)
                self.inputs[field] = box
            else:
                self.inputs[field] = QLineEdit("unknown")
            form.addRow(field, self.inputs[field])
        layout.addLayout(form)
        add = QPushButton("Add device")
        add.clicked.connect(self.add_device)
        layout.addWidget(add)
        self.filter = QComboBox()
        self.filter.addItems(["All"] + MANUFACTURERS)
        self.filter.currentTextChanged.connect(self.refresh_devices)
        layout.addWidget(self.filter)
        self.table = QTableWidget(0, len(FIELDS))
        self.table.setHorizontalHeaderLabels(FIELDS)
        layout.addWidget(self.table)
        row = QHBoxLayout()
        for label, fn in (("Export CSV", self.export_csv), ("Export JSON", self.export_json)):
            b = QPushButton(label)
            b.clicked.connect(fn)
            row.addWidget(b)
        layout.addLayout(row)
        return w

    def build_monitor(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        self.figure = Figure(figsize=(6, 3))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.axes = self.figure.add_subplot(111)
        self.axes.set_xlabel("time (ms)")
        self.axes.set_ylabel("detector input (mV)")
        layout.addWidget(self.canvas)
        start = QPushButton("Start passive monitor (100 samples)")
        start.clicked.connect(self.run_monitor)
        layout.addWidget(start)
        return w

    def build_report_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        self.report_text = QTextEdit()
        button = QPushButton("Generate report for last session")
        button.clicked.connect(self.make_report)
        layout.addWidget(button)
        layout.addWidget(self.report_text)
        return w

    def connect(self):
        port = find_port()
        if not port:
            self.status.setText("No Espressif USB device found")
            return
        self.link = Link(port)
        self.status.setText(f"Connected on {port}")
        self.refresh_interlock()

    def refresh_interlock(self):
        if self.link:
            self.interlock.setText("Interlock: " + self.link.interlock_status())

    def add_device(self):
        record = {}
        for field, widget in self.inputs.items():
            record[field] = widget.currentText() if isinstance(widget, QComboBox) else widget.text().strip()
        self.db.add_device(record)
        self.refresh_devices()

    def refresh_devices(self):
        selected = self.filter.currentText() if hasattr(self, "filter") else "All"
        rows = self.db.devices(None if selected == "All" else selected)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, field in enumerate(FIELDS):
                self.table.setItem(r, c, QTableWidgetItem(str(row.get(field, ""))))

    def run_monitor(self):
        if not self.link:
            return
        started = datetime.now().isoformat(timespec="seconds")
        self.session_id = self.db.start_session(started, None, self.link.interlock_status())
        rows = self.link.monitor(100)
        for t, v in rows:
            self.db.add_measurement(self.session_id, t, v)
        self.db.end_session(self.session_id, datetime.now().isoformat(timespec="seconds"))
        self.db.commit()
        self.axes.clear()
        self.axes.plot([t for t, _ in rows], [v for _, v in rows])
        self.canvas.draw()

    def make_report(self):
        if self.session_id is None:
            return
        self.report_text.setPlainText(build_report(self.db, self.session_id, {}))

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "devices.csv")
        if path:
            self.db.export_csv(path)

    def export_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export JSON", "devices.json")
        if path:
            self.db.export_json(path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(900, 650)
    window.show()
    sys.exit(app.exec())
