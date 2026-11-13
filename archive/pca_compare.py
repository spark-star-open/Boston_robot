"""Three ways to get the same pose, all through PCA + a parallel-jaw gripper.

  1. colour threshold        (HSV/BGR, what the report used)
  2. grayscale + colour      (the brief asks for grayscale too)
  3. YOLOv8n-seg mask        (the brief's "next step")

Each panel is cropped around the object so the gripper stays readable.
"""
import glob
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "track1_assets", "raw")
GT = os.path.join(HERE, "track1_assets", "gt")
PRED = os.path.join(HERE, "track1_assets", "repro")
OUT = os.path.join(HERE, "track1_assets", "gripper")
os.makedirs(OUT, exist_ok=True)

GREEN = (60, 200, 60)
PAD = 130


def rd(p, gray=False):
    return cv2.imdecode(np.fromfile(p, np.uint8),
                        cv2.IMREAD_GRAYSCALE if gray else cv2.IMREAD_COLOR)


def photo_for(tag):
    hit = glob.glob(os.path.join(RAW, f"s01_{'portrait' if tag == 'dark' else 'landscape'}_*.jpg"))
    return hit[0] if hit else None


def keep_largest(mask):
    """PCA 用 ptp 求跨度，几个游离像素就能把轴拉到天边，先只留最大连通域。"""
    n, lab, stats, _ = cv2.connectedComponentsWithStats((mask > 127).astype(np.uint8), 8)
    if n <= 1:
        return mask
    big = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    return np.where(lab == big, 255, 0).astype(np.uint8)


def pca_pose(mask):
    ys, xs = np.nonzero(mask)
    if len(xs) < 80:
        return None
    pts = np.column_stack([xs, ys]).astype(np.float64)      # (x, y) -- 见 README 的坑
    centre = pts.mean(axis=0)
    centred = pts - centre
    vals, vecs = np.linalg.eigh(np.cov(centred.T))
    order = vals.argsort()[::-1]
    v_long, v_short = vecs[:, order[0]], vecs[:, order[1]]
    if v_long[1] < 0:
        v_long = -v_long
    length = np.ptp(centred @ v_long)
    width = np.ptp(centred @ v_short)
    angle = np.degrees(np.arctan2(v_long[1], v_long[0]))
    if angle > 90:
        angle -= 180
    return dict(centre=centre, v_long=v_long, v_short=v_short,
                length=length, width=width, angle=angle,
                ratio=vals[order[0]] / max(vals[order[1]], 1e-9))


def draw(img, pose, colour=GREEN, clearance=5):
    c, vl, vs = pose["centre"], pose["v_long"], pose["v_short"]
    L, W = pose["length"], pose["width"]

    def pt(a, b):
        return tuple(np.round(c + vl * a + vs * b).astype(int))

    cv2.line(img, pt(-L / 2, 0), pt(L / 2, 0), (255, 170, 60), 2)
    cv2.line(img, pt(0, -W / 2), pt(0, W / 2), (90, 90, 240), 2)
    half, reach = W / 2 + clearance, L / 2 * 0.60
    for s in (-1, 1):
        cv2.line(img, pt(-reach, s * half), pt(reach, s * half), colour, 4)
    wrist = -reach - 22
    cv2.line(img, pt(wrist, -half), pt(wrist, half), colour, 4)
    cv2.line(img, pt(wrist, 0), pt(-reach, 0), colour, 4)
    cv2.circle(img, tuple(np.round(c).astype(int)), 6, (0, 0, 255), -1)
    return img


def panel(photo, mask, title, crop):
    x0, y0, x1, y1 = crop
    view = photo[y0:y1, x0:x1].copy()
    sub = np.zeros_like(view)
    m = mask[y0:y1, x0:x1]
    sub[m > 0] = (0, 255, 255)
    view = cv2.addWeighted(view, 1.0, sub, 0.18, 0)
    pose = pca_pose(mask)
    if pose is None:
        cv2.putText(view, "empty", (14, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (60, 60, 200), 2)
        info = "no mask"
    else:
        p2 = dict(pose)
        p2["centre"] = pose["centre"] - np.array([x0, y0])
        draw(view, p2)
        info = f"{pose['angle']:+.1f}deg  L{pose['length']:.0f}/W{pose['width']:.0f}"
    bar = np.full((46, view.shape[1], 3), 255, np.uint8)
    cv2.putText(bar, title, (12, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (30, 40, 55), 1)
    cv2.putText(bar, info, (12, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (90, 100, 120), 1)
    return np.vstack([bar, view])


def gray_and_colour_masks(img, obj):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    dark = (gray < 140).astype(np.uint8) * 255          # 比背景暗的都算候选
    if obj == "green":
        hue = cv2.inRange(hsv, np.array([40, 60, 40]), np.array([75, 255, 255]))
    else:
        hue = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 255, 80]))
    m = cv2.bitwise_and(dark, hue)
    k = np.ones((5, 5), np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)
    return m


rows = []
for tag in ("dark", "light"):
    pp = photo_for(tag)
    if not pp:
        continue
    photo = rd(pp)
    for obj in ("green", "black"):
        gt = rd(os.path.join(GT, f"{tag}_{obj}.png"), gray=True)
        if gt is None:
            continue
        gt = (gt > 127).astype(np.uint8) * 255
        colour = rd(os.path.join(PRED, f"{tag}_{'hsv' if tag else 'hsv'}_{obj}_mask.png"), gray=True)
        colour = keep_largest(((colour > 127).astype(np.uint8) * 255)) if colour is not None else np.zeros_like(gt)
        grayc = keep_largest(gray_and_colour_masks(photo, obj))
        yolo_p = os.path.join(PRED, f"{tag}_yolo_{obj}_mask.png")
        yolo = rd(yolo_p, gray=True) if os.path.exists(yolo_p) else None
        yolo = keep_largest(((yolo > 127).astype(np.uint8) * 255)) if yolo is not None else np.zeros_like(gt)

        ys, xs = np.nonzero(gt)
        crop = (max(0, xs.min() - PAD), max(0, ys.min() - PAD),
                min(photo.shape[1], xs.max() + PAD), min(photo.shape[0], ys.max() + PAD))

        panels = [panel(photo, colour, "colour threshold", crop),
                  panel(photo, grayc, "grayscale + colour", crop),
                  panel(photo, yolo, "YOLO seg + PCA", crop)]
        h = min(p.shape[0] for p in panels)
        panels = [p[:h] for p in panels] if all(p.shape[0] == h for p in panels) else panels
        out = np.hstack(panels)
        path = os.path.join(OUT, f"{tag}_{obj}_methods.jpg")
        cv2.imencode(".jpg", out, [cv2.IMWRITE_JPEG_QUALITY, 92])[1].tofile(path)

        for name, m in (("colour", colour), ("gray+colour", grayc), ("yolo", yolo)):
            pose = pca_pose(m)
            if pose:
                rows.append((tag, obj, name, pose["centre"], pose["angle"],
                             pose["length"], pose["width"], pose["ratio"]))
                print(f"{tag:5s} {obj:5s} {name:12s} centre=({pose['centre'][0]:6.1f},"
                      f"{pose['centre'][1]:6.1f})  angle={pose['angle']:+6.1f}  "
                      f"L={pose['length']:6.1f} W={pose['width']:6.1f}  ratio={pose['ratio']:.2f}")
            else:
                print(f"{tag:5s} {obj:5s} {name:12s} — no mask")
        print(f"      -> {os.path.basename(path)}")
