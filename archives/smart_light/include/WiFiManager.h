#ifndef WIFIMANAGER_H
#define WIFIMANAGER_H

#include <ESP8266WiFi.h>
#include "Storage.h"

#define SMARTCONFIG_TIMEOUT 180000
#define RECONNECT_INTERVAL 5000
#define MAX_RECONNECT_ATTEMPTS 10

enum WifiConnectionState {
  WIFI_DISCONNECTED,
  WIFI_CONNECTING,
  WIFI_CONNECTED,
  WIFI_SMARTCONFIG
};

class WiFiManager {
public:
  WiFiManager(Storage& storage);
  
  void begin();
  void update();
  bool isConnected();
  bool isSmartConfigMode();
  WifiConnectionState getState();
  void startSmartConfig();
  void stopSmartConfig();
  void connect();
  void disconnect();
  void forceReconnect();
  String getSSID();
  String getIP();
  int getReconnectAttempts();
  
private:
  Storage& _storage;
  WifiConnectionState _state;
  bool _smartConfigMode;
  unsigned long _smartConfigStartTime;
  unsigned long _lastReconnectAttempt;
  int _reconnectAttempts;
  
  void attemptReconnect();
};

#endif
