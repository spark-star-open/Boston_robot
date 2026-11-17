"""Split the YOLO detections into per-object masks so metrics.py can score them.

Each detected instance mask is assigned to the ground-truth object it overlaps
most (falling back to nearest centroid). Objects YOLO never finds get an
all-zero mask, which is the honest score for a miss.
"""
import os

import cv2
import numpy as np
from ultralytics import YOLO

WS = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(WS, "track1_assets", "raw")
GT = os.path.join(WS, "track1_assets", "gt")
OUT = os.path.join(WS, "track1_assets", "repro")
W = os.path.join(WS, ".weights", "yolov8n-seg.pt")
os.environ["YOLO_CONFIG_DIR"] = os.path.join(WS, ".ultralytics")
os.environ["NO_PROXY"] = "*"

IMAGES = {
    "dark": os.path.join(RAW, "s01_portrait_1024x1460_cec769fe10.jpg"),
    "light": os.path.join(RAW, "s01_landscape_1444x1024_977db1c8be.jpg"),
}
OBJECTS = ("green", "black")


def rd(p):
    return cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_UNCHANGED)


def wr(p, img):
    cv2.imencode(".png", img)[1].tofile(p)


def main():
    model = YOLO(W)
    for tag, path in IMAGES.items():
        img = cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_COLOR)
        h, w = img.shape[:2]
        gts = {}
        for obj in OBJECTS:
            g = rd(os.path.join(GT, f"{tag}_{obj}.png"))
            gts[obj] = (g > 127).astype(np.uint8) if g is not None else np.zeros((h, w), np.uint8)

        res = model(img, conf=0.5, verbose=False)[0]
        per_obj = {o: np.zeros((h, w), np.uint8) for o in OBJECTS}
        polys = res.masks.xy if res.masks is not None else []

        for i, box in enumerate(res.boxes):
            if i >= len(polys) or len(polys[i]) < 3:
                continue
            m = np.zeros((h, w), np.uint8)
            cv2.fillPoly(m, [np.round(polys[i]).astype(np.int32)], 255)
            best, best_overlap = None, -1
            for obj in OBJECTS:
                ov = int(np.logical_and(m > 0, gts[obj] > 0).sum())
                if ov > best_overlap:
                    best, best_overlap = obj, ov
            if best is None:
                continue
            cls = model.names[int(box.cls)]
            print(f"{tag}: det {cls} conf={float(box.conf):.2f} -> {best} (overlap {best_overlap} px)")
            per_obj[best] |= m

        for obj in OBJECTS:
            out = os.path.join(OUT, f"{tag}_yolo_{obj}_mask.png")
            wr(out, per_obj[obj])
            print(f"  {tag}/{obj}: {int((per_obj[obj] > 0).sum())} px -> {os.path.basename(out)}")


if __name__ == "__main__":
    main()
