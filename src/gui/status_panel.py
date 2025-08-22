# -*- coding: future_fstrings -*-
# gui/status_panel.py
import Tkinter as tk
import time
from datetime import datetime
import torch
from config import MODEL_SAVE_DIR

class StatusPanel:
    """Panel showing robot status like battery level and training status."""
    
    def __init__(self, parent, robot, head_tracker=None, training_mode=False):
        """Initialize the status panel.
        
        Args:
            parent: Parent frame/window
            robot: NaoRobot instance
            head_tracker: HeadTracker instance for training
            training_mode: Boolean indicating if in training mode
        """
        self.parent = parent
        self.robot = robot
        self.head_tracker = head_tracker
        self.training_mode = training_mode
        self.training_samples = 0
        
        # Battery status
        self._create_battery_display()
        
        # Training status (if in training mode)
        if training_mode and head_tracker:
            self._create_training_display()
    
    def _create_battery_display(self):
        """Create battery level display."""
        self.battery_label = tk.Label(
            self.parent, 
            text="Battery Level: 0%", 
            font=("Helvetica", 12)
        )
        self.battery_label.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        
        self.canvas = tk.Canvas(self.parent, width=200, height=50, bg="white")
        self.canvas.grid(row=1, column=0, columnspan=2, padx=10, pady=10)
        self.battery_bar = self.canvas.create_rectangle(10, 10, 10, 40, fill="green")
    
    def _create_training_display(self):
        """Create training status display."""
        self.training_label = tk.Label(
            self.parent, 
            text="Training Samples: 0", 
            font=("Helvetica", 12)
        )
        self.training_label.grid(row=2, column=0, columnspan=2, padx=10, pady=10)
        
        save_model_button = tk.Button(
            self.parent, 
            text="Save Model", 
            command=self.save_model, 
            font=("Helvetica", 12)
        )
        save_model_button.grid(row=3, column=0, columnspan=2, padx=10, pady=10)
    
    def update_battery_status(self):
        """Update the battery status display."""
        try:
            battery_charge = self.robot.battery_service.getBatteryCharge()
            self.battery_label.config(text=f"Battery Level: {battery_charge}%")
            battery_width = 10 + (battery_charge * 1.8)
            self.canvas.coords(self.battery_bar, 10, 10, battery_width, 40)
            return True
        except Exception as e:
            print(f"Error updating battery status: {e}")
            return False
    
    def update_training_status(self, loss=None):
        """Update the training status display."""
        if not self.training_mode or not hasattr(self, 'training_label'):
            return
            
        self.training_samples += 1
        status = f"Training Samples: {self.training_samples}"
        if loss is not None:
            status += f" | Loss: {loss:.4f}"
        self.training_label.config(text=status)
    
    def save_model(self):
        """Save the current model."""
        if not self.head_tracker:
            return
            
        try:
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = f"{MODEL_SAVE_DIR}/model_samplesize_{self.training_samples}_{current_time}.pth"
            
            success = self.head_tracker.save_model(save_path)
            
            if success:
                msg = f"Model saved with {self.training_samples} samples"
                self.robot.tts.say(msg)
                print(msg)
            else:
                self.robot.tts.say("Error saving model")
        except Exception as e:
            error_msg = f"Error saving model: {e}"
            print(error_msg)
            self.robot.tts.say("Error saving model")