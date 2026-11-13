"""Segment one image and draw a PCA pose for each detected region."""
import argparse
from pathlib import Path
import sys
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.segmentation import segment, multi_mask
from src.pose import pca_pose
from src.gripper import draw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    parser.add_argument('--method', choices=['hsv', 'rgb', 'multi'], default='multi')
    parser.add_argument('--object', choices=['green', 'black', 'red'], default='green')
    parser.add_argument('--min-area', type=float, default=1500)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'outputs' / 'pipeline')
    args = parser.parse_args()
    try:
        image = cv2.imdecode(np.fromfile(args.image, np.uint8), cv2.IMREAD_COLOR)
    except OSError as exc:
        parser.error(str(exc))
    if image is None:
        parser.error(f'无法读取图片: {args.image}')
    mask = multi_mask(image) if args.method == 'multi' else segment(image, args.method, args.object)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted((c for c in contours if cv2.contourArea(c) >= args.min_area), key=lambda c: cv2.boundingRect(c)[0])
    result = image.copy()
    for i, contour in enumerate(contours, 1):
        single = np.zeros_like(mask)
        cv2.drawContours(single, [contour], -1, 255, -1)
        pose = pca_pose(single)
        if pose is None:
            continue
        draw(result, pose)
        x, y = pose['centre']
        cv2.putText(result, f'#{i}', (int(x)+10, int(y)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        print(f"#{i} center=({x:.1f}, {y:.1f}) angle={pose['angle']:.1f} deg area={cv2.contourArea(contour):.1f}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for suffix, img in [('mask.png', mask), ('result.jpg', result)]:
        path = args.output_dir / f'{args.image.stem}_{args.method}_{suffix}'
        ok, buf = cv2.imencode(path.suffix, img)
        if not ok:
            raise RuntimeError(f'无法编码 {path}')
        buf.tofile(path)
        print(path)
    print(f'检测到 {len(contours)} 个轮廓')

if __name__ == '__main__':
    main()
