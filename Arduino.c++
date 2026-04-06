#include <Servo.h>

#define NUM_SENSORS 4

int trigPins[NUM_SENSORS] = {2,3,4,5};
int echoPins[NUM_SENSORS] = {7,8,9,10};

Servo servoX, servoY;

enum Mode {
  IDLE,
  TRACK
};

Mode currentMode = IDLE;

float readSensor(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long dur = pulseIn(echoPin, HIGH, 30000);

  if (dur == 0) return -1;
  return (dur * 0.0343) / 2;
}

void setup() {
  Serial.begin(9600);

  for (int i = 0; i < NUM_SENSORS; i++) {
    pinMode(trigPins[i], OUTPUT);
    pinMode(echoPins[i], INPUT);
  }

  //Pan-tilt Pins
  servoX.attach(11);  
  servoY.attach(12); 

  //Laser
  pinMode(13 , OUTPUT);
}

//Handling Serial Inputs
String inputBuffer = "";
void handleSerial() {
  while (Serial.available()) {
    char c = Serial.read();

    if (c == '\n') {
      inputBuffer.trim();

      if (inputBuffer == "START") {
        currentMode = TRACK;
        Serial.println("MODE:TRACK");
      }
      else if (inputBuffer == "STOP") {
        currentMode = IDLE;
        Serial.println("MODE:IDLE");
      }
    else if (inputBuffer.startsWith("T")) {
      digitalWrite(13 , HIGH);
      int x, y;

      if (sscanf(inputBuffer.c_str(), "T,%d,%d", &x, &y) == 2) {
        if (currentMode == TRACK) {
          x = constrain(x, 50, 130);
          y = constrain(y, 50, 130);

          static int prevX = 90, prevY = 90;
          x = 0.7 * prevX + 0.3 * x;
          y = 0.7 * prevY + 0.3 * y;

          servoX.write(x);
          servoY.write(y);

          prevX = x;
          prevY = y;
        }
      }
    }

      inputBuffer = ""; // clear buffer
    }
    else {
      inputBuffer += c;
    }
  }
}

void loop() {
  handleSerial();

  if (currentMode == IDLE) {
    digitalWrite(13, LOW);
    for (int i = 0; i < NUM_SENSORS; i++) {
      float d = readSensor(trigPins[i], echoPins[i]);

      Serial.print("D,");
      Serial.print(i);
      Serial.print(",");
      Serial.println(d);
    }

    delay(50); // ~50 Hz
  }
  // TRACK mode does NOT send distance for now
}
