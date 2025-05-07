#include "Arduino_BMI270_BMM150.h"


// Button pin
const int buttonPin = 2;


void setup() {
  Serial.begin(115200);
  while (!Serial);


  pinMode(buttonPin, INPUT_PULLUP); // Use internal pull-up resistor


  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1);
  }


  Serial.println("Arduino Nano 33 IMU - Simple Version");
  Serial.println("===================================");
  Serial.println("HOLD button to send data, RELEASE to stop");
}


void loop() {
  // Button uses INPUT_PULLUP, so LOW = pressed
  if (digitalRead(buttonPin) == LOW) {
    float ax, ay, az;
    float gx, gy, gz;


    // Only print if data is available
    if (IMU.accelerationAvailable() && IMU.gyroscopeAvailable()) {
      IMU.readAcceleration(ax, ay, az);
      IMU.readGyroscope(gx, gy, gz);


      Serial.print(millis());
      Serial.print(",");
      Serial.print(ax);
      Serial.print(",");
      Serial.print(ay);
      Serial.print(",");
      Serial.print(az);
      Serial.print(",");
      Serial.print(gx);
      Serial.print(",");
      Serial.print(gy);
      Serial.print(",");
      Serial.println(gz);
    }


    delay(10); // Limit data rate
  }
}
