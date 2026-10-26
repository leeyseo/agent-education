"""2부 녹화 때 claude.ai에 올릴 가상 자료를 만든다 (모닝빵 베이커리 2호점, 전부 지어낸 내용).

  python s2/rec/make_materials.py      → s2/rec/자료/ 에 PDF 2개, PNG 2개

기획서와 회의 자료는 일부러 두 군데가 서로 다르다(오픈 시기, 브로셔 접지).
EP7에서 "자료끼리 안 맞는 부분"을 AI가 찾아내는 장면을 찍기 위해서다.
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent / "자료"
FONT = "<link href='https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&family=Nanum+Pen+Script&display=block' rel='stylesheet'>"

BRIEF = FONT + """
<style>
  body { font-family: 'Noto Sans KR', sans-serif; color: #222; margin: 0; padding: 48px 56px; font-size: 14px; line-height: 1.7; }
  h1 { font-size: 26px; margin: 0 0 4px; } .by { color: #666; margin-bottom: 28px; }
  h2 { font-size: 17px; margin: 26px 0 6px; border-bottom: 2px solid #222; padding-bottom: 4px; }
  ul { margin: 0; padding-left: 20px; } q { font-style: italic; }
</style>
<h1>모닝빵 베이커리 2호점 오픈 준비 기획서</h1>
<div class="by">픽셀공방 김기획 · 2026년 10월</div>
<h2>1. 가게 소개</h2>
<ul>
  <li>2012년에 문을 연 동네 빵집. 사장님이 매일 새벽 5시에 오븐을 켠다.</li>
  <li>대표 메뉴: 모닝빵, 우유식빵, 소금빵</li>
  <li>손님 대부분은 걸어서 오는 동네 단골. 최근 인스타그램을 보고 찾아오는 손님이 늘었다.</li>
</ul>
<h2>2. 2호점</h2>
<ul>
  <li>위치: 지하철역 앞 상가 1층. 출근길에 지나가는 사람이 많다.</li>
  <li>오픈: 2026년 11월 말 예정</li>
  <li>노리는 손님: 출근길 직장인, 아침을 자주 거르는 사람</li>
</ul>
<h2>3. 맡은 일</h2>
<ul>
  <li>로고 리뉴얼 (1호점 간판도 함께 바꿀 예정)</li>
  <li>오픈 안내 브로셔: A4 3단 접지</li>
  <li>홈페이지 리뉴얼: 폰에서 깨지는 문제 해결, 메뉴와 가격을 사장님이 쉽게 고칠 수 있게</li>
</ul>
<h2>4. 사장님 요청 (회의 메모)</h2>
<ul>
  <li><q>1호점 단골이 2호점도 같은 집인 줄 알았으면 좋겠어요.</q></li>
  <li><q>너무 세련돼서 비싸 보이면 안 돼요.</q></li>
  <li><q>인스타 보고 오는 손님이 많은데, 폰에서 홈페이지가 다 깨져요.</q></li>
</ul>
<h2>5. 아직 정하지 않은 것</h2>
<ul><li>예산</li><li>2호점에만 파는 메뉴를 둘지</li></ul>
"""

SLIDE = """
<section><div class="k">픽셀공방 · 2026.10</div><h1>모닝빵 2호점<br>리브랜딩 킥오프</h1></section>
<section><div class="k">지금 고민</div><ol>
  <li>로고가 2016년 그대로다</li><li>홈페이지가 폰에서 깨진다</li><li>2호점이 '같은 집'으로 보여야 한다</li></ol></section>
<section><div class="k">일정</div><ol>
  <li>로고 확정 · 11월 첫 주</li><li>브로셔 인쇄 · 11월 셋째 주</li><li>홈페이지 · 12월 첫 주</li><li>2호점 오픈 · 12월 첫 주</li></ol></section>
<section><div class="k">브로셔</div><ol>
  <li>A4 2단 리플릿</li><li>앞면: 2호점 오픈 소식과 약도</li><li>뒷면: 대표 메뉴 3가지</li></ol></section>
"""
DECK = FONT + """
<style>
  @page { size: 1280px 720px; margin: 0; }
  body { margin: 0; font-family: 'Noto Sans KR', sans-serif; }
  section { width: 1280px; height: 720px; box-sizing: border-box; padding: 90px 110px; background: #FFF8F1; color: #3B2A22;
    page-break-after: always; position: relative; }
  section::after { content: ''; position: absolute; left: 110px; bottom: 70px; width: 120px; height: 10px; background: #FF7A2F; }
  .k { font-size: 28px; font-weight: 700; color: #FF7A2F; }
  h1 { font-size: 84px; line-height: 1.2; margin: 30px 0 0; }
  ol { font-size: 46px; font-weight: 700; line-height: 1.9; margin: 30px 0 0; padding-left: 60px; }
</style>
""" + SLIDE

MENU = FONT + """
<style>
  body { margin: 0; }
  .board { width: 900px; height: 1200px; box-sizing: border-box; background: #2F3A33; border: 28px solid #8B5A3C; color: #F4F1E8;
    font-family: 'Nanum Pen Script', cursive; padding: 60px 70px; }
  h1 { font-size: 110px; margin: 0; text-align: center; font-weight: 400; }
  .sub { text-align: center; font-size: 46px; color: #E8C27A; margin-bottom: 40px; }
  .row { display: flex; justify-content: space-between; font-size: 72px; line-height: 1.45; border-bottom: 3px dashed #5C6B60; }
  .foot { margin-top: 50px; text-align: center; font-size: 56px; color: #E8C27A; }
</style>
<div class="board">
  <h1>모닝빵 메뉴</h1><div class="sub">1호점 · since 2012</div>
  <div class="row"><span>모닝빵 (6개)</span><span>3,000</span></div>
  <div class="row"><span>우유식빵</span><span>4,500</span></div>
  <div class="row"><span>소금빵</span><span>2,800</span></div>
  <div class="row"><span>단팥빵</span><span>2,500</span></div>
  <div class="row"><span>아메리카노</span><span>2,000</span></div>
  <div class="foot">매일 새벽 다섯 시에 굽습니다</div>
</div>
"""

OLD_LOGO = """
<style>body { margin: 0; }</style>
<div style="width:800px;height:300px;background:#fff;display:flex;align-items:center;justify-content:center">
  <div style="background:#8A8A8A;color:#fff;font:bold 52px Gulim,'Times New Roman',serif;padding:30px 44px;white-space:nowrap">MORNING BREAD 모닝빵</div>
</div>
"""


def main():
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page()
        page.set_content(BRIEF, wait_until="networkidle")
        page.pdf(path=str(OUT / "모닝빵_2호점_기획서.pdf"), format="A4", print_background=True)
        page.set_content(DECK, wait_until="networkidle")
        page.pdf(path=str(OUT / "모닝빵_2호점_회의자료.pdf"), width="1280px", height="720px", print_background=True)
        for name, html, size in (("1호점_메뉴판.png", MENU, (900, 1200)), ("기존_로고_2016.png", OLD_LOGO, (800, 300))):
            page.set_viewport_size({"width": size[0], "height": size[1]})
            page.set_content(html, wait_until="networkidle")
            page.screenshot(path=str(OUT / name))
        browser.close()
    for f in sorted(OUT.iterdir()):
        print(f.name)


if __name__ == "__main__":
    main()
