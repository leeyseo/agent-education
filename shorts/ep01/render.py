"""ep01.html을 한 프레임씩 찍어 세로 숏츠 mp4(1080x1920, 30fps)로 만든다.

  python render.py                  전체 영상 렌더링
  python render.py --stills 2 9 20  해당 초의 화면만 PNG로 저장 (확인용)
"""
import argparse
import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
FPS = 30
OUT = HERE / "EP01_AI는_검색창이_아닙니다.mp4"


def open_page(p):
    browser = p.chromium.launch(channel="chrome")
    page = browser.new_page(viewport={"width": 1080, "height": 1920})
    page.goto((HERE / "ep01.html").as_uri() + "?render=1")
    page.wait_for_function("window.READY === true", timeout=30000)
    return browser, page


def stills(times, outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser, page = open_page(p)
        for t in times:
            page.evaluate(f"seek({t})")
            path = outdir / f"still_{t:05.1f}.png"
            page.screenshot(path=str(path))
            print(path)
        browser.close()


def video():
    with sync_playwright() as p:
        browser, page = open_page(p)
        total = page.evaluate("TIMELINE.total")
        frames = int(round(total * FPS))
        ff = subprocess.Popen([
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
            "-i", str(HERE / "audio" / "narration.wav"),
            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(OUT),
        ], stdin=subprocess.PIPE)
        for i in range(frames):
            page.evaluate(f"seek({i / FPS})")
            ff.stdin.write(page.screenshot(type="jpeg", quality=93))
            if i % 150 == 0:
                print(f"{i}/{frames} 프레임", flush=True)
        ff.stdin.close()
        ff.wait()
        browser.close()
    print(OUT)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", nargs="*", type=float)
    ap.add_argument("--outdir", type=Path, default=HERE / "stills")
    args = ap.parse_args()
    if args.stills:
        stills(args.stills, args.outdir)
    else:
        video()
