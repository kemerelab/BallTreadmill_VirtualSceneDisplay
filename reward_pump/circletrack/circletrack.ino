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
    if (c == 'L') {
      digitalWrite(PUMP, LOW);
      delay(1000);
    }else{
      digitalWrite(PUMP, HIGH);
  }
}

