"""Generate the figures used by the beginner tutorial document."""
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "track1_assets", "raw", "s01_portrait_1024x1460_cec769fe10.jpg")
OUT = os.path.join(HERE, "track1_assets", "learn")
os.makedirs(OUT, exist_ok=True)

GUTTER = 16
LABEL_BG = (25, 37, 56)


def rd(p):
    return cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)


def wr(name, img):
    cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 92])[1].tofile(os.path.join(OUT, name))
    print("wrote", name, img.shape[1], "x", img.shape[0])


def badge(img, text):
    h = int(img.shape[0] * 0.09) or 20
    fs = max(0.5, h / 44)
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, fs, 2)
    cv2.rectangle(img, (0, 0), (tw + 18, h), LABEL_BG, -1)
    cv2.putText(img, text, (9, int(h * 0.74)), cv2.FONT_HERSHEY_SIMPLEX, fs, (255, 255, 255), 2)
    return img


def hstack(panels, labels=None, height=None):
    panels = [cv2.cvtColor(p, cv2.COLOR_GRAY2BGR) if p.ndim == 2 else p for p in panels]
    if height:
        panels = [cv2.resize(p, (int(p.shape[1] * height / p.shape[0]), height),
                             interpolation=cv2.INTER_AREA) for p in panels]
    panels = [cv2.copyMakeBorder(p, 0, 0, 0, 0, cv2.BORDER_CONSTANT)
              for p in panels]
    if labels:
        for p, lab in zip(panels, labels):
            badge(p, lab)
    w = sum(p.shape[1] for p in panels) + GUTTER * (len(panels) - 1)
    h = max(p.shape[0] for p in panels)
    canvas = np.full((h, w, 3), 255, np.uint8)
    x = 0
    for p in panels:
        canvas[:p.shape[0], x:x + p.shape[1]] = p
        x += p.shape[1] + GUTTER
    return canvas


img = rd(RAW)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
mask = cv2.inRange(hsv, np.array([40, 40, 40]), np.array([70, 255, 255]))
k5 = np.ones((5, 5), np.uint8)
opened = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k5)
closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, k5)

# 目标区域裁剪（豆子 + 边距）
x0, y0, x1, y1 = 400, 180, 640, 500
crop = img[y0:y1, x0:x1]
crop_mask = mask[y0:y1, x0:x1]

# ---- fig 1: 整图 + 放大后的像素块
thumb = cv2.resize(img, (300, 428), interpolation=cv2.INTER_AREA)
px = img[248:268, 436:456]
px_big = cv2.resize(px, None, fx=20, fy=20, interpolation=cv2.INTER_NEAREST)[:400, :400]
for gx in range(0, px_big.shape[1], 20):      # 每 20 像素画一条格线 = 一格一个像素
    cv2.line(px_big, (gx, 0), (gx, px_big.shape[0]), (210, 210, 210), 1)
for gy in range(0, px_big.shape[0], 20):
    cv2.line(px_big, (0, gy), (px_big.shape[1], gy), (210, 210, 210), 1)
wr("fig1_array.jpg", hstack([thumb, px_big], ["A  the image", "B  x20 pixels"]))

# ---- fig 2: 原图 vs 掩码
wr("fig2_mask.jpg", hstack([crop, cv2.cvtColor(crop_mask, cv2.COLOR_GRAY2BGR)],
                           ["A  photo", "B  mask"]))

# ---- fig 3: 形态学示意（合成，含椒盐噪声）
rng = np.random.default_rng(7)
demo = np.zeros((300, 300), np.uint8)
cv2.ellipse(demo, (150, 150), (88, 120), -35, 0, 360, 255, -1)
noise = rng.random((300, 300))
demo[noise > 0.985] = 255          # 3000 个白色噪点
demo[noise < 0.004] = 0            # 少量黑洞
d_open = cv2.morphologyEx(demo, cv2.MORPH_OPEN, k5)
d_close = cv2.morphologyEx(d_open, cv2.MORPH_CLOSE, k5)
wr("fig3_morph.jpg", hstack([demo, d_open, d_close], ["A  raw", "B  open", "C  open+close"]))

# ---- fig 4: 轮廓
contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
vis = crop.copy()
for c in contours:
    c2 = c - np.array([x0, y0])
    cv2.drawContours(vis, [c2], -1, (0, 255, 255), 3)
wr("fig4_contours.jpg", hstack([vis]))

# ---- fig 5: 位姿
(cx, cy), (w, h), ang = cv2.minAreaRect(contours[0])
box = np.int32(cv2.boxPoints(((cx, cy), (w, h), ang)) - np.array([x0, y0]))
vis2 = crop.copy()
cv2.drawContours(vis2, [box], 0, (0, 255, 255), 3)
cv2.circle(vis2, (int(cx - x0), int(cy - y0)), 7, (0, 0, 255), -1)
cv2.putText(vis2, f"({cx:.0f},{cy:.0f})", (int(cx - x0) - 70, int(cy - y0) - 45),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
cv2.putText(vis2, f"{ang:.1f} deg", (int(cx - x0) + 20, int(cy - y0) + 60),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
wr("fig5_pose.jpg", hstack([vis2]))

# ---- fig 6: IoU 示意
a = (60, 70, 200, 200)
b = (130, 120, 260, 240)
canvas = np.full((320, 320, 3), 255, np.uint8)
gt = np.zeros((320, 320), np.uint8)
pr = np.zeros((320, 320), np.uint8)
cv2.rectangle(gt, a[:2], a[2:], 255, -1)
cv2.rectangle(pr, b[:2], b[2:], 255, -1)
inter = cv2.bitwise_and(gt, pr)
union = cv2.bitwise_or(gt, pr)
canvas[union > 0] = (235, 240, 250)
canvas[gt > 0] = (200, 205, 215)
canvas[inter > 0] = (150, 120, 60)
cv2.rectangle(canvas, a[:2], a[2:], (60, 70, 90), 2)
cv2.rectangle(canvas, b[:2], b[2:], (60, 70, 90), 2)
iou = inter.sum() / union.sum()
cv2.putText(canvas, f"IoU = {iou:.3f}", (90, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (30, 40, 55), 2)
wr("fig6_iou.jpg", hstack([canvas]))

print("\nfigures in", OUT)
