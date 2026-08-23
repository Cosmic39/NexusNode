#include <Arduino.h>
#include <WiFi.h>
#include <Preferences.h>
extern "C" {
#include "esp_netif.h"
#include "esp_wifi.h"
}

const char *NEXUXNODE_FIRMWARE_VERSION = "1.0.0";
const char *PROTOCOL_VERSION = "1.0";
const char *DEFAULT_SSID = "NexusNode";
const char *DEFAULT_PASSWORD = "NexusNode123";

Preferences preferences;
String ssid;
String password;
int channel = 6;
int maxClients = 3;
const int MAX_CLIENTS_SUPPORTED = 10;
String mode = "MODE_AP";
bool apRunning = false;
unsigned long startedAt = 0;
esp_netif_t *apNetif = nullptr;

String valueFor(const String &json, const String &key) {
  String marker = "\"" + key + "\":";
  int start = json.indexOf(marker);
  if (start < 0) return "";
  start += marker.length();
  while (start < (int)json.length() && (json[start] == ' ' || json[start] == '"')) start++;
  int end = start;
  while (end < (int)json.length() && json[end] != '"' && json[end] != ',' && json[end] != '}') end++;
  return json.substring(start, end);
}

String requestId(const String &json) { return valueFor(json, "id"); }

void response(const String &id, const String &command, bool success, const String &extra = "", const String &error = "") {
  Serial.print("{\"id\":"); Serial.print(id.length() ? id : "null");
  Serial.print(",\"type\":\"response\",\"success\":"); Serial.print(success ? "true" : "false");
  Serial.print(",\"command\":\""); Serial.print(command); Serial.print("\"");
  if (error.length()) { Serial.print(",\"error\":\""); Serial.print(error); Serial.print("\""); }
  if (extra.length()) { Serial.print(","); Serial.print(extra); }
  Serial.println("}");
}

void eventMessage(const char *event) {
  Serial.print("{\"type\":\"event\",\"event\":\""); Serial.print(event); Serial.println("\"}");
}

