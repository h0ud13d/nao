# -*- coding: future_fstrings -*-
# main.py - Entry point for the NAO robot application

import sys
import argparse
import Tkinter as tk
import atexit
import config
from controllers import NaoRobot, ConnectionError
from gui import NaoControlGUI

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="NAO Robot Control Application")

    # Define the '--model' argument with choices
    parser.add_argument(
        '--model', 
        type=str, 
        choices=['face', 'yolo', 'tflite', 'both'], 
        required=True, 
        help="Model type to use ('face', 'yolo', 'tflite', or 'both')"
    )

    # Define the '--training' flag argument
    parser.add_argument(
        '--training', 
        action='store_true', 
        help="Enable training mode if this flag is set"
    )

    # Define the optional '--file_path' argument
    parser.add_argument(
        '--file_path', 
        type=str, 
        help="Path to the model file (required if --training is not set)"
    )

    return parser.parse_args()

def validate_arguments(args):
    """Validate command line arguments."""
    # Check if training is False and file_path is not provided
    if not args.training and not args.file_path:
        print("Error: The '--file_path' argument is required when '--training' is not set.")
        sys.exit(1)

def main():
    """Main entry point for the application."""
    # Parse and validate command line arguments
    args = parse_arguments()
    validate_arguments(args)

    try:
        # Initialize the robot
        robot = NaoRobot(config.ROBOT_IP, config.ROBOT_PORT, args.model)
        
        # Initialize the GUI
        root = tk.Tk()
        app = NaoControlGUI(root, robot, args.model, args.training, args.file_path)
        
        # Register cleanup on exit
        def cleanup():
            robot.shutdown()
        atexit.register(cleanup)
        
        # Start the application
        root.mainloop()
        
    except ConnectionError as e:
        print("Connection error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
