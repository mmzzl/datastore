#include "Button.h"

Button::Button(uint8_t pin, ButtonType type) 
  : _pin(pin), _type(type), _currentState(false), _lastState(false), 
    _wasPressed(false), _wasReleased(false), _lastDebounceTime(0), _debounceDelay(50) {
}

void Button::begin() {
  pinMode(_pin, INPUT_PULLUP);
  _currentState = digitalRead(_pin);
  _lastState = _currentState;
}

void Button::update() {
  bool reading = digitalRead(_pin);
  
  if (reading != _lastState) {
    _lastDebounceTime = millis();
  }
  
  if ((millis() - _lastDebounceTime) > _debounceDelay) {
    if (reading != _currentState) {
      _currentState = reading;
      
      if (_currentState == LOW) {
        _wasPressed = true;
      } else {
        _wasReleased = true;
      }
    }
  }
  
  _lastState = reading;
}

bool Button::isPressed() {
  return _currentState == LOW;
}

bool Button::wasPressed() {
  if (_wasPressed) {
    _wasPressed = false;
    return true;
  }
  return false;
}

bool Button::wasReleased() {
  if (_wasReleased) {
    _wasReleased = false;
    return true;
  }
  return false;
}

ButtonType Button::getType() {
  return _type;
}
