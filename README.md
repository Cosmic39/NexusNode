# NexusNode Command Center

> A modular ESP32-powered network appliance with a Python desktop control center.

NexusNode combines an ESP32 network device with **NexuxNode Command Center**, a cyan-and-black desktop control application for configuring, monitoring, and operating the hardware.

The ESP32 performs the actual networking. The desktop application provides configuration, telemetry, connected-device monitoring, diagnostics, and command control.

---

## Current Status

**Working foundation / V1 development build**

- ✅ Standalone private Wi-Fi access point
- ✅ DHCP through the ESP32 SoftAP
- ✅ Private LAN without Internet
- ✅ Multiple connected clients
- ✅ Client-to-client communication
- ✅ Connected-device information
- ✅ Client MAC address
- ✅ Client IP address when DHCP lease information is available
- ✅ Client RSSI
- ✅ ESP32 hardware telemetry
- ✅ AP/network telemetry
- ✅ Python desktop Command Center
- ✅ Serial-port discovery
- ✅ Real ESP32 handshake
- ✅ Automatic disconnect/reconnect handling
- ✅ GUI control of supported settings
- ✅ Connected-device dashboard
- ✅ Terminal command interface
- ✅ Persistent firmware configuration
- ✅ AP+STA extension-mode architecture

The current classic ESP32 is **2.4 GHz only**.

Ethernet and native USB networking are reserved for future hardware revisions.

---

# 🛜 What Is NexusNode?

NexusNode is a small programmable network appliance built around an ESP32.

The current stable mode is a **standalone private Wi-Fi LAN**:

```text
                 NexusNode
                 192.168.4.1
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Laptop       Android 1    Android 2
```

The network does not require an Internet connection.

---

# 🖥️ NexuxNode Command Center

The Command Center is the Python desktop control application.

It provides:

### Dashboard

- Board model
- Chip revision
- CPU frequency
- CPU cores
- Flash size
- ESP-IDF version
- Arduino ESP32 core version
- Firmware version
- Uptime
- Free heap
- COM port
- Connection state

### Wi-Fi / Network

- SSID
- Wi-Fi mode
- Channel
- Wi-Fi protocol
- AP IP
- Subnet
- Gateway
- DHCP status
- AP MAC
- Client count

### Connected Devices

- Device information when supplied by firmware
- IP address
- MAC address
- RSSI
- Connection status
- Last-seen data

### Controls

- Start
- Stop
- Restart
- Change SSID
- Change password
- Change channel
- Change maximum client count
- Other supported configuration controls

### Terminal

The integrated terminal uses the same protocol layer as the graphical controls.

Example commands:

```text
help
status
board
wifi
clients
ip
scan
diagnostics
ping
start
stop
restart
mode ap
mode extension
set ssid NexusLab
set password MyNewPassword
set channel 11
set max_clients 3
```

---

# 🔧 Hardware

## Current Board

The current development hardware is:

```text
Chip           : ESP32-D0WD-V3
Revision       : 301
CPU            : Dual-core, 240 MHz
Flash          : 4 MB
Wi-Fi          : 2.4 GHz 802.11 b/g/n
ESP-IDF        : v5.5.5
Arduino Core   : 3.3.11
```

### Current hardware limitations

The classic ESP32:

- supports 2.4 GHz Wi-Fi
- does not directly support 5 GHz Wi-Fi
- does not provide native USB networking through its normal USB-UART connection
- does not provide Ethernet without additional hardware

A future hardware revision can use an ESP32-S3 or another native-USB-capable platform for USB networking, plus an Ethernet controller/module for Ethernet features.

---

# 📁 Project Structure

```text
NexusNode/
│
├── app.py
├── README.md
├── requirements.txt
├── project_code_document.md
│
├── firmware/
│   ├── nexuxnode1/
│   │   └── nexuxnode1.ino
│   │
│   └── nexusnode2.ino
│
└── nexusnode/
    ├── __init__.py
    ├── config.py
    ├── protocol.py
    ├── serial_manager.py
    │
    └── ui/
        ├── __init__.py
        └── main_window.py
```

---

# ⚙️ Firmware

NexusNode currently has two important firmware roles.

## 1. `firmware/nexuxnode1/nexuxnode1.ino`

This is the **main Command Center firmware**.

Use this firmware when operating NexusNode through the Python desktop application.

It provides:

- Serial protocol
- HELLO handshake
- Configuration commands
- AP start/stop/restart
- SSID/password configuration
- Channel configuration
- Status telemetry
- Board information
- Network information
- Connected-client information
- Client connect/disconnect events
- Persistent settings through `Preferences`
- Standalone AP mode
- Extension-mode infrastructure

This is the firmware intended for **NexuxNode Command Center**.

---

## 2. `firmware/nexusnode2.ino`

### Standalone Serial Monitor Firmware

This is a **non-UI standalone AP firmware**.

It does **not** require the Python Command Center.

Upload it directly to the ESP32, open the Arduino IDE Serial Monitor at **115200 baud**, and use the ESP32 independently.

