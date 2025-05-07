import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress INFO, WARNING, and ERROR from TensorFlow before importing it

import warnings
warnings.filterwarnings("ignore")  # Suppress Python warnings

import logging
logging.getLogger('tensorflow').setLevel(logging.FATAL)  # Suppress TensorFlow logsimport os

import absl.logging
absl.logging.set_verbosity(absl.logging.ERROR)

import serial
import numpy as np
import time
import requests
from tensorflow.keras.models import load_model
from sklearn.preprocessing import LabelEncoder
from serial.tools.list_ports import comports

class GestureClassifier:
    def __init__(self):
        # Load model and setup labels
        self.model = load_model('imu_gesture_recognition.h5')
        self.label_encoder = LabelEncoder()
        self.label_encoder.classes_ = np.array(['up', 'down', 'left', 'right', 'still', 'shake'])

        # Data collection parameters
        self.WINDOW_SIZE = 35
        self.DATA_TIMEOUT = 1.0
        self.data_buffer = []
        self.last_data_time = time.time()

        # Home Assistant configuration
        self.HA_API_URL = "http://localhost:8123/api/events/wand_gesture"
        self.HA_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJmYTc1YWYwOWNhNTE0YTY1YmQyMGQxYzVlNWMyNmEyNCIsImlhdCI6MTc0NjMyMTgzMiwiZXhwIjoyMDYxNjgxODMyfQ.CRPFFhftJCrTglaK_3CJHmFrvhfjarJwXPVeMnP172g"

        # Gesture mapping (original → HA action)
        self.GESTURE_MAPPING = {
            'up': 'down',
            'down': 'left', 
            'left': 'right',
            'right': 'left',
            'shake': 'up',
            'still': 'still'
        }

    def setup_serial(self):
        """Initialize serial connection to Arduino"""
        ports = [port.device for port in comports()]
        if not ports:
            raise RuntimeError("No serial ports found")

        print("\nAvailable ports:")
        for i, port in enumerate(ports):
            print(f"{i+1}. {port}")

        port = ports[int(input("Select port number: "))-1]
        return serial.Serial(port, 115200, timeout=1)

    def parse_imu_data(self, line):
        """Parse incoming IMU data"""
        try:
            if any(s in line for s in ["Arduino", "===", "HOLD"]):
                return None
            parts = line.strip().split(',')
            return np.array([float(x) for x in parts[1:7]])
        except Exception as e:
            print(f"Data parsing error: {e}")
            return None

    def send_ha_event(self, gesture):
        """Send gesture event to Home Assistant"""
        mapped_gesture = self.GESTURE_MAPPING.get(gesture, gesture)
        try:
            data = {
                "event_type": "wand_gesture",  # Specify event type here
                "gesture": mapped_gesture.lower()  # Send the gesture as the data
            }
            response = requests.post(
                self.HA_API_URL,
                headers={
                    "Authorization": f"Bearer {self.HA_TOKEN}",
                    "Content-Type": "application/json"
                },
                json=data,
                timeout=3
            )
            if response.status_code == 200:
                print(f"Successfully sent '{mapped_gesture}' to Home Assistant")
            else:
                print(f"HA API Error {response.status_code}: {response.text}")
        except Exception as e:
            print(f"Failed to send to HA: {str(e)}")

    def classify_gesture(self):
        """Classify collected IMU data"""
        if len(self.data_buffer) < self.WINDOW_SIZE:
            return None, 0

        data = np.array(self.data_buffer[-self.WINDOW_SIZE:])
        prediction = self.model.predict(data[np.newaxis, ...], verbose=0)
        gesture = self.label_encoder.inverse_transform([np.argmax(prediction)])[0]
        confidence = np.max(prediction)
        
        return gesture, float(confidence)

    def run(self):
        """Main execution loop"""
        try:
            with self.setup_serial() as ser:
                print("\nGesture detection active. Perform movements...")
                print("Press Ctrl+C to quit\n")

                while True:
                    # Read serial data
                    if ser.in_waiting:
                        line = ser.readline().decode('utf-8', errors='ignore').strip()
                        imu_data = self.parse_imu_data(line)
                        if imu_data is not None:
                            self.data_buffer.append(imu_data)
                            self.last_data_time = time.time()

                    # Process when movement stops
                    if (time.time() - self.last_data_time > self.DATA_TIMEOUT) and self.data_buffer:
                        gesture, confidence = self.classify_gesture()
                        if gesture and confidence > 0.7:  # 70% confidence threshold
                            print(f"\n (Confidence: {confidence:.0%})")
                            self.send_ha_event(gesture)
                        self.data_buffer = []  # Reset for next gesture

                    time.sleep(0.01)

        except KeyboardInterrupt:
            print("\nStopped by user")
        except Exception as e:
            print(f"\nFatal error: {e}")

if __name__ == "__main__":
    classifier = GestureClassifier()
    classifier.run()
