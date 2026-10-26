"""효과음과 배경음악을 직접 합성한다 (외부 음원을 쓰지 않아 저작권 걱정이 없다).

make_sfx(events, total, path): 화면에서 모은 [{type, t}] 목록대로 효과음 트랙을 만든다
make_bgm(total, path): 124BPM 가벼운 비트 루프를 만든다
"""
import array
import math
import random
import wave

SR = 48000


def _zeros(sec):
    return array.array("f", bytes(4 * (int(sec * SR) + 1)))


def _add(buf, start, samples, gain=1.0):
    i0 = int(start * SR)
    for j, v in enumerate(samples):
        k = i0 + j
        if 0 <= k < len(buf):
            buf[k] += v * gain


def _write(buf, path, peak=None):
    if peak:
        m = max(1e-9, max(abs(v) for v in buf))
        buf = array.array("f", (v * peak / m for v in buf))
    out = array.array("h", (int(max(-1.0, min(1.0, v)) * 32767) for v in buf))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(out.tobytes())


def tone(freq, dur, decay, f_end=None, shape="sine", attack=0.003):
    n, ph, out = int(dur * SR), 0.0, []
    for i in range(n):
        x = i / n
        f = freq if f_end is None else freq * (f_end / freq) ** x
        ph += 2 * math.pi * f / SR
        s = math.sin(ph) if shape == "sine" else (2 / math.pi) * math.asin(math.sin(ph))
        env = min(1.0, i / (attack * SR + 1)) * math.exp(-decay * i / SR)
        out.append(s * env)
    return out


def noise(dur, decay, lp=0.5, hp=False, seed=1):
    rnd, n, out, y, prev = random.Random(seed), int(dur * SR), [], 0.0, 0.0
    for i in range(n):
        w = rnd.uniform(-1, 1)
        if hp:
            y, prev = w - prev, w
        else:
            y += lp * (w - y)
        out.append(y * math.exp(-decay * i / SR))
    return out


def mix(*parts):
    n = max(len(p) for p, _ in parts)
    out = [0.0] * n
    for p, g in parts:
        for i, v in enumerate(p):
            out[i] += v * g
    return out


def whoosh(dur=0.32, seed=3):
    rnd, n, out, y = random.Random(seed), int(dur * SR), [], 0.0
    for i in range(n):
        x = i / n
        a = 0.03 + 0.35 * math.sin(math.pi * x)   # 필터가 열렸다 닫히며 '슉'
        y += a * (rnd.uniform(-1, 1) - y)
        out.append(y * math.sin(math.pi * x) ** 1.5)
    return out


def scratch(dur=0.3, seed=5):
    rnd, n, out, y, ph = random.Random(seed), int(dur * SR), [], 0.0, 0.0
    for i in range(n):
        x = i / n
        f = 900 * (1 - x) + 160 + 260 * math.sin(2 * math.pi * 14 * x * dur)
        ph += 2 * math.pi * f / SR
        y += 0.4 * (rnd.uniform(-1, 1) - y)
        out.append((0.6 * math.sin(ph) * abs(math.sin(ph * 0.5)) + 0.5 * y) * (1 - x) ** 0.7)
    return out


SFX = {
    "pop": lambda: tone(520, 0.10, 28, f_end=1400),
    "tick": lambda: mix((tone(2600, 0.035, 140), 1.0), (noise(0.012, 400, hp=True), 0.3)),
    "type": lambda: mix((tone(1900, 0.02, 260), 0.6), (noise(0.015, 300, hp=True, seed=7), 0.5)),
    "click": lambda: mix((noise(0.04, 110, lp=0.6, seed=9), 1.0), (tone(1150, 0.04, 90), 0.4)),
    "whoosh": whoosh,
    "scratch": scratch,
    "ding": lambda: mix((tone(1046.5, 0.5, 7), 0.6), (tone(2093, 0.35, 10), 0.15),
                        ([0.0] * int(0.08 * SR) + tone(1568, 0.6, 6), 0.6)),
    "slam": lambda: mix((tone(110, 0.5, 7, f_end=38), 1.0), (noise(0.14, 22, lp=0.25, seed=11), 0.6)),
    "thud": lambda: mix((tone(150, 0.22, 16, f_end=70), 1.0), (noise(0.05, 60, lp=0.3, seed=13), 0.3)),
}
GAIN = {"pop": 0.35, "tick": 0.22, "type": 0.10, "click": 0.35, "whoosh": 0.30, "scratch": 0.45,
        "ding": 0.30, "slam": 0.75, "thud": 0.45}


def make_sfx(events, total, path):
    buf, cache = _zeros(total), {}
    for e in events:
        if e["type"] not in cache:
            cache[e["type"]] = SFX[e["type"]]()
        _add(buf, e["t"], cache[e["type"]], GAIN[e["type"]])
    _write(buf, path)


def make_bgm(total, path, bpm=124):
    beat = 60 / bpm
    buf = _zeros(total)
    kick = tone(140, 0.22, 14, f_end=45)
    clap = mix((noise(0.12, 30, lp=0.7, seed=21), 1.0), (noise(0.12, 30, hp=True, seed=22), 0.6))
    hat = noise(0.035, 120, hp=True, seed=23)
    # C - Am - F - G 진행: (베이스 음, 화음)
    prog = [(130.81, (261.63, 329.63, 392.00)), (110.00, (220.00, 261.63, 329.63)),
            (87.31, (174.61, 220.00, 261.63)), (98.00, (196.00, 246.94, 293.66))]
    bass = {r: tone(r, beat * 0.45, 9, shape="tri") for r, _ in prog}
    stab = {c: mix(*[(tone(f, beat * 0.4, 11, shape="tri"), 1 / 3) for f in c]) for _, c in prog}
    for bar in range(int(total / (4 * beat)) + 1):
        root, chord = prog[bar % 4]
        t0 = bar * 4 * beat
        for b in range(4):
            _add(buf, t0 + b * beat, kick, 0.55)
            _add(buf, t0 + (b + 0.5) * beat, hat, 0.16)
            if b in (1, 3):
                _add(buf, t0 + b * beat, clap, 0.22)
                _add(buf, t0 + (b + 0.5) * beat, stab[chord], 0.16)
        for e, on in enumerate((1, 0, 1, 1, 0, 1, 0, 1)):
            if on:
                _add(buf, t0 + e * beat / 2, bass[root], 0.32)
    # 끝 1초는 서서히 줄인다
    fade = int(1.0 * SR)
    for i in range(fade):
        k = len(buf) - fade + i
        if k >= 0:
            buf[k] *= 1 - i / fade
    _write(buf, path, peak=0.5)
