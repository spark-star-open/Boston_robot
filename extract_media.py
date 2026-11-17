"""Extract every embedded image from the Track 1 report, named by slide + role."""
import hashlib
import os
from pptx import Presentation

SRC = r"C:\Users\30217\Downloads\Track1_Week1_Report.pptx"
OUT = r"C:\Users\30217\Desktop\ds工作\其他\track1_assets\raw"
os.makedirs(OUT, exist_ok=True)

prs = Presentation(SRC)
seen = {}
rows = []
for si, slide in enumerate(prs.slides, 1):
    n = 0
    for shape in slide.shapes:
        if shape.shape_type != 13:  # PICTURE
            continue
        blob = shape.image.blob
        ext = shape.image.ext
        w, h = shape.image.size
        sha = hashlib.sha256(blob).hexdigest()[:10]
        if sha in seen:
            rows.append((si, shape.name, w, h, seen[sha], "dup"))
            continue
        tag = "portrait" if h > w else "landscape" if w > h else "square"
        name = f"s{si:02d}_{tag}_{w}x{h}_{sha}.{ext}"
        with open(os.path.join(OUT, name), "wb") as f:
            f.write(blob)
        seen[sha] = name
        rows.append((si, shape.name, w, h, name, "saved"))
        n += 1

for r in rows:
    print("slide %2d | %-10s | %5dx%-5d | %-6s | %s" % r)
print("\nunique images saved:", len(seen))
