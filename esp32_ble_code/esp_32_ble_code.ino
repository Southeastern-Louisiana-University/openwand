#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEClient.h>
#include <BLEAdvertisedDevice.h>

BLEScan* pBLEScan;
BLEAdvertisedDevice* targetDevice = nullptr;
BLEClient* pClient = nullptr;
BLERemoteCharacteristic* pRemoteCharacteristic = nullptr;

std::vector<float> accelData, gyroData, magData;
bool connected = false;

static void notifyCallback(
  BLERemoteCharacteristic* pBLERemoteCharacteristic,
  uint8_t* pData, size_t length, bool isNotify
) {
  if (length < 13) return;

  char header = pData[0];
  float x, y, z;
  memcpy(&x, pData + 1, 4);
  memcpy(&y, pData + 5, 4);
  memcpy(&z, pData + 9, 4);

  if (header == 'A') accelData = {x, y, z};
  else if (header == 'G') gyroData = {x, y, z};
  else if (header == 'M') magData = {x, y, z};

  if (!accelData.empty() && !gyroData.empty() && !magData.empty()) {
    Serial.println("IMU Data:");
    Serial.printf("Accel: %.2f, %.2f, %.2f\n", accelData[0], accelData[1], accelData[2]);
    Serial.printf("Gyro : %.2f, %.2f, %.2f\n", gyroData[0], gyroData[1], gyroData[2]);
    Serial.printf("Mag  : %.2f, %.2f, %.2f\n", magData[0], magData[1], magData[2]);
    accelData.clear();
    gyroData.clear();
    magData.clear();
  }
}

class MyAdvertisedDeviceCallbacks : public BLEAdvertisedDeviceCallbacks {
  void onResult(BLEAdvertisedDevice advertisedDevice) {
    if (advertisedDevice.getName() == "Nano33IMU") {
      Serial.println("Found Nano33IMU. Stopping scan...");
      targetDevice = new BLEAdvertisedDevice(advertisedDevice); // Save for later use
      pBLEScan->stop();
    }
  }
};

void connectToDevice() {
  pClient = BLEDevice::createClient();
  Serial.println("Connecting to Nano33IMU...");

  if (!pClient->connect(targetDevice)) {
    Serial.println("Failed to connect.");
    return;
  }

  Serial.println("Connected!");

  BLERemoteService* pRemoteService = pClient->getService("19B10000-E8F2-537E-4F6C-D104768A1214");
  if (pRemoteService == nullptr) {
    Serial.println("Service not found.");
    return;
  }

  pRemoteCharacteristic = pRemoteService->getCharacteristic("19B10001-E8F2-537E-4F6C-D104768A1214");
  if (pRemoteCharacteristic == nullptr) {
    Serial.println("Characteristic not found.");
    return;
  }

  if (pRemoteCharacteristic->canNotify()) {
    pRemoteCharacteristic->registerForNotify(notifyCallback);
    connected = true;
    Serial.println("Subscribed to notifications.");
  }
}

void setup() {
  Serial.begin(115200);
  BLEDevice::init("");

  pBLEScan = BLEDevice::getScan();
  pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
  pBLEScan->setActiveScan(true);
  pBLEScan->start(5, false);
}

void loop() {
  if (!connected && targetDevice != nullptr) {
    connectToDevice();
  }

  if (!connected && targetDevice == nullptr) {
    Serial.println("Rescanning...");
    pBLEScan->start(5, false);
  }

  delay(2000);
}
