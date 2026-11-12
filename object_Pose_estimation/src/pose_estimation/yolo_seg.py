"""Next step: replace thresholding with YOLO segmentation, keep the same PCA.

Date: 2026-11-12

Requires the optional dependency:  pip install ultralytics
The first call downloads the weights (default: yolov8n-seg.pt).

Note: a COCO-pretrained model only knows 80 classes, so objects of other kinds
(e.g. toys) are simply not detected. Lower `conf`, use a bigger model, or fine-tune.
"""
from __future__ import annotations

from typing import List

import cv2
import numpy as np

from .core import ObjectPose, pca_pose


def estimate_poses_yolo(img_bgr: np.ndarray, weights: str = "yolov8n-seg.pt",
                        conf: float = 0.25, min_area: int = 500) -> List[ObjectPose]:
    """Run YOLO segmentation, then the same PCA on every detected mask.

    Each returned pose carries label / conf / box so it can be drawn with
    "class confidence" like a normal detector.
    """
    try:
        from ultralytics import YOLO
    except ImportError as e:  # pragma: no cover
        raise ImportError("pip install ultralytics to use --mode yolo") from e

    res = YOLO(weights).predict(img_bgr, conf=conf, verbose=False)[0]
    if res.masks is None:
        return []
    h, w = img_bgr.shape[:2]
    poses = []
    # res.masks.xy (polygons, ORIGINAL pixels, (x, y)) is aligned with res.boxes
    for poly, box in zip(res.masks.xy, res.boxes):
        m = np.zeros((h, w), np.uint8)
        cv2.fillPoly(m, [poly.astype(np.int32)], 255)
        m = m > 0
        if m.sum() < min_area:
            continue
        pose = pca_pose(m)
        pose.label = res.names[int(box.cls)]
        pose.conf = float(box.conf)
        pose.box = tuple(int(round(v)) for v in box.xyxy[0].tolist())
        poses.append(pose)
    poses.sort(key=lambda p: p.center[0])                # left -> right
    return poses
