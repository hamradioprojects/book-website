// Repeater drop timer, ATTiny85 version
// Copyright 2012 Keith Amidon KJ6PUO and Peter Amidon KJ6PUO
// Licensed under Creative Commons Share Alike CC-BY-SA 3.0; see file LICENSE.txt

// ---- Constants
#define ANT 0
#define RED_LED 2
#define GREEN_LED 1
#define BUZZER 0

#define LOOP_DELAY 25

#define MAX_IDLE_FADE_BRIGHTNESS 192

#define INIT_SAMPLE_CNT 92
#define MOVING_AVG_SIZE  16

#define REPEATER_MAX_TIME 30000L
#define REPEATER_LAST_ALERT_RELATIVE 5000L
#define REPEATER_EARLY_ALERT REPEATER_MAX_TIME/2*

#define REPEATER_MED_ALERT (REPEATER_MAX_TIME*3)/4
#define REPEATER_LAST_ALERT REPEATER_MAX_TIME-REPEATER_LAST_ALERT_RELATIVE

#define REPEATER_LAST_ALERT_FLASH_DURATION 500

int threshold = 0;

void setup() {
  setup_and_verify_hardware();
  calculate_rf_threshold();
  delay(500);
  flashNumber(threshold);
}

void setup_and_verify_hardware() {
  // Attempt to force pin low to minimize analog value read from environments
  pinMode(ANT, INPUT);
  digitalWrite(ANT, LOW);
  analogReference(DEFAULT);

  // Setup LED pin
  pinMode(RED_LED, OUTPUT);
  pinMode(GREEN_LED, OUTPUT);

  // Verify LEDs & tone are working
  digitalWrite(RED_LED, HIGH);
  delay(200);
  digitalWrite(GREEN_LED, HIGH);
  tone(BUZZER, 800);
  delay(1000);
  noTone(BUZZER);
  digitalWrite(GREEN_LED, LOW);
  delay(200);
  digitalWrite(RED_LED, LOW);  
}

void calculate_rf_threshold() {
  // To set the RF background threshold sample the antenna INIT_SAMPLE_CNT times.
  // and determine an average reading from a subset of those and the maximum
  // reading seen.  Set the threshold to the average + 1/4 the difference between
  // the average and the max to minimize false positives.
  digitalWrite(RED_LED, HIGH);  // Turn on red LED while determining thresholds
  int max_v = 0;
  for (int i = 0; i < INIT_SAMPLE_CNT; i++) {
    int v = analogRead(ANT);
    if (i % (INIT_SAMPLE_CNT/MOVING_AVG_SIZE) == 0) {
      update_moving_avg(v); // Deliberately ignore return value;
    }
    max_v = max(max_v, v);
    delay(LOOP_DELAY);
  }
  digitalWrite(GREEN_LED, LOW);
  threshold = calculate_moving_avg();
  threshold = threshold + ((max_v - threshold)/4);
  digitalWrite(RED_LED, LOW);
}

void loop() {
  if (update_moving_avg(analogRead(ANT)) <= threshold) {
    do_idle_behavior();
  } else {
    do_transmitting_behavior();
  }
  delay(LOOP_DELAY); // No need to run as fast as possible.
}

int brightness = 0;  // Initial brightness for idle LED pulsing
int fadeAmount = 2;  // Magnitude of next change of brightness for idle LED pulsing

unsigned long start_millis = 0;  // Millisecond timer at which transmission started, 0 for none
void do_idle_behavior() {
  // No longer detecting a transmission, turn everything off then pulse the green LED
  // to slightly less than full brightness to indicate that we the device is powered on.
  start_millis = 0;
  digitalWrite(RED_LED, LOW);
  noTone(BUZZER);
  analogWrite(GREEN_LED,brightness);
  brightness = brightness + fadeAmount;
  if (brightness <= 0 || brightness >= MAX_IDLE_FADE_BRIGHTNESS) {
    fadeAmount = -fadeAmount;
  }
}

int next_alarm = 0;              // Index of next alarm that should occur

