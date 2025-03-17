import serial
import csv
import time
import sys
import signal
import numpy as np

# --- CONFIGURATION ---
SERIAL_PORT = 'COM10'  # Change to your port
BAUD_RATE = 115200
CSV_FILE = 'movement_data.csv'

# --- GLOBAL ---
data_rows = []
current_movement = ''
samples_per_movement = 100
sample_count = 0

def signal_handler(sig, frame):
    print('\nCtrl+C detected. Saving data to CSV...')
    save_to_csv(data_rows)
    sys.exit(0)

def save_to_csv(data):
    if not data:
        print("No data to save.")
        return

    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            'min_ax', 'max_ax', 'mean_ax', 'std_ax',
            'min_ay', 'max_ay', 'mean_ay', 'std_ay',
            'min_az', 'max_az', 'mean_az', 'std_az',
            'min_gx', 'max_gx', 'mean_gx', 'std_gx',
            'min_gy', 'max_gy', 'mean_gy', 'std_gy',
            'min_gz', 'max_gz', 'mean_gz', 'std_gz',
            'min_mx', 'max_mx', 'mean_mx', 'std_mx',
            'min_my', 'max_my', 'mean_my', 'std_my',
            'min_mz', 'max_mz', 'mean_mz', 'std_mz',
            'label'
        ])
        writer.writerows(data)
    print(f"Saved {len(data)} samples to {CSV_FILE}")

def parse_serial_line(line):
    try:
        parts = line.strip().split(',')
        if len(parts) != 10:
            return None
        readings = list(map(float, parts[:9]))
        label = parts[9]
        return readings, label
    except ValueError:
        return None

def collect_sample(serial_connection, label):
    collected_data = []
    print(f"Recording sample {sample_count+1}/100 for movement: {label}")

    while True:
        if serial_connection.in_waiting > 0:
            line = serial_connection.readline().decode('utf-8').strip()

            if "STOP recording" in line:
                break

            parsed = parse_serial_line(line)
            if parsed:
                readings, current_label = parsed
                collected_data.append(readings)

    if not collected_data:
        print("No data collected for this sample.")
        return None

    return compute_features(collected_data, label)

def compute_features(data, label):
    np_data = np.array(data)
    features = []

    for i in range(9):
        axis_data = np_data[:, i]
        features.extend([
            np.min(axis_data),
            np.max(axis_data),
            np.mean(axis_data),
            np.std(axis_data)
        ])

    features.append(label)
    return features

def main():
    global sample_count, current_movement
    signal.signal(signal.SIGINT, signal_handler)

    print(f"Connecting to {SERIAL_PORT} at {BAUD_RATE} baud...")
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
        sys.exit(1)

    print("Connected! Press and hold button on Arduino to record each sample. Ctrl+C to save and exit.")

    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()

            if "START recording" in line:
                # Extract current label from the log line
                parts = line.split(':')
                if len(parts) > 1:
                    label = parts[1].strip().split(' ')[0]
                else:
                    label = 'unknown'

                current_movement = label
                sample = collect_sample(ser, label)

                if sample:
                    data_rows.append(sample)
                    sample_count += 1
                    print(f"Sample {sample_count}/100 for '{label}' recorded.\n")

                if sample_count >= samples_per_movement:
                    sample_count = 0
                    print(f"Completed 100 samples for '{label}'. Move to next movement on Arduino.\n")

if __name__ == '__main__':
    main()
