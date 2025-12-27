#include <Arduino.h>
#include <PubSubClient.h>
#include "Storage.h"
#include "WiFiManager.h"
#include "Button.h"

#define PWM_WHITE_PIN 13
#define PWM_YELLOW_PIN 12
#define BUTTON_POWER_PIN 5
#define BUTTON_UP_PIN 4
#define BUTTON_DOWN_PIN 2
#define BUTTON_SWITCH_PIN 14

WiFiClient espClient;
PubSubClient mqttClient(espClient);

Storage storage;
WiFiManager wifiManager(storage);

Button powerButton(BUTTON_POWER_PIN, BUTTON_POWER);
Button upButton(BUTTON_UP_PIN, BUTTON_BRIGHTNESS_UP);
Button downButton(BUTTON_DOWN_PIN, BUTTON_BRIGHTNESS_DOWN);

int brightness = 0;
bool lightOn = false;
int savedBrightness = 0;
int lightMode = 0;
const char* client_id = "ead3b3d5ed5242a68fe762c87929f11b";
const char* mqtt_topic = "led002";

unsigned long lastMQTTConnectAttempt = 0;
int mqttReconnectAttempts = 0;
const unsigned long MQTT_RECONNECT_INTERVAL = 5000;
const int MAX_MQTT_RECONNECT_ATTEMPTS = 10;

unsigned long lastWiFiCheckTime = 0;
const unsigned long WIFI_CHECK_INTERVAL = 10000;
unsigned long lastMQTTCheckTime = 0;
const unsigned long MQTT_CHECK_INTERVAL = 2000;

void setBrightness(int value) {
  if (value < 0) value = 0;
  if (value > 100) value = 100;
  brightness = value;
  
  int pwmValue = map(brightness, 0, 100, 0, 255);
  
  if (brightness == 0 || lightMode == 0) {
    analogWrite(PWM_WHITE_PIN, 0);
    analogWrite(PWM_YELLOW_PIN, 0);
  } else {
    switch (lightMode) {
      case 1:
        analogWrite(PWM_WHITE_PIN, pwmValue);
        analogWrite(PWM_YELLOW_PIN, 0);
        break;
      case 2:
        analogWrite(PWM_WHITE_PIN, 0);
        analogWrite(PWM_YELLOW_PIN, pwmValue);
        break;
      case 3:
        analogWrite(PWM_WHITE_PIN, pwmValue);
        analogWrite(PWM_YELLOW_PIN, pwmValue);
        break;
    }
  }
}

void turnOn() {
  lightOn = true;
  if (savedBrightness == 0) {
    savedBrightness = 50;
  }
  brightness = savedBrightness;
  setBrightness(brightness);
  Serial.println("灯光开启");
  Serial.print("亮度: ");
  Serial.println(brightness);
  if (mqttClient.connected()) {
    mqttClient.publish("light/state", "on");
    mqttClient.publish("light/brightness", String(brightness).c_str());
  }
}

void turnOff() {
  lightOn = false;
  savedBrightness = brightness;
  setBrightness(0);
  Serial.println("灯光关闭");
  if (mqttClient.connected()) {
    mqttClient.publish("light/state", "off");
  }
}

void toggleLight() {
  if (lightOn) {
    turnOff();
  } else {
    lightMode++;
    if (lightMode > 3) {
      lightMode = 1;
    }
    turnOn();
  }
}

void increaseBrightness() {
  if (!lightOn) {
    turnOn();
  } else {
    int newBrightness = brightness + 10;
    if (newBrightness > 100) newBrightness = 100;
    setBrightness(newBrightness);
    Serial.print("亮度增加: ");
    Serial.println(brightness);
    if (mqttClient.connected()) {
      mqttClient.publish("light/brightness", String(brightness).c_str());
    }
  }
}

void decreaseBrightness() {
  if (lightOn) {
    int newBrightness = brightness - 10;
    if (newBrightness < 0) newBrightness = 0;
    setBrightness(newBrightness);
    Serial.print("亮度减少: ");
    Serial.println(brightness);
    if (mqttClient.connected()) {
      mqttClient.publish("light/brightness", String(brightness).c_str());
    }
  }
}

