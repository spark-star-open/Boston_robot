# Boston_robot
track 1

---

# Track 1：二维物体识别与夹爪示意

从照片生成颜色掩码、轮廓和二维 PCA 位姿，并绘制平行夹爪示意。位置是图像像素坐标，角度是图像平面方向；本项目不包含深度估计、相机标定或机器人运动控制。阈值针对现有实验图片，换场景需要重新调整。

## 目录

- `src/`：分割、PCA 位姿、夹爪绘制和评价函数。
- `scripts/`：图片处理、已有掩码评价、交互式标注入口。
- `examples/`：分步教学示例。
- `data/raw/`：原始图片；`data/ground_truth/`：原实验的半自动标注。
- `outputs/`：生成结果；`outputs/repro/` 保存原实验的 RGB、HSV、YOLO 掩码。
- `reports/`：报告、说明及参考资料；`archive/`：原始脚本备份。

原始脚本保存在 `archive/`，原实验素材保存在 `track1_assets/`。旧脚本中有 Windows 绝对路径，不能保证直接运行。

## 环境

需要 Python 3、NumPy 和带图形界面的 OpenCV。终端进入本目录后：

```bash
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

核心入口不需要 YOLO。原有 YOLO 实验脚本在 `archive/`，另外依赖 ultralytics、PyTorch 和模型权重；旧的报告生成脚本另需 python-pptx、python-docx 等，并可能需要修改原始文件路径。

## 运行

```bash
# 暗光示例：一次找绿色和深色物体
python scripts/run_pipeline.py data/raw/s01_portrait_1024x1460_cec769fe10.jpg
# 单一颜色；RGB 方法内部实际使用 OpenCV 的 BGR 通道顺序
python scripts/run_pipeline.py data/raw/s01_portrait_1024x1460_cec769fe10.jpg --method hsv --object green --min-area 300
# 阅读中间步骤，输出到 outputs/learn/
python examples/learn_pipeline.py
# 比较已有真值和预测掩码
python scripts/evaluate.py
```

处理结果默认写入 `outputs/pipeline/`，同名输入及方法再次运行会覆盖同名结果；可用 `--output-dir` 指定其他目录。`--method multi` 使用原多物体实验的绿色及灰度阈值，`rgb` / `hsv` 使用原单颜色实验的阈值。用 `--help` 查看参数。

评价默认读取 `data/ground_truth/` 和 `outputs/repro/`，可通过 `--gt`、`--pred`、`--methods` 更改。它比较已经存在的掩码，并不运行 YOLO 或生成预测。IoU 为交集除以并集；中心误差单位是像素，方向误差单位是度。近方形或空掩码的角度不可用。原标注包含部分阴影，评价只反映这组样本和标注。

```bash
# 鼠标拖框，Enter/空格接受，r 重画，s 跳过，q 退出
python scripts/label_ground_truth.py
python scripts/label_ground_truth.py dark_green
```

标注需要桌面图形环境，写到 `outputs/ground_truth/` 而不是覆盖原始真值；重标同名目标会覆盖该输出，`boxes.json` 每次运行会重写。如需评估新标注，使用 `python scripts/evaluate.py --gt outputs/ground_truth`。
