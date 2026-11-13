"""Compare predicted masks against the hand-labelled ground truth.

    python metrics.py [--gt DIR] [--pred DIR]

Ground truth : track1_assets/gt/<image>_<object>.png        (white = object)
Predictions  : track1_assets/repro/<image>_<method>_<object>_mask.png
Methods      : rgb, hsv  (add more names once YOLO masks exist)

Reported per row:  IoU, |Δcentre| in px, |Δangle| in degrees
"""
import argparse
import glob
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.metrics import pose, angle_diff, iou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GT_DEFAULT = os.path.join(HERE, "data", "ground_truth")
PRED_DEFAULT = os.path.join(HERE, "outputs", "repro")
OBJECTS = ("green", "black")
IMAGES = ("dark", "light")


def rd_mask(path):
    data = np.fromfile(path, np.uint8)
    m = cv2.imdecode(data, cv2.IMREAD_GRAYSCALE)
    if m is None:
        return None
    return (m > 127).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gt", default=GT_DEFAULT)
    ap.add_argument("--pred", default=PRED_DEFAULT)
    ap.add_argument("--methods", default="rgb,hsv,yolo")
    args = ap.parse_args()
    methods = [m.strip() for m in args.methods.split(",") if m.strip()]

    rows = []
    for img in IMAGES:
        for obj in OBJECTS:
            gt = rd_mask(os.path.join(args.gt, f"{img}_{obj}.png"))
            if gt is None:
                print(f"[warn] no ground truth for {img}/{obj} — run label_gt.py first")
                continue
            g_area = int(gt.sum())
            gp = pose(gt)
            for meth in methods:
                pat = os.path.join(args.pred, f"{img}_{meth}_{obj}_mask.png")
                if not os.path.exists(pat):
                    matches = glob.glob(os.path.join(args.pred, f"{img}_{meth}_{obj}*mask.png"))
                    if not matches:
                        continue
                    pat = matches[0]
                pred = rd_mask(pat)
                if pred is None:
                    continue
                inter = int(np.logical_and(gt, pred).sum())
                union = int(np.logical_or(gt, pred).sum())
                score = iou(gt, pred)
                pp = pose(pred)
                if pp and gp:
                    dc = float(np.hypot(pp[0] - gp[0], pp[1] - gp[1]))
                    da = (angle_diff(pp[2], gp[2])
                          if np.isfinite(pp[2]) and np.isfinite(gp[2]) else float("nan"))
                else:
                    dc = da = float("nan")
                rows.append({
                    "image": img, "object": obj, "method": meth,
                    "iou": score, "dc": dc, "da": da,
                    "gt_area": g_area, "pred_area": int(pred.sum()),
                    "gt_aspect": gp[3] if gp else float("nan"),
                })

    if not rows:
        print("nothing to compare — label the ground truth first (label_gt.py)")
        return 1

    print(f"{'image':6s} {'object':6s} {'method':6s} {'IoU':>6s} {'Δc(px)':>8s} "
          f"{'Δang(°)':>8s} {'GT px':>7s} {'pred px':>8s} {'asp':>5s}")
    print("-" * 70)
    for r in rows:
        da = "  n/a" if not np.isfinite(r["da"]) else f"{r['da']:6.1f}"
        print(f"{r['image']:6s} {r['object']:6s} {r['method']:6s} {r['iou']:6.3f} "
              f"{r['dc']:8.1f} {da:>8s} {r['gt_area']:7d} {r['pred_area']:8d} "
              f"{r['gt_aspect']:5.2f}")

    print("\nmean IoU by method")
    for meth in methods:
        vals = [r["iou"] for r in rows if r["method"] == meth]
        if vals:
            print(f"  {meth:4s}: {np.mean(vals):.3f}   (n={len(vals)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
