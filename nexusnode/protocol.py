from __future__ import annotations

import json
from typing import Any

PROTOCOL_VERSION = "1.0"
COMMANDS = {
    "HELLO", "STATUS", "BOARD_INFO", "NETWORK_INFO", "CLIENTS", "GET_CONFIG",
    "SET_SSID", "SET_PASSWORD", "SET_WIFI_CONFIG", "SET_CHANNEL", "SET_TXPOWER",
    "SET_BANDWIDTH", "SET_MAX_CLIENTS", "START", "STOP", "RESTART", "SET_MODE",
    "GET_MODE", "PING", "DIAGNOSTICS", "SCAN",
}

def encode_command(command: str, request_id: int, **payload: Any) -> str:
    message: dict[str, Any] = {
        "id": request_id,
        "type": "command",
        "protocolVersion": PROTOCOL_VERSION,
        "command": command.upper(),
    }
    message.update(payload)
    return json.dumps(message, separators=(",", ":"))


def decode_message(raw: str) -> dict[str, Any] | None:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if isinstance(data, dict):
        return data
    return None


def normalize_clients(message: dict[str, Any]) -> list[dict[str, Any]] | None:
    """Return only client records supplied by the device, with safe display fields."""
    raw_clients = message.get("clients", message.get("connected_devices"))
    if not isinstance(raw_clients, list):
        return None
    clients: list[dict[str, Any]] = []
    for raw_client in raw_clients:
        if not isinstance(raw_client, dict) or not raw_client.get("mac"):
            continue
        client = dict(raw_client)
        client["mac"] = str(client["mac"]).upper()
        client.setdefault("ip", None)
        client["connected"] = bool(client.get("connected", True))
        client.setdefault("device_name", "Unknown Device")
        client.setdefault("interface", "WIFI")
        clients.append(client)
    return clients


def parse_terminal_command(text: str) -> tuple[str, dict[str, Any]] | None:
    """Translate the human terminal grammar into the wire command grammar."""
    parts = text.strip().split(maxsplit=2)
    if not parts:
        return None
    verb = parts[0].lower()
    if verb == "status":
        return "STATUS", {}
    if verb == "board":
        return "BOARD_INFO", {}
    if verb == "wifi":
        return "NETWORK_INFO", {}
    if verb == "clients":
        return "CLIENTS", {}
    if verb == "ip":
        return "NETWORK_INFO", {}
    if verb == "scan":
        return "SCAN", {}
    if verb == "diagnostics":
        return "DIAGNOSTICS", {}
    if verb == "restart":
        return "RESTART", {}
    if verb == "start":
        return "START", {}
    if verb == "stop":
        return "STOP", {}
    if verb == "ping":
        return "PING", {}
    if verb == "mode" and len(parts) == 2:
        value = parts[1].lower()
        return "SET_MODE", {"mode": "MODE_EXTENSION" if value in {"extension", "ext"} else "MODE_AP"}
    if verb == "set" and len(parts) == 3:
        field, value = parts[1].lower(), parts[2].strip()
        try:
            if field == "ssid":
                return "SET_SSID", {"ssid": value}
            if field == "password":
                return "SET_PASSWORD", {"password": value}
            if field == "channel":
                return "SET_CHANNEL", {"channel": int(value)}
            if field == "txpower":
                return "SET_TXPOWER", {"txPower": value}
            if field == "bandwidth":
                return "SET_BANDWIDTH", {"bandwidth": value}
            if field == "max_clients":
                return "SET_MAX_CLIENTS", {"maxClients": int(value)}
            return None
        except ValueError:
            return None
    return None


