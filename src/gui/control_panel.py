# gui/control_panel.py
import Tkinter as tk
import tkMessageBox as messagebox
from datetime import datetime
import torch
from config import MODEL_SAVE_DIR

class ControlPanel:
    """Panel for robot control buttons and text input."""
    
    def __init__(self, parent, robot, chat_system=None):
        """Initialize the control panel.
        
        Args:
            parent: Parent frame/window
            robot: NaoRobot instance
            chat_system: NAOChatSystem instance (optional)
        """
        self.parent = parent
        self.robot = robot
        self.chat_system = chat_system
        
        # Instructions
        instructions = tk.Label(
            parent,
            text="Use WASD to move, Q/E to rotate.\nUse arrow keys to move the head.\nPress 'c' to save as covered, 'u' to save as uncovered.\nPress Esc to exit.",
            font=("Helvetica", 12),
        )
        instructions.grid(row=0, column=0, columnspan=4, pady=20, sticky="nsew")
        
        # Posture buttons
        self._create_posture_buttons()
        
        # Text input for TTS
        self._create_tts_input()
    
    def _create_posture_buttons(self):
        """Create buttons for robot postures."""
        sit_button = tk.Button(
            self.parent, text="Sit", 
            command=self.robot.make_robot_sit, 
            font=("Helvetica", 12)
        )
        sit_button.grid(row=1, column=0, padx=10, pady=10)
        
        stand_button = tk.Button(
            self.parent, text="Stand", 
            command=self.robot.make_robot_stand, 
            font=("Helvetica", 12)
        )
        stand_button.grid(row=1, column=1, padx=10, pady=10)
        
        superman_button = tk.Button(
            self.parent, text="Superman", 
            command=self.robot.superman, 
            font=("Helvetica", 12)
        )
        superman_button.grid(row=1, column=2, padx=10, pady=10)
        
        crouch_button = tk.Button(
            self.parent, text="Crouch", 
            command=self.robot.make_robot_crouch, 
            font=("Helvetica", 12)
        )
        crouch_button.grid(row=1, column=3, padx=10, pady=10)
    
    def _create_tts_input(self):
        """Create text input for text-to-speech."""
        self.text_entry = tk.Entry(self.parent, width=50, font=("Helvetica", 12))
        self.text_entry.grid(row=2, column=0, columnspan=3, padx=10, pady=10)
        self.robot.assign_value(self.text_entry)
        
        speak_button = tk.Button(
            self.parent, text="Speak", 
            command=self.speak_text, 
            font=("Helvetica", 12)
        )
        speak_button.grid(row=2, column=3, padx=10, pady=10)
        
        # Add click handler to parent window to unfocus text entry
        self.parent.bind('<Button-1>', self._unfocus_text_entry)
        # Add handler for text entry to stop propagation when clicked
        self.text_entry.bind('<Button-1>', lambda e: e.widget.focus_set() or 'break')
    
    def speak_text(self):
        """Speak the text entered in the text entry."""
        text = self.text_entry.get()
        if text.strip() == "":
            messagebox.showwarning("Input Error", "Please enter text to send.")
            return
        
        # Send message to server instead of speaking directly
        if self.chat_system:
            self.chat_system.send_message(text)
        else:
            self.robot.tts.say(text)
            
        self.text_entry.delete(0, 'end')  # Clear the text entry
    
    def _unfocus_text_entry(self, event=None):
        """Unfocus the text entry when clicking elsewhere."""
        # Only unfocus if we didn't click the text entry itself
        if event and event.widget != self.text_entry:
            # Move focus to the main window
            self.parent.focus_set()
            return 'break'  # Prevent event propagation