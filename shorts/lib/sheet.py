"""확인용: 편의 장면마다 중간·끝 직전 화면을 찍어 한 장(<편>/stills/sheet.png)으로 이어 붙인다.

  python lib/sheet.py ep05           장면마다 2장씩 자동으로
  python lib/sheet.py ep05 3.6 10.0  원하는 초만

렌더링 전에 겹침·잘림·타이밍을 빠르게 훑어보는 용도다.
"""
import glob
import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

SHORTS = Path(__file__).resolve().parent.parent


def main(ep, times):
    if not times:
        s = (SHORTS / ep / "timeline.js").read_text(encoding="utf-8")
        tl = json.loads(s[s.index("{"):s.rindex("}") + 1])
        for sc in tl["scenes"]:
            a, b = sc["start"], sc["end"]
            times += [f"{a + (b - a) * 0.5:.1f}", f"{b - 0.35:.1f}"]
    out = SHORTS / ep / "stills"
    shutil.rmtree(out, ignore_errors=True)
    subprocess.run([sys.executable, str(SHORTS / "lib" / "render.py"), ep, "--stills", *times, "--outdir", str(out)],
                   check=True, stdout=subprocess.DEVNULL)
    fs = sorted(glob.glob(str(out / "still_*.png")))
    cols = (len(fs) + 1) // 2 if len(fs) > 6 else len(fs)
    rows = (len(fs) + cols - 1) // cols
    W, H = 380, 676
    sheet = Image.new("RGB", (W * cols + 8 * (cols - 1), H * rows + 8 * (rows - 1)), "white")
    for i, f in enumerate(fs):
        sheet.paste(Image.open(f).convert("RGB").resize((W, H), Image.LANCZOS), ((i % cols) * (W + 8), (i // cols) * (H + 8)))
    sheet.save(out / "sheet.png")
    print(out / "sheet.png")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
