"""Design 캔버스의 아트보드(.dc.html)를 PNG로 찍는다. 영상에 실제 결과물을 넣을 때 쓴다.

  python lib/snap.py s2/design/logo            캔버스의 모든 아트보드 → s2/design/logo/png/<이름>.png
  python lib/snap.py s2/design/logo B1 B2      해당 아트보드만

아트보드는 템플릿 구멍({{ }}) 없이 그대로 그려지는 정적 마크업이어야 로컬에서도 똑같이 나온다.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

SHORTS = Path(__file__).resolve().parent.parent


def main(name, only):
    root = SHORTS / name
    canvas = json.loads((root / "project" / "canvas.json").read_text(encoding="utf-8"))
    out = root / "png"
    out.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        for f, b in canvas["boards"].items():
            stem = f.removesuffix(".dc.html")
            if only and stem not in only:
                continue
            page = browser.new_page(viewport={"width": b["w"], "height": b["h"]})
            page.goto((root / "project" / f).as_uri(), wait_until="networkidle")
            page.evaluate("document.fonts.ready.then(() => true)")
            page.locator("x-dc > div").first.screenshot(path=str(out / f"{stem}.png"))
            page.close()
            print(out / f"{stem}.png")
        browser.close()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
