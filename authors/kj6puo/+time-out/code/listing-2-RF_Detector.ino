#define IN 5
#define LED 13

// take out all Serial IO after debugging 

int threshold = 0;

void setup() {
  Serial.begin(9600);
  pinMode(LED, OUTPUT);

  // Set up for 1.1v internal reference, to be most sensitive.
  // Ground the ADC input through a 10 meg-ohm resistor.
  analogReference(INTERNAL);

  // Calculate current max value of RF field.
  for (int i = 0; i < 100; i++) {
    threshold = max(threshold, analogRead(IN));
    delay(20);
  }
  threshold += 10;
  Serial.print("Threshold is ");
  Serial.println(threshold);
}

void loop() {

  int x = analogRead(IN);
  if (x > threshold) {
    digitalWrite(LED, HIGH); 
    Serial.println(x);
  } else {
    digitalWrite(LED, LOW);
  }

}

