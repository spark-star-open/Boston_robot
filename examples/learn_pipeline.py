"""一步一步看懂目标检测：从一张照片到一个中心点 + 一个角度。

跑法：
    D:\\python\\python.exe learn_pipeline.py

它什么也不预测，只是把同一条流水线拆成 5 个台阶，每个台阶存一张图到
outputs/learn/，你可以按 1→5 的顺序打开，对着看每一步到底发生了什么。
"""
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, "data", "raw", "s01_portrait_1024x1460_cec769fe10.jpg")
OUT = os.path.join(HERE, "outputs", "learn")
os.makedirs(OUT, exist_ok=True)


def read(path):
    """cv2.imread 读不了中文路径，所以先按字节读进来再解码。"""
    return cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_COLOR)


def save(name, img):
    cv2.imencode(".jpg", img)[1].tofile(os.path.join(OUT, name))


img = read(SRC)

# ---------------------------------------------------------------- 台阶 1
# 一张彩色图在内存里就是一个「高 × 宽 × 3」的数字表格，每个数字 0~255。
print("【台阶 1】图像本身")
print("  形状 =", img.shape, "   dtype =", img.dtype)
print("  含义：高", img.shape[0], "像素、宽", img.shape[1], "像素、每像素 3 个通道")
print("  像素(0,0) 的值 =", img[0, 0], " ← 注意顺序是 B, G, R，不是 R, G, B")
save("1_原图.jpg", img)

# ---------------------------------------------------------------- 台阶 2
# 颜色阈值：把「绿色」翻译成数字区间，逐像素判断「在不在区间里」。
# 得到一个二值图（mask）：白=命中，黑=不命中。
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
lower = np.array([40, 40, 40])     # H 下限, S 下限, V 下限
upper = np.array([70, 255, 255])   # H 上限, S 上限, V 上限
mask = cv2.inRange(hsv, lower, upper)

print("\n【台阶 2】颜色阈值 inRange")
print("  mask 形状 =", mask.shape, " 取值只有", np.unique(mask))
print("  白色像素 =", int((mask > 0).sum()), "个，占全图",
      round((mask > 0).mean() * 100, 2), "%")
save("2_掩码.jpg", mask)

# ---------------------------------------------------------------- 台阶 3
# 掩码往往有毛刺和空洞：开运算(先腐蚀后膨胀)去小白点，闭运算(先膨胀后腐蚀)补小黑洞。
kernel = np.ones((5, 5), np.uint8)      # 5×5 的方块，就是「看多大范围的邻居」
opened = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)
print("\n【台阶 3】形态学开/闭")
print("  原始白点 =", int((mask > 0).sum()),
      "→ 开后 =", int((opened > 0).sum()),
      "→ 闭后 =", int((closed > 0).sum()))
save("3_开闭运算后.jpg", closed)

# ---------------------------------------------------------------- 台阶 4
# 找轮廓：沿着白色区域的边界走一圈，返回一串点。
contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
print("\n【台阶 4】找轮廓 findContours")
print("  轮廓数量 =", len(contours), "（包括面积很小的噪点）")
for i, c in enumerate(contours):
    print(f"    #{i} 点数={len(c):4d}  面积={cv2.contourArea(c):8.1f}")

vis = img.copy()
cv2.drawContours(vis, contours, -1, (0, 255, 255), 3)   # 全部画一遍
save("4_所有轮廓.jpg", vis)

# ---------------------------------------------------------------- 台阶 5
# 面积过滤 + 最小外接矩形：矩形给出中心、尺寸、旋转角，这就是「平面位姿」。
MIN_AREA = 300
print("\n【台阶 5】面积过滤 + minAreaRect")
vis2 = img.copy()
for c in contours:
    area = cv2.contourArea(c)
    if area < MIN_AREA:
        continue
    (cx, cy), (w, h), angle = cv2.minAreaRect(c)
    box = cv2.boxPoints(((cx, cy), (w, h), angle))
    box = np.int32(box)
    cv2.drawContours(vis2, [box], 0, (0, 255, 255), 3)
    cv2.circle(vis2, (int(cx), int(cy)), 8, (0, 0, 255), -1)
    cv2.putText(vis2, f"({cx:.0f},{cy:.0f}) {angle:.1f}deg",
                (int(cx) - 90, int(cy) - 20), cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (0, 0, 255), 2)
    print(f"  面积={area:8.1f}  中心=({cx:.1f}, {cy:.1f})  "
          f"尺寸=({w:.1f}x{h:.1f})  角度={angle:.1f}°")
save("5_中心与角度.jpg", vis2)

print("\n完成。打开 outputs/learn/ 里的 1~5 号图，对着看每一步的产物。")
