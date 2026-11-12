"""Command line entry point.

Date: 2026-11-12

Examples
--------
    python main.py --image data/sample.png                 # grayscale + Otsu
    python main.py --image my_table.jpg --mode color --lower 35 60 60 --upper 85 255 255
    python main.py --image my_table.jpg --mode yolo --conf 0.1   # needs ultralytics
    python main.py --image my_table.jpg --mode bg          # uniform table, any object colour
    python main.py --image my_table.jpg --invert           # dark objects on bright table
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent / "src"))
from pose_estimation import draw_pose, estimate_poses  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Object pose estimation (PCA + parallel-jaw gripper)")
    p.add_argument("--image", required=True, help="input image path")
    p.add_argument("--out-dir", default="results", help="where to save outputs")
    p.add_argument("--mode", choices=["gray", "color", "bg", "yolo"], default="gray")
    p.add_argument("--thresh", type=int, default=None, help="gray threshold (default Otsu)")
    p.add_argument("--invert", action="store_true", default=None,
                   help="force invert mask (default: automatic)")
    p.add_argument("--lower", type=int, nargs=3, default=[0, 80, 60], help="HSV lower bound")
    p.add_argument("--upper", type=int, nargs=3, default=[179, 255, 255], help="HSV upper bound")
    p.add_argument("--min-area", type=int, default=500)
    p.add_argument("--margin", type=float, default=10.0, help="gripper opening margin (px)")
    p.add_argument("--conf", type=float, default=0.25,
                   help="YOLO confidence threshold (lower -> more detections)")
    p.add_argument("--weights", default="yolov8n-seg.pt", help="YOLO weights for --mode yolo")
    p.add_argument("--drop-border", action="store_true",
                   help="discard blobs touching the image border (edge artefacts)")
    p.add_argument("--hull", action="store_true",
                   help="use the convex hull of each object (fills notches)")
    p.add_argument("--show", action="store_true", help="open a preview window")
    return p.parse_args()


def main() -> int:
    a = parse_args()
    img = cv2.imread(a.image)
    if img is None:
        print(f"Cannot read image: {a.image}", file=sys.stderr)
        return 1

    if a.mode == "yolo":
        from pose_estimation.yolo_seg import estimate_poses_yolo
        poses = estimate_poses_yolo(img, a.weights, a.conf, a.min_area)
        mask = np.zeros(img.shape[:2], np.uint8)       # union of all YOLO masks
        for p_ in poses:
            mask[p_.mask] = 255
    else:
        poses, mask = estimate_poses(img, a.mode, a.min_area, a.thresh, a.invert,
                                     a.lower, a.upper, a.drop_border, a.hull)

    vis = img.copy()
    for i, pose in enumerate(poses):
        vis = draw_pose(vis, pose, i, a.margin)

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stem = Path(a.image).stem
    cv2.imwrite(str(out / f"{stem}_{a.mode}_pose.png"), vis)
    if mask is not None:
        cv2.imwrite(str(out / f"{stem}_{a.mode}_mask.png"), mask)
    report = {"date": date.today().isoformat(), "image": a.image, "mode": a.mode,
              "objects": [p.as_dict() for p in poses]}
    (out / f"{stem}_{a.mode}_poses.json").write_text(json.dumps(report, indent=2))

    print(f"Found {len(poses)} object(s)")
    for i, p in enumerate(poses):
        d = p.as_dict()
        tag = f"{d['label']} {d['confidence']:.2f} " if "label" in d else ""
        print(f"  #{i}: {tag}center={d['center_xy']} angle={d['angle_deg']} deg "
              f"long={d['long_len_px']}px short={d['short_len_px']}px")
    print(f"Saved to {out.resolve()}")

    if a.show:
        cv2.imshow("pose", vis)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
