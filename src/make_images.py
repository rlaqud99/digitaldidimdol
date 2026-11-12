import json, os, subprocess, sys
import pdfplumber
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from guides import GUIDES

U = "/mnt/user-data/uploads/"
PDF = {
    "pc": U + "03f53004-____________________2026.pdf",
    "ai": U + "e7743306-AI______2026.pdf",
    "ecl": U + "800718df-e-class________.pdf",
    "ocw": U + "2b52d40c-_____OCW______.pdf",
    "law": U + "f032e9c4-__________.pdf",
}
OUT = "/home/claude/site/img"
TMP = "/home/claude/build/render"
os.makedirs(OUT, exist_ok=True); os.makedirs(TMP, exist_ok=True)
SCALE = 2.5  # 180 dpi
plumb = {k: pdfplumber.open(v) for k, v in PDF.items()}

def auto_bbox(key, page, strict=False):
    p = plumb[key].pages[page - 1]
    ims = [(im["x0"], im["top"], im["x1"], im["bottom"]) for im in p.images
           if im["width"] > 60 and im["height"] > 60]
    ims = [b for b in ims if not (b[1] >= 300 and b[2] - b[0] >= 900)]
    if not ims:
        return None
    if len(ims) > 3:
        ims = [max(ims, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))]
    elif strict:
        big = max((b[2] - b[0]) * (b[3] - b[1]) for b in ims)
        ims = [b for b in ims if (b[2] - b[0]) * (b[3] - b[1]) >= big * 0.15]
    return (min(b[0] for b in ims), min(b[1] for b in ims), max(b[2] for b in ims), max(b[3] for b in ims))

def render(key, page):
    fn = f"{TMP}/{key}-{page}.png"
    if not os.path.exists(fn):
        subprocess.run(["pdftoppm", "-r", str(int(72 * SCALE)), "-png", "-singlefile",
                        "-f", str(page), "-l", str(page), PDF[key], fn[:-4]], check=True)
    return Image.open(fn).convert("RGB")

# 개인정보(학번·계정 정보)가 보이는 곳 가리기: 파일명 → (x0, y0, x1, y1) 비율
from PIL import ImageFilter
BLUR = {
    "portal-login-4.jpg": (0.18, 0.74, 0.52, 0.88),
    "eclass-email-2.jpg": (0.36, 0.02, 0.72, 0.13),
    "law-edu-3.jpg": (0.15, 0.415, 0.36, 0.447),
    "law-edu-11.jpg": (0.15, 0.415, 0.36, 0.447),
    "ocw-korean-3.jpg": (0.15, 0.415, 0.36, 0.447),
}

manifest = {}
for g in GUIDES:
    for i, s in enumerate(g["steps"]):
        spec = s.get("img")
        if not spec:
            continue
        if spec[0] == "file":  # manifest_extra.json에 있는 직접 만든 사진
            continue
        key, page = spec[0], spec[1]
        bbox = spec[2] if len(spec) > 2 else auto_bbox(key, page, strict=f"{g['id']}-{i+1}.jpg" not in BLUR)
        im = render(key, page)
        W, H = im.size
        name = f"{g['id']}-{i+1}.jpg"
        pad = 8 if (len(spec) > 2 or name in BLUR) else 0
        x0, y0, x1, y1 = bbox
        box = (max(0, int((x0 - pad) * SCALE)), max(0, int((y0 - pad) * SCALE)),
               min(W, int((x1 + pad) * SCALE)), min(H, int((y1 + pad) * SCALE)))
        c = im.crop(box)
        c.thumbnail((900, 900), Image.LANCZOS)
        name = f"{g['id']}-{i+1}.jpg"
        c.save(f"{OUT}/{name}", "JPEG", quality=74, optimize=True, progressive=True)
        manifest[f"{g['id']}-{i}"] = {"src": "img/" + name, "w": c.size[0], "h": c.size[1]}

for fn, (a, b_, c, d) in BLUR.items():
    p = f"{OUT}/{fn}"
    if not os.path.exists(p):
        continue
    im = Image.open(p); W, H = im.size
    box = (int(a * W), int(b_ * H), int(c * W), int(d * H))
    im.paste(im.crop(box).filter(ImageFilter.GaussianBlur(7)), box)
    im.save(p, "JPEG", quality=74, optimize=True, progressive=True)

json.dump(manifest, open("/home/claude/build/manifest.json", "w"), ensure_ascii=False)
tot = sum(os.path.getsize(f"{OUT}/{f}") for f in os.listdir(OUT))
print(len(manifest), "images", round(tot / 1e6, 2), "MB")
