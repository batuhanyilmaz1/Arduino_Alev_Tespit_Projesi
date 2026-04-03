#include <Servo.h>

#define ALEV_SENSOR 4
#define KIRMIZI_LED 13
#define BUZZER_PIN 8
#define SERVO_PIN 5
#define YESIL_LED 3

/*
  Servo kalibrasyonu:
  - SERVO_RAW_LEFT: sensor tam sola bakarken gereken write() degeri
  - SERVO_RAW_CENTER: sensor duz ortaya bakarken gereken write() degeri
  - SERVO_RAW_RIGHT: sensor tam saga bakarken gereken write() degeri

  Arduino servo feedback vermez; bu nedenle "gercek" aci olarak ancak
  komut edilen konumu kalibre edip raporlayabiliriz.
*/
const int SERVO_RAW_LEFT = 0;
const int SERVO_RAW_CENTER = 90;
const int SERVO_RAW_RIGHT = 180;

/*
  Yeni analiz mantigi:
  - Alev ilk goruldugunde servo hemen durmaz.
  - Sensor alevi gordugu sure boyunca taramaya devam edilir.
  - Gorulen araligin orta noktasi "tespit acisi" kabul edilir.
  - Servo o orta noktaya donup alarm verir.

  Boylece ilk temas noktasi yerine alevin merkezine daha yakin bir aci elde edilir.
*/
const unsigned long STATE_INTERVAL_MS = 55;
const unsigned long TRACK_GAP_MS = 90;
const unsigned long TRACK_TIMEOUT_MS = 2500;
const unsigned long CLEAR_DEBOUNCE_MS = 350;

Servo sg90s;

int rawPos = SERVO_RAW_CENTER;
int sweepDir = 1;

bool scanning = true;
bool ledsAuto = true;
bool alarmActive = false;
bool trackingSpan = false;

int confirmedAngle = 90;
int trackStartAngle = 0;
int trackEndAngle = 0;

unsigned long trackStartedMs = 0;
unsigned long lastFlameSeenMs = 0;
unsigned long clearCandidateMs = 0;
unsigned long lastStateMs = 0;

int clampRawServo(int raw) {
  if (raw < SERVO_RAW_LEFT) {
    return SERVO_RAW_LEFT;
  }
  if (raw > SERVO_RAW_RIGHT) {
    return SERVO_RAW_RIGHT;
  }
  return raw;
}

int mapConstrainedLong(
  long value,
  long inMin,
  long inMax,
  long outMin,
  long outMax
) {
  if (inMin == inMax) {
    return (int)outMin;
  }

  long mapped = map(value, inMin, inMax, outMin, outMax);
  if (outMin < outMax) {
    if (mapped < outMin) {
      mapped = outMin;
    }
    if (mapped > outMax) {
      mapped = outMax;
    }
  } else {
    if (mapped < outMax) {
      mapped = outMax;
    }
    if (mapped > outMin) {
      mapped = outMin;
    }
  }
  return (int)mapped;
}

int logicalAngleFromRaw(int raw) {
  const int clamped = clampRawServo(raw);
  const int center = constrain(SERVO_RAW_CENTER, SERVO_RAW_LEFT, SERVO_RAW_RIGHT);

  if (center <= SERVO_RAW_LEFT || center >= SERVO_RAW_RIGHT) {
    return mapConstrainedLong(clamped, SERVO_RAW_LEFT, SERVO_RAW_RIGHT, 0, 180);
  }

  if (clamped <= center) {
    return mapConstrainedLong(clamped, SERVO_RAW_LEFT, center, 0, 90);
  }

  return mapConstrainedLong(clamped, center, SERVO_RAW_RIGHT, 90, 180);
}

int rawFromLogicalAngle(int angle) {
  const int clamped = constrain(angle, 0, 180);
  const int center = constrain(SERVO_RAW_CENTER, SERVO_RAW_LEFT, SERVO_RAW_RIGHT);

  if (center <= SERVO_RAW_LEFT || center >= SERVO_RAW_RIGHT) {
    return mapConstrainedLong(clamped, 0, 180, SERVO_RAW_LEFT, SERVO_RAW_RIGHT);
  }

  if (clamped <= 90) {
    return mapConstrainedLong(clamped, 0, 90, SERVO_RAW_LEFT, center);
  }

  return mapConstrainedLong(clamped, 90, 180, center, SERVO_RAW_RIGHT);
}

int currentAngle() {
  return logicalAngleFromRaw(rawPos);
}

bool atSweepEdge() {
  return rawPos <= SERVO_RAW_LEFT || rawPos >= SERVO_RAW_RIGHT;
}

void moveServoToRaw(int raw) {
  rawPos = clampRawServo(raw);
  sg90s.write(rawPos);
}

