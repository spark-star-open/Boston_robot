"""Click 4 boxes -> GrabCut turns each into a ground-truth mask.

Usage:  python label_gt.py
  * A window opens for dark.jpg, then light.jpg; for each image you label
    "green" first, then "black".
  * Drag a box loosely around the object (a little margin is fine), release.
  * ENTER / SPACE = accept,  r = redraw,  s = skip this object,  q = quit.
  * Output: outputs/ground_truth/<image>_<object>.png  (+ boxes.json)
"""
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, "data", "raw")
GT = os.path.join(HERE, "outputs", "ground_truth")
os.makedirs(GT, exist_ok=True)

JOBS = [
    ("dark", os.path.join(RAW, "s01_portrait_1024x1460_cec769fe10.jpg"), ["green", "black"]),
    ("light", os.path.join(RAW, "s01_landscape_1444x1024_977db1c8be.jpg"), ["green", "black"]),
]
MAXW, MAXH = 880, 860


def rd(path):
    return cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_COLOR)


def wr(path, img):
    ok, buf = cv2.imencode(".png", img)
    if ok:
        buf.tofile(path)


def grabcut(img, rect):
    x, y, w, h = rect
    pad = int(0.03 * max(w, h))
    x0, y0 = max(0, x - pad), max(0, y - pad)
    x1, y1 = min(img.shape[1] - 1, x + w + pad), min(img.shape[0] - 1, y + h + pad)
    rect = (x0, y0, x1 - x0, y1 - y0)
    mask = np.zeros(img.shape[:2], np.uint8)
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(img, mask, rect, bgd, fgd, 5, cv2.GC_INIT_WITH_RECT)
    out = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    # keep only the largest blob, so stray pixels outside the object drop out
    n, lab, stats, _ = cv2.connectedComponentsWithStats(out, 8)
    if n > 1:
        biggest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        out = np.where(lab == biggest, 255, 0).astype(np.uint8)
    return out


def run(only=None):
    state = {"drag": False, "start": None, "cur": None, "rect": None, "mask": None}
    boxes = {}

    for tag, path, objects in JOBS:
        if only and f"{tag}_" not in only and only != tag:
            continue
        if not os.path.exists(path):
            print(f"[skip] missing {path}")
            continue
        full = rd(path)
        s = min(MAXW / full.shape[1], MAXH / full.shape[0], 1.0)
        disp = cv2.resize(full, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)

        for obj in objects:
            state.update(rect=None, mask=None, drag=False)

            def on_mouse(event, x, y, flags, _param):
                if event == cv2.EVENT_LBUTTONDOWN:
                    state["drag"], state["start"], state["cur"] = True, (x, y), (x, y)
                elif event == cv2.EVENT_MOUSEMOVE and state["drag"]:
                    state["cur"] = (x, y)
                elif event == cv2.EVENT_LBUTTONUP and state["drag"]:
                    state["drag"] = False
                    x0, y0 = state["start"]
                    if abs(x - x0) > 8 and abs(y - y0) > 8:
                        state["rect"] = (min(x0, x), min(y0, y), abs(x - x0), abs(y - y0))

            win = f"label {tag}.jpg / {obj}"
            cv2.namedWindow(win, cv2.WINDOW_AUTOSIZE)
            cv2.setMouseCallback(win, on_mouse)
            print(f"\n== {tag}.jpg  ->  {obj} ==\n"
                  f"   drag a box around the {obj} object; ENTER=accept  r=redraw  s=skip  q=quit")

            while True:
                view = disp.copy()
                if state["rect"] and state["mask"] is None:
                    x, y, w, h = state["rect"]
                    sx, sy = 1 / s, 1 / s
                    state["mask"] = grabcut(full, (int(x * sx), int(y * sy), int(w * sx), int(h * sy)))
                if state["mask"] is not None:
                    small = cv2.resize(state["mask"], (disp.shape[1], disp.shape[0]),
                                       interpolation=cv2.INTER_NEAREST)
                    tint = np.zeros_like(disp)
                    tint[small > 0] = (0, 255, 255)
                    view = cv2.addWeighted(view, 1.0, tint, 0.35, 0)
                    cnts, _ = cv2.findContours(small, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    cv2.drawContours(view, cnts, -1, (0, 255, 255), 2)
                if state["drag"] and state["start"] and state["cur"]:
                    cv2.rectangle(view, state["start"], state["cur"], (0, 255, 0), 1)
                cv2.imshow(win, view)
                k = cv2.waitKey(20) & 0xFF
                if k in (13, 32) and state["mask"] is not None:
                    wr(os.path.join(GT, f"{tag}_{obj}.png"), state["mask"])
                    boxes[f"{tag}_{obj}"] = list(state["rect"])
                    print(f"   saved {tag}_{obj}.png  ({int((state['mask'] > 0).sum())} px)")
                    break
                if k == ord("r"):
                    state.update(rect=None, mask=None)
                elif k == ord("s"):
                    print("   skipped")
                    break
                elif k in (ord("q"), 27):
                    cv2.destroyAllWindows()
                    print("   aborted")
                    with open(os.path.join(GT, "boxes.json"), "w", encoding="utf-8") as f:
                        json.dump(boxes, f, indent=2)
                    return
            cv2.destroyWindow(win)

    cv2.destroyAllWindows()
    with open(os.path.join(GT, "boxes.json"), "w", encoding="utf-8") as f:
        json.dump(boxes, f, indent=2)
    print(f"\ndone: {len(boxes)} masks -> {GT}")


if __name__ == "__main__":
    # "python label_gt.py dark_green" re-labels just that one object
    sys.exit(run(sys.argv[1] if len(sys.argv) > 1 else None))
