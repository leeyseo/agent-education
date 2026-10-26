"""편 하나의 내레이션 음성과 타임라인을 만든다.

  python lib/build.py ep02

1) <편>/script.json의 대사를 줄마다 ElevenLabs(Brian)로 읽어 <편>/audio/line_XX.wav를 만든다
2) 음성 길이에 맞춰 장면·자막 시간을 계산해 <편>/timeline.js에 쓴다
3) 전체 내레이션 트랙 <편>/audio/narration.wav를 만든다

API 키는 <편>/.env → shorts/.env → shorts/ep01/.env 순서로 찾은 파일의 ELEVENLABS_API_KEY를 쓴다.
같은 대사는 다시 요청하지 않으므로, 대사를 고친 줄만 크레딧이 든다.
"""
import array
import html
import json
import os
import re
import subprocess
import sys
import wave
from pathlib import Path

SHORTS = Path(__file__).resolve().parent.parent
SERIES = "AI 신입 길들이기"
VOICE_ID = "nPczCjzI2devNBz1zQrb"   # Brian (기본 제공 목소리라 무료 플랜에서도 API 사용 가능)
MODEL = "eleven_v4"
SETTINGS = {"stability": 0.7, "similarity_boost": 0.5}   # 내레이션용 권장값
SR = 24000
LINE_GAP = 0.35
MIN_CHUNK = 4

# 화면 글자는 그대로 두고, 읽을 때만 한국어 발음으로 바꾼다 (긴 것부터)
SAY = {
    "CLAUDE.md": "클로드 엠디", "Claude Code": "클로드 코드", "Claude Design": "클로드 디자인", "Claude": "클로드",
    "Cowork": "코워크", "VS Code": "브이에스 코드", "FileZilla": "파일질라", "HTML": "에이치티엠엘",
    "FTP": "에프티피", "PPT": "피피티", "AI": "에이아이", "CDO": "씨디오",
}


def plain(s):
    return s.replace("[[", "").replace("]]", "")


def make_spoken(extra):
    table = {**SAY, **extra}
    keys = sorted(table, key=len, reverse=True)

    def spoken(s):
        s = plain(s)
        for k in keys:
            s = s.replace(k, table[k])
        return s
    return spoken


def to_html(s):
    # 강조 단어는 줄바꿈으로 쪼개지지 않게 공백을 붙여 쓴다
    s = re.sub(r"\[\[(.+?)\]\]", lambda m: "[[" + m.group(1).replace(" ", " ") + "]]", s)
    return html.escape(s).replace("[[", '<span class="hl">').replace("]]", "</span>")


def load_key(ep_dir):
    from dotenv import load_dotenv

    for env in (ep_dir / ".env", SHORTS / ".env", SHORTS / "ep01" / ".env"):
        if env.exists():
            load_dotenv(env)
            break
    if not os.environ.get("ELEVENLABS_API_KEY"):
        raise SystemExit("ElevenLabs API 키가 없습니다. .env 파일에 ELEVENLABS_API_KEY=... 를 넣어 주세요.")


def tts(ep_dir, text, wav, prev, nxt, used):
    sig = f"{VOICE_ID}|{MODEL}|{json.dumps(SETTINGS, sort_keys=True)}|{prev}|{text}|{nxt}"
    key = wav.with_suffix(".key")
    if wav.exists() and key.exists() and key.read_text(encoding="utf-8") == sig:
        return
    load_key(ep_dir)   # SDK가 불러올 때 키를 읽으므로 반드시 먼저
    from elevenlabs import ElevenLabs, VoiceSettings

    src = wav.with_suffix(".mp3")
    try:
        audio = ElevenLabs().text_to_speech.convert(
            voice_id=VOICE_ID, text=text, model_id=MODEL, language_code="ko",
            voice_settings=VoiceSettings(**SETTINGS), output_format="mp3_44100_128",
            previous_text=prev or None, next_text=nxt or None, seed=7,
        )
        with open(src, "wb") as f:
            for chunk in audio:
                f.write(chunk)
    except Exception as e:
        raise SystemExit(f"ElevenLabs 오류: {e}")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-ac", "1", "-ar", str(SR), str(wav)], check=True)
    key.write_text(sig, encoding="utf-8")
    used.append(len(text))


