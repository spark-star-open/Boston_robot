"""Colour thresholds from the original experiment; input images are BGR."""
import cv2
import numpy as np

RANGES = {
    'rgb': {'red': ((0, 0, 120), (80, 80, 255)), 'green': ((0, 120, 0), (80, 255, 80)), 'black': ((0, 0, 0), (60, 60, 60))},
    'hsv': {'red': ((0, 120, 70), (10, 255, 255)), 'green': ((40, 40, 40), (70, 255, 255)), 'black': ((0, 0, 0), (180, 255, 70))},
}

def segment(image, method='hsv', object_name='green'):
    """Return a cleaned binary mask for one target colour."""
    lo, hi = RANGES[method][object_name]
    frame = cv2.cvtColor(image, cv2.COLOR_BGR2HSV) if method == 'hsv' else image
    mask = cv2.inRange(frame, np.array(lo, np.uint8), np.array(hi, np.uint8))
    kernel = np.ones((5, 5), np.uint8)
    return cv2.morphologyEx(cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel), cv2.MORPH_CLOSE, kernel)

def multi_mask(image):
    """Original multi-object experiment: green hue plus dark grayscale."""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mask = cv2.bitwise_or(cv2.inRange(hsv, (35, 60, 40), (80, 255, 255)), cv2.inRange(gray, 0, 85))
    kernel = np.ones((5, 5), np.uint8)
    return cv2.morphologyEx(cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel), cv2.MORPH_CLOSE, kernel)
