"""第一课配套：把「图像是数字表格」这件事打印出来看。

    D:\\python\\python.exe learn_01_image.py
"""
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "track1_assets", "raw",
                    "s01_portrait_1024x1460_cec769fe10.jpg")

img = cv2.imdecode(np.fromfile(PATH, np.uint8), cv2.IMREAD_COLOR)

print("1) 读进来的是什么")
print("   类型 :", type(img).__name__, "（一个 numpy 数组，不是文件）")
print("   形状 :", img.shape)
print("   形状拆开 :", img.shape[0], "行  ×", img.shape[1], "列  ×", img.shape[2], "个通道")
print("   数据类型 :", img.dtype, "（无符号 8 位整数，只能装 0~255）")
print("   元素个数 :", img.size, "=", img.shape[0], "×", img.shape[1], "× 3")

print("\n2) 整个数组有多大")
print("   最小 :", img.min(), "   最大 :", img.max())
print("   平均 :", round(float(img.mean()), 1))

print("\n3) 取一个像素")
print("   img[0, 0]      =", img[0, 0], " ← 第 0 行第 0 列，三个数")
print("   也就是 B =", img[0, 0, 0], " G =", img[0, 0, 1], " R =", img[0, 0, 2])
print("   注意顺序是 B、G、R，所以第一个数不是红")

print("\n4) 取一行、一列")
print("   img[0]      的形状 =", img[0].shape, " ← 第一行，1024 个像素，每个 3 个数")
print("   img[:, 0]   的形状 =", img[:, 0].shape, " ← 第一列，1460 个像素")

print("\n5) 取一小块（3 行 3 列），看看原始数字长什么样")
print(img[300:303, 500:503])
print("   ↑ 这三行就是图像里 3×3 个像素的 BGR 值，一一对应表格里的格子")

print("\n6) 换个位置，值就变了")
print("   背景（白纸巾）img[100, 100] =", img[100, 100])
print("   豆子上         img[340, 520] =", img[340, 520])
