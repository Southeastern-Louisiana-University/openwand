import serial
import csv

# Set up connection
port = 'COM3'  # Replace with your Arduino's port. If conected by bluetooth it should be COM5 or COM6, check your device manager ports if your unsure
baud_rate = 9600
ser = serial.Serial(port, baud_rate)
print(f"Connected to Arduino on {port}")

# Creates a CSV file
file_name = "wand_movements.csv"
with open(file_name, mode='w', newline='') as file:
    writer = csv.writer(file)
    # header row
    writer.writerow(["ax", "ay", "az", "gx", "gy", "gz"])

    print("Recording data... Press Ctrl+C to stop.")
    try:
        while True:
            if ser.in_waiting > 0:
                # Reads the data from serial port
                line = ser.readline().decode('utf-8').strip()
                print(f"Raw line: {line}")  

              
                if not line.replace(',', '').replace('.', '').replace('-', '').isdigit():
                    print(f"Skipping invalid line: {line}")  
                    continue

            
                try:
                    data = list(map(float, line.split(',')))
                    print(f"Processed data: {data}") 
                except ValueError as e:
                    print(f"Error converting line to floats: {e}")  
                    continue

                # Write the data to the CSV file
                writer.writerow(data)
                print(f"Recorded: {data}")  

    except KeyboardInterrupt:
        print("Recording stopped.")

