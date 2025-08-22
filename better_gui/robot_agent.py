# -*- coding: future_fstrings -*-
# robot_agent.py
# File responsible for either accepting inputs or acting as the medium of inputs, all sent to robot_environment
from robot_environment import NaoEnvironment
from camera_controller import CameraController

class NaoActions:
    def __init__(self, nao_env_obj):
        self.nao = nao_env_obj
        self.camera_controller = CameraController(self)
        self.current_camera_id = 0

    def speak(self, message):
        self.nao.tts_endpoint(message)

    def change_posture(self, new_pos, speed):
        self.nao.posture_endpoint(new_pos, speed)

    def walk(self, x, y, theta):
        self.nao.motion_endpoint(x, y, theta)

    def movehead(self, head_yaw_speed=0, head_pitch_speed=0, center=False):
        if center:
            self.nao.head_endpoint(0, 0, center=True)
        else:
            self.nao.head_endpoint(head_yaw_speed, head_pitch_speed)

    def start_camera(self, callback):
        return self.camera_controller.start(callback)
        
    def stop_camera(self):
        return self.camera_controller.stop()
        
    def change_camera(self, camera_id):
        # This function is kept for backward compatibility
        # We ignore the camera_id parameter and always use the top camera (0)
        self.current_camera_id = 0
        
    def get_camera_fps(self):
        return self.camera_controller.get_current_fps()

    # Legacy method - kept for backward compatibility
    def get_camera_image(self, camera_id=0):
        return self.nao.camera_endpoint(camera_id)

