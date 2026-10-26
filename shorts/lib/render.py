"""편 하나의 index.html을 한 프레임씩 찍어 세로 숏츠 mp4(1080x1920, 30fps)로 만든다.

  python lib/render.py ep02                    전체 영상 렌더링 → ep02/<script.json의 file>
  python lib/render.py ep02 --stills 2 9 20    해당 초의 화면만 PNG로 저장 (확인용)
"""
import argparse
import json
import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright

SHORTS = Path(__file__).resolve().parent.parent
FPS = 30
HAS_CLIP = "document.querySelectorAll('canvas[data-src]').length > 0"   # 화면 녹화 클립이 있는 편


def open_page(p, ep_dir):
    browser = p.chromium.launch(channel="chrome")
    page = browser.new_page(viewport={"width": 1080, "height": 1920})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto((ep_dir / "index.html").as_uri() + "?render=1")
    try:
        page.wait_for_function("window.READY === true", timeout=30000)
    except Exception:
        raise SystemExit(f"페이지 준비 실패: {errors}")
    return browser, page


def seek(page, t, has_video):
    page.evaluate(f"seek({t})")
    if has_video:
        page.evaluate("window.settle()")   # 녹화 클립이 그 프레임으로 탐색을 마칠 때까지


def stills(ep_dir, times, outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser, page = open_page(p, ep_dir)
        has_video = page.evaluate(HAS_CLIP)
        for t in times:
            seek(page, t, has_video)
            path = outdir / f"still_{t:05.1f}.png"
            page.screenshot(path=str(path))
            print(path)
        browser.close()


def video(ep_dir):
    script = json.loads((ep_dir / "script.json").read_text(encoding="utf-8"))
    out = ep_dir / script["file"]
    with sync_playwright() as p:
        browser, page = open_page(p, ep_dir)
        total = page.evaluate("TIMELINE.total")
        frames = int(round(total * FPS))
        ff = subprocess.Popen([
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
            "-i", str(ep_dir / "audio" / "narration.wav"),
            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out),
        ], stdin=subprocess.PIPE)
        has_video = page.evaluate(HAS_CLIP)
        for i in range(frames):
            seek(page, i / FPS, has_video)
            ff.stdin.write(page.screenshot(type="jpeg", quality=93))
        ff.stdin.close()
        ff.wait()
        browser.close()
    print(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("ep")
    ap.add_argument("--stills", nargs="*", type=float)
    ap.add_argument("--outdir", type=Path)
    args = ap.parse_args()
    ep_dir = SHORTS / args.ep
    if args.stills:
        stills(ep_dir, args.stills, args.outdir or ep_dir / "stills")
    else:
        video(ep_dir)
