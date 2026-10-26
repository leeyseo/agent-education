"""Design 캔버스의 아트보드(.dc.html)를 PNG로 찍는다. 영상에 실제 결과물을 넣을 때 쓴다.

  python lib/snap.py s2/design/logo            캔버스의 모든 아트보드 → s2/design/logo/png/<이름>.png
  python lib/snap.py s2/design/logo B1 B2      해당 아트보드만
  python lib/snap.py s2/design/brochure --pdf 브로셔_A.pdf LA-out LA-in
                                               아트보드를 차례로 한 쪽씩 묶은 PDF → s2/design/brochure/pdf/브로셔_A.pdf
  python lib/snap.py s2/design/homepage --width 390 Main Menu
                                               늘었다 줄었다 하는 페이지를 폭 390으로 → png/Main@390.png (내용 높이 전체)

아트보드는 템플릿 구멍({{ }}) 없이 그대로 그려지는 정적 마크업이어야 로컬에서도 똑같이 나온다.
PDF는 화면 그대로(RGB, 재단 여백 없음)다. 인쇄소에 넘기기 전에는 색 모드와 재단 여백을 따로 맞춘다.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

SHORTS = Path(__file__).resolve().parent.parent


def boards(root, only):
    canvas = json.loads((root / "project" / "canvas.json").read_text(encoding="utf-8"))
    for f, b in canvas["boards"].items():
        stem = f.removesuffix(".dc.html")
        if not only or stem in only:
            yield stem, root / "project" / f, b


def snap(browser, root, only, width=None):
    out = root / "png"
    out.mkdir(exist_ok=True)
    for stem, path, b in boards(root, only):
        name = f"{stem}@{width}.png" if width else f"{stem}.png"
        page = browser.new_page(viewport={"width": width or b["w"], "height": b["h"]})
        page.goto(path.as_uri(), wait_until="networkidle")
        page.evaluate("document.fonts.ready.then(() => true)")
        page.locator("x-dc > div").first.screenshot(path=str(out / name))
        page.close()
        print(out / name)


def pdf(browser, root, name, only):
    # 아트보드마다 글꼴 링크와 본문(x-dc > div)을 모아, 한 쪽에 하나씩 이어 붙인 문서를 인쇄한다
    parts, links, size = [], [], None
    for stem in only:
        (_, path, b), = boards(root, [stem])
        size = size or (b["w"], b["h"])
        page = browser.new_page()
        page.goto(path.as_uri(), wait_until="networkidle")
        links += [h for h in page.eval_on_selector_all("helmet link[rel=stylesheet]", "els => els.map(e => e.href)") if h not in links]
        parts.append(page.eval_on_selector("x-dc > div", "el => el.outerHTML"))
        page.close()
    w, h = size
    doc = "".join(f'<link rel="stylesheet" href="{u}">' for u in links) + f"""
      <style>@page {{ size: {w}px {h}px; margin: 0; }} body {{ margin: 0; }}
      section {{ width: {w}px; height: {h}px; overflow: hidden; break-after: page; }}</style>
      """ + "".join(f"<section>{p}</section>" for p in parts)
    out = root / "pdf"
    out.mkdir(exist_ok=True)
    page = browser.new_page()
    page.set_content(doc, wait_until="networkidle")
    page.evaluate("document.fonts.ready.then(() => true)")
    page.pdf(path=str(out / name), width=f"{w}px", height=f"{h}px", print_background=True)
    page.close()
    print(out / name)


def main(name, args):
    root = SHORTS / name
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        if args[:1] == ["--pdf"]:
            pdf(browser, root, args[1], args[2:])
        elif args[:1] == ["--width"]:
            snap(browser, root, args[2:], int(args[1]))
        else:
            snap(browser, root, args)
        browser.close()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
