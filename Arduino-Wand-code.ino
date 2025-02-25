#include "Arduino_BMI270_BMM150.h"


const int buttonPin = 2;
bool recording = false;  


void setup() {
  Serial.begin(9600);
  while (!Serial);


 
  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1);
  }


 
  pinMode(buttonPin, INPUT_PULLUP);
}


void loop() {
 
  if (digitalRead(buttonPin) == LOW) {
    if (!recording) {
      Serial.println("");
      recording = true;
    }


    float ax, ay, az;


    if (IMU.accelerationAvailable()) {
      IMU.readAcceleration(ax, ay, az);
    //ax-blue; ay-orange; az-green; on the serial plotter
   
      Serial.print(ax); Serial.print(",");
      Serial.print(ay); Serial.print(",");
      Serial.println(az);
   
    }
  } else {
    if (recording) {
      Serial.println("");
      recording = false;
    }
  }
