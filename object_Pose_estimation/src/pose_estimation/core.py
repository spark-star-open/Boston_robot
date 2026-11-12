"""Core algorithm: segmentation -> contours -> PCA -> parallel-jaw gripper.

Date: 2026-11-12

Coordinate convention (the classic trap, see Peter's tip):
    * NumPy arrays are indexed (row, col) == (y, x)
    * OpenCV drawing / contour functions use (x, y)
All points inside this module are kept in (x, y) order. The single place where
(row, col) is converted to (x, y) is `mask_to_xy`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

import cv2
import numpy as np


# --------------------------------------------------------------------------- #
# Data structure
# --------------------------------------------------------------------------- #
@dataclass
class ObjectPose:
    """Pose of one object in the image (all in pixel units, (x, y) order)."""

    center: np.ndarray            # (2,) centroid
    long_axis: np.ndarray         # (2,) unit vector of 1st principal component
    short_axis: np.ndarray        # (2,) unit vector of 2nd principal component
    long_len: float               # extent of the object along the long axis
    short_len: float              # extent of the object along the short axis
    angle_deg: float              # long-axis angle, image coords, in (-90, 90]
    area: float                   # pixel count of the object
    mask: np.ndarray = field(repr=False, default=None)  # bool (H, W)
    # optional detector info (filled by the YOLO backend)
    label: Optional[str] = None                         # class name, e.g. "mouse"
    conf: Optional[float] = None                        # detection confidence 0-1
    box: Optional[Tuple[int, int, int, int]] = None     # (x1, y1, x2, y2)

    def as_dict(self) -> dict:
        extra = {}
        if self.label is not None:
            extra = {"label": self.label, "confidence": round(float(self.conf), 3),
                     "box_xyxy": [int(v) for v in self.box]}
        return {**extra,
            "center_xy": [round(float(v), 2) for v in self.center],
            "angle_deg": round(float(self.angle_deg), 2),
            "long_len_px": round(float(self.long_len), 2),
            "short_len_px": round(float(self.short_len), 2),
            "area_px": int(self.area),
        }


# --------------------------------------------------------------------------- #
# Step 1: segmentation (grayscale + colour thresholding)
# --------------------------------------------------------------------------- #
def segment_gray(img_bgr: np.ndarray, thresh: Optional[int] = None,
                 invert: Optional[bool] = None) -> np.ndarray:
    """Grayscale threshold. `thresh=None` -> Otsu.

    `invert=None` -> automatic: the object is assumed to be the *minority*
    class, so we flip the mask if more than half of the image is foreground.
    Returns a uint8 mask (0 / 255).
    """
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    if thresh is None:
        _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        _, mask = cv2.threshold(gray, thresh, 255, cv2.THRESH_BINARY)
    if invert is None:
        invert = (mask > 0).mean() > 0.5
    return cv2.bitwise_not(mask) if invert else mask


def segment_color(img_bgr: np.ndarray, lower_hsv: Sequence[int],
                  upper_hsv: Sequence[int]) -> np.ndarray:
    """HSV colour threshold (OpenCV HSV: H 0-179, S/V 0-255)."""
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    return cv2.inRange(hsv, np.array(lower_hsv, np.uint8), np.array(upper_hsv, np.uint8))


def estimate_background(img_bgr: np.ndarray, scale: int = 8, iters: int = 6) -> np.ndarray:
    """Estimate the table colour per pixel as a smooth quadratic surface in Lab.

    The surface is fitted with iterative outlier rejection, so the objects
    (which differ strongly from the table) are ignored while uneven light /
    vignetting is modelled. Returns a float32 Lab image of the input size.
    """
    h, w = img_bgr.shape[:2]
    small = cv2.resize(img_bgr, (max(8, w // scale), max(8, h // scale)),
                       interpolation=cv2.INTER_AREA)
    lab = cv2.cvtColor(small, cv2.COLOR_BGR2LAB).astype(np.float32)
    sh, sw = lab.shape[:2]

    def design(xs, ys):
        x, y = xs / max(sw - 1, 1) - 0.5, ys / max(sh - 1, 1) - 0.5
        return np.stack([np.ones_like(x), x, y, x * x, x * y, y * y], axis=-1)

    gy, gx = np.mgrid[0:sh, 0:sw].astype(np.float32)
    A_small = design(gx, gy).reshape(-1, 6)
    Y = lab.reshape(-1, 3)
    inlier = np.ones(len(Y), bool)
    coef = np.zeros((6, 3), np.float32)
    for _ in range(iters):
        coef, *_ = np.linalg.lstsq(A_small[inlier], Y[inlier], rcond=None)
        res = np.linalg.norm(Y - A_small @ coef, axis=1)
        mad = np.median(res[inlier]) + 1e-6
        new_inlier = res < max(3.0 * 1.4826 * mad, 4.0)
        if new_inlier.sum() < 0.2 * len(Y) or (new_inlier == inlier).all():
            break
        inlier = new_inlier
    gy, gx = np.mgrid[0:h, 0:w].astype(np.float32)
    # evaluate the surface at full resolution (coordinates mapped to small grid)
    A_full = design(gx / scale, gy / scale).reshape(-1, 6)
    return (A_full @ coef).reshape(h, w, 3).astype(np.float32)


def segment_background(img_bgr: np.ndarray, thresh: Optional[float] = None,
                       min_thresh: float = 12.0) -> np.ndarray:
    """Foreground = pixels whose Lab colour differs from the estimated table.

    Unlike plain gray thresholding this finds dark AND bright AND coloured
    objects on a uniform table, and the fitted background removes dark corners.
    `thresh=None` -> Otsu on the colour-distance map, but never below `min_thresh`.
    """
    blur = cv2.GaussianBlur(img_bgr, (5, 5), 0)
    lab = cv2.cvtColor(blur, cv2.COLOR_BGR2LAB).astype(np.float32)
    dist = np.linalg.norm(lab - estimate_background(img_bgr), axis=2)
    if thresh is None:
        d8 = np.clip(dist, 0, 255).astype(np.uint8)
        otsu, _ = cv2.threshold(d8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        thresh = max(float(otsu), min_thresh)
    return ((dist > thresh) * 255).astype(np.uint8)


def fill_holes(mask: np.ndarray) -> np.ndarray:
    """Fill interior holes (e.g. the white logo / face on an object)."""
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = np.zeros_like(mask)
    cv2.drawContours(out, cnts, -1, 255, thickness=cv2.FILLED)
    return out


def clean_mask(mask: np.ndarray, kernel_size: int = 5,
               close_size: Optional[int] = None) -> np.ndarray:
    """Morphological open (remove specks) then close (fill gaps / notches)."""
    close_size = close_size or kernel_size
    ko = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    kc = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_size, close_size))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, ko)
    return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kc)


# --------------------------------------------------------------------------- #
# Step 2: split into objects with cv2.findContours
# --------------------------------------------------------------------------- #
def split_objects(mask: np.ndarray, min_area: int = 500,
                  drop_border: bool = False, hull: bool = False) -> List[np.ndarray]:
    """Return one boolean mask per external contour with area >= min_area.

    drop_border=True discards blobs touching the image border (usually
    vignetting / table-edge artefacts rather than whole objects).
    hull=True replaces each blob by its convex hull (fills notches caused by
    highlights / logos on convex objects such as a mouse).
    """
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    h, w = mask.shape[:2]
    out = []
    for c in contours:
        if cv2.contourArea(c) < min_area:
            continue
        if drop_border:
            x, y, bw, bh = cv2.boundingRect(c)
            if x <= 0 or y <= 0 or x + bw >= w or y + bh >= h:
                continue
        if hull:
            c = cv2.convexHull(c)
        single = np.zeros(mask.shape, np.uint8)
        cv2.drawContours(single, [c], -1, 255, thickness=cv2.FILLED)
        out.append(single > 0)
    # sort left-to-right so object ids are stable between runs
    out.sort(key=lambda m: np.nonzero(m)[1].mean())
    return out


# --------------------------------------------------------------------------- #
# Step 3: PCA
# --------------------------------------------------------------------------- #
def mask_to_xy(mask: np.ndarray) -> np.ndarray:
    """Boolean mask -> (N, 2) array of (x, y).

    np.nonzero returns (row, col) = (y, x); we swap here, once and for all.
    """
    rows, cols = np.nonzero(mask)
    return np.column_stack([cols, rows]).astype(np.float64)


def pca_pose(mask: np.ndarray) -> ObjectPose:
    """PCA on the object pixels -> centre, long / short axis and extents."""
    pts = mask_to_xy(mask)
    if len(pts) < 3:
        raise ValueError("Not enough pixels for PCA")
    center = pts.mean(axis=0)
    centered = pts - center
    cov = np.cov(centered.T)
    eigvals, eigvecs = np.linalg.eigh(cov)          # ascending order
    order = np.argsort(eigvals)[::-1]               # big -> small
    long_axis = eigvecs[:, order[0]]
    short_axis = eigvecs[:, order[1]]

    # make the direction deterministic: long axis points to the right
    if long_axis[0] < 0 or (long_axis[0] == 0 and long_axis[1] < 0):
        long_axis = -long_axis
    # short axis = long axis rotated by +90 deg (keeps the frame right-handed)
    short_axis = np.array([-long_axis[1], long_axis[0]])

    proj_l = centered @ long_axis
    proj_s = centered @ short_axis
    angle = np.degrees(np.arctan2(long_axis[1], long_axis[0]))
    if angle <= -90:
        angle += 180
    return ObjectPose(
        center=center, long_axis=long_axis, short_axis=short_axis,
        long_len=float(proj_l.max() - proj_l.min()),
        short_len=float(proj_s.max() - proj_s.min()),
        angle_deg=float(angle), area=float(len(pts)), mask=mask,
    )


def estimate_poses(img_bgr: np.ndarray, mode: str = "gray", min_area: int = 500,
                   thresh: Optional[int] = None, invert: Optional[bool] = None,
                   lower_hsv: Sequence[int] = (0, 80, 60),
                   upper_hsv: Sequence[int] = (179, 255, 255),
                   drop_border: bool = False, hull: bool = False,
                   ) -> Tuple[List[ObjectPose], np.ndarray]:
    """Full classical pipeline. Returns (poses, cleaned_mask)."""
    if mode == "gray":
        mask = segment_gray(img_bgr, thresh, invert)
    elif mode == "color":
        mask = segment_color(img_bgr, lower_hsv, upper_hsv)
    elif mode == "bg":
        mask = segment_background(img_bgr, thresh)
    else:
        raise ValueError(f"unknown mode {mode!r}")
    # 'bg' mode: bigger closing to bridge highlights / logos
    mask = fill_holes(clean_mask(mask, 5, 31 if mode == "bg" else 5))
    return [pca_pose(m) for m in split_objects(mask, min_area, drop_border, hull)], mask


# --------------------------------------------------------------------------- #
# Step 4: gripper geometry + drawing
# --------------------------------------------------------------------------- #
def gripper_geometry(pose: ObjectPose, margin: float = 10.0,
                     finger_len: Optional[float] = None) -> dict:
    """Parallel-jaw gripper that closes along the SHORT axis.

    The two jaws sit at +/- (short_len/2 + margin) from the centre along the
    short axis; each jaw is a finger lying parallel to the long axis.
    """
    half_open = pose.short_len / 2.0 + margin
    if finger_len is None:
        finger_len = max(20.0, 0.25 * pose.long_len)
    c, u, v = pose.center, pose.long_axis, pose.short_axis
    jaw_a = c + v * half_open
    jaw_b = c - v * half_open
    return {
        "opening_px": 2 * half_open,
        "bar": (jaw_a, jaw_b),                          # line joining the jaws
        "finger_a": (jaw_a - u * finger_len / 2, jaw_a + u * finger_len / 2),
        "finger_b": (jaw_b - u * finger_len / 2, jaw_b + u * finger_len / 2),
    }


def _pt(p) -> Tuple[int, int]:
    """(x, y) float -> int tuple for OpenCV."""
    return int(round(p[0])), int(round(p[1]))


def _label(vis, text, org, scale, colour, thick):
    """Text with a filled background so it stays readable on any image."""
    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw, th), base = cv2.getTextSize(text, font, scale, thick)
    x, y = org
    x = int(max(0, min(x, vis.shape[1] - tw - 4)))
    y = int(max(th + base + 2, min(y, vis.shape[0] - 2)))
    cv2.rectangle(vis, (x, y - th - base - 2), (x + tw + 4, y + 2), colour, -1)
    cv2.putText(vis, text, (x + 2, y - base // 2), font, scale, (255, 255, 255),
                thick, cv2.LINE_AA)


def _line(vis, p1, p2, colour, width, arrow=False):
    """Line with a black outline underneath so it is visible on any background."""
    f = cv2.arrowedLine if arrow else cv2.line
    kw = {"tipLength": 0.06} if arrow else {}
    f(vis, _pt(p1), _pt(p2), (0, 0, 0), width + 3, cv2.LINE_AA, **kw)
    f(vis, _pt(p1), _pt(p2), colour, width, cv2.LINE_AA, **kw)


# colours (BGR)
C_LONG, C_SHORT, C_GRIP, C_MASK = (255, 0, 255), (0, 0, 255), (0, 230, 255), (0, 200, 0)


def draw_pose(img_bgr: np.ndarray, pose: ObjectPose, idx: int = 0,
              margin: float = 10.0) -> np.ndarray:
    """Draw mask, box + label (if detected), principal axes and gripper.

    Legend:  magenta = long axis, red = short axis, yellow = parallel-jaw gripper
    (closes along the short axis), green = object mask.
    Line widths / fonts scale with image size.
    """
    vis = img_bgr.copy()
    sc = max(1.0, max(vis.shape[:2]) / 800.0)           # overlay scale factor
    lw = max(3, int(round(3 * sc)))
    fs, ft = 0.6 * sc, max(1, int(round(1.5 * sc)))
    c = pose.center

    # translucent mask fill + contour
    fill = vis.copy()
    fill[pose.mask] = C_MASK
    vis = cv2.addWeighted(fill, 0.20, vis, 0.80, 0)
    cnts, _ = cv2.findContours(pose.mask.astype(np.uint8) * 255,
                               cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(vis, cnts, -1, C_MASK, max(2, lw - 1), cv2.LINE_AA)

    if pose.box is not None:                             # detector box + "class conf"
        x1, y1, x2, y2 = pose.box
        cv2.rectangle(vis, (x1, y1), (x2, y2), (255, 120, 0), lw)
        _label(vis, f"{pose.label} {pose.conf:.2f}", (x1, y1), fs, (255, 120, 0), ft)

    # gripper: bar between the jaws + two thick fingers parallel to the long axis
    g = gripper_geometry(pose, margin)
    _line(vis, g["bar"][0], g["bar"][1], C_GRIP, lw * 3)
    for key in ("finger_a", "finger_b"):
        _line(vis, g[key][0], g[key][1], C_GRIP, lw * 3)
    # principal axes (arrows pointing in the + direction of each eigenvector)
    for axis, length, colour, name in ((pose.long_axis, pose.long_len, C_LONG, "long"),
                                       (pose.short_axis, pose.short_len, C_SHORT, "short")):
        _line(vis, c - axis * length / 2, c + axis * length / 2, colour, lw, arrow=True)
        _label(vis, f"{name} {length:.0f}px", c + axis * (length / 2 + 6 * sc), fs * 0.8, colour, ft)

    cv2.circle(vis, _pt(c), lw * 2, (0, 0, 0), -1)
    cv2.circle(vis, _pt(c), lw * 2 - 1, (255, 255, 255), -1)

    tag = f"{pose.label} " if pose.label else f"#{idx} "
    if pose.box is not None:                             # below the box, no overlap
        org = (pose.box[0], pose.box[3] + int(26 * sc))
    else:
        org = (_pt(c)[0] + 10 * sc, _pt(c)[1] + 22 * sc)
    _label(vis, f"{tag}{pose.angle_deg:.0f} deg", org, fs, (60, 60, 60), ft)
    return vis
