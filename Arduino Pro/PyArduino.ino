#define LED 13

int last = 0;

void setup() {
pinMode(LED, OUTPUT);
Serial.begin(9600);
}

void loop() {
  if (Serial.available()) {
    char c = Serial.read();
    if ((c == 'A') && (last != 1)) {
      digitalWrite(LED, LOW);
      last = 1;
      delay(1000);
    }
    if ((c == 'B') && (last != 2)) {
      digitalWrite(LED, LOW);
      last = 2;
      delay(1000);
    }
    digitalWrite(LED, HIGH);
  }
}

