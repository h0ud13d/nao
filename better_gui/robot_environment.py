# -*- coding: future_fstrings -*-
# robot_environment.py 
# File responsible for taking in various inputs and sending them to the NAO bot
import qi
import time
import PIL.Image
from io import BytesIO
import numpy as np
import config



class ConnectionError(Exception):
    pass

class NaoEnvironment:
    def __init__(self, ip, port):
        self.ip = str(ip)
        self.port = str(port)
        self.session = None
        self.services = {}
        
    def init_robot(self):
        for attempt in range(3):
            try:
                self.session = qi.Session()
                url = f"tcp://{self.ip}:{self.port}"
                print(f"Attempting to connect to: {url}")

                self.session.connect(url)
                print("Successfully connected to the robot!")

                self._init_services()

                return True

            except RuntimeError as e:
                print(f"ERROR: Connection attempt #{attempt+1} failed: {e}")
                if attempt < 2:
                    print("Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    print("Max connection attempts reached. Unable to connect.")
                    self.session = None
                    return False
    
    def _init_services(self):
        ### Initialize commonly used services after connection
        self.services["tts"] = self.session.service("ALTextToSpeech")
        self.services["motion"] = self.session.service("ALMotion")
        self.services["posture"] = self.session.service("ALRobotPosture")
        self.services["video"] = self.session.service("ALVideoDevice")
    
    def get_service(self, service_name):
        ### Get a service, creating it if not already cached
        if service_name not in self.services:
            self.services[service_name] = self.session.service(service_name)
        return self.services[service_name]
    
    def tts_endpoint(self, message):
        ### Send text to speech
        if self.session is None:
            raise ConnectionError("Not connected to robot")
        
        tts = self.services.get("tts")
        #if tts is None:
        #    tts = self.get_service("ALTextToSpeech")
        
        tts.say(message)


    def motion_endpoint(self, x, y, theta):
        if self.session is None:
            raise ConnectionError("Not connected to robot")

        motion = self.services.get("motion")
        if x != 0.0 or y != 0.0 or theta != 0.0:
            motion.moveToward(x, y, theta)
        else:
            motion.stopMove()
    
    def head_endpoint(self, head_yaw_speed, head_pitch_speed, center=False):
        motion = self.services.get("motion")
        if center:
            # Center the head with a smoother motion
            motion.setAngles(["HeadYaw", "HeadPitch"], [0.0, 0.0], 0.2)
        elif head_yaw_speed != 0.0 or head_pitch_speed != 0.0:
            current_yaw, current_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
            
            # Calculate new positions with direct speed application
            # Back to the original behavior that was working
            new_yaw = current_yaw + head_yaw_speed
            new_pitch = current_pitch + head_pitch_speed
            
            # Enforce angle limits
            new_yaw = max(min(new_yaw, 2.0857), -2.0857)  # Yaw limits from NAO docs
            new_pitch = max(min(new_pitch, 0.5149), -0.6720)  # Pitch limits from NAO docs
            
            # Set angles with faster movement speed for responsiveness
            motion.setAngles(["HeadYaw", "HeadPitch"], [new_yaw, new_pitch], 0.2)

    def posture_endpoint(self, name, speed):
        ### http://doc.aldebaran.com/2-1/naoqi/motion/alrobotposture-api.html#ALRobotPostureProxy::getPostureList
        ### Change Posture of NAO
        ### Methods are the following
        #ALRobotPostureProxy::getPostureList()
        #ALRobotPostureProxy::getPosture()
        #ALRobotPostureProxy::goToPosture()
        #ALRobotPostureProxy::applyPosture()
        #ALRobotPostureProxy::stopMove()
        #ALRobotPostureProxy::getPostureFamily()
        #ALRobotPostureProxy::getPostureFamilyList()
        #ALRobotPostureProxy::setMaxTryNumber()

        if self.session is None:
            raise ConnectionError("Not connected to robot")
        
        posture = self.services.get("posture")
        print(posture)
        posture.goToPosture(name, speed)

    def camera_endpoint(self, camera_id=0):
        # Get an image from NAO's camera
        # camera_id: 0 for top camera, 1 for bottom camera
        # Returns: The image as a PIL Image object

        if self.session is None:
            raise ConnectionError("Not connected to robot")
        video = self.services["video"]

        # Subscribe to camera feed (resolution 2 = 640x480, colorspace 11 = RGB)
        resolution = config.RESOLUTION
        colorspace = config.CAMERA_COLOR_SPACE
        fps = config.CAMERA_COLOR_SPACE

        # Create a unique handle for this client
        client_name = f"python_client_{int(time.time())}"

        # Subscribe to the camera
        handle = video.subscribeCamera(client_name, camera_id, resolution, colorspace, fps)
        try:
            # Get the image
            image = video.getImageRemote(handle)
            if image is None:
                return None
            # Image format is [width, height, layers, colorspace, timestamp, binary data]
            width, height = image[0], image[1]
            array = image[6]
            
            # Convert binary data to PIL Image
            try:
                # Create image from binary data
                img_data = np.frombuffer(array, np.uint8).reshape(height, width, 3)
                img = PIL.Image.fromarray(img_data)
                
                # Convert to jpeg data for Tkinter
                b = BytesIO()
                img.save(b, 'jpeg')
                return b.getvalue()
                
            except ImportError:
                print("PIL or numpy not available, returning raw data")
                return array
                
        finally:
            # Always unsubscribe 
            video.unsubscribe(handle)





