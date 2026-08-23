from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DeviceMode(str, Enum):
    STANDALONE_AP = "standalone_ap"
    EXTENSION = "extension"


class ExtensionSource(str, Enum):
    WIRELESS = "wireless"
    ETHERNET = "ethernet"


@dataclass
class DeviceTelemetry:
    model: str = "ESP32-D0WD-V3"
    board_name: str = "NexusNode"
    port: str = "AUTO"
    chip: str = "ESP32-D0WD-V3"
    cpu_mhz: int = 240
    flash_mb: int = 4
    sdk_version: str = "ESP-IDF 5.5.5"
    core_version: str = "Arduino ESP32 Core 3.3.11"
    wifi_mode: str = "AP"
    ssid: str = "NexusNode"
    ap_ip: str = "192.168.4.1"
    subnet: str = "255.255.255.0"
    gateway: str = "192.168.4.1"
    dhcp_enabled: bool = True
    client_count: int = 0
    target_clients: int = 3
    mode: DeviceMode = DeviceMode.STANDALONE_AP
    extension_source: ExtensionSource = ExtensionSource.WIRELESS
    upstream_ssid: str = ""
    upstream_password: str = ""
    connected: bool = False
    free_heap: int = 225924
    uptime: int = 923
    channel: int = 6
    mac: str = "24:6F:28:00:00:01"
    wifi_protocol: str = "802.11 b/g/n (2.4 GHz)"
    firmware_version: str = "v0.1.0"
    connected_devices: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "board": {"name": self.board_name, "model": self.model},
            "port": self.port,
            "chip": self.chip,
            "cpu_mhz": self.cpu_mhz,
            "flash_mb": self.flash_mb,
            "sdk_version": self.sdk_version,
            "core_version": self.core_version,
            "wifi_mode": self.wifi_mode,
            "ssid": self.ssid,
            "ap_ip": self.ap_ip,
            "subnet": self.subnet,
            "gateway": self.gateway,
            "dhcp_enabled": self.dhcp_enabled,
            "client_count": self.client_count,
            "target_clients": self.target_clients,
            "mode": self.mode.value,
            "extension_source": self.extension_source.value,
            "upstream_ssid": self.upstream_ssid,
            "connected": self.connected,
            "free_heap": self.free_heap,
            "uptime": self.uptime,
            "channel": self.channel,
            "mac": self.mac,
            "wifi_protocol": self.wifi_protocol,
            "firmware_version": self.firmware_version,
            "connected_devices": self.connected_devices,
        }
