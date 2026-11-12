"""Simple object pose estimator: threshold -> contours -> PCA -> gripper.

Date: 2026-11-12
"""
from .core import (ObjectPose, clean_mask, draw_pose, estimate_poses,
                   gripper_geometry, mask_to_xy, pca_pose, segment_color,
                   segment_gray, split_objects)

__all__ = [
    "ObjectPose", "clean_mask", "draw_pose", "estimate_poses", "gripper_geometry",
    "mask_to_xy", "pca_pose", "segment_color", "segment_gray", "split_objects",
]
__version__ = "0.1.0"
