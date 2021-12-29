// ----------------------------------------------------------------
// Save this file as RGBLCD.cpp to use the Adafruit RGBLCD Shield
// ----------------------------------------------------------------

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_MCP23017.h>
#include <Adafruit_RGBLCDShield.h>

// The shield uses the I2C SCL and SDA pins. On classic Arduinos
// this is Analog 4 and 5 so you can't use those for analogRead() anymore
// However, you can connect other I2C sensors to the I2C bus and share
// the I2C bus.
Adafruit_RGBLCDShield lcd = Adafruit_RGBLCDShield();

void lcdbegin() {
  lcd.begin(16, 2);
  lcdcolor(RED);
  lcdclear();
}

void lcdcolor(byte color) {
  lcd.setBacklight(color);
}

#include "LineWrap.h"
