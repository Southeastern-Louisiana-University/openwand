import serial
import time
import argparse
import serial.tools.list_ports
import numpy as np
import pickle
from sklearn.preprocessing import StandardScaler
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Parse command line arguments
parser = argparse.ArgumentParser(description='ESP32 IMU Data Reader')
parser.add_argument('--port', type=str, default=None, help='Serial port')
parser.add_argument('--baud', type=int, default=115200, help='Baud rate')
parser.add_argument('--model', type=str, default='model.pkl', help='Path to ML model file')
parser.add_argument('--scaler', type=str, default='scaler.pkl', help='Path to scaler file')
parser.add_argument('--window', type=int, default=20, help='Samples before prediction')
parser.add_argument('--ha-url', type=str, default=os.getenv('HA_URL', 'http://localhost:8123'), help='Home Assistant URL')
parser.add_argument('--ha-token', type=str, default=os.getenv('HA_TOKEN'), help='Home Assistant Token')
args = parser.parse_args()

# Validate token
if not args.ha_token:
    raise ValueError("No Home Assistant token provided. Set HA_TOKEN in .env or use --ha-token")

# --- Load model and scaler ---
try:
    print(f"Loading model from {args.model}...")
    with open(args.model, 'rb') as f:
        model = pickle.load(f)
    print("Model loaded successfully!")
    
    print(f"Loading scaler from {args.scaler}...")
    with open(args.scaler, 'rb') as f:
        scaler = pickle.load(f)
    print("Scaler loaded successfully!")
except FileNotFoundError as e:
    print(f"Error: {e}")
    print("Will continue without making predictions.")
    model = None
    scaler = None
except Exception as e:
    print(f"Unexpected error: {e}")
    print("Will continue without making predictions.")
    model = None
    scaler = None

# Initialize data buffers
data_buffer = {
    'ax': [], 'ay': [], 'az': [],
    'gx': [], 'gy': [], 'gz': [],
    'mx': [], 'my': [], 'mz': []
}

def send_ha_event(gesture):
    """Securely send gesture event to Home Assistant"""
    url = f"{args.ha_url}/api/events/wand_gesture"
    headers = {
        "Authorization": f"Bearer {args.ha_token}",
        "Content-Type": "application/json"
    }
    data = {"gesture": gesture}
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=5)
        response.raise_for_status()
        print(f"HA Event: {gesture} (Status: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"Error sending to HA: {str(e)[:100]}...")

def extract_imu_data(line):
    """Extract IMU data from the Arduino's specific format"""
    if not line.startswith("IMU Data:"):
        return None

    try:
        # Split into sections
        sections = [s.strip() for s in line.split('\n') if s.strip()]
        
        # Parse accelerometer
        accel = [float(x) for x in sections[1].replace("Accel:", "").split(',')]
        
        # Parse gyroscope (note the space after Gyro)
        gyro = [float(x) for x in sections[2].replace("Gyro :", "").split(',')]
        
        # Parse magnetometer (note the space after Mag)
        mag = [float(x) for x in sections[3].replace("Mag  :", "").split(',')]

        return {
            'accel': accel[:3],  # Ensure only 3 values
            'gyro': gyro[:3],
            'mag': mag[:3]
        }
    except Exception as e:
        print(f"Data parsing error: {e}")
        return None
    
    return result

def compute_features():
    """Calculate statistical features from buffer"""
    features = []
    for key in data_buffer:
        arr = np.array(data_buffer[key])
        features += [
            arr.min() if len(arr) > 0 else 0,
            arr.max() if len(arr) > 0 else 0,
            arr.mean() if len(arr) > 0 else 0,
            arr.std() if len(arr) > 1 else 0
        ]
    return features

def reset_buffer():
    """Clear all data buffers"""
    for key in data_buffer:
        data_buffer[key] = []

def make_prediction():
    """Run ML prediction on collected data"""
    if model is None or scaler is None:
        print("Skipping prediction - no model loaded")
        reset_buffer()
        return
    
    try:
        features = compute_features()
        X = np.array(features).reshape(1, -1)
        X_scaled = scaler.transform(X)
        prediction = model.predict(X_scaled)[0]
        
        print(f"\nPredicted Gesture: {prediction}\n")
        send_ha_event(prediction)
        reset_buffer()
    except Exception as e:
        print(f"Prediction failed: {e}")

def main():
    """Main serial reading loop"""
    # Port detection
    available_ports = [p.device for p in serial.tools.list_ports.comports()]
    if not available_ports:
        print("No serial ports found!")
        return

    port = args.port or available_ports[0]
    if args.port is None and len(available_ports) > 1:
        print("Available ports:")
        for i, p in enumerate(available_ports):
            print(f"{i}: {p}")
        try:
            port = available_ports[int(input("Select port: "))]
        except:
            print("Using first port")

    # Serial connection
    ser = None
    for baud in [args.baud, 9600]:
        try:
            ser = serial.Serial(port, baud, timeout=1)
            print(f"Connected to {port} at {baud} baud")
            break
        except Exception as e:
            print(f"Failed at {baud} baud: {e}")
    
    if not ser:
        print("Couldn't establish serial connection")
        return

    # Main loop
    try:
        sample_count = 0
        start_time = time.time()
        
        while True:
            try:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if not line:
                    continue

                sample_count += 1
                if "IMU Data:" in line:
                    data = extract_imu_data(line)
                    if not data:
                        continue

                    # Update buffers
                    if 'accel' in data:
                        data_buffer['ax'].append(data['accel'][0])
                        data_buffer['ay'].append(data['accel'][1])
                        data_buffer['az'].append(data['accel'][2])
                    
                    if 'gyro' in data:
                        data_buffer['gx'].append(data['gyro'][0])
                        data_buffer['gy'].append(data['gyro'][1])
                        data_buffer['gz'].append(data['gyro'][2])
                    
                    if 'mag' in data:
                        data_buffer['mx'].append(data['mag'][0])
                        data_buffer['my'].append(data['mag'][1])
                        data_buffer['mz'].append(data['mag'][2])

                    # Check prediction window
                    if all(len(v) >= args.window for v in data_buffer.values()):
                        make_prediction()

                # Periodic status
                if time.time() - start_time > 10:
                    print(f"\nSamples: {sample_count} | Last Gesture: {data_buffer.get('last_gesture', 'None')}\n")
                    start_time = time.time()
                    sample_count = 0

            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"Loop error: {e}")

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        if ser and ser.is_open:
            ser.close()

if __name__ == "__main__":
    main()