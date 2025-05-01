iimport serial
import time
import argparse
import serial.tools.list_ports
import numpy as np
import pickle
from sklearn.preprocessing import StandardScaler

# Parse command line arguments
parser = argparse.ArgumentParser(description='ESP32 IMU Data Reader')
parser.add_argument('--port', type=str, default=None, help='Serial port')
parser.add_argument('--baud', type=int, default=115200, help='Baud rate')
parser.add_argument('--model', type=str, default='model.pkl', help='Path to ML model file')
parser.add_argument('--scaler', type=str, default='scaler.pkl', help='Path to scaler file')
parser.add_argument('--window', type=int, default=20, help='Samples before prediction')
args = parser.parse_args()

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

def extract_imu_data(line):
    """Extract IMU data from a line containing 'IMU Data:'"""
    if "IMU Data:" not in line:
        return None
    
    result = {}
    
    # Extract accelerometer data
    if "Accel:" in line:
        try:
            accel_part = line.split("Accel:")[1].split("Gyro")[0]
            values = [float(val.strip()) for val in accel_part.split(",")]
            if len(values) >= 3:
                result['accel'] = values[:3]
        except:
            pass
    
    # Extract gyroscope data
    if "Gyro" in line:
        try:
            gyro_part = line.split("Gyro :")[1].split("Mag")[0]
            values = [float(val.strip()) for val in gyro_part.split(",")]
            if len(values) >= 3:
                result['gyro'] = values[:3]
        except:
            pass
    
    # Extract magnetometer data
    if "Mag" in line:
        try:
            mag_part = line.split("Mag :")[1]
            values = [float(val.strip()) for val in mag_part.split(",")]
            if len(values) >= 3:
                result['mag'] = values[:3]
        except:
            pass
    
    return result

def compute_features():
    """Compute statistical features from the data buffer"""
    features = []
    for key in data_buffer:
        array = np.array(data_buffer[key])
        if len(array) > 0:
            features += [
                array.min(), 
                array.max(), 
                array.mean(), 
                array.std() if len(array) > 1 else 0
            ]
        else:
            features += [0, 0, 0, 0]
    return features

def reset_buffer():
    """Reset all data buffers"""
    for key in data_buffer:
        data_buffer[key] = []

def make_prediction():
    """Make a prediction based on current data buffer"""
    if model is None or scaler is None:
        print("Model or scaler not loaded. Cannot make prediction.")
        reset_buffer()
        return
    
    try:
        features = compute_features()
        X = np.array(features).reshape(1, -1)
        X_scaled = scaler.transform(X)
        prediction = model.predict(X_scaled)
        prediction_idx = prediction[0]
        
        print(f"\n--- PREDICTION: {prediction_idx} ---\n")
        
        reset_buffer()
    except Exception as e:
        print(f"Error making prediction: {e}")

def main():
    # List available ports
    available_ports = [port.device for port in serial.tools.list_ports.comports()]
    print(f"Available serial ports: {available_ports}")
    
    # Select a port
    port = args.port
    if port is None:
        if not available_ports:
            print("No serial ports found. Please check your connections.")
            return
        
        print("No port specified. Please select a port:")
        for i, p in enumerate(available_ports):
            print(f"{i}: {p}")
        
        try:
            idx = int(input("Enter port number: "))
            if 0 <= idx < len(available_ports):
                port = available_ports[idx]
            else:
                print("Invalid selection. Exiting.")
                return
        except:
            print("Invalid input. Exiting.")
            return
    
    # Try opening the port with different settings
    ser = None
    for baudrate in [115200, 9600]:
        for timeout in [1, 0.1, 2]:
            try:
                print(f"Trying to open {port} with baudrate {baudrate}, timeout {timeout}...")
                ser = serial.Serial(port, baudrate, timeout=timeout)
                print(f"Success! Connected with baudrate {baudrate}, timeout {timeout}")
                break
            except Exception as e:
                print(f"Failed: {e}")
        
        if ser is not None:
            break
    
    if ser is None:
        print("Could not open the serial port with any settings. Please check your connections.")
        return
    
    print("\n===== ESP32 IMU DATA READER =====")
    print("Press Ctrl+C to exit")
    print("================================\n")
    
    sample_count = 0
    data_count = 0
    start_time = time.time()
    
    try:
        while True:
            try:
                # Read a line of data
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                
                if line:
                    sample_count += 1
                    print(f"Line {sample_count}: {line}")
                    
                    # Try to extract IMU data
                    if "IMU Data:" in line:
                        data = extract_imu_data(line)
                        
                        if data:
                            data_count += 1
                            print(f"  → Extracted data: {data}")
                            
                            # Update data buffers
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
                            
                            # Show buffer sizes
                            acc_count = len(data_buffer['ax'])
                            gyro_count = len(data_buffer['gx'])
                            mag_count = len(data_buffer['mx'])
                            print(f"  → Buffer sizes: A={acc_count}, G={gyro_count}, M={mag_count}/{args.window}")
                            
                            # Make prediction if we have enough data
                            if acc_count >= args.window and gyro_count >= args.window and mag_count >= args.window:
                                make_prediction()
                    
                # Every 10 seconds, print a status update
                if time.time() - start_time > 10:
                    elapsed = time.time() - start_time
                    print(f"\n--- Stats: {sample_count} lines, {data_count} data points in {elapsed:.1f} seconds ---\n")
                    start_time = time.time()
                    sample_count = 0
                    data_count = 0
                    
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"Error: {e}")
            
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\nReader stopped by user")
    finally:
        if ser is not None:
            ser.close()
            print("Serial port closed")

if __name__ == "__main__":
    main()