void do_transmitting_behavior() {
  // Trigger alarms when appropriate amount of time has passed  
  if (start_millis == 0) {
     start_millis = millis();
     next_alarm = 0;
  }
  int duration = millis() - start_millis;
  if (duration < REPEATER_MED_ALERT && next_alarm < 1) {
    // A short high-pitched chirp and solid green LED indicate the timer has started
    digitalWrite(GREEN_LED, HIGH);
    tone(BUZZER, 900, 200);
    next_alarm = 1;
  } else if (duration >= REPEATER_EARLY_ALERT && next_alarm < 2) {
    // A longer beep and orange (red + green) LED color indicate the early warning has passed
    tone(BUZZER,600,500);
    digitalWrite(RED_LED, HIGH);
    next_alarm = 2;
  } else if (duration >= REPEATER_MED_ALERT && next_alarm < 3) {
    // Another longer beep and solid red LED color indicate the late warning has passed
    tone(BUZZER,700,200);
    digitalWrite(GREEN_LED, LOW);
    digitalWrite(RED_LED, HIGH);
    next_alarm = 3;
  } else if (duration >= REPEATER_LAST_ALERT && next_alarm < 4) {
    // A continuous tone and flash solid red LED color indicate the timer has expired
    tone(BUZZER,900);
    int i;
    while (update_moving_avg(analogRead(ANT)) > threshold) {
      if (i % (REPEATER_LAST_ALERT_FLASH_DURATION/LOOP_DELAY) == 0) {
        if (i % (2*REPEATER_LAST_ALERT_FLASH_DURATION/LOOP_DELAY) == 0) {
          digitalWrite(RED_LED, LOW);
        } else {
          digitalWrite(RED_LED, HIGH);
        }
      }
      delay(LOOP_DELAY);
      i++;
    }
  }
}

// ---- Utility functions: calculating moving average of rf readings
int moving_avg_readings[MOVING_AVG_SIZE];    // Array for storing old readings
int *moving_avg_head = moving_avg_readings;  // Location of most recent reading
int *moving_avg_tail = moving_avg_readings;  // Location of oldest reading

int update_moving_avg(int value) {
  // Update a moving average of the last MOVING_AVG_SIZE readings.
  // Returns the new average.
  *moving_avg_head = value;
  if (++moving_avg_head >= &moving_avg_readings[MOVING_AVG_SIZE]) {
    moving_avg_head = moving_avg_readings;  // wrap on overflow
  }
  if (moving_avg_head == moving_avg_tail) {
    // This is only true if we've already read MOVING_AVG_SIZE values,
    // in which case we need to move the tail pointer.
    if (++moving_avg_tail >= &moving_avg_readings[MOVING_AVG_SIZE]) {
      moving_avg_tail = moving_avg_readings;   // wrap on overflow
    }
  }
  return calculate_moving_avg();
}

// TODO: There are more efficient ways to calculate the moving
// TODO: average and handle array wrap.  Implement them?

int calculate_moving_avg() {
  // Calculate the moving average based on existing readings
  int *p = moving_avg_tail;
  int total = 0;
  int cnt = 0;
  
  while (p != moving_avg_head) {
    cnt++;
    total += *p;
    if (++p >= &moving_avg_readings[MOVING_AVG_SIZE]) {
      p = moving_avg_readings;  // wrap on overflow
    }
  }
  return total/cnt;
}

// ---- Utility functions: display
void flashNumber(int num) {
  // Display a number using only the red and green LEDs
  
  //  Start sequence
  digitalWrite(RED_LED, HIGH);
  delay(100);
  digitalWrite(GREEN_LED, HIGH);
  delay(100);
  digitalWrite(RED_LED, LOW);
  delay(100);
  digitalWrite(GREEN_LED, LOW);  
  delay(500);
  
  // Flash hundreds
  delay(500);
  for (int i = 0; i < num / 100; i++) {  
    digitalWrite(GREEN_LED, HIGH);
    delay(200);
    digitalWrite(GREEN_LED, LOW);
    delay(200);
  }
  // Flash tens
  delay(500);
  for (int i = 0; i < (num % 100) / 10; i++) {
    digitalWrite(RED_LED, HIGH);
    digitalWrite(GREEN_LED, HIGH);
    delay(200);
    digitalWrite(RED_LED, LOW);
    digitalWrite(GREEN_LED, LOW);
    delay(200);
  }
  // Flash ones
  delay(500);
  for (int i = 0; i < (num % 100) % 10; i++) {
    digitalWrite(RED_LED, HIGH);
    delay(200);
    digitalWrite(RED_LED, LOW);
    delay(200);
  }
  // End sequence
  delay(500);
  digitalWrite(GREEN_LED, HIGH);
  delay(100);
  digitalWrite(RED_LED, HIGH);
  delay(100);
  digitalWrite(GREEN_LED, LOW);
  delay(100);
  digitalWrite(RED_LED, LOW);  
}
