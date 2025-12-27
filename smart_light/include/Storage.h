#ifndef STORAGE_H
#define STORAGE_H

#include <Arduino.h>

#define EEPROM_SIZE 512

struct WiFiConfig {
  char ssid[64];
  char password[64];
  bool configured;
};

class Storage {
public:
  Storage();
  
  void begin();
  void saveConfig(const WiFiConfig& config);
  void loadConfig(WiFiConfig& config);
  void clearConfig();
  bool isConfigured();
};

#endif
