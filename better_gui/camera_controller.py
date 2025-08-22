# -*- coding: future_fstrings -*-
"""
NAO Robot Control - Camera Module
Handles camera operations for NAO robot with optimized FPS
"""

import time
import threading
import collections
from PIL import Image, ImageTk
import numpy as np
import config

class CameraController:
    def __init__(self, robot_controller):
        self.robot_controller = robot_controller
        self.running = False
        self.thread = None
        self.video_client = None
        self.current_image = None
        self.update_callback = None
        self.camera_id = 0
        
        # Frame buffer for smoother playback
        self.frame_buffer = collections.deque(maxlen=10)  # Increased buffer size
        self.buffer_lock = threading.Lock()
        
        # FPS tracking
        self.fps = 0
        self.frame_count = 0
        self.last_fps_time = time.time()
        
        # Last displayed frame time to control display rate
        self.last_display_time = 0
    
    def start(self, update_callback=None):
        """Start the camera feed"""
        if not self.robot_controller.nao or not self.robot_controller.nao.services.get("video"):
            return False
            
        if self.running:
            return True  # Already running
            
        self.update_callback = update_callback
        self.running = True
        
        # Start the camera thread
        self.thread = threading.Thread(target=self._camera_capture_loop)
        self.thread.daemon = True
        self.thread.start()
        
        # Start the display thread if callback provided
        if self.update_callback:
            self.display_thread = threading.Thread(target=self._display_loop)
            self.display_thread.daemon = True
            self.display_thread.start()
        
        return True
    
    def stop(self):
        """Stop the camera feed"""
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
            
        if hasattr(self, 'display_thread') and self.display_thread:
            self.display_thread.join(timeout=1.0)
            self.display_thread = None
            
        if self.video_client and self.robot_controller.nao.services.get("video"):
            try:
                video_proxy = self.robot_controller.nao.services.get("video")
                video_proxy.unsubscribe(self.video_client)
            except:
                pass
            self.video_client = None
            
        self.current_image = None
        with self.buffer_lock:
            self.frame_buffer.clear()
            
        return True
    
    def get_current_fps(self):
        """Get the current FPS rate"""
        return self.fps
    
    def _camera_capture_loop(self):
        """Camera capture loop that runs in a separate thread"""
        try:
            video_proxy = self.robot_controller.nao.services.get("video")
            
            # Subscribe to the camera with optimized parameters - using only top camera (0)
            self.video_client = video_proxy.subscribe(
                "python_client", 
                config.CAMERA_RESOLUTION, 
                config.CAMERA_COLOR_SPACE, 
                config.CAMERA_FPS
            )
            
            # Set camera parameters for better performance
            try:
                video_proxy.setParameter(self.video_client, "Contrast", 64)
                video_proxy.setParameter(self.video_client, "Brightness", 64)
                video_proxy.setParameter(self.video_client, "Saturation", 128)
                video_proxy.setParameter(self.video_client, "Sharpness", 0)
                # Disable auto exposure to reduce flicker
                video_proxy.setParameter(self.video_client, "AutoExposition", 0)
                # Fixed exposure to reduce flicker
                video_proxy.setParameter(self.video_client, "Exposure", 80)
            except Exception as e:
                print(f"Camera parameter error: {e}")
                # Continue anyway, parameters might not be available
            
            last_image = None
            
            while self.running:
                try:
                    # Update FPS counter
                    self.frame_count += 1
                    current_time = time.time()
                    if current_time - self.last_fps_time >= 1.0:
                        self.fps = self.frame_count
                        self.frame_count = 0
                        self.last_fps_time = current_time
                    
                    # Get a camera image
                    image = video_proxy.getImageRemote(self.video_client)
                    
                    if image:
                        # Extract image data
                        width = image[0]
                        height = image[1]
                        image_data = image[6]
                        
                        # Create PIL image
                        pil_image = Image.frombytes("RGB", (width, height), str(image_data))
                        # Scale image to fit the dashboard canvas (480x360) while maintaining aspect ratio
                        pil_image = pil_image.resize((480, 360), Image.ANTIALIAS)
                        
                        # Convert to PhotoImage
                        tk_image = ImageTk.PhotoImage(pil_image)
                        last_image = tk_image
                        
                        # Add to buffer (with thread safety)
                        with self.buffer_lock:
                            self.frame_buffer.append(tk_image)
                    elif last_image:
                        # If no new image but we have a previous one, reuse it
                        # This prevents black frames during temporary camera hiccups
                        with self.buffer_lock:
                            self.frame_buffer.append(last_image)
                    
                    # Release resources
                    video_proxy.releaseImage(self.video_client)
                    
                    # Sleep to control capture rate (smaller interval = smoother capture)
                    time.sleep(0.005)  # Target up to 200 FPS for capture
                    
                except Exception as e:
                    print(f"Camera frame error: {e}")
                    time.sleep(0.1)  # Wait before retrying
            
            # Unsubscribe when finished
            if self.video_client:
                video_proxy.unsubscribe(self.video_client)
                self.video_client = None
                
        except Exception as e:
            print(f"Camera thread error: {e}")
            self.running = False
    
    def _display_loop(self):
        """Display loop that shows images from the buffer"""
        target_fps = 30  # Target 30 FPS for display
        display_interval = 1.0 / target_fps
        
        while self.running:
            current_time = time.time()
            # Only update if enough time has passed since last update
            if current_time - self.last_display_time >= display_interval:
                self.last_display_time = current_time
                
                # Get a frame from the buffer (with thread safety)
                with self.buffer_lock:
                    if self.frame_buffer:
                        frame = self.frame_buffer[-1]  # Get the newest frame
                    else:
                        frame = None
                
                # Update the display if we have a frame and callback
                if frame and self.update_callback:
                    # Keep track of the current image to prevent garbage collection
                    self.current_image = frame
                    # Call the UI callback with the image and current FPS
                    self.update_callback(frame, self.fps)
            
            # Short sleep to prevent high CPU usage
            time.sleep(0.001)
            
    # Legacy function
    def switch_camera(self, camera_id):
        """Switch between top (0) and bottom (1) camera"""
        # Stop current camera
        old_running = self.running
        if self.running:
            self.stop()
        
        # Change camera ID and restart if needed
        self.camera_id = camera_id
        
        if old_running:
            self.start(self.update_callback)
