#include "WiFiManager.h"

WiFiManager::WiFiManager(Storage& storage) 
  : _storage(storage), _state(WIFI_DISCONNECTED), _smartConfigMode(false), 
    _smartConfigStartTime(0), _lastReconnectAttempt(0), _reconnectAttempts(0) {
}

void WiFiManager::begin() {
  if (!_storage.isConfigured()) {
    startSmartConfig();
    return;
  }
  
  connect();
}

void WiFiManager::update() {
  if (_smartConfigMode) {
    if (WiFi.smartConfigDone()) {
      Serial.println("SmartConfig配网成功!");
      Serial.print("SSID: ");
      Serial.println(WiFi.SSID());
      
      WiFiConfig config;
      WiFi.SSID().toCharArray(config.ssid, 64);
      WiFi.psk().toCharArray(config.password, 64);
      config.configured = true;
      _storage.saveConfig(config);
      
      _smartConfigMode = false;
      Serial.println("配置已保存，重启设备...");
      delay(1000);
      ESP.restart();
    }
    
    if (millis() - _smartConfigStartTime > SMARTCONFIG_TIMEOUT) {
      Serial.println("SmartConfig超时，重启设备");
      ESP.restart();
    }
  } else {
    if (WiFi.status() == WL_CONNECTED) {
      if (_state != WIFI_CONNECTED) {
        _state = WIFI_CONNECTED;
        _reconnectAttempts = 0;
        Serial.println("WiFi已连接!");
        Serial.print("IP地址: ");
        Serial.println(WiFi.localIP());
      }
    } else {
      if (_state == WIFI_CONNECTED) {
        Serial.println("WiFi连接断开!");
        _state = WIFI_DISCONNECTED;
      }
      
      attemptReconnect();
    }
  }
}

bool WiFiManager::isConnected() {
  return WiFi.status() == WL_CONNECTED;
}

bool WiFiManager::isSmartConfigMode() {
  return _smartConfigMode;
}

WifiConnectionState WiFiManager::getState() {
  return _state;
}

void WiFiManager::startSmartConfig() {
  _smartConfigMode = true;
  _state = WIFI_SMARTCONFIG;
  _smartConfigStartTime = millis();
  _reconnectAttempts = 0;
  
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  
  Serial.println("进入SmartConfig配网模式...");
  Serial.println("请使用微信小程序或ESP8266 SmartConfig应用进行配网");
  
  WiFi.beginSmartConfig();
}

void WiFiManager::stopSmartConfig() {
  if (_smartConfigMode) {
    WiFi.stopSmartConfig();
    _smartConfigMode = false;
  }
}

void WiFiManager::connect() {
  WiFiConfig config;
  _storage.loadConfig(config);
  
  if (!config.configured) {
    startSmartConfig();
    return;
  }
  
  Serial.println("连接WiFi...");
  Serial.print("SSID: ");
  Serial.println(config.ssid);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(config.ssid, config.password);
  
  _state = WIFI_CONNECTING;
  _reconnectAttempts = 0;
  _lastReconnectAttempt = millis();
}

void WiFiManager::disconnect() {
  WiFi.disconnect();
  _state = WIFI_DISCONNECTED;
}

void WiFiManager::forceReconnect() {
  Serial.println("强制重连WiFi...");
  WiFi.disconnect();
  delay(100);
  _reconnectAttempts = 0;
  connect();
}

String WiFiManager::getSSID() {
  return WiFi.SSID();
}

String WiFiManager::getIP() {
  return WiFi.localIP().toString();
}

int WiFiManager::getReconnectAttempts() {
  return _reconnectAttempts;
}

void WiFiManager::attemptReconnect() {
  unsigned long currentTime = millis();
  
  if (currentTime - _lastReconnectAttempt >= RECONNECT_INTERVAL) {
    _lastReconnectAttempt = currentTime;
    _reconnectAttempts++;
    
    if (_reconnectAttempts > MAX_RECONNECT_ATTEMPTS) {
      Serial.println("WiFi重连次数过多，进入SmartConfig模式");
      startSmartConfig();
      return;
    }
    
    Serial.print("尝试重连WiFi (");
    Serial.print(_reconnectAttempts);
    Serial.print("/");
    Serial.print(MAX_RECONNECT_ATTEMPTS);
    Serial.println(")...");
    
    WiFi.reconnect();
  }
}
