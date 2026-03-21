#include "Storage.h"
#include <EEPROM.h>

Storage::Storage() {
}

void Storage::begin() {
  EEPROM.begin(EEPROM_SIZE);
}

void Storage::saveConfig(const WiFiConfig& config) {
  EEPROM.put(0, config);
  EEPROM.commit();
}

void Storage::loadConfig(WiFiConfig& config) {
  EEPROM.get(0, config);
}

void Storage::clearConfig() {
  WiFiConfig emptyConfig = {"", "", false};
  EEPROM.put(0, emptyConfig);
  EEPROM.commit();
}

bool Storage::isConfigured() {
  WiFiConfig config;
  loadConfig(config);
  return config.configured;
}
