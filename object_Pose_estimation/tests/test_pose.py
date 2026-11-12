"""Unit tests. Date: 2026-11-12   Run:  pytest -q"""
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pose_estimation import (draw_pose, estimate_poses, gripper_geometry,  # noqa: E402
                             mask_to_xy)


def make_img(cx, cy, L, S, ang):
    img = np.full((400, 500, 3), 230, np.uint8)
    box = cv2.boxPoints(((cx, cy), (L, S), ang)).astype(np.int32)
    cv2.fillPoly(img, [box], (30, 30, 150))
    return img


def angle_diff(a, b):
    d = abs(a - b) % 180
    return min(d, 180 - d)


@pytest.mark.parametrize("ang", [0, 30, 60, 90, -30, -60])
def test_angle_and_center(ang):
    img = make_img(250, 200, 200, 60, ang)
    poses, _ = estimate_poses(img)
    assert len(poses) == 1
    p = poses[0]
    assert angle_diff(p.angle_deg, ang) < 2.0
    assert np.allclose(p.center, [250, 200], atol=2.0)
    assert abs(p.long_len - 200) < 6 and abs(p.short_len - 60) < 6


def test_multiple_objects():
    img = make_img(120, 120, 120, 40, 20)
    cv2.fillPoly(img, [cv2.boxPoints(((380, 280), (140, 50), -40)).astype(np.int32)], (30, 30, 150))
    poses, _ = estimate_poses(img)
    assert len(poses) == 2
    assert poses[0].center[0] < poses[1].center[0]      # sorted left -> right


def test_xy_order_not_swapped():
    """mask_to_xy must return (x, y), not (row, col)."""
    m = np.zeros((10, 20), bool)
    m[2, 15] = True                                      # row 2, col 15
    assert mask_to_xy(m)[0].tolist() == [15, 2]


def test_gripper_is_on_short_axis():
    img = make_img(250, 200, 200, 60, 0)                 # horizontal bar
    p = estimate_poses(img)[0][0]
    g = gripper_geometry(p, margin=10)
    a, b = g["bar"]
    assert abs(a[0] - b[0]) < 2                          # jaws stacked vertically
    assert abs(abs(a[1] - b[1]) - (p.short_len + 20)) < 1e-6


def test_draw_does_not_modify_input():
    img = make_img(250, 200, 200, 60, 15)
    ref = img.copy()
    p = estimate_poses(img)[0][0]
    vis = draw_pose(img, p)
    assert np.array_equal(img, ref) and not np.array_equal(vis, ref)


def test_bg_mode_dark_and_bright_objects_with_vignette():
    """'bg' mode must find a dark AND a bright object on a table with dark corners."""
    h, w = 400, 500
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot(xx - w / 2, yy - h / 2) / np.hypot(w / 2, h / 2)
    img = np.repeat((190 - 50 * r ** 2)[..., None], 3, axis=2).astype(np.uint8)
    cv2.fillPoly(img, [cv2.boxPoints(((150, 200), (160, 60), 30)).astype(np.int32)], (30, 30, 30))
    cv2.fillPoly(img, [cv2.boxPoints(((350, 200), (160, 60), -40)).astype(np.int32)], (60, 230, 250))
    poses, _ = estimate_poses(img, mode="bg")
    assert len(poses) == 2
    assert angle_diff(poses[0].angle_deg, 30) < 3 and angle_diff(poses[1].angle_deg, -40) < 3