def build_telemetry(state: dict[str, Any], ports: list[str] | None = None) -> dict[str, Any]:
    devices = state.get("connected_devices", [])
    payload = {
        "type": "status",
        "board": state.get("board", {"name": "NexusNode", "model": "ESP32-D0WD-V3"}),
        "port": state.get("port", ports[0] if ports else "AUTO"),
        "chip": state.get("chip", "ESP32-D0WD-V3"),
        "cpu_mhz": state.get("cpu_mhz", 240),
        "flash_mb": state.get("flash_mb", 4),
        "sdk_version": state.get("sdk_version", "ESP-IDF 5.5.5"),
        "core_version": state.get("core_version", "Arduino ESP32 Core 3.3.11"),
        "wifi_mode": state.get("wifi_mode", "AP"),
        "ssid": state.get("ssid", "NexusNode"),
        "ap_ip": state.get("ap_ip", "192.168.4.1"),
        "subnet": state.get("subnet", "255.255.255.0"),
        "gateway": state.get("gateway", "192.168.4.1"),
        "dhcp_enabled": state.get("dhcp_enabled", True),
        "client_count": state.get("client_count", len(devices)),
        "target_clients": state.get("target_clients", 3),
        "mode": state.get("mode", "standalone_ap"),
        "extension_source": state.get("extension_source", "wireless"),
        "upstream_ssid": state.get("upstream_ssid", ""),
        "connected": state.get("connected", False),
        "free_heap": state.get("free_heap", 225924),
        "uptime": state.get("uptime", 923),
        "channel": state.get("channel", 6),
        "mac": state.get("mac", "24:6F:28:00:00:01"),
        "wifi_protocol": state.get("wifi_protocol", "802.11 b/g/n (2.4 GHz)"),
        "firmware_version": state.get("firmware_version", "v0.1.0"),
        "connected_devices": devices if isinstance(devices, list) else [],
    }
    return payload


def handle_command(command: str, state: dict[str, Any]) -> str:
    cmd = (command or "").strip().lower()
    if not cmd or cmd in {"help", "?"}:
        return "Commands: status, wifi, clients, ip, channel, mode ap, mode extension, scan, restart, clear, help"

    if cmd == "status":
        return json.dumps(build_telemetry(state), indent=2, sort_keys=True)

    if cmd == "wifi":
        return json.dumps({
            "ssid": state.get("ssid", "NexusNode"),
            "mode": state.get("wifi_mode", "AP"),
            "channel": state.get("channel", 6),
            "protocol": state.get("wifi_protocol", "802.11 b/g/n (2.4 GHz)"),
            "connected": state.get("connected", True),
        }, indent=2)

    if cmd == "clients":
        devices = state.get("connected_devices", [])
        return json.dumps({"type": "clients", "count": len(devices), "clients": devices}, indent=2)

    if cmd == "ip":
        return json.dumps({"ap_ip": state.get("ap_ip", "192.168.4.1"), "subnet": state.get("subnet", "255.255.255.0")}, indent=2)

    if cmd.startswith("channel "):
        try:
            value = int(cmd.split(" ", 1)[1].strip())
            state["channel"] = value
            return json.dumps({"channel": value, "status": "updated"}, indent=2)
        except ValueError:
            return "Channel command requires a numeric value. Example: channel 6"

    if cmd.startswith("mode "):
        value = cmd.split(" ", 1)[1].strip()
        if value in {"ap", "standalone", "standalone_ap"}:
            state["mode"] = "standalone_ap"
            state["wifi_mode"] = "AP"
            return json.dumps({"mode": "standalone_ap", "status": "updated"}, indent=2)
        if value in {"extension", "ext"}:
            state["mode"] = "extension"
            state["wifi_mode"] = "AP+STA"
            return json.dumps({"mode": "extension", "status": "updated"}, indent=2)
        return "Unsupported mode. Use: mode ap or mode extension"

    if cmd == "scan":
        return json.dumps({
            "scan": [
                {"ssid": "NexusNode", "strength": -42, "channel": 6},
                {"ssid": "NearbyOffice", "strength": -68, "channel": 1},
            ]
        }, indent=2)

    if cmd == "restart":
        state["uptime"] = 0
        return json.dumps({"status": "restarting", "firmware_version": state.get("firmware_version", "v0.1.0")}, indent=2)

    if cmd == "clear":
        return "Terminal cleared."

    return f"Unknown command: {command}. Try help."
