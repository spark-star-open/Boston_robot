"""Re-run the RGB (BGR) and HSV threshold pipelines with the parameters frozen in
the report, so we can (a) check the deck's numbers are reproducible and
(b) produce real masks for metric computation.

Params are copied from the report:
  BGR  green (0,120,0)-(80,255,80) | black (0,0,0)-(60,60,60) | red (0,0,120)-(80,80,255)
  HSV  green (40,40,40)-(70,255,255) | black (0,0,0)-(180,255,70) | red (0,120,70)-(10,255,255)
  5x5 open + close, RETR_EXTERNAL, area >= 300 px, minAreaRect
"""
import json
import os

import cv2
import numpy as np

RAW = r"C:\Users\30217\Desktop\ds工作\其他\track1_assets\raw"
OUT = r"C:\Users\30217\Desktop\ds工作\其他\track1_assets\repro"
os.makedirs(OUT, exist_ok=True)

IMAGES = {
    "dark": os.path.join(RAW, "s01_portrait_1024x1460_cec769fe10.jpg"),
    "light": os.path.join(RAW, "s01_landscape_1444x1024_977db1c8be.jpg"),
}

BGR_RANGES = {
    "red": ((0, 0, 120), (80, 80, 255)),
    "green": ((0, 120, 0), (80, 255, 80)),
    "black": ((0, 0, 0), (60, 60, 60)),
}
HSV_RANGES = {
    "green": ((40, 40, 40), (70, 255, 255)),
    "black": ((0, 0, 0), (180, 255, 70)),
    "red": ((0, 120, 70), (10, 255, 255)),
}
KERNEL = np.ones((5, 5), np.uint8)
MIN_AREA = 300


def imread_unicode(path, flags=cv2.IMREAD_COLOR):
    """cv2.imread cannot open non-ASCII paths on Windows; go through bytes."""
    data = np.fromfile(path, dtype=np.uint8)
    return cv2.imdecode(data, flags)


def imwrite_unicode(path, img):
    ok, buf = cv2.imencode(os.path.splitext(path)[1], img)
    if ok:
        buf.tofile(path)
    return ok


def normalize_angle(angle):
    """OpenCV 4.5+/5.x returns [0, 90); convert to (-90, 90] for comparison."""
    if angle > 45:
        angle -= 90
    return angle


def components(frame, ranges, space):
    if space == "hsv":
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    out = {}
    for name, (lo, hi) in ranges.items():
        mask = cv2.inRange(frame, np.array(lo, np.uint8), np.array(hi, np.uint8))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, KERNEL)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, KERNEL)
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        items = []
        for c in cnts:
            a = cv2.contourArea(c)
            if a < MIN_AREA:
                continue
            (cx, cy), (w, h), ang = cv2.minAreaRect(c)
            items.append({
                "area": round(a, 1),
                "center": [round(cx, 1), round(cy, 1)],
                "size": [round(w, 1), round(h, 1)],
                "angle": round(normalize_angle(ang), 1),
            })
        items.sort(key=lambda d: -d["area"])
        out[name] = items
        imwrite_unicode(os.path.join(OUT, f"{tag}_{space}_{name}_mask.png"), mask)
    return out


report = {}
for tag, path in IMAGES.items():
    img = imread_unicode(path)
    assert img is not None, path
    report[tag] = {
        "shape": list(img.shape[:2]),
        "rgb": components(img.copy(), BGR_RANGES, "rgb"),
        "hsv": components(img.copy(), HSV_RANGES, "hsv"),
    }
    print(f"\n########## {tag}.jpg  {img.shape[1]}x{img.shape[0]} ##########")
    for space in ("rgb", "hsv"):
        print(f"  -- {space.upper()} --")
        for name, items in report[tag][space].items():
            if not items:
                print(f"    {name:6s}: (no component >= {MIN_AREA} px)")
            for i, it in enumerate(items):
                print(f"    {name:6s} #{i + 1}: area={it['area']:9.1f}  "
                      f"centre=({it['center'][0]:7.1f},{it['center'][1]:7.1f})  "
                      f"size=({it['size'][0]:6.1f}x{it['size'][1]:5.1f})  angle={it['angle']:6.1f}")

with open(os.path.join(OUT, "components.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)
print("\nsaved ->", OUT)
