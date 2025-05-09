import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import warnings
warnings.filterwarnings("ignore")
import absl.logging
absl.logging.set_verbosity(absl.logging.ERROR) 
import sys
import time
import numpy as np
import requests
import serial  # Added this import
from serial.tools.list_ports import comports
from datetime import datetime
from tensorflow.keras.models import load_model
from sklearn.preprocessing import LabelEncoder

class GestureClassifier:
    def __init__(self, com_port=None):
        # Model setup
        self.model = load_model('imu_gesture_recognition.h5')
        self.label_encoder = LabelEncoder()
        self.label_encoder.classes_ = np.array(['up', 'down', 'left', 'right', 'still', 'shake'])
        
        # Serial configuration
        self.com_port = com_port
        self.ser = None
        self.WINDOW_SIZE = 35
        self.DATA_TIMEOUT = 1.0
        self.data_buffer = []
        self.last_data_time = time.time()
        
        # Home Assistant configuration
        self.HA_API_URL = "http://localhost:8123/api/events/wand_gesture"
        self.HA_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJmYTc1YWYwOWNhNTE0YTY1YmQyMGQxYzVlNWMyNmEyNCIsImlhdCI6MTc0NjMyMTgzMiwiZXhwIjoyMDYxNjgxODMyfQ.CRPFFhftJCrTglaK_3CJHmFrvhfjarJwXPVeMnP172g"
        self.GESTURE_MAPPING = {
            'up': 'down',
            'down': 'left', 
            'left': 'right',
            'right': 'left',
            'shake': 'up',
            'still': 'still',
        }

    def setup_serial(self):
        """Setup serial port connection"""
        if not self.com_port:
            ports = comports()
            if not ports:
                raise RuntimeError("No COM ports found!")
            
            print("\nAvailable COM Ports:")
            for i, port in enumerate(ports, 1):
                print(f"{i}. {port.device} - {port.description or 'Unknown'}")
            
            while True:
                try:
                    selection = input("\nSelect COM port number: ")
                    selection = int(selection)
                    if 1 <= selection <= len(ports):
                        self.com_port = ports[selection-1].device
                        break
                    print("Invalid selection. Try again.")
                except ValueError:
                    print("Please enter a number")

        try:
            print(f"\nConnecting to {self.com_port}...")
            ser = serial.Serial(
                port=self.com_port,
                baudrate=115200,
                timeout=1
            )
            print(f"Successfully connected to {self.com_port}")
            return ser
            
        except serial.SerialException as e:
            print(f"\nFailed to connect to {self.com_port}")
            print(f"Error: {e}")
            print("\nTroubleshooting:")
            print("1. Make sure Arduino is connected")
            print("2. Close other programs using this port")
            print("3. Try unplugging and replugging Arduino")
            raise

    def send_ha_event(self, gesture):
        """Send gesture event to Home Assistant"""
        mapped_gesture = self.GESTURE_MAPPING.get(gesture, gesture)
        print(f"→ {mapped_gesture.upper()}")  # Only print the final mapped gesture
        
        try:
            response = requests.post(
                self.HA_API_URL,
                headers={
                    "Authorization": f"Bearer {self.HA_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={
                    "event_type": "wand_gesture",
                    "gesture": mapped_gesture.lower()
                },
                timeout=3
            )
            if response.status_code != 200:
                print(f"Error sending to HA: {response.text}")
        except Exception as e:
            print(f"Connection Error: {str(e)}")

    def parse_imu_data(self, line):
        try:
            if any(s in line for s in ["Arduino", "===", "HOLD"]):
                return None
            parts = line.strip().split(',')
            if len(parts) != 7:
                return None
            return np.array([float(x) for x in parts[1:7]])
        except Exception as e:
            print(f"Data error: {e}")
            return None

    def run(self):
        try:
            with open('gesture_log.txt', 'w') as f:
                f.write(f"[{datetime.now().strftime('%H:%M:%S')}] Log started\n")
            
            with self.setup_serial() as ser:
                self.ser = ser
                # Movement legend display
                print("\nGesture Controls Legend:")
                print("=================================")
                print("UP\t\t- Brightness up")
                print("DOWN\t\t- Candlelight mode")
                print("LEFT\t\t- Purple color")
                print("RIGHT\t\t- Random color")
                print("STILL\t\t- Lights off")
                print("=================================")
                print("\nGesture detection ready. Detected gestures will be shown below:\n")
                
                while True:
                    if ser.in_waiting:
                        line = ser.readline().decode('utf-8', errors='ignore').strip()
                        
                        with open('gesture_log.txt', 'a') as f:
                            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] RAW: {line}\n")
                        
                        imu_data = self.parse_imu_data(line)
                        if imu_data is not None:
                            self.data_buffer.append(imu_data)
                            self.last_data_time = time.time()

                    if (time.time() - self.last_data_time > self.DATA_TIMEOUT) and self.data_buffer:
                        if len(self.data_buffer) >= self.WINDOW_SIZE:
                            data = np.array(self.data_buffer[-self.WINDOW_SIZE:])
                            prediction = self.model.predict(data[np.newaxis, ...], verbose=0)
                            gesture = self.label_encoder.inverse_transform([np.argmax(prediction)])[0]
                            
                            with open('gesture_log.txt', 'a') as f:
                                f.write(f"[{datetime.now().strftime('%H:%M:%S')}] GESTURE: {gesture}\n")
                            
                            self.send_ha_event(gesture)
                            
                        self.data_buffer = []

                    time.sleep(0.01)

        except KeyboardInterrupt:
            print("\nStopping...")
        except Exception as e:
            print(f"\nError: {e}")
        finally:
            if hasattr(self, 'ser') and self.ser and self.ser.is_open:
                self.ser.close()

if __name__ == "__main__":
    print("=== Magic Wand Control ===")
    com_port = sys.argv[1] if len(sys.argv) > 1 else None
    classifier = GestureClassifier(com_port)
    classifier.run()