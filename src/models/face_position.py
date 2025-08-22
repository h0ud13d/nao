# -*- coding: future_fstrings -*-
# models/face_position.py

def determine_position(coords, top_left, bottom_right):
    """
    Determine the relative position of a face in the frame.
    
    Args:
        coords: Tuple (top, right, bottom, left) of face coordinates
        top_left: Tuple (x, y) of the top-left coordinate of center box
        bottom_right: Tuple (x, y) of the bottom-right coordinate of center box
        
    Returns:
        String describing the position (e.g., "Right", "Left", "Top right", etc.)
    """
    # Calculate the middle point of the face
    middle_point = ((coords[0] + coords[2]) / 2, (coords[1] + coords[3]) / 2)
    mid_point_x, mid_point_y = middle_point[1], middle_point[0]
    top_left_x, top_left_y = top_left[0], top_left[1]
    bottom_right_x, bottom_right_y = bottom_right[0], bottom_right[1]

    # Determine position based on where the middle point is relative to the center box
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

def head_relative_to_center(pred, top_left, bottom_right):
    """
    Determine the relative position of the face to the center of the frame.
    
    Args:
        pred: Dictionary containing face detection predictions
        top_left: Tuple of top-left coordinates of center frame
        bottom_right: Tuple of bottom-right coordinates of center frame
        
    Returns:
        String describing the position
    """
    if not pred['face_locations']:
        print("Position: Not detected")
        return "Not detected"
        
    if isinstance(pred['face_locations'][0][0], (int, long, float)):
        position = determine_position(pred['face_locations'][0], top_left, bottom_right)
        print(f"Position: {position}")
        return position
    else:
        print(f"Bad prediction: {pred}")
        return "Not detected"