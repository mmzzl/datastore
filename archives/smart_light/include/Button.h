#ifndef BUTTON_H
#define BUTTON_H

#include <Arduino.h>

enum ButtonType {
  BUTTON_POWER,
  BUTTON_BRIGHTNESS_UP,
  BUTTON_BRIGHTNESS_DOWN
};

class Button {
public:
  Button(uint8_t pin, ButtonType type);
  
  void begin();
  void update();
  bool isPressed();
  bool wasPressed();
  bool wasReleased();
  ButtonType getType();
  
private:
  uint8_t _pin;
  ButtonType _type;
  bool _currentState;
  bool _lastState;
  bool _wasPressed;
  bool _wasReleased;
  unsigned long _lastDebounceTime;
  unsigned long _debounceDelay;
};

#endif
