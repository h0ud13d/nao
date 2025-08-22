# -*- coding: future_fstrings -*-
# models/head_tracking.py
import torch
import torch.nn as nn
from collections import deque
import numpy as np
from config import SEQUENCE_LENGTH

class HeadTrackingLSTM(nn.Module):
    """LSTM model for head tracking and movement prediction."""
    def __init__(self, input_size=4, hidden_size=64, output_size=2):
        super(HeadTrackingLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)
        
    def forward(self, x, hidden=None):
        batch_size = x.size(0)
        if hidden is None:
            h0 = torch.zeros(1, batch_size, self.hidden_size)
            c0 = torch.zeros(1, batch_size, self.hidden_size)
            hidden = (h0, c0)
        lstm_out, hidden = self.lstm(x, hidden)
        output = self.fc(lstm_out[:, -1, :])
        return output, hidden

class HeadTracker(object):
    """Handles head tracking, training, and movement prediction."""
    def __init__(self, motion_service):
        self.motion_service = motion_service
        self.model = HeadTrackingLSTM()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        self.criterion = nn.MSELoss()
        
        # Store sequences of face positions
        self.position_history = deque(maxlen=SEQUENCE_LENGTH)
        self.sequence_length = SEQUENCE_LENGTH
        self.training_data = []
        
        # Define standard movements based on face position
        self.position_to_movement = {
            "Right": [-0.05, 0.0],    
            "Left": [0.05, 0.0],      
            "Middle top": [0.0, -0.06],    
            "Middle bottom": [0.0, 0.07], 
            "Top right": [-0.05, -0.06],
            "Top left": [0.05, -0.06],
            "Bottom right": [-0.05, 0.07],
            "Bottom left": [0.05, 0.07],
            "In the middle": [0.0, 0.0],
            "Not detected": [0.0, 0.0]
        }

    def get_movement_from_position(self, position):
        """Convert a position label to movement vector."""
        if position in ["In the middle", "Not detected"]:
            return None
        return self.position_to_movement.get(position, [0.0, 0.0])
    
    def normalize_face_position(self, face_coords, frame_dims=(320, 240)):
        """Convert face coordinates to normalized features."""
        top, right, bottom, left = face_coords
        center_x = (left + right) / 2.0 / frame_dims[0]
        center_y = (top + bottom) / 2.0 / frame_dims[1]
        width = (right - left) / frame_dims[0]
        height = (bottom - top) / frame_dims[1]
        return [center_x, center_y, width, height]
    
    def add_training_sample(self, face_coords, position):
        """Add a new training sample."""
        if face_coords is not None:
            features = self.normalize_face_position(face_coords)
            movement = self.get_movement_from_position(position)
            if movement is not None:
                self.training_data.append((features, movement))
    
    def train_step(self):
        """Train on a sequence of samples if enough data is available."""
        if len(self.training_data) < self.sequence_length:
            return None
            
        # Prepare sequence
        sequence = [sample[0] for sample in self.training_data[-self.sequence_length:]]
        target_movement = self.training_data[-1][1]  # Target is the movement for the last frame in sequence

        # Convert to tensor
        features = torch.tensor(sequence, dtype=torch.float32).unsqueeze(0)
        target = torch.tensor([target_movement], dtype=torch.float32)
        
        # Forward pass
        self.optimizer.zero_grad()
        output, _ = self.model(features)
        loss = self.criterion(output, target)
        
        # Backward pass
        loss.backward()
        self.optimizer.step()
        
        return loss.item()
    
    def predict_movement(self, face_coords_sequence):
        """Predict movement based on a sequence of face positions."""
        if len(face_coords_sequence) < self.sequence_length:
            return None
            
        features = [self.normalize_face_position(coords) for coords in face_coords_sequence]
        features_tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(0)
        
        with torch.no_grad():
            movement, _ = self.model(features_tensor)
            return movement.squeeze().tolist()

    def apply_movement(self, movement):
        """Apply predicted movement to robot head with safety limits."""
        if movement is None:
            return
            
        try:
            current_yaw, current_pitch = self.motion_service.getAngles(["HeadYaw", "HeadPitch"], True)
            new_yaw = current_yaw + movement[0]
            new_pitch = current_pitch + movement[1]
            
            # Apply safety limits
            new_yaw = max(min(new_yaw, 2.0857), -2.0857)  # Yaw limits in radians
            new_pitch = max(min(new_pitch, 0.5149), -0.6720)  # Pitch limits in radians
            
            self.motion_service.setAngles(
                ["HeadYaw", "HeadPitch"],
                [new_yaw, new_pitch],
                0.1  # Movement speed
            )
        except Exception as e:
            print(f"Error applying movement: {e}")
            
    def save_model(self, path):
        """Save the model state and training data."""
        try:
            save_data = {
                'model_state_dict': self.model.state_dict(),
                'optimizer_state_dict': self.optimizer.state_dict(),
                'training_samples': len(self.training_data),
                'training_data': self.training_data,
                'position_to_movement': self.position_to_movement
            }
            torch.save(save_data, path)
            return True
        except Exception as e:
            print(f"Error saving model: {e}")
            return False
            
    def load_model(self, path):
        """Load a previously saved model."""
        try:
            checkpoint = torch.load(path)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.training_data = checkpoint['training_data']
            self.position_to_movement = checkpoint['position_to_movement']
            return True, checkpoint.get('training_samples', 0)
        except Exception as e:
            print(f"Error loading model: {e}")
            return False, 0