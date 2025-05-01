# OpenWand
This project uses a Arduino Nano (Ble 33 sense rev2), ESP32, Hue Philips bulbs and bridge, and Home Assistant integration software.

# Goals
Train a machine learning AI to operate the open source Home Assistant software to in essence operate your own home with the ease of casting a spell symbol in the 
2D/3D plane in front of you.

# Requirements (Initial Phase of Development)
Parts:
- Arduino Nano (Ble 33 sense rev2)
  - link to view/purchase item below: https://store-usa.arduino.cc/products/nano-33-ble-sense-rev2?srsltid=AfmBOooczgQTJtdyWRWWQVJghmGmQSC8zoNgwr_ypAFrXNcrLOVX3QD9
- Breadboard
  - link to view/purchase Breadboard: https://store-usa.arduino.cc/products/breadboard-400-contacts?queryID=64d91b135bb447391439199b0def6c53
- ESP32
  - link to ESP32: 
- PC or laptop that can run Arduino IDE
  - link to IDE: https://www.arduino.cc/en/software
- Home Assistant
  - link to Home Assistant: https://www.home-assistant.io/
- Hue Phillips Bulbs
  - link to Bulb/Bridge set: 

# Requirements (Code Develpment Phase)
- Drivers for computer to acknowledge the connection for the ESP32. Needed for Verifying and Uploading code into the ESP32.
  - link to download drivers: https://www.silabs.com/developer-tools/usb-to-uart-bridge-vcp-drivers?tab=downloads
  - Upon Downloading drivers, you must unzip the file, navigate to Device Manager(Windows key + X), then update drivers. Manual selection of which drivers to update is recommended
    simply navigate to the unzipped file you downloaded and select the application, more detailed documentation is provided inside the files downloaded.

# Libraries needed for Arduino Ide(Arduino Nano 33)
- "ArduinoBLE" "Version 1.4.0"
- "Arduino_BMI270_BMM150" "Version 1.2.1"
- "Arduino_LSM9DS1" "Version 1.1.1"

# Libraries needed for Arduino IDE(ESP32 Dev Module)
- Same libraries as the Arduino Nano 33, however the first library, "ArduinoBLE" must be uninstalled as it will have conflicts with the "ESP32 Dev Module".

