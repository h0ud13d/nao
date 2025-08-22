# -*- coding: future_fstrings -*-
import Tkinter as tk
import numpy as np
import tkMessageBox as messagebox
import threading
from PIL import Image, ImageTk
import torch
import cv2
from datetime import datetime
import requests
import base64
from robot import NaoRobot
from utils import capture_frame, save_image, send_image_to_server
from config import CENTER_BOX
from head_movement import head_relative_to_center, HeadTracker
from nao_zmq import NAOChatSystem



def load_class_names(filename):
    with open(filename, "r") as f:
        class_names = f.read().splitlines()
    return class_names

class_names = load_class_names('./../models/coco.names')

class NaoControlGUI:
    def __init__(self, root, robot, mode, training_bool, file_path):
        self.root = root
        self.robot = robot
        self.mode = mode
        # Initialize services from the robot instance
        self.motion_service = self.robot.motion_service
        self.posture_service = self.robot.posture_service
        self.video_service = self.robot.video_service
        self.video_client = self.robot.video_client
        self.battery_service = self.robot.battery_service
        self.tts = self.robot.tts
        self.tts.setParameter("defaultVoiceSpeed", 100)
        self.last_state_covered = False

        self.head_only = False
        # activate only head
        if self.head_only:
            self.motion_service.setStiffnesses("Head", 1.0)  # Enable only head motors
            self.posture_service.goToPosture('Crouch', 0.50)  # Go to crouch
            self.motion_service.setStiffnesses("Body", 0.0)   # Disable body motors
            self.motion_service.setStiffnesses("Head", 1.0) 
        else:
            self.motion_service.wakeUp()
            self.posture_service.goToPosture('Crouch', 0.50)

        self.root.title("NAO Robot Control")
        self.root.geometry("600x600")

        instructions = tk.Label(
            root,
            text="Use WASD to move, Q/E to rotate.\nUse arrow keys to move the head.\nPress 'c' to save as covered, 'u' to save as uncovered.\nPress Esc to exit.",
            font=("Helvetica", 12),
        )

        instructions.grid(row=0, column=0, columnspan=4, pady=20, sticky="nsew")

        # Add posture buttons using grid
        sit_button = tk.Button(root, text="Sit", command=self.robot.make_robot_sit, font=("Helvetica", 12))
        sit_button.grid(row=1, column=0, padx=10, pady=10)

        stand_button = tk.Button(root, text="Stand", command=self.robot.make_robot_stand, font=("Helvetica", 12))
        stand_button.grid(row=1, column=1, padx=10, pady=10)

        superman_button = tk.Button(root, text="Superman", command=self.robot.superman, font=("Helvetica", 12))
        superman_button.grid(row=1, column=2, padx=10, pady=10)

        crouch_button = tk.Button(root, text="Crouch", command=self.robot.make_robot_crouch, font=("Helvetica", 12))
        crouch_button.grid(row=1, column=3, padx=10, pady=10)

        # Text input for TTS with focus handling
        self.text_entry = tk.Entry(root, width=50, font=("Helvetica", 12))
        self.text_entry.grid(row=2, column=0, columnspan=3, padx=10, pady=10)
        self.robot.assign_value(self.text_entry)

        speak_button = tk.Button(root, text="Speak", command=self.speak_text, font=("Helvetica", 12))
        speak_button.grid(row=2, column=3, padx=10, pady=10)

        self.initialize_chat_system()
        self.head_tracker = HeadTracker(self.motion_service)
        self.training_mode = training_bool
        self.file_path = file_path
        self.training_samples = 0
        
        # Add training label - Python 2.7 Tkinter
        self.training_label = tk.Label(root, text="Training Samples: 0")
        self.training_label.grid(row=6, column=0, columnspan=4, padx=10, pady=10)

        # Video feed label
        self.video_label = tk.Label(root)
        self.video_label.grid(row=3, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

        save_model_button = tk.Button(root, text="Save Model", command=self.save_model, font=("Helvetica", 12))
        save_model_button.grid(row=7, column=0, columnspan=4, padx=10, pady=10)

        #load_model_button = tk.Button(root, text="Load Model", command=lambda: self.load_model(self.file_path), font=("Helvetica", 12))
        #load_model_button.grid(row=8, column=0, columnspan=4, padx=10, pady=10)

        # Dimensions for center frame box, the single number (e.g. 100) implies 100x100
        self.center_frame_dimensions = CENTER_BOX
        self.top_l = 0
        self.bottom_r = 0

        # Create a canvas to display the battery status
        self.battery_label = tk.Label(root, text="Battery Level: 0%", font=("Helvetica", 12))
        self.battery_label.grid(row=4, column=0, columnspan=4, padx=10, pady=10)

        self.canvas = tk.Canvas(root, width=200, height=50, bg="white")
        self.canvas.grid(row=5, column=0, columnspan=4, padx=10, pady=10)
        self.battery_bar = self.canvas.create_rectangle(10, 10, 10, 40, fill="green")

        # Add click handler to root window to unfocus text entry
        root.bind('<Button-1>', self.unfocus_text_entry)
        # Add handler for text entry to stop propagation when clicked
        self.text_entry.bind('<Button-1>', lambda e: e.widget.focus_set() or 'break')
        # Add handler for video label to unfocus text entry
        self.video_label.bind('<Button-1>', self.unfocus_text_entry)

        # Bind key events
        self.root.bind('<KeyPress>', self.robot.on_key_press)
        self.root.bind('<KeyRelease>', self.robot.on_key_release)
        self.root.bind('<Escape>', self.handle_escape_event)

        # Add cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self.cleanup)

#        self.tts.say("Hello RAIR LAB! I've gained consciousness.")

        self.update_battery_status()  # Start battery updates
        self.root.after(50, self.update_video_stream)  # Start video stream with slight delay
        self.root.after(50, self.initialize_robot_movement)  # Start robot movement updates


    def update_video_stream(self):
        try:
            image = capture_frame(self.video_service, self.video_client)
            if image is None:
                self.root.after(100, self.update_video_stream)
                return

            display_image = image.copy()
            prediction = send_image_to_server(image, self.mode)
            
            if prediction and self.mode == "face":
                try:
                    display_image = self.annotate_image(display_image, prediction, self.mode)
                    position = head_relative_to_center(prediction, self.top_l, self.bottom_r)
                    
                    if prediction['face_locations']:
                        face_coords = prediction['face_locations'][0]
                        
                        if self.training_mode:
                            # Add to training data and train
                            movement = self.head_tracker.get_movement_from_position(position)
                            if movement is not None:
                                self.head_tracker.apply_movement(movement)
                            self.head_tracker.add_training_sample(face_coords, position)
                            loss = self.head_tracker.train_step()
                            
                            self.training_samples += 1
                            status = "Training Samples: %d" % self.training_samples
                            if loss is not None:
                                status += " | Loss: %.4f" % loss
                            self.training_label.config(text=status)
                        else:
                            # Use trained model for prediction
                            #self.load_model(self.file_path)

                            self.head_tracker.position_history.append(face_coords)
                            if len(self.head_tracker.position_history) >= self.head_tracker.sequence_length:
                                movement = self.head_tracker.predict_movement(list(self.head_tracker.position_history))
                                self.head_tracker.apply_movement(movement)
                            """
                            #single frame tracking
                            self.head_tracker.position_history.append(face_coords)
                            if len(self.head_tracker.position_history) >= self.head_tracker.sequence_length:
                                movement = self.head_tracker.predict_movement(list(self.head_tracker.position_history))
                                self.head_tracker.apply_movement(movement)
                            """

                            # multiple frame tracking
                            #self.head_tracker.position_history.append(face_coords)
                            #if len(self.head_tracker.position_history) >= self.head_tracker.sequence_length:
                            #    movement = self.head_tracker.predict_movement()  # Call without arguments
                            #    self.head_tracker.apply_movement(movement)
                                
                except Exception as e:
                    print("Error in training: %s" % str(e))
                        
                # Convert and display image
                try:
                    img = Image.fromarray(display_image)
                    imgtk = ImageTk.PhotoImage(image=img)
                    self.video_label.imgtk = imgtk
                    self.video_label.configure(image=imgtk)
                except Exception as e:
                    print("Error updating display: {}".format(e))
                    
                self.root.after(50, self.update_video_stream)
                
        except Exception as e:
            print("Error in video stream update: %s" % str(e))
            self.root.after(100, self.update_video_stream)



    def save_model(self):
        try:
            current_time = datetime.now().strftime("%H%M%S")  # Format: YYYYMMDD_HHMMSS
            save_path = "movement_models/samplesize_%d_%s.pth" % (self.training_samples, current_time)
            save_data = {
                'model_state_dict': self.head_tracker.model.state_dict(),
                'optimizer_state_dict': self.head_tracker.optimizer.state_dict(),
                'training_samples': self.training_samples,
                'training_data': self.head_tracker.training_data,
                'position_to_movement': self.head_tracker.position_to_movement
            }
            torch.save(save_data, save_path)
            msg = "Model saved with %d samples" % self.training_samples
            self.tts.say(msg)
            print(msg)
        except Exception as e:
            error_msg = "Error saving model: %s" % str(e)
            print(error_msg)
            self.tts.say("Error saving model")    

    def load_model(self, model_path):
        try:
            checkpoint = torch.load(model_path)
            self.head_tracker.model.load_state_dict(checkpoint['model_state_dict'])
            self.head_tracker.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.training_samples = checkpoint['training_samples']
            self.head_tracker.training_data = checkpoint['training_data']
            self.head_tracker.position_to_movement = checkpoint['position_to_movement']
            self.training_mode = False  # Ensure inference mode is set
            #print("Model loaded successfully, ready for inference.")
        except Exception as e:
            print("Error loading model: %s" % str(e))


    def annotate_image(self, image, server_results, mode):
        """Annotate image based on detection results."""
        try:
            height, width = image.shape[:2]
            self.top_l, self.bottom_r = self.calculate_frame(width, height, self.center_frame_dimensions) 
            cv2.rectangle(image, self.top_l, self.bottom_r, (255, 0, 0), 2)

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
                        return image
                        
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
           
        return image

    def update_battery_status(self):
        battery_charge = self.battery_service.getBatteryCharge()
        self.battery_label.config(text="Battery Level: {}%".format(battery_charge))
        battery_width = 10 + (battery_charge * 1.8)
        self.canvas.coords(self.battery_bar, 10, 10, battery_width, 40)
        self.root.after(10000, self.update_battery_status)

    def initialize_robot_movement(self):
        """Update robot movement and schedule next update."""
        try:
            self.robot.update_robot_movement()
            self.root.after(10, self.initialize_robot_movement)
        except Exception as e:
            print("Error in robot movement: {}".format(e))
            # Try again after error
            self.root.after(10, self.initialize_robot_movement)
            
    def initialize_chat_system(self):
        # Replace with your computer's IP address
        self.chat_system = NAOChatSystem(is_robot=True, server_ip="172.18.0.1")
        
        def handle_response(text):
            self.tts.say(text)
        
        self.chat_system.register_callback(handle_response)

    def handle_escape_event(self, event):
            self.root.quit()
            self.robot.shutdown()


    def speak_text(self):
        """Replace your existing speak_text method with this"""
        text = self.text_entry.get()
        if text.strip() == "":
            messagebox.showwarning("Input Error", "Please enter text to send.")
            return
        
        # Send message to server instead of speaking directly
        self.chat_system.send_message(text)
        self.text_entry.delete(0, 'end')  # Clear the text entry


    def cleanup(self):
        """Modify your cleanup method to include"""
        try:
            if hasattr(self, 'video_client'):
                self.video_service.unsubscribe(self.video_client)
            if hasattr(self, 'chat_system'):
                self.chat_system.close()
            if hasattr(self, 'root'):
                for after_id in self.root.tk.call('after', 'info'):
                    self.root.after_cancel(after_id)
            self.robot.shutdown()
            self.root.quit()
        except Exception as e:
            print("Error during cleanup: {}".format(e))

    def unfocus_text_entry(self, event=None):
        # Only unfocus if we didn't click the text entry itself
        if event and event.widget != self.text_entry:
            # Move focus to the main window
            self.root.focus_set()
            return 'break'  # Prevent event propagation


    # draws red rectangle in center of frame of 125x125, frame is 640x480
    def calculate_frame(self, w, h, dim):
        mid_w, mid_h, diff= w/2, h/2, dim / 2
        return (mid_w - diff, mid_h - diff), (mid_w + diff, mid_h + diff)

        

        #print("width {} height {}".format(width, height))

