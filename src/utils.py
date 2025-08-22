# -*- coding: future_fstrings -*-
import cv2
import numpy as np
import base64
import requests
import os
import time

def capture_frame(video_service, video_client):
    """Capture a frame from NAO's video service with error handling."""
    try:
        image = video_service.getImageRemote(video_client)
        if image is None or len(image) < 7:  # Check for valid image data
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
        
        url = "http://127.0.0.1:5000/predict/%s" % mode
        
        response = requests.post(
            url,  
            json={"image": image_base64}
        )
#        if mode == 'face':
#            print(response.json())
        
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

def save_image(image, directory, prefix="image"):
    if not os.path.exists(directory):
        os.makedirs(directory)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(directory, "{0}_{1}.jpg".format(prefix, timestamp))
    cv2.imwrite(filename, image)
    num_files = len([f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))])
    print("Saved: {0}, Total: {1}".format(filename, num_files))
    return filename, num_files
