"""Generate a synthetic test image with rotated rectangles / ellipses of known angles.

Date: 2026-11-12

Use it to sanity-check the estimator (ground truth is printed), then switch to
your own photos of objects on your table.python make_sample.py
"""
import json
from pathlib import Path

import cv2
import numpy as np

# (cx, cy, long, short, angle_deg, shape)
OBJECTS = [
    (150, 150, 180, 60, 30, "rect"),
    (420, 140, 150, 50, -45, "ellipse"),
    (300, 360, 200, 70, 80, "rect"),
]


def main(out="data/sample.png"):
    img = np.full((500, 600, 3), 225, np.uint8)               # light "table"
    rng = np.random.default_rng(0)
    for cx, cy, L, S, ang, shape in OBJECTS:
        if shape == "rect":
            box = cv2.boxPoints(((cx, cy), (L, S), ang)).astype(np.int32)
            cv2.fillPoly(img, [box], (40, 60, 160))
        else:
            cv2.ellipse(img, ((cx, cy), (L, S), ang), (40, 130, 40), -1)
    noise = rng.normal(0, 6, img.shape)
    img = np.clip(img + noise, 0, 255).astype(np.uint8)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(out, img)
    Path(out).with_suffix(".gt.json").write_text(json.dumps(
        [dict(center=[c, d], long=L, short=S, angle=a) for c, d, L, S, a, _ in OBJECTS], indent=2))
    print("Ground truth (angle of the long axis, image coords, y down):")
    for o in OBJECTS:
        print("  centre=(%d,%d) angle=%d" % (o[0], o[1], o[4]))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
