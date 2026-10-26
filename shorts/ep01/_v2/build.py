"""EP1 내레이션 음성과 타임라인을 만든다.

1) 줄마다 Windows 한국어 음성(Heami)으로 wav를 만든다 (audio/line_XX.wav)
2) 음성 길이에 맞춰 장면·자막 시간을 계산해 timeline.js에 쓴다
3) 전체 내레이션 트랙 audio/narration.wav를 만든다

대사를 고친 뒤 `python build.py` → `python render.py` 순서로 다시 돌리면 된다.
"""
import array
import html
import json
import re
import subprocess
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUDIO = HERE / "audio"
RATE = 4          # 말하기 속도 (-10 ~ 10)
SR = 24000
LINE_GAP = 0.12   # 같은 장면 안에서 줄 사이 쉼(초)
MIN_CHUNK = 4     # 자막 한 덩어리의 최소 글자 수

# 장면별 내레이션. [[ ]] 안은 자막에서 노란색으로 강조한다.
# lead: 장면 시작 후 첫 대사까지, tail: 마지막 대사 후 장면 끝까지(초), nocap: 자막 없음(화면 글자로 대신)
SCENES = [
    {"id": "s0", "lead": 0.05, "tail": 0.5, "nocap": True, "lines": [
        "말 한마디에, 파일 열두 개가 끝났습니다.",
    ]},
    {"id": "s1", "lead": 0.15, "tail": 0.25, "lines": [
        "근데 아직도 AI를 [[검색창]]처럼 쓰세요?",
        "AI는 [[세 단계]]로 나뉩니다.",
    ]},
    {"id": "s2", "lead": 0.15, "tail": 0.4, "lines": [
        "[[검색]]은 도서관 사서. 위치만 알려주고, 읽는 건 [[내가]].",
    ]},
    {"id": "s3", "lead": 0.15, "tail": 0.9, "lines": [
        "[[챗봇]]은 전화 상담원. 방법은 알려주지만, 복붙은 [[내 손]].",
    ]},
    {"id": "s4", "lead": 0.15, "tail": 0.9, "lines": [
        "[[에이전트]]는 내 자리에 앉은 신입. 열고, 고치고, [[확인까지]] 직접.",
    ]},
    {"id": "s5", "lead": 0.15, "tail": 1.4, "lines": [
        "[[찾아주는]] AI, [[말해주는]] AI, [[해주는]] AI.",
        "다음 편, 같은 일을 [[직접 시켜]] 봅니다.",
    ]},
]


def plain(s):
    return s.replace("[[", "").replace("]]", "")


def spoken(s):
    return plain(s).replace("AI", "에이아이")


def tokens(chunk):
    # 강조 단어는 한 덩어리로 튀어나오고 줄바꿈으로 쪼개지지 않게 공백을 붙여 쓴다
    chunk = re.sub(r"\[\[(.+?)\]\]", lambda m: "[[" + m.group(1).replace(" ", " ") + "]]", chunk)
    return chunk.split(" ")


def tok_html(tok):
    return html.escape(tok).replace("[[", '<span class="hl">').replace("]]", "</span>")


def tts(text, wav):
    key = wav.with_suffix(".key")
    if wav.exists() and key.exists() and key.read_text(encoding="utf-8") == f"{RATE}|{text}":
        return
    txt = wav.with_suffix(".txt")
    txt.write_text(text, encoding="utf-8")
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(HERE / "tts.ps1"),
                    "-InFile", str(txt), "-OutFile", str(wav), "-Rate", str(RATE)], check=True)
    key.write_text(f"{RATE}|{text}", encoding="utf-8")


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
    t, n = 0.0, 0
    scenes, captions, track = [], [], []
    for sc in SCENES:
        start = t
        t += sc["lead"]
        marks, scene_words = [], []
        for li, line in enumerate(sc["lines"]):
            n += 1
            wav = AUDIO / f"line_{n:02d}.wav"
            tts(spoken(line), wav)
            samples = load_trimmed(wav)
            dur = len(samples) / SR
            track.append((t, samples))
            cs = chunks(line)
            ws = [weight(c) for c in cs]
            ct = t
            for ci, (c, w) in enumerate(zip(cs, ws)):
                cd = dur * w / sum(ws)
                marks.append(round(ct - start, 3))
                # 단어마다 나오는 시각: 덩어리 안에서 소리 길이에 비례해 나눈다
                toks = tokens(c)
                tws = [weight(x) for x in toks]
                wt, words = ct, []
                for tok, tw in zip(toks, tws):
                    words.append({"t": round(wt, 3), "html": tok_html(tok), "hl": "[[" in tok})
                    scene_words.append({"t": round(wt - start, 3), "w": plain(tok)})
                    wt += cd * tw / sum(tws)
                if not sc.get("nocap"):
                    end = ct + cd + (0.3 if ci == len(cs) - 1 else 0)
                    captions.append({"start": round(ct, 3), "end": round(end, 3), "words": words})
                ct += cd
            t += dur + (LINE_GAP if li < len(sc["lines"]) - 1 else 0)
        t += sc["tail"]
        scenes.append({"id": sc["id"], "start": round(start, 3), "end": round(t, 3),
                       "marks": marks, "words": scene_words})

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
