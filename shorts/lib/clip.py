"""화면 녹화본을 영상에 넣기 좋은 클립으로 바꾼다.

  python lib/clip.py s2/rec/raw/7-2.mp4 s2/rec/clips/ep07_report.mp4
  python lib/clip.py s2/rec/raw/7-2.mp4 s2/rec/clips/ep07_report.mp4 --from 3 --to 48 --crop 960:1200:480:60

--from/--to  쓸 구간(초)
--crop       잘라낼 영역 w:h:x:y (ffmpeg crop 형식, 원본 픽셀 기준)

소리는 버리고, 모든 프레임을 키프레임으로 만든다. 장면 코드가 clip()으로 아무 시각이나 정확히 탐색할 수 있게 하기 위해서다.
"""
import argparse
import subprocess
from pathlib import Path

SHORTS = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--from", dest="start", type=float)
    ap.add_argument("--to", dest="end", type=float)
    ap.add_argument("--crop")
    args = ap.parse_args()
    src, dst = SHORTS / args.src, SHORTS / args.dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    cut = (["-ss", str(args.start)] if args.start is not None else []) + (["-to", str(args.end)] if args.end is not None else [])
    vf = ([f"crop={args.crop}"] if args.crop else []) + ["scale='min(1920,iw)':-2", "fps=30"]
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *cut, "-i", str(src), "-an", "-vf", ",".join(vf),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-g", "1", "-pix_fmt", "yuv420p", str(dst)],
                   check=True)
    print(dst)


if __name__ == "__main__":
    main()
