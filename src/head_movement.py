# -*- coding: future_fstrings -*-
import numpy as np
import torch
import torch.nn as nn
from config import CENTER_BOX
from collections import deque
"""
class HeadTrackingLSTM(nn.Module):
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

class HeadTracker:
    def __init__(self, motion_service):
        self.motion_service = motion_service
        self.model = HeadTrackingLSTM()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        self.criterion = nn.MSELoss()
        
        # Store sequences of face positions
        self.position_history = deque(maxlen=10)
        # was 10 with single frame
        self.sequence_length = 5
        self.training_data = []
        
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
        if position in ["In the middle", "Not detected"]:
            return None
        return self.position_to_movement.get(position, [0.0, 0.0])
    
    def normalize_face_position(self, face_coords, frame_dims=(320, 240)):
        #Convert face coordinates to normalized features
        top, right, bottom, left = face_coords
        center_x = (left + right) / 2.0 / frame_dims[0]
        center_y = (top + bottom) / 2.0 / frame_dims[1]
        width = (right - left) / frame_dims[0]
        height = (bottom - top) / frame_dims[1]
        return [center_x, center_y, width, height]
    
    def add_training_sample(self, face_coords, position):
        #Add a new training sample
        if face_coords is not None:
            features = self.normalize_face_position(face_coords)
            movement = self.get_movement_from_position(position)
            if movement is not None:
                self.training_data.append((features, movement))
    
    def train_step(self):
        #Train on a sequence of samples if enough data is available
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
    
    def predict_movement(self):
        #Predict movement based on accumulated sequence of face positions
        if len(self.position_history) < self.sequence_length:
            return None
        
        # Prepare sequence
        sequence = list(self.position_history)
        features_tensor = torch.tensor(sequence, dtype=torch.float32).unsqueeze(0)
        
        # Run prediction
        with torch.no_grad():
            movement, _ = self.model(features_tensor)
            return movement.squeeze().tolist()

    def apply_movement(self, movement):
        #Apply predicted movement to robot head
        if movement is None:
            return
            
        try:
            current_yaw, current_pitch = self.motion_service.getAngles(["HeadYaw", "HeadPitch"], True)
            new_yaw = current_yaw + movement[0]
            new_pitch = current_pitch + movement[1]
            
            # Apply safety limits
            new_yaw = max(min(new_yaw, 2.0857), -2.0857)
            new_pitch = max(min(new_pitch, 0.5149), -0.6720)
            
            self.motion_service.setAngles(
                ["HeadYaw", "HeadPitch"],
                [new_yaw, new_pitch],
                0.1
            )
        except Exception as e:
            print("Error applying movement: %s" % str(e))

def head_relative_to_center(pred, top_left, bottom_right, tracker=None, training=True):
    if not pred[u'face_locations']:
        print("Position: Not detected")
        return "Not detected"
        
    if isinstance(pred[u'face_locations'][0][0], (int, long, float)):
        position = determine(pred[u'face_locations'][0], top_left, bottom_right)
        print("Position: %s" % position)
        
        if tracker is not None and position not in ["In the middle", "Not detected"]:
            if training:
                tracker.add_training_sample(pred[u'face_locations'][0], position)
                # Apply movement during training too
                movement = tracker.get_movement_from_position(position)
                if movement is not None:
                    try:
                        current_yaw, current_pitch = tracker.motion_service.getAngles(["HeadYaw", "HeadPitch"], True)
                        new_yaw = current_yaw + movement[0]
                        new_pitch = current_pitch + movement[1]
                        
                        new_yaw = max(min(new_yaw, 2.0857), -2.0857)
                        new_pitch = max(min(new_pitch, 0.5149), -0.6720)
                        
                        tracker.motion_service.setAngles(
                            ["HeadYaw", "HeadPitch"],
                            [new_yaw, new_pitch],
                            0.1
                        )
                    except Exception as e:
                        print("Error applying training movement: %s" % str(e))
        
        return position
    else:
        print("Bad %s" % str(pred))
        return "Not detected"

def determine(coords, top_left, bottom_right):
    middle_point = ((coords[0] + coords[2]) / 2, (coords[1] + coords[3]) / 2)
    mid_point_x, mid_point_y = middle_point[1], middle_point[0]
    top_left_x, top_left_y = top_left[0], top_left[1]
    bottom_right_x, bottom_right_y = bottom_right[0], bottom_right[1]

    if (mid_point_x > bottom_right_x) and (mid_point_y > top_left_y) and (mid_point_y < bottom_right_y):
        return "Right"
    elif (mid_point_x > bottom_right_x) and (mid_point_y > bottom_right_y):
        return "Bottom right"
    elif (mid_point_x > bottom_right_x) and (mid_point_y < top_left_y):
        return "Top right"
    elif (mid_point_x > top_left_x) and (mid_point_x < bottom_right_x) and (mid_point_y < top_left_y):
        return "Middle top"
    elif (mid_point_x > top_left_x) and (mid_point_x < bottom_right_x) and (mid_point_y > bottom_right_y):
        return "Middle bottom"
    elif (mid_point_x < top_left_x) and (mid_point_y > top_left_y) and (mid_point_y < bottom_right_y):
        return "Left"
    elif (mid_point_x < top_left_x) and (mid_point_y > bottom_right_y):
        return "Bottom left"
    elif (mid_point_x < top_left_x) and (mid_point_y < top_left_y):
        return "Top left"
    else:
        return "In the middle"
"""




#taking in a single frame
# head_movement.py
import numpy as np
import torch
import torch.nn as nn
from config import CENTER_BOX
from collections import deque

