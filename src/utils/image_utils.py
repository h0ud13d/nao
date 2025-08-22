# -*- coding: future_fstrings -*-
# utils/image_utils.py
import cv2
import numpy as np
import base64
import requests
import os
import time
from config import PREDICTION_SERVER_URL, COVERED_DIR, UNCOVERED_DIR

def capture_frame(video_service, video_client):
    """Capture a frame from NAO's video service with error handling."""
    try:
        image = video_service.getImageRemote(video_client)
        if image is None or len(image) < 7:
            print("Invalid image data received")
            return None
            
        image_width = image[0]
        image_height = image[1]
        
        # Create numpy array from image data
        try:
            image_array = np.frombuffer(image[6], dtype=np.uint8)
            image_array = image_array.reshape((image_height, image_width, 3))
            return image_array
        except Exception as e:
            print("Error reshaping image: {}".format(e))
            return None
            
    except KeyboardInterrupt:
        print("\nStopping video capture...")
        raise
    except Exception as e:
        print("Error capturing frame: {}".format(e))
        return None

def send_image_to_server(image, mode):
    """Send captured image to the flask server and receive a prediction."""
    try:
        _, image_encoded = cv2.imencode('.jpg', image)
        image_base64 = base64.b64encode(image_encoded.tostring())  # Use tostring() for Python 2.7
        
        url = f"{PREDICTION_SERVER_URL}/{mode}"
        
        response = requests.post(
            url,  
            json={"image": image_base64}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print("Server error: {}".format(response.status_code))
            return None
            
    except requests.exceptions.ConnectionError:
        print("Connection failed. Is the server running?")
        return None
    except Exception as e:
        print("Error sending image to server: {}".format(e))
        return None

def save_image(image, directory=None, prefix="image"):
    """Save an image to the specified directory with timestamp."""
    # Use configured directories if none provided
    if directory is None:
        if prefix == "covered":
            directory = COVERED_DIR
        elif prefix == "uncovered":
            directory = UNCOVERED_DIR
            
    if not os.path.exists(directory):
        os.makedirs(directory)
        
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(directory, "{0}_{1}.jpg".format(prefix, timestamp))
    cv2.imwrite(filename, image)
    num_files = len([f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))])
    print("Saved: {0}, Total: {1}".format(filename, num_files))
    return filename, num_files

def annotate_image(image, server_results, mode, class_names, center_frame_dim):
    """Annotate image based on detection results."""
    try:
        height, width = image.shape[:2]
        top_l, bottom_r = calculate_frame(width, height, center_frame_dim)
        
        # Draw center box
        cv2.rectangle(image, top_l, bottom_r, (255, 0, 0), 2)

        if mode == 'yolo' and 'yolo_prediction' in server_results:
            predictions = server_results['yolo_prediction']
            
            for result in predictions:
                try:
                    confidence = float(result['confidence'])
                    class_id = int(result['class'])
                    bbox = result['bounding_box']
                    
                    if not bbox or len(bbox) != 4:
                        print("Invalid bounding box:", bbox)
                        continue
                    
                    top_left = (int(bbox[0]), int(bbox[1]))
                    bottom_right = (int(bbox[2]), int(bbox[3]))
                    
                    class_name = class_names[class_id] if class_id < len(class_names) else "Unknown"
                    
                    # BGR color (green)
                    cv2.rectangle(image, top_left, bottom_right, (0, 255, 0), 2)
                    
                    label = "{0}: {1:.2f}".format(class_name, confidence)
                    cv2.putText(image, label, (top_left[0], top_left[1] - 10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    
                except Exception as e:
                    print("Error processing YOLO result: {}".format(e))
                    continue
                    
        elif mode == 'face':
            try:
                face_locations = server_results['face_locations']
                
                if not face_locations:
                    return image, top_l, bottom_r
                    
                for face_loc in face_locations:
                    try:
                        top, right, bottom, left = face_loc
                        
                        # BGR color (green)
                        cv2.rectangle(image, (left, top), (right, bottom), (0, 255, 0), 2)
                        
                        cv2.putText(image, "Face", (left, top - 10),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    except Exception as e:
                        print("Error drawing individual face: {}".format(str(e)))
                        continue
                    
            except Exception as e:
                print("Error processing face results: {}".format(str(e)))
                import traceback
                traceback.print_exc()
                      
    except Exception as e:
        print("Error in image annotation: {}".format(str(e)))
        import traceback
        traceback.print_exc()
       
    return image, top_l, bottom_r

def calculate_frame(w, h, dim):
    """Calculate the center frame coordinates."""
    mid_w, mid_h, diff = w/2, h/2, dim / 2
    return (int(mid_w - diff), int(mid_h - diff)), (int(mid_w + diff), int(mid_h + diff))

def load_class_names(filename):
    """Load class names from file."""
    try:
        with open(filename, "r") as f:
            class_names = f.read().splitlines()
        return class_names
    except Exception as e:
        print(f"Error loading class names: {e}")
        return []