void handleButtons() {
  powerButton.update();
  upButton.update();
  downButton.update();
  
  if (powerButton.wasPressed()) {
    Serial.println("开关按键按下");
    toggleLight();
  }
  
  if (upButton.wasPressed()) {
    Serial.println("增加亮度按键按下");
    increaseBrightness();
  }
  
  if (downButton.wasPressed()) {
    Serial.println("减少亮度按键按下");
    decreaseBrightness();
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  Serial.print("收到MQTT消息 [");
  Serial.print(topic);
  Serial.print("]: ");

  char message[length + 1];
  for (unsigned int i = 0; i < length; i++) {
    message[i] = (char)payload[i];
  }
  message[length] = '\0';
  Serial.println(message);

  if (strcmp(topic, mqtt_topic) == 0) {
    if (strcmp(message, "on") == 0) {
      if (!lightOn) {
        lightMode++;
        if (lightMode > 3) {
          lightMode = 1;
        }
        turnOn();
      }
    } else if (strcmp(message, "off") == 0) {
      turnOff();
    } else {
      char* token = strtok(message, "#");
      int part = 0;
      int newBrightness = -1;
      
      while (token != NULL && part < 2) {
        if (part == 0) {
          newBrightness = atoi(token);
        } else if (part == 1) {
          newBrightness = atoi(token);
        }
        token = strtok(NULL, "#");
        part++;
      }
      
      if (newBrightness >= 0) {
        brightness = newBrightness;
        savedBrightness = newBrightness;
        setBrightness(newBrightness);
        Serial.print("设置亮度: ");
        Serial.println(brightness);
      }
    }
  }
}

void connectMQTT() {
  if (wifiManager.isSmartConfigMode() || !wifiManager.isConnected()) {
    return;
  }

  if (!mqttClient.connected()) {
    unsigned long currentTime = millis();
    
    if (currentTime - lastMQTTConnectAttempt >= MQTT_RECONNECT_INTERVAL) {
      lastMQTTConnectAttempt = currentTime;
      mqttReconnectAttempts++;
      
      if (mqttReconnectAttempts > MAX_MQTT_RECONNECT_ATTEMPTS) {
        Serial.println("MQTT重连次数过多，停止重连");
        return;
      }
      
      Serial.print("尝试连接MQTT (");
      Serial.print(mqttReconnectAttempts);
      Serial.print("/");
      Serial.print(MAX_MQTT_RECONNECT_ATTEMPTS);
      Serial.println(")...");
      
      if (mqttClient.connect(client_id)) {
        Serial.println("MQTT连接成功!");
        mqttClient.subscribe(mqtt_topic);
        mqttReconnectAttempts = 0;
        
        mqttClient.publish("light/status", "online");
        mqttClient.publish("light/state", lightOn ? "on" : "off");
        mqttClient.publish("light/brightness", String(brightness).c_str());
        switch (lightMode) {
          case 1:
            mqttClient.publish("light/mode", "white");
            break;
          case 2:
            mqttClient.publish("light/mode", "yellow");
            break;
          case 3:
            mqttClient.publish("light/mode", "both");
            break;
          default:
            mqttClient.publish("light/mode", "off");
            break;
        }
      } else {
        Serial.print("MQTT连接失败, rc=");
        Serial.println(mqttClient.state());
      }
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(100);
  
  Serial.println("\n\nSmart Light启动中...");
  
  storage.begin();
  
  pinMode(PWM_WHITE_PIN, OUTPUT);
  pinMode(PWM_YELLOW_PIN, OUTPUT);
  analogWriteFreq(23000);
  // digitalWrite(PWM_WHITE_PIN, LOW);
  powerButton.begin();
  upButton.begin();
  downButton.begin();
  
  wifiManager.begin();
  
  mqttClient.setServer("bemfa.com", 9501);
  mqttClient.setCallback(mqttCallback);
  
  lastWiFiCheckTime = millis();
  lastMQTTCheckTime = millis();
  
  Serial.println("初始化完成!");
}

void loop() {
  handleButtons();
  
  unsigned long currentTime = millis();
  
  if (currentTime - lastWiFiCheckTime >= WIFI_CHECK_INTERVAL) {
    lastWiFiCheckTime = currentTime;
    wifiManager.update();
  }
  
  if (!wifiManager.isSmartConfigMode()) {
    if (currentTime - lastMQTTCheckTime >= MQTT_CHECK_INTERVAL) {
      lastMQTTCheckTime = currentTime;
      connectMQTT();
    }
    mqttClient.loop();
  }
  
  delay(10);
}
