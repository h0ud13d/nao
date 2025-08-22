import os
import json
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf
import logging
import base64
from flask import Flask, request, jsonify
import numpy as np
import cv2
import time
from ultralytics import YOLO
import face_recognition

# Configure logging
logging.basicConfig(level=logging.ERROR)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# Load models at startup
try:
    interpreter = tf.lite.Interpreter(model_path="./../models/peekaboo_model.tflite")
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    print("TFLite model loaded successfully")
except Exception as e:
    print(f"Error loading TFLite model: {str(e)}")
    interpreter = None

try:
    yolo_model = YOLO('./../models/yolov8n.pt')
    print("YOLO model loaded successfully")
except Exception as e:
    print(f"Error loading YOLO model: {str(e)}")
    yolo_model = None

def preprocess_image(image):
    """Preprocess the image to fit the TensorFlow Lite model's input size."""
    image_resized = cv2.resize(image, (224, 224))
    image_normalized = image_resized.astype('float32') / 255.0
    image_reshaped = np.expand_dims(image_normalized, axis=0)
    return image_reshaped

def predict_tflite(image):
    """Run inference using the TensorFlow Lite model."""
    try:
        interpreter.set_tensor(input_details[0]['index'], image)
        interpreter.invoke()
        output_data = interpreter.get_tensor(output_details[0]['index'])
        return output_data
    except Exception as e:
        print(f"Error in TFLite prediction: {str(e)}")
        return None

def predict_yolo(image):
    """Run YOLO object detection."""
    try:
        results = yolo_model(image)
        predictions = []
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = [int(x) for x in box.xyxy[0].tolist()]
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                
                predictions.append({
                    "confidence": confidence,
                    "class": class_id,
                    "bounding_box": [x1, y1, x2, y2]
                })
                
        print(f"YOLO predictions: {predictions}")
        return predictions
    except Exception as e:
        print(f"Error in YOLO prediction: {str(e)}")
        return None

def detect_faces(image):
    """Run face detection and return face locations."""
    try:
        # Resize image for faster detection but keep it larger than before
        small_frame = cv2.resize(image, (0, 0), fx=0.5, fy=0.5)

        # Convert BGR to RGB (simplified)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        face_locations = face_recognition.face_locations(
            rgb_small_frame,
            model="hog",  
            number_of_times_to_upsample=1  # Reduced for speed
        )
        
        # Scale back up face locations
        scale = 2  # Since we used fx=0.5
        face_locations_full = [
            [int(top * scale), int(right * scale), 
             int(bottom * scale), int(left * scale)]
            for top, right, bottom, left in face_locations
        ]
        
        return face_locations_full
    except Exception as e:
        print(f"Error in face detection: {str(e)}")
        return []

@app.route("/predict/<model_type>", methods=["POST"])
def predict_endpoint(model_type):
    """Endpoint that takes model type as part of the URL."""
    #print(f"\nReceived prediction request for model: {model_type}")
    
    if model_type not in ['tflite', 'yolo', 'face', 'both']:
        return jsonify({'error': 'Invalid model type. Use tflite, yolo, face, or both'}), 400
    
    try:
        data = request.json
        if not data or 'image' not in data:
            return jsonify({'error': 'No image data provided'}), 400
            
        image_base64 = data['image']
        
        # Decode the base64 image
        #print("Decoding image...")
        image_bytes = base64.b64decode(image_base64)
        image_np = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
        
        if image is None:
            return jsonify({'error': 'Failed to decode image'}), 400
            
        #print(f"Image shape: {image.shape}")
        
        response = {}
        
        # Run predictions based on requested model
        if model_type in ['tflite', 'both']:
            if interpreter is not None:
                preprocessed_image = preprocess_image(image)
                tflite_result = predict_tflite(preprocessed_image)
                if tflite_result is not None:
                    response['tflite_prediction'] = tflite_result.tolist()
            else:
                response['tflite_error'] = 'TFLite model not loaded'
        
        if model_type in ['yolo', 'both']:
            if yolo_model is not None:
                yolo_result = predict_yolo(image)
                if yolo_result is not None:
                    response['yolo_prediction'] = yolo_result
            else:
                response['yolo_error'] = 'YOLO model not loaded'
                
        if model_type in ['face', 'both']:
            #print('Processing face detection...')
            face_locations = detect_faces(image)
            response['face_locations'] = face_locations
                #response['face_locations'] = face_locations
        else:
            response['face_error'] = 'Face detection failed'
                #response['face_locations'] = face_locations
        
        #print(f"Sending response: {response}")
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in predict_endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route("/status", methods=["GET"])
def status():
    """Check server status and available models."""
    return jsonify({
        'status': 'running',
        'available_models': {
            'tflite': interpreter is not None,
            'yolo': yolo_model is not None,
            'face': True
        }
    })

if __name__ == "__main__":
    print("\nServer starting...")
    print("\nModel Status:")
    print(f"- TFLite model: {'Loaded' if interpreter is not None else 'Not loaded'}")
    print(f"- YOLO model: {'Loaded' if yolo_model is not None else 'Not loaded'}")
    print("- Face detection: Available")
    print("\nAvailable endpoints:")
    print("- POST /predict/tflite : Use TFLite model")
    print("- POST /predict/yolo   : Use YOLO model")
    print("- POST /predict/face   : Use face detection")
    print("- POST /predict/both   : Use all models")
    print("- GET  /status        : Check server status")
    
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