It creates the standalone NexusNode network and prints diagnostic information such as:

```text
NEXUSNODE
--------------------------------

AP DATA
SSID            : NexusNode
AP IP           : 192.168.4.1
Subnet          : 255.255.255.0
Gateway         : 192.168.4.1
Channel         : 6
DHCP            : ENABLED
Internet        : DISABLED
Clients         : 2 / 3

CONNECTED DEVICES
--------------------------------
Device #1
MAC             : XX:XX:XX:XX:XX:XX
IP              : 192.168.4.10
RSSI            : -52 dBm
Status          : ONLINE

Device #2
MAC             : XX:XX:XX:XX:XX:XX
IP              : 192.168.4.11
RSSI            : -63 dBm
Status          : ONLINE
```

### When to use `nexusnode2.ino`

Use it when you want:

- a quick standalone AP
- no Python application
- no graphical UI
- direct Serial Monitor diagnostics
- a simple recovery/test firmware
- direct inspection of connected-device information

This firmware is intentionally separate from the Command Center workflow.

---

# 🚀 Installation

## 1. Install Python

Use Python 3.12 or newer.

Check:

```bash
python --version
```

---

## 2. Clone the Repository

```bash
git clone <YOUR-REPOSITORY-URL>
cd NexusNode
```

Replace `<YOUR-REPOSITORY-URL>` with your GitHub repository URL.

---

## 3. Create a Virtual Environment

Windows:

```bash
python -m venv .venv
```

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Command Prompt:

```cmd
.venv\Scripts\activate
```

---

## 4. Install Python Dependencies

```bash
python -m pip install -r requirements.txt
```

Main dependencies:

- **PySide6** — desktop UI
- **pyserial** — COM-port discovery and ESP32 communication
- **pytest** — project testing

---

# 🔌 ESP32 Setup

## 1. Install Arduino IDE

Download Arduino IDE from:

https://www.arduino.cc/en/software/

## 2. Install the ESP32 Board Package

In Arduino IDE:

```text
Tools
→ Board
→ Boards Manager
```

Search:

```text
esp32
```

Install:

**esp32 by Espressif Systems**

Use an ESP32 Arduino 3.3.x toolchain compatible with the project.

---

# 🛜 First-Time Setup — Command Center

Use:

```text
firmware/nexuxnode1/nexuxnode1.ino
```

### Step 1 — Connect the ESP32

Connect the ESP32 to the PC using a USB data cable.

### Step 2 — Open the firmware

Open:

```text
firmware/nexuxnode1/nexuxnode1.ino
```

### Step 3 — Select the board

For the current classic ESP32, select the appropriate ESP32 board profile, typically:

```text
ESP32 Dev Module
```

### Step 4 — Select the COM port

```text
Tools
→ Port
```

Select the ESP32 port.

### Step 5 — Upload

Compile and upload the firmware.

### Step 6 — Close Serial Monitor

Close Arduino IDE Serial Monitor before starting the Python application so the COM port is free.

### Step 7 — Run the Command Center

From the project root:

```bash
python app.py
```

The application will:

1. Detect serial ports
2. Identify the NexusNode device
3. Open the COM connection
4. Perform the HELLO handshake
5. Read board information
6. Read network information
7. Read configuration
8. Read connected clients
9. Start live telemetry

Connection state:

```text
🔴 DISCONNECTED
        ↓
🟡 CONNECTING
        ↓
🟢 CONNECTED
```

---

# 🧪 Standalone Setup — Serial Monitor Mode

Use:

```text
firmware/nexusnode2.ino
```

This mode does not require Python.

### Step 1

Open:

```text
firmware/nexusnode2.ino
```

### Step 2

Select the ESP32 board and COM port.

### Step 3

Upload.

### Step 4

Open:

```text
Tools
→ Serial Monitor
```

Set:

```text
115200 baud
```

### Step 5

Connect devices to:

```text
SSID: NexusNode
Password: NexusNode123
```

The Serial Monitor will show:

- AP information
- AP IP
- subnet
- gateway
- DHCP state
- channel
- client count
- client MAC addresses
- client IP addresses when the DHCP lease is available
- RSSI
- system information
- uptime
- free heap

---

# 🌐 Default Network

```text
SSID:       NexusNode
Password:   NexusNode123

AP IP:      192.168.4.1
Subnet:     255.255.255.0
Network:    192.168.4.0/24

DHCP:       Enabled
Channel:    6
Clients:    3 target
Internet:   None
```

Expected layout:

```text
                 NexusNode
                192.168.4.1
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
       Laptop      Android 1   Android 2
```

The clients can communicate locally without an Internet connection.

---

# 🎛️ Using the Command Center

## Standalone AP

Select:

```text
Standalone AP
```

The ESP32 creates the local NexusNode network.

The dashboard displays the actual hardware/network state reported by the ESP32.

---

## Change SSID

Enter a new SSID and press **Apply**.

