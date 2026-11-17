"""第 1 课：认识一张图。

跑法：D:\\python\\python.exe step1_image.py
"""
import cv2
import numpy as np

# 1. 照片在哪里（字符串，前面加 r 表示「别把反斜杠当转义符」）
path = r"C:\Users\30217\Desktop\ds工作\其他\track1_assets\raw\s01_portrait_1024x1460_cec769fe10.jpg"

# 2. 读进来，变成一个数组（这行先当咒语背下来，第 4 课再拆）
img = cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_COLOR)

# 3. 看看它长什么样
print("形状：", img.shape)
print("左上角那个像素：", img[0, 0])
print("豆子中间那个像素：", img[335, 519])
print("黑橡皮上面那个像素：", img[1090, 680])
