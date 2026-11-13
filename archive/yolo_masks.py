"""Fetch yolov8n-seg.pt (direct, then via the local proxy) and run the YOLO baseline.

Writes per-object binary masks for the metric comparison and a rendered overlay
for eyeballing.
"""
import os
import sys

WS = os.path.dirname(os.path.abspath(__file__))
WEIGHTS_DIR = os.path.join(WS, ".weights")
RAW = os.path.join(WS, "track1_assets", "raw")
OUT = os.path.join(WS, "track1_assets", "yolo")
os.makedirs(WEIGHTS_DIR, exist_ok=True)
os.makedirs(OUT, exist_ok=True)
os.environ["YOLO_CONFIG_DIR"] = os.path.join(WS, ".ultralytics")
os.environ["NO_PROXY"] = "*"

W = os.path.join(WEIGHTS_DIR, "yolov8n-seg.pt")
URLS = [
    "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n-seg.pt",
    "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n-seg.pt",
]


def download():
    import requests
    if os.path.exists(W) and os.path.getsize(W) > 6_000_000:
        print("weights already present:", os.path.getsize(W), "bytes")
        return
    for proxy in (None, "http://127.0.0.1:7890"):
        for url in URLS:
            try:
                kw = {"timeout": (10, 120)}
                if proxy:
                    kw["proxies"] = {"http": proxy, "https": proxy}
                r = requests.get(url, stream=True, **kw)
                if r.status_code != 200:
                    print(f"  {r.status_code} {url} (proxy={proxy})")
                    continue
                total = int(r.headers.get("content-length", 0))
                with open(W, "wb") as f:
                    for chunk in r.iter_content(1 << 16):
                        f.write(chunk)
                print(f"downloaded {os.path.getsize(W)} / {total} bytes  proxy={proxy}")
                if os.path.getsize(W) > 6_000_000:
                    return
            except Exception as e:
                print(f"  fail proxy={proxy}: {type(e).__name__}: {e}")
    raise SystemExit("could not download weights")


def main():
    download()

    import cv2
    import numpy as np
    from ultralytics import YOLO

    model = YOLO(W)
    images = {
        "dark": os.path.join(RAW, "s01_portrait_1024x1460_cec769fe10.jpg"),
        "light": os.path.join(RAW, "s01_landscape_1444x1024_977db1c8be.jpg"),
    }

    for tag, path in images.items():
        img = cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_COLOR)
        res = model(img, conf=0.5, verbose=False)[0]
        h, w = img.shape[:2]
        print(f"\n### {tag}.jpg  {w}x{h}  detections={len(res.boxes)}")
        canvas = np.zeros((h, w, 3), np.uint8)
        polys = res.masks.xy if res.masks is not None else []
        for i, box in enumerate(res.boxes):
            cls = model.names[int(box.cls)]
            conf = float(box.conf)
            x1, y1, x2, y2 = [round(float(v), 1) for v in box.xyxy[0]]
            poly = polys[i] if i < len(polys) else np.empty((0, 2))
            area = 0.0
            if len(poly) >= 3:
                p = np.round(poly).astype(np.int32)
                cv2.fillPoly(canvas, [p], (255, 255, 255))
                area = cv2.contourArea(p)
            print(f"  #{i + 1} {cls:12s} conf={conf:.2f} box=({x1},{y1})-({x2},{y2}) mask_area={area:.0f}")

        gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
        cv2.imencode(".png", gray)[1].tofile(os.path.join(OUT, f"{tag}_yolo_all_mask.png"))
        overlay = img.copy()
        overlay[gray > 127] = (0.45 * overlay[gray > 127] + 0.55 * np.array([0, 255, 0])).astype(np.uint8)
        plot = res.plot()
        cv2.imencode(".jpg", np.hstack([overlay, plot]))[1].tofile(
            os.path.join(OUT, f"{tag}_yolo_overlay.jpg"))
        print(f"  union mask px = {int((gray > 127).sum())}")


if __name__ == "__main__":
    sys.exit(main())