class HeadTrackingLSTM(nn.Module):
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
    def __init__(self, motion_service):
        self.motion_service = motion_service
        self.model = HeadTrackingLSTM()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        self.criterion = nn.MSELoss()
        
        self.position_history = deque(maxlen=10)
        self.sequence_length = 10
        self.training_data = []
        
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
        if position in ["In the middle", "Not detected"]:
            return None
        return self.position_to_movement.get(position, [0.0, 0.0])
    
    def normalize_face_position(self, face_coords, frame_dims=(320, 240)):
        top, right, bottom, left = face_coords
        center_x = (left + right) / 2.0 / frame_dims[0]
        center_y = (top + bottom) / 2.0 / frame_dims[1]
        width = (right - left) / frame_dims[0]
        height = (bottom - top) / frame_dims[1]
        return [center_x, center_y, width, height]
    
    def add_training_sample(self, face_coords, position):
        #Add a new training sample
        if face_coords is not None:
            features = self.normalize_face_position(face_coords)
            movement = self.get_movement_from_position(position)
            if movement is not None:
                self.training_data.append((features, movement))
    
    def train_step(self):
        if len(self.training_data) < self.sequence_length:
            return None
            
        # Prepare sequence
        features = torch.tensor([sample[0] for sample in self.training_data[-self.sequence_length:]], 
                              dtype=torch.float32).unsqueeze(0)
        target = torch.tensor([self.training_data[-1][1]], dtype=torch.float32)
        
        # Forward pass
        self.optimizer.zero_grad()
        output, _ = self.model(features)
        loss = self.criterion(output, target)
        
        # Backward pass
        loss.backward()
        self.optimizer.step()
        
        return loss.item()
    
    def predict_movement(self, face_coords_sequence):
        if len(face_coords_sequence) < self.sequence_length:
            return None
            
        features = [self.normalize_face_position(coords) for coords in face_coords_sequence]
        features_tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(0)
        
        with torch.no_grad():
            movement, _ = self.model(features_tensor)
            return movement.squeeze().tolist()

    def apply_movement(self, movement):
        if movement is None:
            return
            
        try:
            current_yaw, current_pitch = self.motion_service.getAngles(["HeadYaw", "HeadPitch"], True)
            new_yaw = current_yaw + movement[0]
            new_pitch = current_pitch + movement[1]
            
            # Apply safety limits
            new_yaw = max(min(new_yaw, 2.0857), -2.0857)
            new_pitch = max(min(new_pitch, 0.5149), -0.6720)
            
            self.motion_service.setAngles(
                ["HeadYaw", "HeadPitch"],
                [new_yaw, new_pitch],
                0.1
            )
        except Exception as e:
            print("Error applying movement: %s" % str(e))

def head_relative_to_center(pred, top_left, bottom_right, tracker=None, training=True):
    if not pred[u'face_locations']:
        print("Position: Not detected")
        return "Not detected"
        
    if isinstance(pred[u'face_locations'][0][0], (int, long, float)):
        position = determine(pred[u'face_locations'][0], top_left, bottom_right)
        print("Position: %s" % position)
        
        if tracker is not None and position not in ["In the middle", "Not detected"]:
            if training:
                tracker.add_training_sample(pred[u'face_locations'][0], position)
                # Apply movement during training too
                movement = tracker.get_movement_from_position(position)
                if movement is not None:
                    try:
                        current_yaw, current_pitch = tracker.motion_service.getAngles(["HeadYaw", "HeadPitch"], True)
                        new_yaw = current_yaw + movement[0]
                        new_pitch = current_pitch + movement[1]
                        
                        new_yaw = max(min(new_yaw, 2.0857), -2.0857)
                        new_pitch = max(min(new_pitch, 0.5149), -0.6720)
                        
                        tracker.motion_service.setAngles(
                            ["HeadYaw", "HeadPitch"],
                            [new_yaw, new_pitch],
                            0.1
                        )
                    except Exception as e:
                        print("Error applying training movement: %s" % str(e))
        
        return position
    else:
        print("Bad %s" % str(pred))
        return "Not detected"

def determine(coords, top_left, bottom_right):
    middle_point = ((coords[0] + coords[2]) / 2, (coords[1] + coords[3]) / 2)
    mid_point_x, mid_point_y = middle_point[1], middle_point[0]
    top_left_x, top_left_y = top_left[0], top_left[1]
    bottom_right_x, bottom_right_y = bottom_right[0], bottom_right[1]

    if (mid_point_x > bottom_right_x) and (mid_point_y > top_left_y) and (mid_point_y < bottom_right_y):
        return "Right"
    elif (mid_point_x > bottom_right_x) and (mid_point_y > bottom_right_y):
        return "Bottom right"
    elif (mid_point_x > bottom_right_x) and (mid_point_y < top_left_y):
        return "Top right"
    elif (mid_point_x > top_left_x) and (mid_point_x < bottom_right_x) and (mid_point_y < top_left_y):
        return "Middle top"
    elif (mid_point_x > top_left_x) and (mid_point_x < bottom_right_x) and (mid_point_y > bottom_right_y):
        return "Middle bottom"
    elif (mid_point_x < top_left_x) and (mid_point_y > top_left_y) and (mid_point_y < bottom_right_y):
        return "Left"
    elif (mid_point_x < top_left_x) and (mid_point_y > bottom_right_y):
        return "Bottom left"
    elif (mid_point_x < top_left_x) and (mid_point_y < top_left_y):
        return "Top left"
    else:
        return "In the middle"