The Command Center sends the configuration to the firmware.

The ESP32 changes the actual AP.

The UI then refreshes from the hardware state.

---

## Change Password

Enter a new password and apply it.

Passwords are masked in the UI and are not included in normal telemetry or command logs.

---

## Change Channel

Select a supported channel and apply the configuration.

The ESP32 applies the real channel change.

---

# 🧾 Terminal Commands

| Command | Purpose |
|---|---|
| `help` | Show available commands |
| `status` | Current runtime/network status |
| `board` | Board and SDK information |
| `wifi` | Wi-Fi state |
| `clients` | Connected-client information |
| `ip` | AP IP/subnet information |
| `scan` | Wi-Fi scan request |
| `diagnostics` | Diagnostics request |
| `ping` | Protocol responsiveness test |
| `start` | Start AP |
| `stop` | Stop AP |
| `restart` | Restart AP |
| `mode ap` | Standalone AP mode |
| `mode extension` | Extension mode |
| `set ssid <name>` | Change AP SSID |
| `set password <password>` | Change AP password |
| `set channel <1-13>` | Change Wi-Fi channel |
| `set max_clients <1-10>` | Change maximum clients |

---

# 📡 Extension Mode

The application contains an extension-mode architecture using AP+STA.

The current classic ESP32 can connect to an upstream **2.4 GHz** network while also exposing an AP.

The current project does not implement full Internet/NAT routing.

The current hardware cannot directly use a 5 GHz upstream Wi-Fi network.

Ethernet mode is reserved for future hardware.

---

# 🧠 Architecture

```text
User
 │
 ▼
PySide6 MainWindow
 │
 ▼
SerialManager
 │
 │ newline-delimited JSON
 │ 115200 baud
 ▼
ESP32 Firmware
 │
 ├── Wi-Fi AP / AP+STA
 ├── DHCP
 ├── Preferences storage
 ├── Client events
 └── Telemetry
```

The protocol uses:

- JSON
- newline-delimited messages
- request IDs
- protocol versioning

Example:

```json
{"id":1,"type":"command","protocolVersion":"1.0","command":"STATUS"}
```

---

# 🔒 Security Notes

- Wi-Fi passwords are masked in the desktop UI.
- Password values are not included in normal telemetry.
- Passwords are redacted from normal command logs.
- Firmware stores the Wi-Fi password in ESP32 `Preferences`.

Do not commit real credentials to GitHub.

Protect physical access to the ESP32 and development workstation.

---

# 🛠️ Troubleshooting

## Command Center stays disconnected

Check:

1. ESP32 is powered.
2. Matching firmware is uploaded.
3. Correct COM port exists.
4. Arduino Serial Monitor is closed.
5. No other application is using the COM port.
6. ESP32 identifies itself as NexusNode.
7. Firmware and Command Center use the same protocol version.

---

## Configuration does not apply

Check firmware validation limits:

```text
SSID:          1-32 characters
Password:      8-63 characters
Channel:       1-13
Max clients:   1-10
```

---

## Client IP is missing

A Wi-Fi station can connect before its DHCP lease is available.

A device may temporarily show:

```text
IP: unavailable
```

The IP should appear after the DHCP exchange completes and client information is refreshed.

---

## COM port is unavailable

Make sure:

- Arduino Serial Monitor is closed.
- Another serial application is not using the port.
- The USB cable supports data.
- The correct COM port is selected.
- The ESP32 is still connected.

---

# 🧪 Development Checks

Compile Python:

```bash
python -m compileall app.py nexusnode
```

Run tests:

```bash
python -m pytest
```

Hardware functionality requires a real ESP32 and cannot be completely verified through Python-only tests.

---

# 🗺️ Roadmap

## V1 — Foundation

- [x] ESP32 Wi-Fi AP
- [x] Private LAN
- [x] DHCP
- [x] Multiple clients
- [x] Client-to-client communication
- [x] Board telemetry
- [x] Network telemetry
- [x] Connected-device information
- [x] Python Command Center
- [x] Real serial protocol
- [x] Configuration synchronization
- [x] Automatic reconnect
- [x] Standalone Serial Monitor firmware

## Future

- [ ] More advanced device identification
- [ ] Expanded diagnostics
- [ ] Full Wi-Fi extension workflow
- [ ] Ethernet module
- [ ] Ethernet → Wi-Fi
- [ ] Ethernet → USB
- [ ] Native USB network-device hardware
- [ ] Higher-performance router architecture

---

# 🤝 Contributing

When modifying NexusNode:

1. Keep Python and ESP32 firmware synchronized.
2. Do not invent hardware capabilities.
3. Keep protocol changes synchronized on both sides.
4. Never log credentials.
5. Test networking with real hardware.
6. Preserve standalone AP functionality.
7. Keep `nexusnode2.ino` usable as the independent Serial Monitor recovery/test firmware.

---

# 📜 License

Add the chosen project license here before publishing the repository.

---

## NexusNode

**Small hardware. Local networking. Full control.**
