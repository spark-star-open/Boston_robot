"""PCA pose + parallel-jaw gripper -- the piece the Track 1 brief actually asks for.

For each object it prints centre / heading / long-short axes, then draws:
  blue  = long axis (from PCA eigenvectors)
  red   = short axis
  green = parallel-jaw gripper, fingers parallel to the long axis

Run:  D:\\python\\python.exe pca_gripper.py
"""
import glob
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "track1_assets", "raw")
GT = os.path.join(HERE, "track1_assets", "gt")
OUT = os.path.join(HERE, "track1_assets", "gripper")
os.makedirs(OUT, exist_ok=True)


def rd(p, gray=False):
    return cv2.imdecode(np.fromfile(p, np.uint8),
                        cv2.IMREAD_GRAYSCALE if gray else cv2.IMREAD_COLOR)


def photo_for(tag):
    pat = os.path.join(RAW, f"s01_{'portrait' if tag == 'dark' else 'landscape'}_*.jpg")
    hit = glob.glob(pat)
    return hit[0] if hit else None


def pca_pose(mask):
    """Return centre, long-axis unit vector, short-axis unit vector, lengths, angle."""
    ys, xs = np.nonzero(mask)
    if len(xs) < 50:
        return None
    pts = np.column_stack([xs, ys]).astype(np.float64)     # (x, y)
    centre = pts.mean(axis=0)
    centred = pts - centre
    cov = np.cov(centred.T)
    vals, vecs = np.linalg.eigh(cov)                       # 升序
    order = vals.argsort()[::-1]
    v_long = vecs[:, order[0]]
    v_short = vecs[:, order[1]]
    if v_long[1] < 0:                                      # 让长轴指向下方，角度更稳定
        v_long = -v_long
    proj_long = centred @ v_long
    proj_short = centred @ v_short
    length = proj_long.max() - proj_long.min()
    width = proj_short.max() - proj_short.min()
    angle = np.degrees(np.arctan2(v_long[1], v_long[0]))
    if angle > 90:
        angle -= 180
    return centre, v_long, v_short, length, width, angle, (vals[order[0]], vals[order[1]])


def draw_gripper(img, centre, v_long, v_short, length, width, clearance=6, colour=(60, 200, 60)):
    """Two fingers parallel to the long axis, opening across the short axis."""
    half_gap = width / 2 + clearance
    reach = length / 2 * 0.72

    def pt(along, across):
        return tuple(np.round(centre + v_long * along + v_short * across).astype(int))

    for sign in (-1, 1):
        cv2.line(img, pt(-reach, sign * half_gap), pt(reach, sign * half_gap), colour, 5)
    # 手腕：在物体外侧把两根手指连起来
    wrist = -reach - 26
    cv2.line(img, pt(wrist, -half_gap), pt(wrist, half_gap), colour, 5)
    cv2.line(img, pt(wrist, 0), pt(-reach, 0), colour, 5)
    return img


def annotate(img, mask, label, colour=(0, 220, 255)):
    pose = pca_pose(mask)
    vis = img.copy()
    if pose is None:
        cv2.putText(vis, f"{label}: empty mask", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, colour, 2)
        return vis, None
    centre, v_long, v_short, length, width, angle, vals = pose

    # 长短轴
    c = tuple(np.round(centre).astype(int))
    cv2.line(vis, tuple(np.round(centre - v_long * length / 2).astype(int)),
             tuple(np.round(centre + v_long * length / 2).astype(int)), (255, 160, 60), 3)
    cv2.line(vis, tuple(np.round(centre - v_short * width / 2).astype(int)),
             tuple(np.round(centre + v_short * width / 2).astype(int)), (80, 80, 240), 3)
    cv2.circle(vis, c, 7, (0, 0, 255), -1)
    draw_gripper(vis, centre, v_long, v_short, length, width)

    cv2.putText(vis, f"{label}", (16, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (20, 30, 45), 2)
    cv2.putText(vis, f"centre ({centre[0]:.0f},{centre[1]:.0f})  {angle:+.1f} deg",
                (16, 66), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20, 30, 45), 2)
    cv2.putText(vis, f"long {length:.0f} px  short {width:.0f} px",
                (16, 94), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20, 30, 45), 2)
    return vis, (centre, angle, length, width, vals)


for tag in ("dark", "light"):
    pp = photo_for(tag)
    if not pp:
        continue
    photo = rd(pp)
    for obj in ("green", "black"):
        gp = os.path.join(GT, f"{tag}_{obj}.png")
        if not os.path.exists(gp):
            continue
        m = rd(gp, gray=True)
        mask = (m > 127).astype(np.uint8)
        vis, info = annotate(photo, mask, f"{tag} {obj}")
        if info:
            c, ang, L, W, vals = info
            ratio = vals[0] / max(vals[1], 1e-9)
            print(f"{tag:5s} {obj:5s} centre=({c[0]:.1f},{c[1]:.1f})  angle={ang:+.1f}°  "
                  f"long={L:.1f} short={W:.1f}  eig-ratio={ratio:.1f}")
        path = os.path.join(OUT, f"{tag}_{obj}_gripper.jpg")
        cv2.imencode(".jpg", vis, [cv2.IMWRITE_JPEG_QUALITY, 92])[1].tofile(path)

print("\nimgs ->", OUT)
