/*
  IMU Data Collection for Movement Classification
  Arduino Nano 33 BLE Sense Rev 2
*/

#include "Arduino_BMI270_BMM150.h"

// Button configuration
const int buttonPin = 2;  
bool recording = false;   
bool prevButtonState = HIGH; 

// Movement management
const int MOVEMENTS_COUNT = 3;
const String MOVEMENTS[MOVEMENTS_COUNT] = {"square", "circle", "triangle"};
int currentMovementIndex = 0;
String movement = MOVEMENTS[0];

// Sample management
const int SAMPLES_PER_MOVEMENT = 100;
int sampleCount = 0;       

void setup() {
  Serial.begin(115200);
  while (!Serial);

  if (!IMU.begin()) {
    Serial.println("IMU init failed");
    while (1);
  }
  
  pinMode(buttonPin, INPUT_PULLUP);

  Serial.println("ax,ay,az,gx,gy,gz,mx,my,mz,label");
  Serial.println("Ready to record. Press and hold the button.");
}

void loop() {
  int buttonState = digitalRead(buttonPin);

  if (buttonState == LOW && prevButtonState == HIGH) {
    recording = true;
    Serial.println("START recording: " + movement);
    delay(50);
  } 
  else if (buttonState == HIGH && prevButtonState == LOW) {
    recording = false;
    Serial.println("STOP recording");
    sampleCount++;

    if (sampleCount >= SAMPLES_PER_MOVEMENT) {
      currentMovementIndex++;
      sampleCount = 0;

      if (currentMovementIndex >= MOVEMENTS_COUNT) {
        Serial.println("All movements recorded. Restarting...");
        currentMovementIndex = 0;
      }

      movement = MOVEMENTS[currentMovementIndex];
      Serial.println("Next movement: " + movement);
    }

    delay(50);
  }

  prevButtonState = buttonState;

  if (recording) {
    collectAndSendData();
  }

  delay(20);
}

void collectAndSendData() {
  float ax, ay, az;
  float gx, gy, gz;
  float mx, my, mz;

  if (IMU.accelerationAvailable() &&
      IMU.gyroscopeAvailable() &&
      IMU.magneticFieldAvailable()) {

    IMU.readAcceleration(ax, ay, az);
    IMU.readGyroscope(gx, gy, gz);
    IMU.readMagneticField(mx, my, mz);

    Serial.print(ax); Serial.print(',');
    Serial.print(ay); Serial.print(',');
    Serial.print(az); Serial.print(',');
    Serial.print(gx); Serial.print(',');
    Serial.print(gy); Serial.print(',');
    Serial.print(gz); Serial.print(',');
    Serial.print(mx); Serial.print(',');
    Serial.print(my); Serial.print(',');
    Serial.print(mz); Serial.print(',');
    Serial.println(movement);
  }
}
