import cv2 as cv
import numpy as np


# 1. 读取图片
image = cv.imread("object_Pose_estimation/images/headphone.JPG")

if image is None:
    print("图片读取失败，请检查文件路径。")
    raise SystemExit


# 2. 转换为灰度图
gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)


# THRESH_BINARY 会把亮度高于阈值的区域变成白色。
threshold_value = 128

_, mask = cv.threshold(
    gray,
    threshold_value,
    255,
    cv.THRESH_BINARY
)


# ===== 新增：清理分割结果 =====
# 开运算：去掉较小的白色噪点
# 闭运算：填补物体内部较小的黑色空隙
kernel = np.ones((5, 5), dtype=np.uint8)

mask = cv.morphologyEx(mask, cv.MORPH_OPEN, kernel)
mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel)


# 3. 寻找外轮廓
contours, hierarchy = cv.findContours(
    mask,
    cv.RETR_EXTERNAL,
    cv.CHAIN_APPROX_SIMPLE
)

result = image.copy()

for contour in contours:
    area = cv.contourArea(contour)

    # 过滤较小的噪点；如果噪点仍然很多，可以调大这个值
    if area < 500:
        continue

    # 绘制绿色轮廓
    cv.drawContours(result, [contour], -1, (0, 255, 0), 2)


    # 4. 提取当前物体的像素
    object_mask = np.zeros_like(mask)

    # 将当前轮廓内部填充为白色
    cv.drawContours(object_mask, [contour], -1, 255, cv.FILLED)

    # 与原始掩膜相交，保留物体的白色像素
    object_mask = cv.bitwise_and(object_mask, mask)

    # NumPy 返回的是 (行, 列)，即 (y, x)
    rows, columns = np.nonzero(object_mask)

    if len(rows) < 2:
        continue

    # 转换为 OpenCV 使用的 (x, y)
    points = np.column_stack((columns, rows)).astype(np.float64)


    # 5. PCA：计算中心、长轴和短轴
    center = np.mean(points, axis=0)
    centered_points = points - center

    _, _, axes = np.linalg.svd(centered_points, full_matrices=False)

    long_axis = axes[0]
    short_axis = axes[1]

    print("物体面积：", area)
    print("物体中心：", center)
    print("长轴方向：", long_axis)
    print("短轴方向：", short_axis)


    # 6. 绘制中心和坐标轴
    center_point = tuple(np.round(center).astype(int))

    long_end = tuple(np.round(center + long_axis * 50).astype(int))
    short_end = tuple(np.round(center + short_axis * 50).astype(int))

    # 白点：物体中心
    cv.circle(result, center_point, 4, (255, 255, 255), -1)

    # 蓝色箭头：长轴；黄色箭头：短轴
    cv.arrowedLine(result, center_point, long_end, (255, 0, 0), 2)
    cv.arrowedLine(result, center_point, short_end, (0, 255, 255), 2)


    # 7. 计算夹爪位置
    # 将每个像素相对中心的位置投影到短轴上
    projections = centered_points @ short_axis

    # 得到物体沿短轴方向的两侧边界
    short_min = np.min(projections)
    short_max = np.max(projections)

    # 夹爪和物体之间预留的距离，单位：像素
    padding = 10

    # 两根手指的中心，分别位于物体短轴两侧
    finger_a = center + short_axis * (short_min - padding)
    finger_b = center + short_axis * (short_max + padding)

    # 手指沿长轴方向延伸，全长为 30 像素
    half_finger = long_axis * 15

    a_start = tuple(np.round(finger_a - half_finger).astype(int))
    a_end = tuple(np.round(finger_a + half_finger).astype(int))

    b_start = tuple(np.round(finger_b - half_finger).astype(int))
    b_end = tuple(np.round(finger_b + half_finger).astype(int))

    # 红色：夹爪手指和连接线
    cv.line(result, a_start, a_end, (0, 0, 255), 3)
    cv.line(result, b_start, b_end, (0, 0, 255), 3)
    cv.line(result, a_start, b_start, (0, 0, 255), 2)


# 8. 显示结果
cv.imshow("Original", image)
cv.imshow("Mask", mask)
cv.imshow("Pose", result)

cv.waitKey(0)
cv.destroyAllWindows()