void moveServoToLogicalAngle(int angle) {
  moveServoToRaw(rawFromLogicalAngle(angle));
}

void sendState() {
  const bool moving = !alarmActive && scanning;
  const int reportAngle = alarmActive ? confirmedAngle : currentAngle();

  Serial.print("STATE|a=");
  Serial.print(reportAngle);
  Serial.print(",f=");
  Serial.print(alarmActive ? 1 : 0);
  Serial.print(",s=");
  Serial.print(moving ? 1 : 0);
  Serial.print("\n");
}

void sendStateThrottled() {
  const unsigned long now = millis();
  if (now - lastStateMs >= STATE_INTERVAL_MS) {
    lastStateMs = now;
    sendState();
  }
}

void forceSendState() {
  lastStateMs = millis();
  sendState();
}

void applyLeds() {
  if (!ledsAuto) {
    digitalWrite(YESIL_LED, LOW);
    digitalWrite(KIRMIZI_LED, LOW);
    return;
  }

  if (alarmActive) {
    digitalWrite(YESIL_LED, LOW);
    digitalWrite(KIRMIZI_LED, HIGH);
  } else {
    digitalWrite(YESIL_LED, HIGH);
    digitalWrite(KIRMIZI_LED, LOW);
  }
}

void drainSerial() {
  while (Serial.available()) {
    (void)Serial.read();
  }
}

void beginTrackingSpan(int angle) {
  trackingSpan = true;
  trackStartAngle = angle;
  trackEndAngle = angle;
  trackStartedMs = millis();
  lastFlameSeenMs = trackStartedMs;
}

void emitAlarmAtAngle(int angle) {
  confirmedAngle = constrain(angle, 0, 180);
  alarmActive = true;
  trackingSpan = false;
  clearCandidateMs = 0;

  moveServoToLogicalAngle(confirmedAngle);

  Serial.print("ALARM|a=");
  Serial.print(confirmedAngle);
  Serial.print("\n");
  Serial.println("YANGIN");
  forceSendState();
}

void finishTrackingSpan() {
  const int minAngle = min(trackStartAngle, trackEndAngle);
  const int maxAngle = max(trackStartAngle, trackEndAngle);
  const int midpoint = (minAngle + maxAngle) / 2;
  emitAlarmAtAngle(midpoint);
}

void emitClear() {
  alarmActive = false;
  trackingSpan = false;
  clearCandidateMs = 0;

  Serial.println("CLEAR");
  Serial.println("YOK");
  forceSendState();
}

void updateFlameAnalysis() {
  const bool flame = (digitalRead(ALEV_SENSOR) == LOW);
  const unsigned long now = millis();
  const int angle = currentAngle();

  if (alarmActive) {
    if (flame) {
      clearCandidateMs = 0;
    } else if (clearCandidateMs == 0) {
      clearCandidateMs = now;
    } else if (now - clearCandidateMs >= CLEAR_DEBOUNCE_MS) {
      emitClear();
    }
    return;
  }

  if (!trackingSpan) {
    if (flame) {
      beginTrackingSpan(angle);
    }
    return;
  }

  if (flame) {
    trackEndAngle = angle;
    lastFlameSeenMs = now;

    if (atSweepEdge() || (now - trackStartedMs >= TRACK_TIMEOUT_MS)) {
      finishTrackingSpan();
    }
    return;
  }

  if (now - lastFlameSeenMs >= TRACK_GAP_MS) {
    finishTrackingSpan();
  }
}

void setup() {
  pinMode(ALEV_SENSOR, INPUT_PULLUP);
  pinMode(KIRMIZI_LED, OUTPUT);
  pinMode(YESIL_LED, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  sg90s.attach(SERVO_PIN);
  Serial.begin(9600);

  confirmedAngle = 90;
  moveServoToLogicalAngle(confirmedAngle);
  forceSendState();
}

void loop() {
  drainSerial();

  if (!alarmActive) {
    if (scanning) {
      moveServoToRaw(rawPos + sweepDir);
      if (rawPos >= SERVO_RAW_RIGHT) {
        moveServoToRaw(SERVO_RAW_RIGHT);
        sweepDir = -1;
      } else if (rawPos <= SERVO_RAW_LEFT) {
        moveServoToRaw(SERVO_RAW_LEFT);
        sweepDir = 1;
      }
    }
    delay(scanning ? 15 : 35);
  } else {
    digitalWrite(BUZZER_PIN, HIGH);
    delay(80);
    digitalWrite(BUZZER_PIN, LOW);
    delay(80);
  }

  drainSerial();

  updateFlameAnalysis();
  applyLeds();
  drainSerial();

  sendStateThrottled();
}
