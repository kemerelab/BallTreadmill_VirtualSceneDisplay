#define PUMP A5

int last = 0;

void setup() {
pinMode(PUMP, OUTPUT);
digitalWrite(PUMP, HIGH);
Serial.begin(9600);
}

void loop() {
  if (Serial.available()) {
    char c = Serial.read();
    if ((c == 'A') && (last != 1)) {
      digitalWrite(PUMP, LOW);
      last = 1;
      delay(1000);
    }
    if ((c == 'B') && (last != 2)) {
      digitalWrite(PUMP, LOW);
      last = 2;
      delay(1000);
    }
    digitalWrite(PUMP, HIGH);
  }
}

