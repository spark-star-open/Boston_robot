"""One mask, many objects: find every blob, then run PCA + gripper on each.

This is the piece of the brief that says "use cv2.findContours to handle
multiple objects". The mask is the union of every colour we care about, so a
single pass finds all of them; each surviving contour gets its own pose.

    D:\\python\\python.exe multi_object.py                 # 用 dark.jpg
    D:\\python\\python.exe multi_object.py path\\to\\new.jpg  # 用你自己拍的新图
"""
import glob
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "track1_assets", "raw")
OUT = os.path.join(HERE, "track1_assets", "multi")
os.makedirs(OUT, exist_ok=True)

MIN_AREA = 1500          # 比单物体那步的 300 大，因为现在要排除投影和纸褶皱
KERNEL = np.ones((5, 5), np.uint8)


def rd(p):
    return cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)


def build_mask(img):
    """所有「我们要的物体」合成一张掩码：绿色靠色相，深色靠亮度。"""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    green = cv2.inRange(hsv, np.array([35, 60, 40]), np.array([80, 255, 255]))
    dark = cv2.inRange(gray, 0, 85)                    # 黑橡皮 + 它的投影
    mask = cv2.bitwise_or(green, dark)

    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, KERNEL)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, KERNEL)
    return mask


def pca_pose(mask):
    ys, xs = np.nonzero(mask)
    if len(xs) < 80:
        return None
    pts = np.column_stack([xs, ys]).astype(np.float64)      # (x, y)，见底注
    centre = pts.mean(axis=0)
    q = pts - centre
    vals, vecs = np.linalg.eigh(np.cov(q.T))
    order = vals.argsort()[::-1]
    v_long, v_short = vecs[:, order[0]], vecs[:, order[1]]
    if v_long[1] < 0:
        v_long = -v_long
    angle = np.degrees(np.arctan2(v_long[1], v_long[0]))
    if angle > 90:
        angle -= 180
    return dict(centre=centre, v_long=v_long, v_short=v_short,
                length=np.ptp(q @ v_long), width=np.ptp(q @ v_short), angle=angle)


def draw(img, pose, clearance=5, colour=(60, 200, 60)):
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


def run(path, tag):
    img = rd(path)
    mask = build_mask(img)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    kept, dropped = [], []
    for c in contours:
        area = cv2.contourArea(c)
        (kept if area >= MIN_AREA else dropped).append((area, c))

    kept.sort(key=lambda t: cv2.boundingRect(t[1])[0])        # 从左到右编号
    print(f"\n=== {os.path.basename(path)} ===")
    print(f"轮廓总数 {len(contours)}：留下 {len(kept)} 个，丢掉 {len(dropped)} 个"
          f"（面积 < {MIN_AREA}）")
    if dropped:
        print("  丢掉的最小几个面积：", sorted(int(a) for a, _ in dropped)[:6])

    vis = img.copy()
    for i, (area, c) in enumerate(kept, start=1):
        single = np.zeros_like(mask)
        cv2.drawContours(single, [c], -1, 255, -1)             # 每个轮廓单独成一张掩码
        pose = pca_pose(single)
        if pose is None:
            continue
        draw(vis, pose)
        cxy = pose["centre"]
        tag_txt = f"#{i}"
        org = (int(cxy[0]) + 10, int(cxy[1]) - 12)
        (tw, th), _ = cv2.getTextSize(tag_txt, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)
        cv2.rectangle(vis, (org[0] - 6, org[1] - th - 6), (org[0] + tw + 6, org[1] + 8),
                      (255, 255, 255), -1)
        cv2.putText(vis, tag_txt, org, cv2.FONT_HERSHEY_SIMPLEX, 0.9, (20, 30, 45), 2)
        print(f"  #{i} 面积={area:8.1f}  中心=({cxy[0]:6.1f},{cxy[1]:6.1f})  "
              f"朝向={pose['angle']:+6.1f}°  长={pose['length']:5.1f} 短={pose['width']:5.1f}")

    out = os.path.join(OUT, f"{tag}_multi.jpg")
    cv2.imencode(".jpg", vis, [cv2.IMWRITE_JPEG_QUALITY, 92])[1].tofile(out)
    print("  ->", out)


if __name__ == "__main__":
    targets = [sys.argv[1]] if len(sys.argv) > 1 else sorted(
        glob.glob(os.path.join(RAW, "s01_*.jpg")))
    for p in targets:
        run(p, os.path.splitext(os.path.basename(p))[0][:12])
