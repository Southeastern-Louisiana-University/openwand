import pandas as pd
import numpy as np
import tensorflow as tf
import os
print(os.path.exists("C:/Users/tescu/Desktop/Schoo/CMPS/CMPS 411/openwand/Arduino-Wand-code/Code/wand_code_5/model_for_arduino.tflite"))


# Load TensorFlow Lite model
model = tf.lite.Interpreter(model_path="C:/Users/tescu/Desktop/Schoo/CMPS/CMPS 411/openwand/Arduino-Wand-code/Code/wand_code_5/model_for_arduino.tflite")
model.allocate_tensors()

# Get input and output tensor indices
input_index = model.get_input_details()[0]['index']
output_index = model.get_output_details()[0]['index']

# Load CSV data
csv_file = 'arduino_imu_movements.csv'  # Path to your CSV file
df = pd.read_csv(csv_file)

print("Columns in the CSV:", df.columns)

# Extract features (ax, ay, az, gx, gy, gz) and labels (gesture)
features = df[['ax', 'ay', 'az', 'gx', 'gy', 'gz']].values
labels = df['gesture'].values

# Normalize the features (mean and std can be adjusted or pre-calculated)
mean = np.mean(features, axis=0)
std = np.std(features, axis=0)
normalized_features = (features - mean) / std

# Ensure the shape is correct for TensorFlow Lite model input
# Typically, TensorFlow Lite models expect an input shape like [batch_size, num_features]
# If the model expects a batch size of 1 (common for real-time predictions), reshape to (1, num_features)
def make_prediction(data):
    # Reshape the input data to match the expected input shape (1, num_features)
    input_data = np.expand_dims(data, axis=0).astype(np.float32)  # Ensure it has the correct dtype
    model.set_tensor(input_index, input_data)
    model.invoke()

    # Get model output
    output = model.get_tensor(output_index)

    # Get the gesture with the highest probability (assuming the output is 1D array of probabilities)
    gesture_index = np.argmax(output)
    gestures = ["M", "T", "X", "CIRCLE", "SQUARE", "TRIANGLE"]
    
    # If the output is 2D (e.g., [1, num_classes]), make sure to grab the first element
    return gestures[gesture_index], output[0][gesture_index]  # Confidence is the probability of the predicted class

# Classify all rows in the CSV
predictions = []
for i in range(len(normalized_features)):
    predicted_gesture, confidence = make_prediction(normalized_features[i])
    predictions.append((labels[i], predicted_gesture, confidence))

# Print out the results
for true_label, predicted_gesture, confidence in predictions:
    print(f"True: {true_label}, Predicted: {predicted_gesture}, Confidence: {confidence}")