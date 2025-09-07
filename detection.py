import cv2
import mediapipe as mp
import numpy as np

def init_camera():
    """Initialize camera"""
    camera = cv2.VideoCapture(0)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    return camera

def init_segmentation():
    """Initialize person segmentation - faster than pose detection"""
    return mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=0)

def detect_human(frame, segmentation):
    """Detect human using fast segmentation"""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = segmentation.process(rgb)
    
    if results.segmentation_mask is not None:
        # Find human pixels
        mask = results.segmentation_mask > 0.5
        human_pixels = np.sum(mask)
        
        if human_pixels > 1000:  # Threshold for meaningful presence
            return True, mask
    
    return False, None

def get_human_box(mask):
    """Get bounding box coordinates of human area"""
    if mask is not None:
        # Find bounding box of human pixels
        coords = np.column_stack(np.where(mask))
        if len(coords) > 0:
            y_min, x_min = coords.min(axis=0)
            y_max, x_max = coords.max(axis=0)
            return (x_min, y_min, x_max, y_max)
    
    return None