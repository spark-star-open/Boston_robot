"""Confidence sweep: what does YOLO actually see when the gate is lowered?"""
import os

import cv2
import numpy as np
from ultralytics import YOLO

WS = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(WS, "track1_assets", "raw")
GT = os.path.join(WS, "track1_assets", "gt")
os.environ["YOLO_CONFIG_DIR"] = os.path.join(WS, ".ultralytics")
os.environ["NO_PROXY"] = "*"

IMG = {
    "dark": os.path.join(RAW, "s01_portrait_1024x1460_cec769fe10.jpg"),
    "light": os.path.join(RAW, "s01_landscape_1444x1024_977db1c8be.jpg"),
}
CONFS = [0.50, 0.30, 0.25, 0.20, 0.15, 0.10, 0.05]


def rd(p, gray=False):
    return cv2.imdecode(np.fromfile(p, np.uint8),
                        cv2.IMREAD_GRAYSCALE if gray else cv2.IMREAD_COLOR)


def iou(g, p):
    u = int(np.logical_or(g, p).sum())
    return int(np.logical_and(g, p).sum()) / u if u else 0.0


model = YOLO(os.path.join(WS, ".weights", "yolov8n-seg.pt"))

for tag in ("light", "dark"):
    img = rd(IMG[tag])
    h, w = img.shape[:2]
    gts = {}
    for obj in ("green", "black"):
        g = rd(os.path.join(GT, f"{tag}_{obj}.png"), gray=True)
        gts[obj] = (g > 127).astype(np.uint8) if g is not None else np.zeros((h, w), np.uint8)

    print(f"\n===== {tag}.jpg =====")
    print(f"{'conf':>5} {'#det':>5}  {'green IoU':>9} {'black IoU':>9}   labels")
    for c in CONFS:
        res = model(img, conf=c, verbose=False)[0]
        per = {o: np.zeros((h, w), np.uint8) for o in gts}
        labels = []
        polys = res.masks.xy if res.masks is not None else []
        for i, box in enumerate(res.boxes):
            cls = model.names[int(box.cls)]
            labels.append(f"{cls}:{float(box.conf):.2f}")
            if i >= len(polys) or len(polys[i]) < 3:
                continue
            m = np.zeros((h, w), np.uint8)
            cv2.fillPoly(m, [np.round(polys[i]).astype(np.int32)], 255)
            best = max(gts, key=lambda o: int(np.logical_and(m > 0, gts[o] > 0).sum()))
            per[best] |= m
        print(f"{c:5.2f} {len(res.boxes):5d}  {iou(gts['green'], per['green']):9.3f} "
              f"{iou(gts['black'], per['black']):9.3f}   {', '.join(labels[:4])}")
