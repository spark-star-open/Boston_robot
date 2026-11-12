# Changelog

## 0.4.0 — 2026-11-12
- Fix one object being split into several detections: `--close` (merge fragments, default ~2 % of the long image side), `--min-area-ratio` (drop blobs < 2 % of the largest object), `--min-area` now scales with image size by default

## 0.3.0 — 2026-11-12
- YOLO mode now also saves `*_mask.png` (union of detected masks)
- Clearer overlay: translucent mask, thick outlined arrows for long / short axis with lengths, bold gripper, labels with background
- YOLO mode now draws a detection box with "class confidence" (e.g. `mouse 0.91`) plus the PCA axes / gripper; JSON output includes `label`, `confidence`, `box_xyxy`
- New `--conf` flag for the YOLO confidence threshold
- Overlay line width / font size scale with image size

## 0.2.0 — 2026-11-12
- New `--mode bg`: background-distance segmentation (robust quadratic table model in Lab), fixes mixed dark/coloured objects on a gray table
- New flags `--hull` and `--drop-border`; `fill_holes`; larger closing in bg mode

## 0.1.0 — 2026-11-12
- Initial version: gray/color threshold, `findContours` multi-object split, PCA pose, parallel-jaw gripper drawing
- Optional YOLO segmentation backend (`--mode yolo`)
- Synthetic sample generator and pytest suite
