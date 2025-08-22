# -*- coding: future_fstrings -*-
# gui/main_window.py
import Tkinter as tk
from gui.video_panel import VideoPanel
from gui.control_panel import ControlPanel
from gui.status_panel import StatusPanel
from controllers import NAOChatSystem
from models import HeadTracker
import config

class NaoControlGUI:
    """Main GUI window for NAO robot control."""
    
    def __init__(self, root, robot, mode, training_bool, file_path=None):
        """Initialize the main GUI window.
        
        Args:
            root: Tkinter root window
            robot: NaoRobot instance
            mode: Detection mode ('face', 'yolo', 'tflite', 'both')
            training_bool: Boolean indicating if in training mode
            file_path: Path to model file (for inference mode)
        """
        self.root = root
        self.robot = robot
        self.mode = mode
        self.training_mode = training_bool
        self.file_path = file_path
        
        # Set up window properties
        self.root.title("NAO Robot Control")
        self.root.geometry(f"{config.GUI_WIDTH}x{config.GUI_HEIGHT}")
        
        # Initialize chat system
        self.chat_system = NAOChatSystem(is_robot=True, server_ip=config.ZMQ_SERVER_IP)
        
        # Initialize head tracker if in face mode
        self.head_tracker = None
        if mode in ['face', 'both']:
            self.head_tracker = HeadTracker(self.robot.motion_service)
            if not training_bool and file_path:
                success, samples = self.head_tracker.load_model(file_path)
                if success:
                    print(f"Model loaded successfully with {samples} training samples")
                
        # Create main frames
        self.control_frame = tk.Frame(root)
        self.control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        self.video_frame = tk.Frame(root)
        self.video_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.status_frame = tk.Frame(root)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        # Initialize components
        self.control_panel = ControlPanel(self.control_frame, robot, self.chat_system)
        self.video_panel = VideoPanel(self.video_frame, robot, mode, self.head_tracker)
        self.status_panel = StatusPanel(self.status_frame, robot, self.head_tracker, training_bool)
        
        # Set up callbacks for chat messages
        self._setup_chat_callbacks()
        
        # Bind key events to the main window
        self._setup_key_bindings()
        
        # Set up automatic updates
        self._setup_automatic_updates()
        
        # Set up training mode if needed
        if self.training_mode:
            self.video_panel.set_training_mode(True)
    
    def _setup_chat_callbacks(self):
        """Set up callbacks for the chat system."""
        def handle_response(text):
            self.robot.tts.say(text)
        
        self.chat_system.register_callback(handle_response)
    
    def _setup_key_bindings(self):
        """Set up key bindings for the application."""
        # Bind key events
        self.root.bind('<KeyPress>', self.robot.on_key_press)
        self.root.bind('<KeyRelease>', self.robot.on_key_release)
        self.root.bind('<Escape>', self.handle_escape)
        
        # Add cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self.cleanup)
    
    def _setup_automatic_updates(self):
        """Set up automatic updates for various components."""
        # Start with a slight delay to ensure everything is initialized
        self.root.after(100, self.update_video_stream)
        self.root.after(100, self.update_robot_movement)
        self.root.after(100, self.update_battery_status)
    
    def update_video_stream(self):
        """Update the video stream and schedule the next update."""
        success = self.video_panel.update_frame()
        # Schedule the next update (shorter delay for success, longer for failure)
        delay = 50 if success else 100
        self.root.after(delay, self.update_video_stream)
    
    def update_robot_movement(self):
        """Update robot movement and schedule the next update."""
        try:
            self.robot.update_robot_movement()
            self.root.after(10, self.update_robot_movement)
        except Exception as e:
            print(f"Error in robot movement: {e}")
            # Try again after error with a slight delay
            self.root.after(50, self.update_robot_movement)
    
    def update_battery_status(self):
        """Update battery status and schedule the next update."""
        self.status_panel.update_battery_status()
        # Battery updates are less frequent (every 10 seconds)
        self.root.after(10000, self.update_battery_status)
    
    def handle_escape(self, event):
        """Handle the escape key event."""
        self.root.quit()
        self.robot.shutdown()
    
    def cleanup(self):
        """Clean up resources when closing the application."""
        try:
            # Cancel all scheduled events
            for after_id in self.root.tk.call('after', 'info'):
                self.root.after_cancel(after_id)
                
            # Shutdown robot
            self.robot.shutdown()
            
            # Close chat system
            if hasattr(self, 'chat_system'):
                self.chat_system.close()
                
            # Quit the application
            self.root.quit()
        except Exception as e:
            print(f"Error during cleanup: {e}")