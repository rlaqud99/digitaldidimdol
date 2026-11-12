import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# 결과물(index.html) 위치: 작업 공간에서는 ../site, GitHub 저장소에서는 저장소 맨 위(../)
OUT_DIR = os.path.join(HERE, "..", "site") if os.path.isdir(os.path.join(HERE, "..", "site")) else os.path.join(HERE, "..")
from guides import GUIDES, CATS

man = json.load(open(os.path.join(HERE, "manifest.json")))
man.update(json.load(open(os.path.join(HERE, "manifest_extra.json"))))  # 직접 만든 사진(PPT 등)
out = []
for g in GUIDES:
    g2 = {k: v for k, v in g.items() if k != "steps"}
    g2.setdefault("related", []); g2.setdefault("stuck", [])
    steps = []
    for i, s in enumerate(g["steps"]):
        s2 = {k: v for k, v in s.items() if k != "img"}
        if s.get("img"):
            s2["img"] = man[f"{g['id']}-{i}"]
        steps.append(s2)
    g2["steps"] = steps
    out.append(g2)

html = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
html = html.replace("__CATS__", json.dumps(CATS, ensure_ascii=False))
html = html.replace("__GUIDES__", json.dumps(out, ensure_ascii=False))
open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8").write(html)
print("guides", len(out), "steps", sum(len(g["steps"]) for g in out), "html KB", len(html.encode()) // 1024)