void macText(const uint8_t *mac, char *buffer, size_t length) {
  snprintf(buffer, length, "%02X:%02X:%02X:%02X:%02X:%02X", mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
}

void stationEvent(void *arg, esp_event_base_t base, int32_t eventId, void *eventData) {
  (void)arg; (void)base;
  const uint8_t *mac = nullptr;
  if (eventId == WIFI_EVENT_AP_STACONNECTED) mac = ((wifi_event_ap_staconnected_t *)eventData)->mac;
  if (eventId == WIFI_EVENT_AP_STADISCONNECTED) mac = ((wifi_event_ap_stadisconnected_t *)eventData)->mac;
  if (!mac) return;
  char text[18]; macText(mac, text, sizeof(text));
  Serial.print("{\"type\":\"event\",\"event\":\"");
  Serial.print(eventId == WIFI_EVENT_AP_STACONNECTED ? "CLIENT_CONNECTED" : "CLIENT_DISCONNECTED");
  Serial.print("\",\"mac\":\""); Serial.print(text); Serial.println("\"}");
}

String clientsJson() {
  wifi_sta_list_t stations = {};
  if (!apRunning || esp_wifi_ap_get_sta_list(&stations) != ESP_OK) return "\"count\":0,\"clients\":[]";
  esp_netif_pair_mac_ip_t pairs[MAX_CLIENTS_SUPPORTED] = {};
  const int stationCount = min((int)stations.num, MAX_CLIENTS_SUPPORTED);
  for (int i = 0; i < stationCount; ++i) memcpy(pairs[i].mac, stations.sta[i].mac, 6);
  esp_err_t leaseStatus = ESP_FAIL;
  if (apNetif && stationCount > 0) leaseStatus = esp_netif_dhcps_get_clients_by_mac(apNetif, stationCount, pairs);
  String result = "\"count\":" + String(stationCount) + ",\"clients\":[";
  for (int i = 0; i < stationCount; ++i) {
    if (i) result += ",";
    char mac[18]; macText(stations.sta[i].mac, mac, sizeof(mac));
    result += "{\"mac\":\"" + String(mac) + "\",\"ip\":";
    char ip[16];
    if (leaseStatus == ESP_OK && pairs[i].ip.addr && esp_ip4addr_ntoa(&pairs[i].ip, ip, sizeof(ip))) result += "\"" + String(ip) + "\"";
    else result += "null";
    result += ",\"rssi\":" + String(stations.sta[i].rssi) + ",\"connected\":true}";
  }
  return result + "]";
}

void startAp() {
  IPAddress ip(192, 168, 4, 1), gateway(192, 168, 4, 1), subnet(255, 255, 255, 0);
  WiFi.mode(mode == "MODE_EXTENSION" ? WIFI_AP_STA : WIFI_AP);
  WiFi.softAPConfig(ip, gateway, subnet);
  apRunning = WiFi.softAP(ssid.c_str(), password.c_str(), channel, false, maxClients);
  apNetif = esp_netif_get_handle_from_ifkey("WIFI_AP_DEF");
  if (apRunning) { startedAt = millis(); eventMessage("AP_STARTED"); }
}

void stopAp() { WiFi.softAPdisconnect(true); apRunning = false; eventMessage("AP_STOPPED"); }

String statusJson() {
  String result = "\"online\":" + String(apRunning ? "true" : "false");
  result += ",\"mode\":\"" + mode + "\",\"ssid\":\"" + ssid + "\",\"channel\":" + String(channel);
  result += ",\"client_count\":" + String(WiFi.softAPgetStationNum());
  result += ",\"uptime\":" + String((millis() - startedAt) / 1000);
  result += ",\"free_heap\":" + String(ESP.getFreeHeap());
  result += ",\"ap_ip\":\"" + WiFi.softAPIP().toString() + "\",\"subnet\":\"255.255.255.0\"";
  result += ",\"dhcp_enabled\":true,\"firmware_version\":\"" + String(NEXUXNODE_FIRMWARE_VERSION) + "\"";
  return result;
}

void configChanged() {
  preferences.putString("ssid", ssid); preferences.putString("password", password);
  preferences.putInt("channel", channel); preferences.putInt("maxClients", maxClients);
  if (apRunning) { stopAp(); startAp(); }
  eventMessage("CONFIG_CHANGED");
}

void handleMessage(const String &json) {
  String command = valueFor(json, "command");
  String id = requestId(json);
  if (command == "HELLO") {
    response(id, command, true, "\"device\":\"NexusNode\",\"chip\":\"ESP32-D0WD-V3\",\"firmware\":\"NexuxNode-" + String(NEXUXNODE_FIRMWARE_VERSION) + "\",\"protocolVersion\":\"1.0\"");
  } else if (command == "START") { startAp(); response(id, command, apRunning, "", apRunning ? "" : "Unable to start access point");
  } else if (command == "STOP") { stopAp(); response(id, command, true);
  } else if (command == "RESTART") { stopAp(); startAp(); response(id, command, apRunning);
  } else if (command == "SET_WIFI_CONFIG") { String nextSsid = valueFor(json, "ssid"); String nextPassword = valueFor(json, "password"); int nextChannel = valueFor(json, "channel").toInt(); if (nextSsid.length() < 1 || nextSsid.length() > 32) response(id, command, false, "", "Invalid SSID"); else if (nextPassword.length() < 8 || nextPassword.length() > 63) response(id, command, false, "", "Password must be 8-63 characters"); else { ssid = nextSsid; password = nextPassword; if (nextChannel >= 1 && nextChannel <= 13) channel = nextChannel; String nextMode = valueFor(json, "mode"); if (nextMode == "MODE_AP" || nextMode == "MODE_EXTENSION") mode = nextMode; configChanged(); response(id, command, true); }
  } else if (command == "SET_SSID") { String next = valueFor(json, "ssid"); if (next.length() < 1 || next.length() > 32) response(id, command, false, "", "Invalid SSID"); else { ssid = next; configChanged(); response(id, command, true); }
  } else if (command == "SET_PASSWORD") { String next = valueFor(json, "password"); if (next.length() < 8 || next.length() > 63) response(id, command, false, "", "Password must be 8-63 characters"); else { password = next; configChanged(); response(id, command, true); }
  } else if (command == "SET_CHANNEL") { int next = valueFor(json, "channel").toInt(); if (next < 1 || next > 13) response(id, command, false, "", "Invalid channel"); else { channel = next; configChanged(); response(id, command, true); }
  } else if (command == "SET_MAX_CLIENTS") { int next = valueFor(json, "maxClients").toInt(); if (next < 1 || next > 10) response(id, command, false, "", "Invalid maxClients"); else { maxClients = next; configChanged(); response(id, command, true); }
  } else if (command == "SET_MODE") { String next = valueFor(json, "mode"); if (next != "MODE_AP" && next != "MODE_EXTENSION") response(id, command, false, "", "Unsupported mode"); else { mode = next; configChanged(); response(id, command, true); }
  } else if (command == "SET_TXPOWER" || command == "SET_BANDWIDTH") { response(id, command, false, "", "This hardware setting is not supported by the current firmware API");
  } else if (command == "STATUS") { response(id, command, true, statusJson());
  } else if (command == "BOARD_INFO") { response(id, command, true, "\"board\":{\"model\":\"ESP32-D0WD-V3\",\"cpu_mhz\":240,\"cores\":2,\"flash_mb\":4,\"sdk_version\":\"ESP-IDF 5.5.5\",\"core_version\":\"Arduino ESP32 Core 3.3.11\"}");
  } else if (command == "NETWORK_INFO" || command == "GET_CONFIG") { response(id, command, true, "\"ssid\":\"" + ssid + "\",\"channel\":" + String(channel) + ",\"max_clients\":" + String(maxClients) + ",\"mode\":\"" + mode + "\",\"ap_ip\":\"" + WiFi.softAPIP().toString() + "\",\"subnet\":\"255.255.255.0\",\"gateway\":\"192.168.4.1\",\"dhcp_enabled\":true");
  } else if (command == "CLIENTS") {
    Serial.print("{\"id\":"); Serial.print(id.length() ? id : "null");
    Serial.print(",\"type\":\"clients\",\"success\":true,"); Serial.print(clientsJson()); Serial.println("}");
  } else if (command == "GET_MODE") { response(id, command, true, "\"mode\":\"" + mode + "\"");
  } else if (command == "PING") { response(id, command, true, "\"pong\":true");
  } else if (command == "DIAGNOSTICS" || command == "SCAN") { response(id, command, true, "\"available\":true");
  } else { response(id, command, false, "", "Unknown command"); }
}

void setup() {
  Serial.begin(115200);
  preferences.begin("nexusnode", false);
  ssid = preferences.getString("ssid", DEFAULT_SSID); password = preferences.getString("password", DEFAULT_PASSWORD);
  channel = preferences.getInt("channel", 6); maxClients = preferences.getInt("maxClients", 3);
  startedAt = millis(); startAp();
  esp_event_handler_register(WIFI_EVENT, WIFI_EVENT_AP_STACONNECTED, stationEvent, nullptr);
  esp_event_handler_register(WIFI_EVENT, WIFI_EVENT_AP_STADISCONNECTED, stationEvent, nullptr);
  eventMessage("RESET");
}

void loop() {
  if (Serial.available()) { String line = Serial.readStringUntil('\n'); line.trim(); if (line.startsWith("{")) handleMessage(line); }
}