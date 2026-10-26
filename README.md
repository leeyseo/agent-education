# AI 신입 길들이기 — 에이전트 교육 숏츠

정적 홈페이지를 만들어 카페24에 FTP로 올리던 디자인·홈페이지 제작 업체를 위한 세로 숏츠 19편(EP0~EP18, 총 약 9분 30초)과, 그 영상을 만드는 코드다. AI를 검색창 정도로 알던 사람이 "에이전트에게 일을 맡기고, 의심하며 디렉팅하는 법"까지 가는 것이 목표다.

화면은 HTML 애니메이션을 한 프레임씩 찍어 만들고, 내레이션은 ElevenLabs(Brian 목소리)로 읽는다. 영상·음성 파일은 저장소에 넣지 않았다. 아래 명령으로 언제든 다시 만든다.

## 문서

| 문서 | 내용 |
| --- | --- |
| [01-시리즈-기획](docs/01-시리즈-기획.md) | 대상, 핵심 비유, 등장인물, 4부 구성, 화면 원칙 |
| [02-에피소드-대본](docs/02-에피소드-대본.md) | 19편 내레이션 전체와 길이 |
| [03-제작-가이드](docs/03-제작-가이드.md) | 새 편을 만들고, 확인하고, 렌더링하는 방법 |
| [04-작업-기록](docs/04-작업-기록.md) | 이 작업을 하며 정한 것과 그 이유, 남은 일 |
| [05-디자이너편-기획](docs/05-디자이너편-기획.md) | 후속 시리즈 '디자이너 편' 18편 구성, 실제 결과물 원칙, 로고 시안 작업 기록 |
| [06-디자이너편-대본](docs/06-디자이너편-대본.md) | 디자이너 편 내레이션 (지금까지 만든 EP0~EP8) |
| [07-2부-촬영-가이드](docs/07-2부-촬영-가이드.md) | 2부를 실제 claude.ai 화면 녹화로 바꿀 때의 순서와 지시문 (지금은 모형 화면) |

## 폴더 구조

```
shorts/
  lib/            모든 편이 같이 쓰는 엔진
    engine.js       애니메이션·캐릭터·자막·미리보기 런타임
    base.css        공통 스타일과 화면 부품 (터미널, 채팅, 브라우저, 휴대폰 등)
    build.py        script.json → ElevenLabs 내레이션 + timeline.js
    render.py       index.html → 1080x1920 30fps mp4
    sheet.py        확인용 정지 화면 모음 (stills/sheet.png)
    snap.py         Design 캔버스 아트보드(.dc.html) → PNG (실제 시안을 영상에 넣을 때)
    clip.py         화면 녹화본 → 장면에 넣을 클립 (구간 자르기, 영역 잘라내기)
  ep00 ~ ep18/    편마다 script.json(대사) + index.html(장면)
  ep01/           첫 편. 공통 엔진 이전에 따로 만든 버전 (자체 build.py·render.py)
    _v2/          되돌린 '빠른 버전' 실험 (훅·효과음·배경음악 합성 코드 포함)
  s2/             디자이너 편
    s2.css, s2.js   이 시리즈 공통 부품 (실제 시안 카드, 판정 표시, 회의 테이블, CDO 의자)
    design/logo/    Claude Design 캔버스로 만든 실제 로고 시안 (project/ 원본, png/ 영상용)
    rec/            2부 녹화: 자료/(claude.ai에 올릴 가상 자료), raw/(녹화 원본), clips/(잘라낸 클립)
    ep00 ~ ep08/    편마다 script.json + index.html (EP6~EP8은 claude.ai 모형 화면)
docs/             기획·대본·제작 가이드·작업 기록
```

## 빠르게 시작하기

1. 준비물: Python 3.12, Google Chrome, ffmpeg(PATH에 있어야 함)
   ```
   pip install -r requirements.txt
   ```
2. ElevenLabs API 키를 `shorts/.env`(또는 편 폴더의 `.env`)에 넣는다. `.env`는 커밋되지 않는다.
   ```
   ELEVENLABS_API_KEY=...
   ```
3. 한 편 만들기 (`shorts/` 폴더에서)
   ```
   python lib/build.py ep05     # 내레이션과 타이밍 (ElevenLabs 크레딧 사용)
   python lib/sheet.py ep05     # 장면별 정지 화면 확인 → ep05/stills/sheet.png
   python lib/render.py ep05    # mp4 → ep05/EP05_....mp4
   ```
   EP1은 `cd shorts/ep01 && python build.py && python render.py`
   디자이너 편은 폴더 앞에 `s2/`를 붙인다: `python lib/build.py s2/ep01`
4. 미리보기: `shorts/ep05/index.html`을 브라우저로 열고 "미리보기 재생"

내레이션은 편당 약 110~230자의 ElevenLabs 크레딧이 든다. 같은 대사는 다시 요청하지 않으므로, 대사를 고친 줄만 다시 만든다.
