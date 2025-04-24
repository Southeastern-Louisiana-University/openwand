#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEClient.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>


static BLEUUID serviceUUID("19B10000-E8F2-537E-4F6C-D104768A1214");
static BLEUUID charUUID("19B10001-E8F2-537E-4F6C-D104768A1214");


BLERemoteCharacteristic* pRemoteCharacteristic;
BLEAddress* pServerAddress;
BLEClient* pClient;
bool doConnect = false, connected = false;


// Buffers to store parts
float accel[3] = {0}, gyro[3] = {0};
bool accelReceived = false, gyroReceived = false;


// Helper to print floats
void printVector(const char* label, float* vec) {
  Serial.print(label);
  Serial.print(": ");
  for (int i = 0; i < 3; i++) {
    Serial.print(vec[i], 3);
    Serial.print(i < 2 ? ", " : "\n");
  }
}


void notifyCallback(BLERemoteCharacteristic* pChar, uint8_t* data, size_t len, bool isNotify) {
  if (len < 13) {
    Serial.printf("Incomplete packet (len=%d)\n", len);
    return;
  }


  char type = (char)data[0];
  float values[3];
  memcpy(&values[0], &data[1], 12);


  if (type == 'A') {
    memcpy(accel, values, 3 * sizeof(float));
    accelReceived = true;
  } else if (type == 'G') {
    memcpy(gyro, values, 3 * sizeof(float));
    gyroReceived = true;
  } else {
    Serial.println("Unknown packet type");
    return;
  }


  // Print once both packets are in
  if (accelReceived && gyroReceived) {
    Serial.println("Full IMU frame received:");
    printVector("Accel", accel);
    printVector("Gyro", gyro);
    accelReceived = gyroReceived = false;
  }
}


bool connectToServer(BLEAddress address) {
  Serial.print("Connecting to ");
  Serial.println(address.toString().c_str());


  pClient = BLEDevice::createClient();
  if (!pClient->connect(address)) {
    Serial.println("Connection failed");
    return false;
  }


  Serial.println("Connected to server");


  BLERemoteService* service = pClient->getService(serviceUUID);
  if (!service) return false;


  pRemoteCharacteristic = service->getCharacteristic(charUUID);
  if (!pRemoteCharacteristic || !pRemoteCharacteristic->canNotify()) return false;


  pRemoteCharacteristic->registerForNotify(notifyCallback);
  connected = true;
  return true;
}


class MyAdvertisedDeviceCallbacks : public BLEAdvertisedDeviceCallbacks {
  void onResult(BLEAdvertisedDevice advertisedDevice) {
    if (advertisedDevice.haveServiceUUID() && advertisedDevice.isAdvertisingService(serviceUUID)) {
      BLEDevice::getScan()->stop();
      pServerAddress = new BLEAddress(advertisedDevice.getAddress());
      doConnect = true;
    }
  }
};


void setup() {
  Serial.begin(115200);
  BLEDevice::init("ESP32_IMU_Receiver");


  BLEScan* scan = BLEDevice::getScan();
  scan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
  scan->setActiveScan(true);
  scan->start(5, false);
}


void loop() {
  if (doConnect) {
    connectToServer(*pServerAddress);
    doConnect = false;
  }


  if (!connected) {
    delay(1000);
    Serial.println("Scanning again...");
    BLEDevice::getScan()->start(5, false);
  }


  delay(100);
}
