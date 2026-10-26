"""EP1 내레이션 음성과 타임라인을 만든다.

1) 줄마다 내레이션 wav를 만든다 (audio/line_XX.wav)
   - elevenlabs: ElevenLabs 음성 (pip install elevenlabs). API 키는 이 폴더의 .env 파일의 ELEVENLABS_API_KEY를 쓴다
   - windows: Windows 기본 한국어 음성(Heami)
2) 음성 길이에 맞춰 장면·자막 시간을 계산해 timeline.js에 쓴다
3) 전체 내레이션 트랙 audio/narration.wav를 만든다

대사를 고친 뒤 `python build.py` → `python render.py` 순서로 다시 돌리면 된다.
"""
import array
import html
import json
import os
import re
import subprocess
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUDIO = HERE / "audio"
TTS_ENGINE = "elevenlabs"                  # "elevenlabs" | "windows"
ELEVEN_VOICE_ID = "nPczCjzI2devNBz1zQrb"   # Brian (기본 제공 목소리라 무료 플랜에서도 API 사용 가능. Rachel은 유료)
ELEVEN_MODEL = "eleven_v4"                 # 최신 모델. 한국어 포함 90개 이상 언어
ELEVEN_SETTINGS = {"stability": 0.7, "similarity_boost": 0.5}   # 내레이션용 권장값 (v4는 이 두 값만 쓴다)
RATE = 2          # windows 음성의 말하기 속도 (-10 ~ 10)
SR = 24000
LINE_GAP = 0.35   # 같은 장면 안에서 줄 사이 쉼(초)
MIN_CHUNK = 4     # 자막 한 덩어리의 최소 글자 수

# 장면별 내레이션. [[ ]] 안은 자막에서 노란색으로 강조한다.
# lead: 장면 시작 후 첫 대사까지, tail: 마지막 대사 후 장면 끝까지(초)
SCENES = [
    {"id": "s1", "lead": 0.3, "tail": 0.3, "lines": [
        "AI, 아직도 [[검색창]]처럼 쓰고 계신가요?",
        "AI에는 [[세 단계]]가 있습니다.",
    ]},
    {"id": "s2", "lead": 0.4, "tail": 0.7, "lines": [
        "첫째, [[검색]]. 도서관 사서예요. 책 위치는 알려주지만, 읽고 따라 하는 건 [[제가]] 합니다.",
    ]},
    {"id": "s3", "lead": 0.4, "tail": 1.3, "lines": [
        "둘째, [[챗봇]]. 전화 상담원이에요. 친절하게 방법을 알려주지만, 복사하고 붙여넣는 건 여전히 [[제 손]]입니다.",
    ]},
    {"id": "s4", "lead": 0.4, "tail": 1.7, "lines": [
        "셋째, [[에이전트]]. 제 자리에 앉은 신입이에요. 파일을 직접 열고, 고치고, [[확인까지]] 합니다.",
    ]},
    {"id": "s5", "lead": 0.4, "tail": 2.3, "lines": [
        "[[찾아주는]] AI, [[말해주는]] AI, 그리고 [[해주는]] AI.",
        "다음 편에서는 같은 일을 [[직접 시켜]] 볼게요.",
    ]},
]


def plain(s):
    return s.replace("[[", "").replace("]]", "")


def spoken(s):
    return plain(s).replace("AI", "에이아이")


def to_html(s):
    # 강조 단어는 줄바꿈으로 쪼개지지 않게 공백을 붙여 쓴다
    s = re.sub(r"\[\[(.+?)\]\]", lambda m: "[[" + m.group(1).replace(" ", " ") + "]]", s)
    return html.escape(s).replace("[[", '<span class="hl">').replace("]]", "</span>")


def load_env():
    """이 폴더의 .env를 환경 변수로 읽어 들인다 (SDK가 ELEVENLABS_API_KEY를 환경에서 읽는다)."""
    from dotenv import load_dotenv

    load_dotenv(HERE / ".env")
    if not os.environ.get("ELEVENLABS_API_KEY"):
        raise SystemExit("ElevenLabs API 키가 없습니다. 이 폴더의 .env 파일에 ELEVENLABS_API_KEY=... 를 넣어 주세요.")


