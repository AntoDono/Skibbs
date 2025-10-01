from math import e
import cv2
from detection import init_camera, init_segmentation, detect_human, get_human_box
from drive import Drive
import time
import argparse

# Global parameters
POSITION_COEFFICIENT = 0.5  # Controls how position deviation is scaled
SENSITIVITY_THRESHOLD = 0.05  # 5% threshold before reacting
HUMAN_AREA_TARGET = 0.333  # Target human area as fraction of frame

def calculate_area_deviation(human_area, target_area):
    """Calculate area deviation as percentage of target area"""
    if human_area == 0 or target_area == 0:
        return 0
    
    # Positive means too close (area too big), negative means too far
    deviation = (human_area - target_area) / target_area
    return deviation

def calculate_position_deviation(box_coords, frame_width):
    """Calculate horizontal position deviation in pixels from center"""
    if not box_coords:
        return 0
    
    x_min, y_min, x_max, y_max = box_coords
    human_center_x = (x_min + x_max) // 2
    frame_center_x = frame_width // 2
    
    # Positive means human is to the right, negative means to the left
    pixel_deviation = human_center_x - frame_center_x
    return pixel_deviation

def apply_threshold(value, threshold):
    """Apply sensitivity threshold to a value"""
    if abs(value) < threshold:
        return 0
    return value

def get_deviations(box_coords, human_area, target_area, frame_width):
    """Get x (area) and y (position) deviations with threshold applied"""
    if not box_coords:
        return {"x": 0, "y": 0}
    
    # Calculate raw deviations
    area_dev = calculate_area_deviation(human_area, target_area)
    pos_dev = calculate_position_deviation(box_coords, frame_width)
    
    # Scale position deviation by coefficient
    pos_dev_scaled = pos_dev / (frame_width * POSITION_COEFFICIENT)
    
    # Apply threshold
    x = apply_threshold(area_dev, SENSITIVITY_THRESHOLD)
    y = apply_threshold(pos_dev_scaled, SENSITIVITY_THRESHOLD)
    
    return {"x": x, "y": y}

def get_human_area(box_coords):
    """Get area of human"""
    if box_coords:
        x_min, y_min, x_max, y_max = box_coords
        return (x_max - x_min) * (y_max - y_min)
    return 0

def draw_human_box(frame, box_coords):
    """Draw box around detected human"""
    if box_coords:
        x_min, y_min, x_max, y_max = box_coords
        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
        cv2.putText(frame, 'Human', (x_min, y_min-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    return frame

def control_all_wheels(drive, deviations):
    """Control all wheels based on deviations to center human"""
    x_dev = deviations["x"]  # Area deviation (forward/backward)
    y_dev = deviations["y"]  # Position deviation (left/right)
    
    # Base speed
    base_speed = 0.5
    
    # If no deviations, stop
    if x_dev == 0 and y_dev == 0:
        drive.stop_all()
        return
    
    # Calculate wheel speeds
    # For forward/backward: negative x means too far (go forward), positive x means too close (go backward)
    movement_speed = base_speed * abs(x_dev)
    
    # For turning: positive y means human is right (turn right)
    # Turn by differential speed on left vs right wheels
    if y_dev > 0:  # Human is to the right, turn right
        left_speed = movement_speed
        right_speed = movement_speed * 0.5  # Slow down right wheels
    elif y_dev < 0:  # Human is to the left, turn left
        left_speed = movement_speed * 0.5  # Slow down left wheels
        right_speed = movement_speed
    else:  # Go straight
        left_speed = movement_speed
        right_speed = movement_speed
    
    # Limit speeds to 0-1 range
    left_speed = max(0, min(1, left_speed))
    right_speed = max(0, min(1, right_speed))

    print(f"Left Speed: {left_speed} | Right Speed: {right_speed}")
    
    # Control all wheels based on direction
    if x_dev < 0:  # Too far, go forward
        # Control all wheels - front and rear wheels mirror each other for tank-style steering
        drive.all_drive(front_left_speed=left_speed, front_right_speed=right_speed, 
                        rear_left_speed=left_speed, rear_right_speed=right_speed, duration=None)
    elif x_dev > 0:  # Too close, go backward
        # Control all wheels backward - front and rear wheels mirror each other for tank-style steering
        drive.all_drive_backward(front_left_speed=left_speed, front_right_speed=right_speed, 
                                rear_left_speed=left_speed, rear_right_speed=right_speed, duration=None)

def draw_deviation_info(frame, deviations):
    """Draw deviation info on frame"""
    x_dev = deviations["x"]
    y_dev = deviations["y"]
    
    # Draw deviation percentages
    cv2.putText(frame, f'Area Dev: {x_dev:.2%}', (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, f'Pos Dev: {y_dev:.2%}', (10, 60), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Draw action being taken
    action = "STOPPED"
    if x_dev != 0 or y_dev != 0:
        if x_dev < 0:
            action = "FORWARD"
        elif x_dev > 0:
            action = "BACKWARD"
        if y_dev > 0:
            action += " + RIGHT"
        elif y_dev < 0:
            action += " + LEFT"
    
    cv2.putText(frame, f'Action: {action}', (10, 90), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    return frame

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Human Tracking Robot')
    parser.add_argument('--cmd', action='store_true', help='Run without displaying video frame')
    args = parser.parse_args()
    
    # Set OpenCV backend for headless mode
    if args.cmd:
        import os
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    # Initialize detection components
    camera = init_camera()
    segmentation = init_segmentation()
    drive = Drive()  # Initialize robot drive
    
    target_human_area = None
    
    try:
        while True:
            ret, frame = camera.read()
            if not ret:
                break
            
            # Flip frame horizontally to fix mirrored view
            
            if target_human_area is None:
                target_human_area = frame.shape[1] * frame.shape[0] * HUMAN_AREA_TARGET
                
            # Detect human
            human_detected, mask = detect_human(frame, segmentation) 
            
            # Process if human found
            if human_detected:
                box_coords = get_human_box(mask)
                human_area = get_human_area(box_coords)
                
                # Get deviations
                deviations = get_deviations(box_coords, human_area, target_human_area, frame.shape[1])
                
                # Control robot
                control_all_wheels(drive, deviations)
                
                # Draw visualizations only if not in cmd mode
                if not args.cmd:
                    frame = draw_human_box(frame, box_coords)
                    frame = draw_deviation_info(frame, deviations)
            else:
                # No human detected, stop robot
                drive.stop_all()
                if not args.cmd:
                    cv2.putText(frame, 'No Human Detected', (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            time.sleep(0.1)
                
            # Display frame only if not in cmd mode
            if not args.cmd:
                cv2.imshow('Human Tracking Robot', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
    
    finally:
        # Cleanup
        drive.stop_all()
        drive.cleanup()  # Clean up BTS7960 motor resources
        camera.release()
        if not args.cmd:
            cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
