"""Mask pose and orientation error helpers."""
import cv2
import numpy as np

def pose(mask):
    """Centre + heading + aspect of a binary mask.

    Heading is taken along the LONG side of minAreaRect: OpenCV returns the
    angle of one edge without saying which, so swap by 90 deg when w < h.
    Aspect < ~1.15 means the shape is near-square and the heading is
    ill-conditioned -> report it as NaN instead of a meaningless number.
    """
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    cx, cy = float(xs.mean()), float(ys.mean())
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnt = max(cnts, key=cv2.contourArea)
    (_rx, _ry), (w, h), ang = cv2.minAreaRect(cnt)
    if w < h:
        ang += 90.0
    ang = ((ang + 90.0) % 180.0) - 90.0
    long_side, short_side = max(w, h), min(w, h)
    aspect = long_side / short_side if short_side > 0 else 0.0
    if aspect < 1.15:
        ang = float("nan")
    return cx, cy, ang, aspect


def angle_diff(a, b):
    d = abs(a - b) % 180
    return min(d, 180 - d)


def iou(a, b):
    if a.shape != b.shape:
        raise ValueError("Masks must have the same dimensions")
    union = np.logical_or(a, b).sum()
    return float(np.logical_and(a, b).sum() / union) if union else 0.0