def tts_eleven(text, wav, prev, nxt):
    load_env()   # SDK가 불러올 때 키를 읽으므로 반드시 먼저
    from elevenlabs import ElevenLabs, VoiceSettings

    try:
        audio = ElevenLabs().text_to_speech.convert(
            voice_id=ELEVEN_VOICE_ID,
            text=text,
            model_id=ELEVEN_MODEL,
            language_code="ko",
            voice_settings=VoiceSettings(**ELEVEN_SETTINGS),
            output_format="mp3_44100_128",
            previous_text=prev or None,   # 앞뒤 문장을 알려 줘야 줄 사이 톤이 자연스럽게 이어진다
            next_text=nxt or None,
            seed=7,
        )
        src = wav.with_suffix(".mp3")
        with open(src, "wb") as f:
            for chunk in audio:
                f.write(chunk)
    except Exception as e:
        raise SystemExit(f"ElevenLabs 오류: {e}")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-ac", "1", "-ar", str(SR), str(wav)],
                   check=True)


def tts_windows(text, wav):
    txt = wav.with_suffix(".txt")
    txt.write_text(text, encoding="utf-8")
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(HERE / "tts.ps1"),
                    "-InFile", str(txt), "-OutFile", str(wav), "-Rate", str(RATE)], check=True)


def tts(text, wav, prev="", nxt=""):
    # 같은 음성·같은 대사로 이미 만든 파일이 있으면 다시 만들지 않는다 (ElevenLabs 크레딧 절약)
    if TTS_ENGINE == "elevenlabs":
        sig = (f"elevenlabs|{ELEVEN_VOICE_ID}|{ELEVEN_MODEL}|{json.dumps(ELEVEN_SETTINGS, sort_keys=True)}"
               f"|{prev}|{text}|{nxt}")
    else:
        sig = f"windows|{RATE}|{text}"
    key = wav.with_suffix(".key")
    if wav.exists() and key.exists() and key.read_text(encoding="utf-8") == sig:
        return
    if TTS_ENGINE == "elevenlabs":
        tts_eleven(text, wav, prev, nxt)
    else:
        tts_windows(text, wav)
    key.write_text(sig, encoding="utf-8")


def load_trimmed(wav):
    """앞뒤 무음을 잘라낸 샘플을 돌려준다."""
    with wave.open(str(wav)) as w:
        assert (w.getframerate(), w.getsampwidth(), w.getnchannels()) == (SR, 2, 1)
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


def weight(c):
    # 읽는 데 걸리는 시간 추정: 소리 나는 글자 수 + 쉼표·마침표의 쉼
    return len(re.sub(r"\s", "", spoken(c))) + 2 * len(re.findall(r"[,.?!]", c))


def main():
    AUDIO.mkdir(exist_ok=True)
    all_lines = [spoken(line) for sc in SCENES for line in sc["lines"]]
    t, n = 0.0, 0
    scenes, captions, track = [], [], []
    for sc in SCENES:
        start = t
        t += sc["lead"]
        marks = []
        for li, line in enumerate(sc["lines"]):
            n += 1
            wav = AUDIO / f"line_{n:02d}.wav"
            prev = all_lines[n - 2] if n >= 2 else ""
            nxt = all_lines[n] if n < len(all_lines) else ""
            tts(spoken(line), wav, prev, nxt)
            samples = load_trimmed(wav)
            dur = len(samples) / SR
            track.append((t, samples))
            cs = chunks(line)
            ws = [weight(c) for c in cs]
            ct = t
            for ci, (c, w) in enumerate(zip(cs, ws)):
                cd = dur * w / sum(ws)
                marks.append(round(ct - start, 3))
                end = ct + cd + (0.3 if ci == len(cs) - 1 else 0)
                captions.append({"start": round(ct, 3), "end": round(end, 3), "html": to_html(c)})
                ct += cd
            t += dur + (LINE_GAP if li < len(sc["lines"]) - 1 else 0)
        t += sc["tail"]
        scenes.append({"id": sc["id"], "start": round(start, 3), "end": round(t, 3), "marks": marks})

    total = round(t, 3)
    out = array.array("h", bytes(2 * (int(total * SR) + 1)))
    for st, s in track:
        i = int(st * SR)
        out[i:i + len(s)] = s
    with wave.open(str(AUDIO / "narration.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(out.tobytes())

    tl = {"total": total, "scenes": scenes, "captions": captions}
    (HERE / "timeline.js").write_text("window.TIMELINE = " + json.dumps(tl, ensure_ascii=False, indent=1) + ";\n",
                                      encoding="utf-8")

    print(f"전체 길이: {total:.1f}초")
    for s in scenes:
        print(f"  {s['id']}: {s['start']:5.1f} ~ {s['end']:5.1f}  ({s['end'] - s['start']:.1f}초)  marks={s['marks']}")


if __name__ == "__main__":
    main()
