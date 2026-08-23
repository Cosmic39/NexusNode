from __future__ import annotations

import json
import queue
import time
from typing import Any

from PySide6.QtCore import QObject, QThread, Signal, Slot
import serial
import serial.tools.list_ports

from .protocol import decode_message, encode_command, normalize_clients, parse_terminal_command


class SerialManager(QObject):
    CLIENT_REFRESH_INTERVAL = 1.5

    telemetry_ready = Signal(dict)
    ports_ready = Signal(list)
    log_ready = Signal(str)
    finished = Signal()

    def __init__(self, enable_mock_fallback: bool = False) -> None:
        super().__init__()
        self.enable_mock_fallback = enable_mock_fallback
        self.state: dict[str, Any] = {"connected": False, "port": "DISCONNECTED", "connected_devices": [], "client_count": 0}
        self._running = True
        self._serial_port: str | None = None
        self._active_ser: serial.Serial | None = None
        self._requests: queue.Queue[tuple[str, dict[str, Any]]] = queue.Queue()
        self._next_id = 1
        self._session_id = 0
        self._last_response_at = 0.0
        self._last_clients_refresh_at = 0.0
        self._clients_refresh_requested = False
        self._thread = QThread()
        self.moveToThread(self._thread)
        self._thread.started.connect(self.run)
        self.finished.connect(self._thread.quit)

    def start(self) -> None:
        if not self._thread.isRunning():
            self._thread.start()

    @Slot()
    def run(self) -> None:
        while self._running:
            try:
                scanning_ports = not self._active_ser or not self.state.get("connected", False)
                ports = [
                    port.device
                    for port in serial.tools.list_ports.comports()
                    if "bluetooth" not in port.description.lower()
                ] if scanning_ports else []
                if scanning_ports:
                    self.ports_ready.emit(ports)
                if not self._active_ser or not self._active_ser.is_open:
                    self._attempt_connection(ports)
                try:
                    command, payload = self._requests.get(timeout=0.15)
                    self._execute(command, payload)
                except queue.Empty:
                    if (
                        self._active_ser
                        and self.state.get("connected", False)
                        and (
                            self._clients_refresh_requested
                            or time.monotonic() - self._last_clients_refresh_at >= self.CLIENT_REFRESH_INTERVAL
                        )
                    ):
                        self._clients_refresh_requested = False
                        self._last_clients_refresh_at = time.monotonic()
                        self._request("CLIENTS", {}, timeout=1.0)
                    if self._active_ser and time.monotonic() - self._last_response_at > 1.5:
                        if self._request("STATUS", {}, timeout=0.7) is None:
                            self._close_active_connection("Serial communication lost.")
            except Exception as error:
                self._close_active_connection(f"Serial loop error: {error}")
            self.telemetry_ready.emit(dict(self.state))
            time.sleep(0.25)
        self._close_active_connection("System stopping.")
        self.finished.emit()

    def _attempt_connection(self, ports: list[str]) -> None:
        for port in ports:
            try:
                candidate = serial.Serial(port, 115200, timeout=0.15, write_timeout=0.5, dsrdtr=False, rtscts=False)
                candidate.reset_input_buffer()
                candidate.reset_output_buffer()
                self._active_ser, self._serial_port = candidate, port
                self.state.update({"connected": False, "port": port, "connection_phase": "CONNECTING"})
                hello = self._request("HELLO", {}, timeout=1.5)
                if not hello or not hello.get("success") or hello.get("device") != "NexusNode":
                    raise serial.SerialException("NexusNode handshake rejected")
                if hello.get("protocolVersion") != "1.0":
                    raise serial.SerialException("Unsupported protocol version")
                for command in ("STATUS", "BOARD_INFO", "NETWORK_INFO", "GET_CONFIG", "CLIENTS"):
                    if not self._request(command, {}, timeout=1.0):
                        raise serial.SerialException(f"{command} initialization failed")
                self._session_id += 1
                self.state.update({"connected": True, "port": port, "connection_phase": "CONNECTED"})
                self.log_ready.emit(f"NexusNode connected on {port}")
                return
            except Exception as error:
                self.log_ready.emit(f"Unable to connect to {port}: {error}")
                self._close_active_connection(f"Rejected serial device on {port}.", log=False)
        self.state.update({"connected": False, "port": "DISCONNECTED", "connected_devices": [], "client_count": 0})

    def _request(self, command: str, payload: dict[str, Any], timeout: float) -> dict[str, Any] | None:
        if not self._active_ser or not self._active_ser.is_open:
            return None
        request_id = self._next_id
        self._next_id += 1
        try:
            self._active_ser.write((encode_command(command, request_id, **payload) + "\n").encode("utf-8"))
            self._active_ser.flush()
        except (serial.SerialException, OSError) as error:
            self._close_active_connection(f"Serial write failed: {error}")
            return None
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            raw = self._active_ser.readline().decode("utf-8", errors="replace").strip()
            if not raw:
                continue
            message = decode_message(raw)
            if message is None:
                self.log_ready.emit("ESP32 sent invalid JSON; packet ignored.")
                continue
            self._apply_message(message)
            if message.get("id") is not None:
                self._last_response_at = time.monotonic()
            if message.get("id") == request_id:
                return message
        self.log_ready.emit(f"Timeout waiting for {command}.")
        return None

    def _apply_message(self, message: dict[str, Any]) -> None:
        if message.get("type") == "event":
            event = message.get("event")
            mac = message.get("mac")
            if event == "CLIENT_CONNECTED" and mac:
                clients = self.state.setdefault("connected_devices", [])
                if not any(client.get("mac") == mac for client in clients):
                    clients.append({"mac": str(mac).upper(), "connected": True, "device_name": "Unknown Device", "interface": "WIFI"})
                self.state["client_count"] = len(clients)
                self._clients_refresh_requested = True
            elif event == "CLIENT_DISCONNECTED" and mac:
                self.state["connected_devices"] = [client for client in self.state.get("connected_devices", []) if client.get("mac") != mac]
                self.state["client_count"] = len(self.state["connected_devices"])
                self._clients_refresh_requested = True
            self.log_ready.emit(str(event or "ESP32 event"))
        board = message.get("board")
        if isinstance(board, dict):
            self.state["board"] = board
            board_fields = {
                "model": "chip", "cpu_mhz": "cpu_mhz", "flash_mb": "flash_mb",
                "sdk_version": "sdk_version", "core_version": "core_version",
            }
            for source, target in board_fields.items():
                if source in board:
                    self.state[target] = board[source]
        keys = ("board", "chip", "cpu_mhz", "flash_mb", "sdk_version", "core_version", "wifi_mode", "ssid", "ap_ip", "subnet", "gateway", "dhcp_enabled", "client_count", "target_clients", "mode", "extension_source", "connected", "online", "free_heap", "uptime", "channel", "mac", "wifi_protocol", "firmware_version")
        for key in keys:
            if key in message:
                self.state[key] = message[key]
        clients = normalize_clients(message)
        if clients is not None:
            self.state["connected_devices"] = clients
            self.state["client_count"] = len(clients)
        if isinstance(message.get("data"), dict):
            self._apply_message(message["data"])

    def _execute(self, command: str, payload: dict[str, Any]) -> None:
        safe_payload = {key: ("********" if "password" in key.lower() else value) for key, value in payload.items()}
        self.log_ready.emit(f"> {command} {json.dumps(safe_payload, separators=(',', ':')) if safe_payload else ''}".rstrip())
        response = self._request(command, payload, timeout=3.0)
        if response is None:
            self.log_ready.emit(f"{command}: no response")
        elif not response.get("success", False):
            self.log_ready.emit(f"{command}: {response.get('error', 'operation failed')}")
        else:
            self.log_ready.emit(json.dumps(response, indent=2, sort_keys=True))
            if command in {"SET_SSID", "SET_PASSWORD", "SET_WIFI_CONFIG", "SET_CHANNEL", "SET_TXPOWER", "SET_BANDWIDTH", "SET_MAX_CLIENTS", "START", "STOP", "RESTART", "SET_MODE"}:
                self._request("STATUS", {}, timeout=1.5)

    def _close_active_connection(self, reason: str, log: bool = True) -> None:
        if self._active_ser:
            try:
                self._active_ser.close()
            except serial.SerialException:
                pass
        self._active_ser = None
        self._serial_port = None
        self._session_id += 1
        while not self._requests.empty():
            try:
                self._requests.get_nowait()
            except queue.Empty:
                break
        self.state.update({"connected": False, "port": "DISCONNECTED", "connection_phase": "DISCONNECTED", "connected_devices": [], "client_count": 0})
        self._clients_refresh_requested = False
        self._last_clients_refresh_at = 0.0
        if log:
            self.log_ready.emit(f"Status: {reason}")

    def stop(self) -> None:
        self._running = False
        if self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(2000)

    def handle_command(self, command: str) -> None:
        parsed = parse_terminal_command(command)
        if parsed is None:
            self.log_ready.emit("Invalid command. Try: status, board, wifi, clients, set ssid <name>")
            return
        self._requests.put(parsed)

    def apply_settings(self, *, ssid: str, password: str, mode: Any, extension_source: Any, upstream_ssid: str = "", upstream_password: str = "") -> None:
        payload = {"ssid": ssid, "password": password, "mode": "MODE_EXTENSION" if str(mode).endswith("EXTENSION") else "MODE_AP"}
        if payload["mode"] == "MODE_EXTENSION":
            payload.update({"source": str(extension_source).split(".")[-1].upper(), "upstreamSsid": upstream_ssid, "upstreamPassword": upstream_password})
        self._requests.put(("SET_WIFI_CONFIG", payload))

    def start_system(self) -> None:
        self._requests.put(("START", {}))

    def stop_system(self) -> None:
        self._requests.put(("STOP", {}))
