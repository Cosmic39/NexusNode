/*
 * ============================================================
 * NEXUSNODE V1.0
 * STANDALONE PRIVATE LAN TEST FIRMWARE
 * ============================================================
 *
 * ESP32-D0WD-V3
 *
 * Features:
 *   - Standalone Wi-Fi Access Point
 *   - DHCP
 *   - Private LAN
 *   - AP information
 *   - Connected client count
 *   - Client MAC
 *   - Client IP
 *   - Client RSSI
 *   - Hardware information
 *   - No Internet
 *   - No WAN
 * ============================================================
 */

#include <Arduino.h>
#include <WiFi.h>

#include "esp_wifi.h"
#include "esp_netif.h"

// ============================================================
// CONFIGURATION
// ============================================================

const char* AP_SSID     = "NexusNode";
const char* AP_PASSWORD = "NexusNode123";

constexpr uint8_t AP_CHANNEL  = 6;
constexpr uint8_t MAX_CLIENTS = 3;

// Private LAN
IPAddress AP_IP(192, 168, 4, 1);
IPAddress AP_GATEWAY(192, 168, 4, 1);
IPAddress AP_SUBNET(255, 255, 255, 0);

// ============================================================
// PRINT MAC ADDRESS
// ============================================================

void printMac(const uint8_t* mac) {

    for (int i = 0; i < 6; i++) {

        if (i > 0) {
            Serial.print(":");
        }

        if (mac[i] < 16) {
            Serial.print("0");
        }

        Serial.print(mac[i], HEX);
    }
}

// ============================================================
// GET CLIENT IP FROM DHCP LEASE
// ============================================================

bool getClientIP(
    const uint8_t* mac,
    IPAddress& clientIP
) {

    esp_netif_t* apNetif =
        esp_netif_get_handle_from_ifkey("WIFI_AP_DEF");

    if (apNetif == nullptr) {
        return false;
    }

    esp_netif_pair_mac_ip_t pair{};

    memcpy(pair.mac, mac, 6);

    esp_err_t result =
        esp_netif_dhcps_get_clients_by_mac(
            apNetif,
            1,
            &pair
        );

    if (result != ESP_OK) {
        return false;
    }

    clientIP = IPAddress(pair.ip.addr);

    if (clientIP == IPAddress(0, 0, 0, 0)) {
        return false;
    }

    return true;
}

// ============================================================
// PRINT HARDWARE INFORMATION
// ============================================================

void printHardwareInfo() {

    Serial.println();
    Serial.println("================================================");
    Serial.println("                 HARDWARE INFO");
    Serial.println("================================================");

    Serial.print("Chip Model        : ");
    Serial.println(ESP.getChipModel());

    Serial.print("Chip Revision     : ");
    Serial.println(ESP.getChipRevision());

    Serial.print("CPU Cores         : ");
    Serial.println(ESP.getChipCores());

    Serial.print("CPU Frequency     : ");
    Serial.print(ESP.getCpuFreqMHz());
    Serial.println(" MHz");

    Serial.print("Flash Size        : ");
    Serial.print(ESP.getFlashChipSize() / (1024 * 1024));
    Serial.println(" MB");

    Serial.print("SDK Version       : ");
    Serial.println(ESP.getSdkVersion());

    Serial.print("Arduino Core      : ");
    Serial.println(ESP_ARDUINO_VERSION_STR);

    Serial.print("Free Heap         : ");
    Serial.print(ESP.getFreeHeap());
    Serial.println(" bytes");

    Serial.print("Uptime            : ");
    Serial.print(millis() / 1000);
    Serial.println(" seconds");

    Serial.println("================================================");
}

// ============================================================
// PRINT AP INFORMATION
// ============================================================

void printAPInfo() {

    Serial.println();
    Serial.println("================================================");
    Serial.println("                  ACCESS POINT");
    Serial.println("================================================");

    Serial.print("Mode              : ");
    Serial.println("ACCESS POINT ONLY");

    Serial.print("SSID              : ");
    Serial.println(AP_SSID);

    Serial.print("Password          : ");
    Serial.println(AP_PASSWORD);

    Serial.print("Wi-Fi Protocol    : ");
    Serial.println("802.11 b/g/n");

    Serial.print("Band              : ");
    Serial.println("2.4 GHz");

    Serial.print("Channel           : ");
    Serial.println(AP_CHANNEL);

    Serial.print("AP IP Address     : ");
    Serial.println(WiFi.softAPIP());

    Serial.print("Subnet Mask       : ");
    Serial.println(WiFi.softAPSubnetMask());

    Serial.print("Gateway           : ");
    Serial.println(AP_GATEWAY);

    Serial.print("AP MAC Address    : ");
    Serial.println(WiFi.softAPmacAddress());

    Serial.print("DHCP Server       : ");
    Serial.println("ENABLED");

    Serial.print("Internet          : ");
    Serial.println("DISABLED");

    Serial.print("Maximum Clients   : ");
    Serial.println(MAX_CLIENTS);

    Serial.print("Connected Clients : ");
    Serial.println(WiFi.softAPgetStationNum());

    Serial.println("================================================");
}