def load_trimmed(wav):
    """앞뒤 무음을 잘라낸 샘플을 돌려준다."""
    with wave.open(str(wav)) as w:
        data = array.array("h", w.readframes(w.getnframes()))
    loud = [i for i, v in enumerate(data) if abs(v) > 500]
    pad = int(0.04 * SR)
    return data[max(0, loud[0] - pad):min(len(data), loud[-1] + pad)]


def chunks(line):
    """자막을 쉼표·마침표 단위로 나누되, 너무 짧은 조각은 다음 조각과 합친다."""
    out, buf = [], ""
    for part in re.split(r"(?<=[,.?!])\s+", line.strip()):
        buf = f"{buf} {part}" if buf else part
        if len(re.sub(r"[\s,.?!]", "", plain(buf))) >= MIN_CHUNK:
            out.append(buf)
            buf = ""
    if buf:
        if out:
            out[-1] = f"{out[-1]} {buf}"
        else:
            out.append(buf)
    return out


def main(ep_name):
    ep_dir = SHORTS / ep_name
    script = json.loads((ep_dir / "script.json").read_text(encoding="utf-8"))
    spoken = make_spoken(script.get("say", {}))

    def weight(c):
        # 읽는 데 걸리는 시간 추정: 소리 나는 글자 수 + 쉼표·마침표의 쉼
        return len(re.sub(r"\s", "", spoken(c))) + 2 * len(re.findall(r"[,.?!]", c))

    audio_dir = ep_dir / "audio"
    audio_dir.mkdir(exist_ok=True)
    all_lines = [spoken(line) for sc in script["scenes"] for line in sc["lines"]]
    t, n, used = 0.0, 0, []
    scenes, captions, track = [], [], []
    for sc in script["scenes"]:
        start = t
        t += sc.get("lead", 0.35)
        marks, words = [], []
        for li, line in enumerate(sc["lines"]):
            n += 1
            wav = audio_dir / f"line_{n:02d}.wav"
            prev = all_lines[n - 2] if n >= 2 else ""
            nxt = all_lines[n] if n < len(all_lines) else ""
            tts(ep_dir, spoken(line), wav, prev, nxt, used)
            samples = load_trimmed(wav)
            dur = len(samples) / SR
            track.append((t, samples))
            cs = chunks(line)
            ws = [weight(c) for c in cs]
            ct = t
            for ci, (c, w) in enumerate(zip(cs, ws)):
                cd = dur * w / sum(ws)
                marks.append(round(ct - start, 3))
                # 장면 코드가 "그 단어를 말하는 순간"에 맞출 수 있게 단어별 시각도 넘긴다
                toks = c.split(" ")
                tws = [weight(x) or 1 for x in toks]
                wt = ct
                for tok, tw in zip(toks, tws):
                    words.append({"t": round(wt - start, 3), "w": plain(tok)})
                    wt += cd * tw / sum(tws)
                end = ct + cd + (0.3 if ci == len(cs) - 1 else 0)
                captions.append({"start": round(ct, 3), "end": round(end, 3), "html": to_html(c)})
                ct += cd
            t += dur + (LINE_GAP if li < len(sc["lines"]) - 1 else 0)
        t += sc.get("tail", 0.5)
        scenes.append({"id": sc["id"], "start": round(start, 3), "end": round(t, 3), "marks": marks, "words": words})

    total = round(t, 3)
    out = array.array("h", bytes(2 * (int(total * SR) + 1)))
    for st, s in track:
        i = int(st * SR)
        out[i:i + len(s)] = s
    with wave.open(str(audio_dir / "narration.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(out.tobytes())

    meta = {"ep": script["ep"], "title": script["title"], "series": script.get("series", SERIES),
            "header": script.get("header", {})}
    tl = {"meta": meta, "total": total, "scenes": scenes, "captions": captions}
    (ep_dir / "timeline.js").write_text("window.TIMELINE = " + json.dumps(tl, ensure_ascii=False, indent=1) + ";\n",
                                        encoding="utf-8")

    print(f"[{ep_name}] 전체 {total:.1f}초 · 새로 만든 줄 {len(used)}개 ({sum(used)}자)")
    for s in scenes:
        print(f"  {s['id']}: {s['start']:5.1f} ~ {s['end']:5.1f}  ({s['end'] - s['start']:.1f}초)  marks={s['marks']}")


if __name__ == "__main__":
    main(sys.argv[1])
