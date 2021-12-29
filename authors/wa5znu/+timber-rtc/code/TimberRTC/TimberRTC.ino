/*
 * APRS Recorder
 * Michael Pechner NE6RD
 * RTC Leigh Klotz, Jr WA5ZNU
 */

#include <Arduino.h>

#include "LCD.h"
#include "colors.h"

#include <ArgentRadioShield.h>
#include <Wire.h>
#include <RTClib.h>
#include <SD.h>

#define HELLO_MESSAGE "NE6RD - Waiting"

// SD Card Shield pin numbers
#define CS         8
#define MOSI      11
#define MISO      12
#define SCK       13
#define SDCARD_SELECT 10

#define BUFFERSIZE 255

char buff[BUFFERSIZE];		 // Incoming data buffer
int buflen = 0;			 // Length of buffered data

// Use Hardware Serial for ArgentRadioShield.
ArgentRadioShield argentRadioShield = ArgentRadioShield(&Serial);

// Real-time clock, on board the SD card / RTC Shield
RTC_DS1307 RTC;

void setup() {
  Wire.begin();

  // For RTC
  RTC.begin();

  //Set up the SD Card pins
  pinMode(CS, OUTPUT);
  pinMode(MOSI, OUTPUT);
  pinMode(MISO, INPUT);
  pinMode(SCK, OUTPUT);
  pinMode(SDCARD_SELECT, OUTPUT);

  // Argent RadioShield runs at 4800 baud
  Serial.begin(4800);

  // Setup LCD Screen
  lcdbegin();

  // See if the card is present and can be initialized
  if (!SD.begin(SDCARD_SELECT)) {
    lcdcolor(RED);
    lcdprint("SD Card failed");
  } else {
    // 'Waiting' message stays until we receive something
    lcdprint(HELLO_MESSAGE);
  }
}

// Check for an incoming byte on the serial port.
// Until we get a newline, add characters to buffer.
// On newline, write to SD card and LCD, and start over.
// Handle badly-formed packets.
void loop() {
  while (argentRadioShield.available() > 0) {
    // Get the byte
    char inbyte = argentRadioShield.read();
    if (inbyte == '\n') {
      lcdclear();
      // If end of line, write the packet to the file on the SD card
      appendPacket();
      // And display it on the LCD screen
      displayPacket();
      buflen = 0;
    } else if (ch < 31 && ch != 0x1c && ch != 0x1d && ch != 0x27) {
      // ignore badly-decoded characters but pass MIC-E
    } else if (buflen != BUFFERSIZE) {
      // If we haven't reached end of buffer space, write it.
      buff[buflen++] = inbyte;
    } else {
      lcdprint("Data Too Long");
      // If we read 256 characters and did not receive a EOL, there is a problem
      // so reset buffer and start over.
      buflen = 0;
    }
  }
}

// Write the packet to the SD card
void appendPacket() {
  // Open file_handle file that's just been initialized
  File file_handle = SD.open("APRS.txt", FILE_WRITE | O_APPEND);
  if (file_handle == 0) {
    lcdprint("Cannot open File");
  } else {
    printdate(&file_handle);
    file_handle.print(" ");
    file_handle.write((const uint8_t*)buff, buflen);
    file_handle.print("\n");
    file_handle.close();
  }
}

// Display the callsign and text out of the packet.
void displayPacket() {
  lcdclear();
  lcdcolor(GREEN);

  // Terminate the string buffer with a '\0'
  buff[buflen] = '\0';

  // Find the ">" to that ends the callsign
  char *callsignEnd = strchr(buff, '>');
  if (callsignEnd == NULL || callsignEnd-buff > 16) {
    // either no call or too call long
    lcdprint("BAD PACKET");
    return;
  }

  // If there's no ":" then packet is malformed.
  char *rest = strchr(callsignEnd, ':');
  if (rest == NULL) {
    lcdprint("BAD PACKET");
    return;
  }

  // Print callsign, then 
  // skip APRS destination (after ":")
  // Leave the ':' as a separator.
  lcdprint(buff, callsignEnd - buff);
  lcdprint(rest, strlen(rest));
}
