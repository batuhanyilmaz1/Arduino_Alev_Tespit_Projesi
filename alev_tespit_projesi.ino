#include <Servo.h>

#define ALEV_SENSOR 4
#define KIRMIZI_LED 13
#define BUZZER_PIN 8
#define SERVO_PIN 5
#define YESIL_LED 3

Servo sg90s;
int pos = 0;

void setup() {
  pinMode(ALEV_SENSOR, INPUT);
  pinMode(KIRMIZI_LED, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(YESIL_LED, OUTPUT);
  
  sg90s.attach(SERVO_PIN);
  
  Serial.begin(9600); 
}

void loop() {
  digitalWrite(YESIL_LED, HIGH);
  for (pos = 0; pos <= 180; pos++) {
    sg90s.write(pos);
    yanginKontrol(); 
    delay(15);       
  }
  
  for (pos = 180; pos >= 0; pos--) {
    sg90s.write(pos);
    yanginKontrol();
    delay(15);
  }
}

void yanginKontrol() {
  if (digitalRead(ALEV_SENSOR) == LOW) { 
    digitalWrite(YESIL_LED, LOW);
    digitalWrite(KIRMIZI_LED, HIGH);
    
    int anlik_aci = sg90s.read();
    sg90s.write(anlik_aci);

    while(digitalRead(ALEV_SENSOR) == LOW) {
      digitalWrite(BUZZER_PIN, HIGH); 
      delay(100);                  
      digitalWrite(BUZZER_PIN, LOW); 
      delay(100);
    }
    
    digitalWrite(YESIL_LED, HIGH);
    digitalWrite(KIRMIZI_LED, LOW);
    digitalWrite(BUZZER_PIN, LOW);
  }
}