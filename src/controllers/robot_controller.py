# -*- coding: future_fstrings -*-
# controllers/robot_controller.py
import qi
import time
import os
import random
from utils import save_image, capture_frame, send_image_to_server
from config import COVERED_DIR, UNCOVERED_DIR

class ConnectionError(Exception):
    """Exception raised when the robot connection fails."""
    pass

class NaoRobot:
    """Controller for the NAO robot."""
    
    def __init__(self, ip, port, mode):
        """Initialize the NAO robot connection and services."""
        # Generate a unique client ID
        self.name = ''.join([chr(random.randint(65, 90)) for _ in range(3)])
        self.mode = mode
        print(f"NAO Client ID: {self.name}")
        
        # Connect to the robot
        self.session = self.connect_to_robot(ip, port)
        self.video_client = None
        self.retry_attempts = 10
        
        if not self.session:
            raise ConnectionError("Failed to connect to the robot.")
            
        print("Connected to NAO")
        
        # Initialize video service
        self._setup_video()
        
        # Initialize other services
        self._setup_services()
        
        # Keyboard tracking
        self.pressed_keys = set()
        self.text_entry = None
        
    def _setup_video(self):
        """Set up the video service and client."""
        from config import VIDEO_RESOLUTION, VIDEO_COLOR_SPACE, VIDEO_FPS
        
        self.resolution = VIDEO_RESOLUTION
        self.color_space = VIDEO_COLOR_SPACE
        self.fps = VIDEO_FPS
        
        try:
            self.video_service = self.session.service("ALVideoDevice")
            self.video_service.setActiveCamera(0)
            self.video_client = self.video_service.subscribe(
                self.name, self.resolution, self.color_space, self.fps
            )
            print(f"Video service initialized with client: {self.video_client}")
        except Exception as e:
            print(f"Error setting up video: {e}")
            
    def _setup_services(self):
        """Set up NAO robot services."""
        try:
            self.motion_service = self.session.service("ALMotion")
            self.posture_service = self.session.service("ALRobotPosture")
            self.battery_service = self.session.service("ALBattery")
            self.tts = self.session.service("ALTextToSpeech")
            self.tts.setParameter("defaultVoiceSpeed", 100)
        except Exception as e:
            print(f"Error setting up services: {e}")
    
    def assign_value(self, text_entry):
        """Assign text entry widget for keyboard focus checks."""
        self.text_entry = text_entry
    
    def connect_to_robot(self, ip, port, max_attempts=3):
        """Connect to the NAO robot with retry logic."""
        for attempt in range(max_attempts):
            try:
                session = qi.Session()
                session.connect(f"tcp://{ip}:{port}")
                return session
            except RuntimeError as e:
                print(f"Connection attempt {attempt+1} failed: {e}")
                time.sleep(5)
        raise ConnectionError("Could not connect to the robot. Please check the robot's IP and power status.")
    
    def wake_up(self):
        """Wake up the robot from rest mode."""
        self.motion_service.wakeUp()
    
    def rest(self):
        """Put the robot in rest mode."""
        self.motion_service.rest()
    
    def make_robot_sit(self):
        """Make the robot sit."""
        self.posture_service.goToPosture("Sit", 0.7)
    
    def make_robot_stand(self):
        """Make the robot stand."""
        self.posture_service.goToPosture("Stand", 0.7)
    
    def superman(self):
        """Put robot in zero position."""
        self.posture_service.goToPosture("StandZero", 0.7)
    
    def make_robot_crouch(self):
        """Make the robot crouch."""
        self.posture_service.goToPosture("Crouch", 0.7)
    
    def on_key_press(self, event):
        """Handle key press events."""
        # Check if the focus is on the text entry box
        if self.text_entry and self.text_entry.focus_get() == self.text_entry:
            return  # Ignore key presses if typing in the text entry box
        
        # Add the key to our pressed keys set
        key = event.keysym.lower()
        self.pressed_keys.add(key)
        
        # Process image capture keys
        if key == 'p':
            # Capture an image and send it for prediction
            self._process_prediction_key()
        elif key == 'c':
            # Save image as covered
            self._save_as_covered()
        elif key == 'u':
            # Save image as uncovered
            self._save_as_uncovered()
    
    def on_key_release(self, event):
        """Handle key release events."""
        if self.text_entry and self.text_entry.focus_get() != self.text_entry:
            self.pressed_keys.discard(event.keysym.lower())
    
    def _process_prediction_key(self):
        """Process 'p' key for prediction."""
        image = capture_frame(self.video_service, self.video_client)
        if image is not None:
            prediction = send_image_to_server(image, self.mode)
            if prediction and prediction[0] < 0.5:
                self.tts.say("Peekaboo!")
            print(prediction)
    
    def _save_as_covered(self):
        """Save current frame as a covered image."""
        image = capture_frame(self.video_service, self.video_client)
        if image is not None:
            save_image(image, COVERED_DIR, 'covered')
            self.tts.say("Covered image saved.")
    
    def _save_as_uncovered(self):
        """Save current frame as an uncovered image."""
        image = capture_frame(self.video_service, self.video_client)
        if image is not None:
            save_image(image, UNCOVERED_DIR, 'uncovered')
            self.tts.say("Uncovered image saved.")
    
    def update_robot_movement(self):
        """Update robot movement based on pressed keys."""
        x = 0.0       # Forward/backward speed
        y = 0.0       # Left/right speed
        theta = 0.0   # Rotation speed
        head_yaw = 0.0
        head_pitch = 0.0
        
        # Map keys to movements
        if 'w' in self.pressed_keys:
            x += 0.5  # Move forward
        if 's' in self.pressed_keys:
            x -= 0.5  # Move backward
        if 'a' in self.pressed_keys:
            y += 0.5  # Move left
        if 'd' in self.pressed_keys:
            y -= 0.5  # Move right
        if 'q' in self.pressed_keys:
            theta += 0.5  # Rotate left
        if 'e' in self.pressed_keys:
            theta -= 0.5  # Rotate right
        
        # Handle head movement
        if 'up' in self.pressed_keys:
            head_pitch = 0.07  # Look up
        if 'down' in self.pressed_keys:
            head_pitch = -0.06  # Look down
        if 'left' in self.pressed_keys:
            head_yaw += 0.05  # Turn head left
        if 'right' in self.pressed_keys:
            head_yaw -= 0.05  # Turn head right
        
        # Apply body movement
        if x != 0.0 or y != 0.0 or theta != 0.0:
            self.motion_service.moveToward(x, y, theta)
        else:
            self.motion_service.stopMove()
        
        # Apply head movement
        if head_yaw != 0.0 or head_pitch != 0.0:
            self._apply_head_movement(head_yaw, head_pitch)
    
    def _apply_head_movement(self, yaw_change, pitch_change):
        """Apply changes to head position with safety limits."""
        try:
            current_yaw, current_pitch = self.motion_service.getAngles(["HeadYaw", "HeadPitch"], True)
            new_yaw = current_yaw + yaw_change
            new_pitch = current_pitch + pitch_change
            
            # Apply safety limits
            new_yaw = max(min(new_yaw, 2.0857), -2.0857)
            new_pitch = max(min(new_pitch, 0.5149), -0.6720)
            
            self.motion_service.setAngles(
                ["HeadYaw", "HeadPitch"],
                [new_yaw, new_pitch],
                0.1  # Movement speed
            )
        except Exception as e:
            print(f"Error applying head movement: {e}")
    
    def shutdown(self):
        """Shut down the robot and clean up resources."""
        try:
            print("Shutting down robot...")
            self.motion_service.stopMove()
            self.motion_service.rest()
            if self.video_client:
                self.video_service.unsubscribe(self.video_client)
                self.video_client = None
            print("Robot shutdown complete")
        except Exception as e:
            print(f"Error during shutdown: {e}")