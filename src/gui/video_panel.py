# -*- coding: future_fstrings -*-
# gui/video_panel.py
import Tkinter as tk
from PIL import Image, ImageTk
import time
from utils import capture_frame, send_image_to_server, annotate_image, load_class_names
from config import COCO_NAMES, CENTER_BOX
from models import head_relative_to_center

class VideoPanel:
    """Panel for displaying the video feed with annotations."""
    
    def __init__(self, parent, robot, mode, head_tracker=None):
        """Initialize the video panel.
        
        Args:
            parent: Parent frame/window
            robot: NaoRobot instance
            mode: Detection mode ('face', 'yolo', 'tflite')
            head_tracker: HeadTracker instance (optional)
        """
        self.parent = parent
        self.robot = robot
        self.mode = mode
        self.head_tracker = head_tracker
        self.training_mode = False
        self.top_l = None
        self.bottom_r = None
        self.last_state_covered = False
        
        # Video feed label
        self.video_label = tk.Label(parent)
        self.video_label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Load class names if in YOLO mode
        self.class_names = load_class_names(COCO_NAMES) if mode in ['yolo', 'both'] else []
        
        # Center frame dimensions
        self.center_frame_dimensions = CENTER_BOX
    
    def set_training_mode(self, training_mode):
        """Set training mode on or off."""
        self.training_mode = training_mode
    
    def update_frame(self):
        """Update the video frame with detection results."""
        try:
            # Capture frame from robot
            image = capture_frame(self.robot.video_service, self.robot.video_client)
            if image is None:
                return False
            
            # Send image for detection
            prediction = send_image_to_server(image, self.mode)
            
            # Check if prediction is valid
            if not prediction:
                return False
                
            display_image = image.copy()
            
            # Annotate image based on detection results
            display_image, self.top_l, self.bottom_r = annotate_image(
                display_image, prediction, self.mode, self.class_names, 
                self.center_frame_dimensions
            )
            
            # Process face tracking if in face mode
            if self.mode == 'face' and self.head_tracker and prediction.get('face_locations'):
                self._process_face_tracking(prediction)
            
            # Convert and display image
            try:
                img = Image.fromarray(display_image)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
                return True
            except Exception as e:
                print(f"Error updating display: {e}")
                return False
                
        except Exception as e:
            print(f"Error in video frame update: {e}")
            return False
    
    def _process_face_tracking(self, prediction):
        """Process face tracking for detected faces."""
        if not prediction.get('face_locations'):
            return
            
        position = head_relative_to_center(prediction, self.top_l, self.bottom_r)
        
        # If face is detected
        if prediction['face_locations']:
            face_coords = prediction['face_locations'][0]
            
            if self.training_mode and self.head_tracker:
                # Training mode - add sample and get movement
                movement = self.head_tracker.get_movement_from_position(position)
                if movement is not None:
                    self.head_tracker.apply_movement(movement)
                self.head_tracker.add_training_sample(face_coords, position)
                
            elif self.head_tracker:
                # Inference mode - use model for prediction
                self.head_tracker.position_history.append(face_coords)
                if len(self.head_tracker.position_history) >= self.head_tracker.sequence_length:
                    movement = self.head_tracker.predict_movement(list(self.head_tracker.position_history))
                    self.head_tracker.apply_movement(movement)