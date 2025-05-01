#include <ArduinoBLE.h>
#include <Arduino_BMI270_BMM150.h>

BLEService imuService("19B10000-E8F2-537E-4F6C-D104768A1214");
BLECharacteristic imuCharacteristic("19B10001-E8F2-537E-4F6C-D104768A1214", 
                                    BLERead | BLENotify, 20);

const int buttonPin = 2;

void setup() {
  Serial.begin(9600);
  unsigned long start = millis();
  while (!Serial && millis() - start < 1500);

  pinMode(buttonPin, INPUT_PULLUP);

  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1);
  }

  if (!BLE.begin()) {
    Serial.println("Starting BLE failed!");
    while (1);
  }

  BLE.setLocalName("Nano33IMU");
  BLE.setAdvertisedService(imuService);
  imuService.addCharacteristic(imuCharacteristic);
  BLE.addService(imuService);
  BLE.advertise();

  Serial.println("BLE IMU Peripheral is now advertising");
}

void loop() {
  BLEDevice central = BLE.central();
  if (central) {
    Serial.print("Connected to central: ");
    Serial.println(central.address());

    while (central.connected()) {
      if (digitalRead(buttonPin) == LOW) {
        float aX, aY, aZ, gX, gY, gZ, mX, mY, mZ;

        if (IMU.accelerationAvailable() && IMU.gyroscopeAvailable() && IMU.magneticFieldAvailable()) {
          IMU.readAcceleration(aX, aY, aZ);
          IMU.readGyroscope(gX, gY, gZ);
          IMU.readMagneticField(mX, mY, mZ);

          // Accelerometer packet
          uint8_t accelPacket[13];
          accelPacket[0] = 'A';
          memcpy(&accelPacket[1], &aX, 4);
          memcpy(&accelPacket[5], &aY, 4);
          memcpy(&accelPacket[9], &aZ, 4);
          imuCharacteristic.writeValue(accelPacket, 13);
          delay(10);

          // Gyroscope packet
          uint8_t gyroPacket[13];
          gyroPacket[0] = 'G';
          memcpy(&gyroPacket[1], &gX, 4);
          memcpy(&gyroPacket[5], &gY, 4);
          memcpy(&gyroPacket[9], &gZ, 4);
          imuCharacteristic.writeValue(gyroPacket, 13);
          delay(10);

          // Magnetometer packet
          uint8_t magPacket[13];
          magPacket[0] = 'M';
          memcpy(&magPacket[1], &mX, 4);
          memcpy(&magPacket[5], &mY, 4);
          memcpy(&magPacket[9], &mZ, 4);
          imuCharacteristic.writeValue(magPacket, 13);
          delay(10);

          Serial.println("Sent IMU data (A, G, M)");
        }

        delay(200); // Avoid flooding
      }
    }

    Serial.println("Disconnected from central");
  }
}