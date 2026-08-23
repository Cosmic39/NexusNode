from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from nexusnode.config import DeviceMode, ExtensionSource
from nexusnode.serial_manager import SerialManager


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("NEXUSNODE COMMAND CENTER")
        self.resize(1250, 900)
        self.setStyleSheet(
            """
            QWidget { background: #0a0f18; color: #d9f9ff; font-family: 'Segoe UI'; }
            QMainWindow { background: #0a0f18; }
            QLabel { color: #d9f9ff; }
            QLineEdit, QComboBox, QTextEdit, QTableWidget { background: #111b2a; color: #d9f9ff; border: 1px solid #1d2d42; border-radius: 8px; }
            QPushButton { background: #15354d; color: #d9f9ff; border: 1px solid #1d7f9a; border-radius: 8px; padding: 10px 16px; }
            QPushButton:hover { background: #184a69; }
            QGroupBox { border: 1px solid #1c3552; border-radius: 10px; margin-top: 12px; padding-top: 12px; }
            QGroupBox::title { color: #8fe8ff; subcontrol-origin: margin; left: 12px; }
            QTableWidget { gridline-color: #1c3552; }
            QHeaderView::section { background: #0f1d2d; color: #7ddff5; }
            """
        )

        self.serial_manager = SerialManager(enable_mock_fallback=False)
        self.serial_manager.telemetry_ready.connect(self.apply_telemetry)
        self.serial_manager.ports_ready.connect(self.update_ports)
        self.serial_manager.log_ready.connect(self.append_terminal)

        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.layout = QVBoxLayout(self.central)

        # Header Section
        self.header = QHBoxLayout()
        self.title = QLabel("NEXUSNODE COMMAND CENTER")
        self.title.setStyleSheet("font-size: 24px; font-weight: 700; color: #8fe8ff; letter-spacing: 2px;")
        self.header.addWidget(self.title)
        self.header.addStretch()
        self.status_indicator = QLabel("DISCONNECTED")
        self.status_indicator.setAlignment(Qt.AlignCenter)
        self.status_indicator.setStyleSheet(
            "background: #3b1212; color: #ff8a8a; border: 1px solid #d64646; border-radius: 12px; padding: 8px 18px; font-weight: 700;"
        )
        self.header.addWidget(self.status_indicator)
        self.layout.addLayout(self.header)

        # Main Content Layout
        self.content = QHBoxLayout()
        self.left_panel = QVBoxLayout()
        self.right_panel = QVBoxLayout()

        # Board Group
        self.board_group = QGroupBox("BOARD")
        self.board_layout = QFormLayout(self.board_group)
        self.model_label = QLabel("---")
        self.port_label = QLabel("DISCONNECTED")
        self.cpu_label = QLabel("---")
        self.flash_label = QLabel("---")
        self.sdk_label = QLabel("---")
        self.core_label = QLabel("---")
        self.board_layout.addRow("Model:", self.model_label)
        self.board_layout.addRow("COM:", self.port_label)
        self.board_layout.addRow("CPU:", self.cpu_label)
        self.board_layout.addRow("Flash:", self.flash_label)
        self.board_layout.addRow("SDK:", self.sdk_label)
        self.board_layout.addRow("Core:", self.core_label)
        self.left_panel.addWidget(self.board_group)

        # Mode Selection Group
        self.mode_group_box = QGroupBox("MODE CONFIGURATION")
        self.mode_layout = QVBoxLayout(self.mode_group_box)
        self.mode_row = QHBoxLayout()
        self.standalone_btn = QRadioButton("Standalone AP")
        self.extension_btn = QRadioButton("Extension")
        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.standalone_btn, 0)
        self.mode_group.addButton(self.extension_btn, 1)
        self.mode_group.setExclusive(True)
        self.standalone_btn.setChecked(True)
        self.mode_row.addWidget(self.standalone_btn)
        self.mode_row.addWidget(self.extension_btn)
        self.mode_layout.addLayout(self.mode_row)

        # Extension Source Dropdown
        self.source_label = QLabel("Extension source:")
        self.extension_source_combo = QComboBox()
        self.extension_source_combo.addItems(["Wireless", "Ethernet"])
        self.mode_layout.addWidget(self.source_label)
        self.mode_layout.addWidget(self.extension_source_combo)

        # Dynamic Config Form Fields
        self.config_form = QFormLayout()
        self.ssid_label = QLabel("Local AP SSID:")
        self.ssid_input = QLineEdit("NexusNode")
        self.password_label = QLabel("Local AP Password:")
        self.password_input = QLineEdit("NexusNode123")
        self.password_input.setEchoMode(QLineEdit.Password)

        self.upstream_ssid_label = QLabel("Upstream SSID:")
        self.upstream_ssid_input = QLineEdit("")
        self.upstream_password_label = QLabel("Upstream Password:")
        self.upstream_password_input = QLineEdit("")
        self.upstream_password_input.setEchoMode(QLineEdit.Password)

        self.config_form.addRow(self.ssid_label, self.ssid_input)
        self.config_form.addRow(self.password_label, self.password_input)
        self.config_form.addRow(self.upstream_ssid_label, self.upstream_ssid_input)
        self.config_form.addRow(self.upstream_password_label, self.upstream_password_input)
        self.mode_layout.addLayout(self.config_form)

        self.apply_button = QPushButton("Apply configuration")
        self.apply_button.clicked.connect(self.apply_configuration)
        self.mode_layout.addWidget(self.apply_button)
        self.left_panel.addWidget(self.mode_group_box)

        self.standalone_btn.toggled.connect(self.update_mode_ui)
        self.extension_btn.toggled.connect(self.update_mode_ui)

        # Network Group
        self.network_group = QGroupBox("ACCESS POINT")
        self.network_layout = QFormLayout(self.network_group)
        self.ssid_value = QLabel("---")
        self.ap_ip_value = QLabel("---")
        self.channel_value = QLabel("---")
        self.clients_value = QLabel("0 / 3")
        self.network_layout.addRow("SSID:", self.ssid_value)
        self.network_layout.addRow("AP IP:", self.ap_ip_value)
        self.network_layout.addRow("Channel:", self.channel_value)
        self.network_layout.addRow("Clients:", self.clients_value)
        self.left_panel.addWidget(self.network_group)

        # Power Controls
        self.controls = QHBoxLayout()
        self.start_button = QPushButton("START SYSTEM")
        self.stop_button = QPushButton("STOP SYSTEM")
        self.controls.addWidget(self.start_button)
        self.controls.addWidget(self.stop_button)
        self.left_panel.addLayout(self.controls)

        # Connected Devices Table
        self.devices_group = QGroupBox("CONNECTED DEVICES")
        self.devices_layout = QVBoxLayout(self.devices_group)
        self.device_table = QTableWidget(0, 6)
        self.device_table.setHorizontalHeaderLabels(["Device", "IP ADDRESS", "MAC ADDRESS", "RSSI", "STATUS", "LAST SEEN"])
        self.device_table.horizontalHeader().setStretchLastSection(True)
        self.devices_layout.addWidget(self.device_table)
        self.right_panel.addWidget(self.devices_group)

        # Terminal Panel
        self.terminal_group = QGroupBox("TERMINAL")
        self.terminal_layout = QVBoxLayout(self.terminal_group)
        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setText("NexusNode Command Center initialized\n")
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter command...")
        self.command_input.returnPressed.connect(self.execute_command)
        self.terminal_layout.addWidget(self.terminal_output)
        self.terminal_layout.addWidget(self.command_input)
        self.right_panel.addWidget(self.terminal_group)

        self.content.addLayout(self.left_panel, 1)
        self.content.addLayout(self.right_panel, 1)
        self.layout.addLayout(self.content)

        self.start_button.clicked.connect(self.start_system)
        self.stop_button.clicked.connect(self.stop_system)
        self._bootstrapped = False

        self.update_mode_ui()

    def update_mode_ui(self) -> None:
        """Dynamically adapts configuration fields based on mode."""
        if self.standalone_btn.isChecked():
            self.ssid_label.setText("Local AP SSID:")
            self.password_label.setText("Local AP Password:")
            self.source_label.hide()
            self.extension_source_combo.hide()
            self.upstream_ssid_label.hide()
            self.upstream_ssid_input.hide()
            self.upstream_password_label.hide()
            self.upstream_password_input.hide()
        else:
            self.ssid_label.setText("Local AP SSID:")
            self.password_label.setText("Local AP Password:")
            self.source_label.show()
            self.extension_source_combo.show()
            self.upstream_ssid_label.show()
            self.upstream_ssid_input.show()
            self.upstream_password_label.show()
            self.upstream_password_input.show()

    def update_ports(self, ports: list[str]) -> None:
        if not ports and not self.serial_manager.state.get("connected", False):
            self.port_label.setText("DISCONNECTED")

    def apply_telemetry(self, telemetry: dict[str, Any]) -> None:
        connected = bool(telemetry.get("connected", False))
        phase = telemetry.get("connection_phase", "")

        online = bool(telemetry.get("online", False))
        if phase == "CONNECTING":
            self.status_indicator.setText("CONNECTING")
            self.status_indicator.setStyleSheet(
                "background: #3b2b12; color: #ffd27a; border: 1px solid #d69b2d; border-radius: 12px; padding: 8px 18px; font-weight: 700;"
            )
        elif connected:
            self.status_indicator.setText("ONLINE" if online else "CONNECTED / OFFLINE")
            self.status_indicator.setStyleSheet(
                "background: #0d3a2d; color: #7af3b7; border: 1px solid #1fbf77; border-radius: 12px; padding: 8px 18px; font-weight: 700;"
            )
        else:
            self.status_indicator.setText("DISCONNECTED")
            self.status_indicator.setStyleSheet(
                "background: #3b1212; color: #ff8a8a; border: 1px solid #d64646; border-radius: 12px; padding: 8px 18px; font-weight: 700;"
            )

        board = telemetry.get("board", {})
        self.model_label.setText(str(board.get("model", "ESP32-D0WD-V3")) if connected else "---")
        self.port_label.setText(str(telemetry.get("port", "DISCONNECTED")))
        self.cpu_label.setText(f"{telemetry.get('cpu_mhz', 240)} MHz" if connected else "---")
        self.flash_label.setText(f"{telemetry.get('flash_mb', 4)} MB" if connected else "---")
        self.sdk_label.setText(str(telemetry.get("sdk_version", "ESP-IDF 5.5.5")) if connected else "---")
        self.core_label.setText(str(telemetry.get("core_version", "Arduino ESP32 Core 3.3.11")) if connected else "---")

        self.ssid_value.setText(str(telemetry.get("ssid", "NexusNode")) if connected else "---")
        self.ap_ip_value.setText(str(telemetry.get("ap_ip", "192.168.4.1")) if connected else "---")
        self.channel_value.setText(str(telemetry.get("channel", 6)) if connected else "---")
        self.clients_value.setText(
            f"{telemetry.get('client_count', 0)} / {telemetry.get('target_clients', 3)}" if connected else "0 / 3"
        )
        if connected and not self.ssid_input.hasFocus():
            self.ssid_input.setText(str(telemetry.get("ssid", "NexusNode")))
        if connected:
            mode = str(telemetry.get("mode", "MODE_AP")).lower()
            self.standalone_btn.setChecked(mode in {"mode_ap", "standalone_ap"})
            self.extension_btn.setChecked(mode in {"mode_extension", "extension"})

        devices = telemetry.get("connected_devices", []) if connected else []
        self.device_table.setRowCount(len(devices))
        for row_idx, device in enumerate(devices):
            name = device.get("device_name") or device.get("name") or "Unknown Device"
            ip = device.get("ip")
            rssi = device.get("rssi")
            status = "ONLINE" if device.get("connected", True) else "OFFLINE"
            self.device_table.setItem(row_idx, 0, QTableWidgetItem(str(name)))
            self.device_table.setItem(row_idx, 1, QTableWidgetItem(str(ip) if ip else "-"))
            self.device_table.setItem(row_idx, 2, QTableWidgetItem(str(device.get("mac", "-"))))
            self.device_table.setItem(row_idx, 3, QTableWidgetItem(f"{rssi} dBm" if rssi is not None else "-"))
            self.device_table.setItem(row_idx, 4, QTableWidgetItem(status))
            self.device_table.setItem(row_idx, 5, QTableWidgetItem(str(device.get("last_seen", "-"))))
            self.device_table.item(row_idx, 4).setForeground(Qt.green if status == "ONLINE" else Qt.gray)

    def append_terminal(self, message: str) -> None:
        self.terminal_output.append(message)
        self.terminal_output.ensureCursorVisible()

    def execute_command(self) -> None:
        command = self.command_input.text().strip()
        if not command:
            return
        self.command_input.clear()
        self.serial_manager.handle_command(command)

    def apply_configuration(self) -> None:
        selected_mode = DeviceMode.STANDALONE_AP if self.standalone_btn.isChecked() else DeviceMode.EXTENSION
        selected_source = (
            ExtensionSource.WIRELESS
            if self.extension_source_combo.currentText().lower() == "wireless"
            else ExtensionSource.ETHERNET
        )
        ssid = self.ssid_input.text().strip() or "NexusNode"
        password = self.password_input.text().strip()
        upstream_ssid = self.upstream_ssid_input.text().strip()
        upstream_password = self.upstream_password_input.text().strip()

        self.serial_manager.apply_settings(
            ssid=ssid,
            password=password,
            mode=selected_mode,
            extension_source=selected_source,
            upstream_ssid=upstream_ssid,
            upstream_password=upstream_password,
        )

    def start_system(self) -> None:
        self.append_terminal("> START")
        self.serial_manager.start_system()

    def stop_system(self) -> None:
        self.append_terminal("> STOP")
        self.serial_manager.stop_system()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._bootstrapped:
            self._bootstrapped = True
            self.serial_manager.start()

    def closeEvent(self, event) -> None:
        self.serial_manager.stop()
        super().closeEvent(event)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())