// ============================================================
// PRINT CONNECTED CLIENTS
// ============================================================

void printConnectedClients() {

    wifi_sta_list_t stationList{};

    esp_err_t result =
        esp_wifi_ap_get_sta_list(&stationList);

    Serial.println();
    Serial.println("================================================");
    Serial.println("                CONNECTED DEVICES");
    Serial.println("================================================");

    if (result != ESP_OK) {

        Serial.println(
            "[ERROR] Unable to retrieve station list."
        );

        Serial.println("================================================");
        return;
    }

    if (stationList.num == 0) {

        Serial.println("No devices currently connected.");
        Serial.println("================================================");
        return;
    }

    Serial.print("Connected Devices: ");
    Serial.print(stationList.num);
    Serial.print(" / ");
    Serial.println(MAX_CLIENTS);

    Serial.println();

    for (int i = 0; i < stationList.num; i++) {

        wifi_sta_info_t& station = stationList.sta[i];

        Serial.println("-----------------------------------------------");

        Serial.print("Device #");
        Serial.println(i + 1);

        Serial.print("MAC Address       : ");
        printMac(station.mac);
        Serial.println();

        Serial.print("RSSI              : ");
        Serial.print(station.rssi);
        Serial.println(" dBm");

        IPAddress clientIP;

        if (getClientIP(station.mac, clientIP)) {

            Serial.print("IP Address        : ");
            Serial.println(clientIP);

        } else {

            Serial.println(
                "IP Address        : DHCP lease pending"
            );
        }

        Serial.println("Status            : ONLINE");
    }

    Serial.println("-----------------------------------------------");
    Serial.println("================================================");
}

// ============================================================
// PRINT LIVE STATUS
// ============================================================

void printLiveStatus() {

    uint8_t clients =
        WiFi.softAPgetStationNum();

    Serial.println();
    Serial.println("================================================");
    Serial.println("                  LIVE STATUS");
    Serial.println("================================================");

    Serial.print("AP State          : ");
    Serial.println("ONLINE");

    Serial.print("AP IP             : ");
    Serial.println(WiFi.softAPIP());

    Serial.print("Clients           : ");
    Serial.print(clients);
    Serial.print(" / ");
    Serial.println(MAX_CLIENTS);

    Serial.print("Free Heap         : ");
    Serial.print(ESP.getFreeHeap());
    Serial.println(" bytes");

    Serial.print("Uptime            : ");
    Serial.print(millis() / 1000);
    Serial.println(" seconds");

    Serial.println("================================================");
}

// ============================================================
// START ACCESS POINT
// ============================================================

bool startAccessPoint() {

    Serial.println();
    Serial.println("[WIFI] Initializing NexusNode AP...");

    // AP ONLY
    WiFi.mode(WIFI_AP);

    if (!WiFi.softAPConfig(
            AP_IP,
            AP_GATEWAY,
            AP_SUBNET
        )) {

        Serial.println(
            "[ERROR] AP network configuration failed."
        );

        return false;
    }

    bool started =
        WiFi.softAP(
            AP_SSID,
            AP_PASSWORD,
            AP_CHANNEL,
            false,
            MAX_CLIENTS
        );

    if (!started) {

        Serial.println(
            "[ERROR] Access Point startup failed."
        );

        return false;
    }

    Serial.println("[WIFI] NexusNode AP started.");

    return true;
}

// ============================================================
// SETUP
// ============================================================

void setup() {

    Serial.begin(115200);

    delay(2500);

    Serial.println();
    Serial.println();
    Serial.println("################################################");
    Serial.println("#                                              #");
    Serial.println("#               NEXUSNODE V1.0                 #");
    Serial.println("#          STANDALONE PRIVATE LAN              #");
    Serial.println("#                                              #");
    Serial.println("################################################");

    printHardwareInfo();

    if (!startAccessPoint()) {

        Serial.println();
        Serial.println("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!");
        Serial.println("[FATAL] NEXUSNODE FAILED TO START");
        Serial.println("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!");

        return;
    }

    printAPInfo();

    Serial.println();
    Serial.println("NEXUSNODE IS ONLINE.");
    Serial.println("Waiting for devices...");
}

// ============================================================
// LOOP
// ============================================================

void loop() {

    static unsigned long lastUpdate = 0;

    // Update every 3 seconds
    if (millis() - lastUpdate >= 3000) {

        lastUpdate = millis();

        printLiveStatus();
        printAPInfo();
        printConnectedClients();
    }
}