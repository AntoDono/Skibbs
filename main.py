import cv2
from detection import init_camera, init_segmentation, detect_human, get_human_box

def get_direction(box_coords, human_area, target_human_area, frame_width):
    """Get direction human should move based on their position"""
    if box_coords:
        direction = ""
        
        x_min, y_min, x_max, y_max = box_coords
        # Get center of the human box
        human_center_x = (x_min + x_max) // 2
        frame_center_x = frame_width // 2
        
        # This means that human is further away from the camera
        if human_area < target_human_area:
            direction += "FOWARD "
        else:
            direction += "BACKWARD "
        
        # If human is on left side, they should move RIGHT
        if human_center_x < frame_center_x:
            direction += "RIGHT"
        else:
            direction += "LEFT"
    
    return direction

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

def draw_direction_text(frame, direction):
    """Draw direction text at top-left corner"""
    if direction:
        cv2.putText(frame, f'Corrective Move: {direction}', (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    return frame

def main():
    # Initialize detection components
    camera = init_camera()
    segmentation = init_segmentation()
    human_area_coefficient = 0.333 # desired human to fill up 1/3 of the frame
    target_human_area = None
    
    while True:
        ret, frame = camera.read()
        if not ret:
            break
        
        if target_human_area is None:
            target_human_area = frame.shape[1] * frame.shape[0] * human_area_coefficient
            
        # Detect human
        human_detected, mask = detect_human(frame, segmentation)
        
        # Draw box if human found
        if human_detected:
            box_coords = get_human_box(mask)
            human_area = get_human_area(box_coords)
            direction = get_direction(box_coords, human_area, target_human_area, frame.shape[1])
            frame = draw_human_box(frame, box_coords)
            frame = draw_direction_text(frame, direction)
            
        # Display frame
        cv2.imshow('Human Detection', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    camera.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
