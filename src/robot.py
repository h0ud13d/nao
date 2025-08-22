# -*- coding: future_fstrings -*-
# robot.py

import qi
import cv2
import numpy as np
import os
import time
import config
from utils import send_image_to_server, capture_frame, save_image
import random

class ConnectionError(Exception):
    pass

class NaoRobot:
    def __init__(self, ip, port, mode): 
        self.session = self.connect_to_robot(ip, port)
        self.video_client = None
        self.retry_attempts = 10
        self.mode = mode
        self.name = ""

        for i in range(3):
            self.name += chr(random.randint(65, 90))
        print("Name is ",self.name)
        print("CONNECTED")

        if self.session:
            # config for camera
            self.resolution = config.VIDEO_RESOLUTION
            self.color_space = config.VIDEO_COLOR_SPACE
            self.fps = config.VIDEO_FPS
            self.video_service = self.session.service("ALVideoDevice")
            self.video_service.setActiveCamera(0)
            print('got video_service', self.video_service)
            self.video_client = self.video_service.subscribe(self.name, self.resolution, self.color_space, self.fps)
            # Variable to track if the last state was covered
            self.last_state_covered = False              

            # connection to robot internals
            self.motion_service = self.session.service("ALMotion")
            self.posture_service = self.session.service("ALRobotPosture")
            self.battery_service = self.session.service("ALBattery")
            self.tts = self.session.service("ALTextToSpeech")

            #self.text_entry = text_entry  #


            # DS to keep track of keys being pressed
            self.pressed_keys = set()


            #self.tts.say("I AM FRANKENSTEIN")
        else:
            raise ConnectionError("Failed to connect to the robot.")

    def subscribe_to_video(self):
        # Unsubscribe any previous client if already subscribed
        #if self.video_client:
        #    self.video_service.unsubscribe(self.video_client)
        #    print("Unsubscribed from previous video client: {}".format(self.video_client))

        # Subscribe to a new video client with retry logic
        for attempt in range(self.retry_attempts):
            self.video_client = self.video_service.subscribe("python_client", self.resolution, self.color_space, self.fps)
            if self.video_client:
                print('got video client: {}'.format(self.video_client))
                break  # Successful subscription
            else:
                print("Failed to subscribe video client on attempt {}/{}".format(attempt + 1, self.retry_attempts))
                time.sleep(2)  # Wait before retrying
        print("Failed to subscribe video client after {} attempts".format(self.retry_attempts))

    def unsubscribe_video(self):
        # Unsubscribe the current video client if subscribed
        if self.video_client:
            self.video_service.unsubscribe(self.video_client)
            print("Unsubscribed video client: {}".format(self.video_client))
            self.video_client = None


    def assign_value(self, t_e):
        self.text_entry = t_e


    def connect_to_robot(self, ip, port, max_attempts=3):
        for attempt in range(max_attempts):
            try:
                session = qi.Session()
                session.connect("tcp://{0}:{1}".format(ip, port))
                self.session = session
                return session
            except RuntimeError as e:
                print("Connection attempt {0} failed: {1}".format(attempt+1, e))
                time.sleep(5)
        raise ConnectionError("COULDNT CONNECT LOSER! TRY AGAIN")

    def wake_up(self):
        self.motion_service.wakeUp()

    def rest(self):
        self.motion_service.rest()

    def make_robot_sit(self):
        self.posture_service.goToPosture("Sit", 0.7)

    def make_robot_stand(self):
        self.posture_service.goToPosture("Stand", 0.7)

    def superman(self):
        self.posture_service.goToPosture("StandZero", 0.7)

    def make_robot_crouch(self):
        self.posture_service.goToPosture("Crouch", 0.7)


    # Logic for taking photogrpahs and testing it
    def on_key_press(self, event):
        # Check if the focus is on the text entry box
        if self.text_entry.focus_get() == self.text_entry:
            return  # Ignore key presses if typing in the text entry box

        self.pressed_keys.add(event.keysym.lower())
        self.update_robot_movement()

        uncovered_dir = "./../uncovered"
        covered_dir = "./../covered"

        if event.keysym.lower() == 'p':
            # Capture an image and send it for prediction when 'p' is pressed
            image = capture_frame(self.video_service, self.video_client)
            if image is not None:
                prediction = send_image_to_server(image, self.mode)
                if prediction[0] < 0.5:
                    self.tts.say("Peekaboo!")
                print(prediction)

        # Capture images as 'covered' or 'uncovered'
        if event.keysym.lower() == 'c':
            image = capture_frame(self.video_service, self.video_client)
            if image is not None:
                save_image(image, covered_dir, 'covered')
                self.tts.say("Covered image saved.")

        elif event.keysym.lower() == 'u':
            image = capture_frame(self.video_service, self.video_client)
            if image is not None:
                save_image(image, uncovered_dir, 'uncovered')
                self.tts.say("Uncovered image saved.")

    def on_key_release(self, event):
        if self.text_entry.focus_get() != self.text_entry:
            self.pressed_keys.discard(event.keysym.lower())

    def update_robot_movement(self):
        x = 0.0  # Forward/backward speed
        y = 0.0  # Left/right speed
        theta = 0.0  # Rotation speed
        head_yaw_speed = 0.0
        head_pitch_speed = 0.0
        vertical_speed = 0.05  # Speed for vertical movement

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
            head_pitch_speed = 0.07  # Look up (reduced from 0.1)
        if 'down' in self.pressed_keys:
            head_pitch_speed = -0.06  # Look down (reduced from -0.1)
        if 'left' in self.pressed_keys:
            head_yaw_speed += 0.05  # Turn head left (reduced from 0.2)
        if 'right' in self.pressed_keys:
            head_yaw_speed -= 0.05  # Turn head right (reduced from 0.2)

        # Apply body movement
        if x != 0.0 or y != 0.0 or theta != 0.0:
            self.motion_service.moveToward(x, y, theta)
        else:
            self.motion_service.stopMove()

        # Apply head movement
        if head_yaw_speed != 0.0 or head_pitch_speed != 0.0:
            current_yaw, current_pitch = self.motion_service.getAngles(["HeadYaw", "HeadPitch"], True)
            new_yaw = current_yaw + head_yaw_speed
            new_pitch = current_pitch + head_pitch_speed
            new_yaw = max(min(new_yaw, 2.0857), -2.0857)
            new_pitch = max(min(new_pitch, 0.5149), -0.6720)
            self.motion_service.setAngles(["HeadYaw", "HeadPitch"], [new_yaw, new_pitch], 0.1)

    def shutdown(self):
        self.motion_service.stopMove()
        self.motion_service.rest()
        self.video_service.unsubscribe(self.video_client)

