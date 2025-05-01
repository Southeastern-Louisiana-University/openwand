# OpenWand
This project uses a Arduino Nano (Ble 33 sense rev2).

# Goals
Train a machine learning AI to operate the open source Home Assistant OS to in essence operate your own home with the ease of casting a spell symbol in the 
2D/3D plane in front of you.

# Requirements (Initial Phase of Development)
Parts:
- Arduino Nano (Ble 33 sense rev2)
  - link to view/purchase item below: https://store-usa.arduino.cc/products/nano-33-ble-sense-rev2?srsltid=AfmBOooczgQTJtdyWRWWQVJghmGmQSC8zoNgwr_ypAFrXNcrLOVX3QD9
- Breadboard
  - link to view/purchase Breadboard: https://store-usa.arduino.cc/products/breadboard-400-contacts?queryID=64d91b135bb447391439199b0def6c53  
- PC or laptop that can run Arduino IDE
  - link to IDE: https://www.arduino.cc/en/software
- Home Assistant
  - link to Home Assistant: https://www.home-assistant.io/


# Libraries needed for Arduino Ide(Arduino Nano 33)
- "ArduinoBLE"
- Arduino_BMI270_BMM150"
- "Arduino_LSM9DS1"

# Libraries needed for Arduino IDE(ESP32 Dev Module)
- Same libraries as the Arduino Nano 33, however the first library, "ArduinoBLE" must be uninstalled as it will have conflicts with the "ESP32 Dev Module".
