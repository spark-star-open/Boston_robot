# Experiment Notebook

Keep what you tried, screenshots (`results/`) and error messages. One entry per attempt.

## 2026-11-12 — Synthetic sample (baseline)

- **Data:** `data/sample.png` from `make_sample.py` (3 objects, known angles 30 / -45 / 80°)
- **Command:** `python main.py --image data/sample.png`
- **Result:** 3 objects found; angle error ≤ 0.25°, centre error ≤ 0.5 px
- **Screenshot:** `results/sample_gray_pose.png`
- **Note:** `--mode color` with a blue HSV range finds 0 objects (objects are red/green) → HSV range must match the object.

## TODO (own photos)

- [√] Photo of objects on my table → `data/`
- [√ ] Gray vs. color thresholding comparison
- [√ ] Failure case (shadow / touching objects) + screenshot
- [ ] YOLO segmentation + same PCA (`--mode yolo`)
- [ ] One interesting finding to share:

## Errors / fixes

| Date | Error / symptom | Cause | Fix |
|---|---|---|---|
| | | | |
