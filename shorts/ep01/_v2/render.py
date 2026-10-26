"""ep01.html을 한 프레임씩 찍어 세로 숏츠 mp4(1080x1920, 30fps)로 만든다.

  python render.py                  전체 영상 렌더링 (효과음·배경음악 합성 포함)
  python render.py --stills 2 9 20  해당 초의 화면만 PNG로 저장 (확인용)
"""
import argparse
import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright

import sound

HERE = Path(__file__).resolve().parent
AUDIO = HERE / "audio"
FPS = 30
BGM_VOLUME = 0.6   # 0이면 배경음악 없음
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


def make_audio(events, total):
    """내레이션 + 효과음 + 배경음악(목소리가 나오면 자동으로 작아짐)을 audio/mix.wav로 섞는다."""
    sound.make_sfx(events, total, AUDIO / "sfx.wav")
    sound.make_bgm(total, AUDIO / "bgm.wav")
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(AUDIO / "narration.wav"), "-i", str(AUDIO / "sfx.wav"), "-i", str(AUDIO / "bgm.wav"),
        "-filter_complex",
        f"[0:a]aresample=48000,asplit=2[v1][v2];[2:a]volume={BGM_VOLUME}[b];"
        "[b][v2]sidechaincompress=threshold=0.02:ratio=8:attack=10:release=300[bd];"
        "[v1][1:a][bd]amix=inputs=3:normalize=0:duration=first,alimiter=limit=0.95[a]",
        "-map", "[a]", "-ar", "48000", str(AUDIO / "mix.wav"),
    ], check=True)


def video():
    with sync_playwright() as p:
        browser, page = open_page(p)
        total = page.evaluate("TIMELINE.total")
        events = page.evaluate("collectSfx()")
        print(f"효과음 {len(events)}개 합성 중…", flush=True)
        make_audio(events, total)
        frames = int(round(total * FPS))
        ff = subprocess.Popen([
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
            "-i", str(AUDIO / "mix.wav"),
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
