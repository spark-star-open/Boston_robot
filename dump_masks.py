"""Save a side-by-side picture of the three methods for each object.

Debugging is not the only way to see what a mask looks like -- this writes the
comparison straight to disk so it can be opened in any image viewer.

    D:\\python\\python.exe dump_masks.py
"""
import glob
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "track1_assets", "raw")
GT = os.path.join(HERE, "track1_assets", "gt")
PRED = os.path.join(HERE, "track1_assets", "repro")
OUT = os.path.join(HERE, "track1_assets", "compare")
os.makedirs(OUT, exist_ok=True)

METHODS = [("rgb", (60, 120, 240)), ("hsv", (60, 190, 90)), ("yolo", (220, 140, 40))]
OBJECTS = ("green", "black")


def rd(path, gray=False):
    flag = cv2.IMREAD_GRAYSCALE if gray else cv2.IMREAD_COLOR
    return cv2.imdecode(np.fromfile(path, np.uint8), flag)


def photo_for(tag):
    pat = os.path.join(RAW, f"s01_{'portrait' if tag == 'dark' else 'landscape'}_*.jpg")
    hit = glob.glob(pat)
    return hit[0] if hit else None


def iou(gt, pred):
    inter = int(np.logical_and(gt, pred).sum())
    union = int(np.logical_or(gt, pred).sum())
    return inter / union if union else 0.0


def panel(photo, gt, pred, label, color, score):
    vis = photo.copy()
    if pred is not None and pred.any():
        tint = np.zeros_like(vis)
        tint[pred > 0] = color
        vis = cv2.addWeighted(vis, 1.0, tint, 0.35, 0)
        cnts, _ = cv2.findContours(pred, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(vis, cnts, -1, color, 3)
    cnts, _ = cv2.findContours(gt, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(vis, cnts, -1, (0, 255, 255), 2)      # GT always yellow, thin

    if not pred.any() or pred is None:
        label = label + "    (no detection)"
    bar = np.full((54, vis.shape[1], 3), 255, np.uint8)
    cv2.putText(bar, f"{label}   IoU {score:.3f}", (10, 36),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (30, 40, 55), 2)
    return np.vstack([bar, vis])


for tag in ("dark", "light"):
    photo_path = photo_for(tag)
    if not photo_path:
        print(f"[skip] no photo for {tag}")
        continue
    photo = rd(photo_path)
    for obj in OBJECTS:
        gt = rd(os.path.join(GT, f"{tag}_{obj}.png"), gray=True)
        if gt is None:
            print(f"[skip] no GT for {tag}/{obj}")
            continue
        gt = (gt > 127).astype(np.uint8)
        panels = []
        for name, color in METHODS:
            mp = os.path.join(PRED, f"{tag}_{name}_{obj}_mask.png")
            pred = rd(mp, gray=True) if os.path.exists(mp) else None
            pred = (pred > 127).astype(np.uint8) if pred is not None else np.zeros_like(gt)
            panels.append(panel(photo, gt, pred, name.upper(), color, iou(gt, pred)))
        h = min(p.shape[0] for p in panels)
        panels = [cv2.resize(p, (int(p.shape[1] * h / p.shape[0]), h)) for p in panels]
        out = np.hstack(panels)
        out = cv2.resize(out, (int(out.shape[1] * 0.62), int(out.shape[0] * 0.62)))
        path = os.path.join(OUT, f"{tag}_{obj}_compare.jpg")
        cv2.imencode(".jpg", out, [cv2.IMWRITE_JPEG_QUALITY, 90])[1].tofile(path)
        print("wrote", path, out.shape[1], "x", out.shape[0])

print("\nopen the four images in", OUT)
