// 디자이너 편 공통: 실제 로고 시안(Design 캔버스에서 lib/snap.py로 찍은 PNG)과 CDO 의자
// engine.js 다음, 편의 장면 스크립트 앞에 불러온다. start() 전에 이미지를 채워 두면 엔진이 로딩을 기다린다.

const LOGO_DIR = '../design/logo/png/';
// 1차 시안 12개. 화면 번호 = 순서 + 1 (캔버스의 01~12와 같다)
const R1 = ['Main', 'L02', 'L03', 'L04', 'L05', 'L06', 'L07', 'L08', 'L09', 'L10', 'L11', 'L12'];
const logoImg = id => `<img src="${LOGO_DIR}${id}.png" alt="">`;

// <div class="lg" data-logo="B1"> → 그 시안 이미지
$$('[data-logo]').forEach(el => el.insertAdjacentHTML('afterbegin', logoImg(el.dataset.logo)));

// <div class="lgrid4" id="s3-grid" data-r1> → 1차 시안 12개 격자. 칸 id는 s3-grid-1 ~ s3-grid-12, 판정 표시는 그 안의 .mk
$$('[data-r1]').forEach(el => {
  el.innerHTML = R1.map((id, i) => `<div class="lg" id="${el.id}-${i + 1}">${logoImg(id)}
    <div class="no">${String(i + 1).padStart(2, '0')}</div><div class="mk"></div></div>`).join('');
});
const cell = (grid, n) => $(`${grid}-${n}`);
// 판정 표시: kind = x(버려) | o(살려) | t(보강)
function mark(grid, n, kind, text, t, at) {
  const m = cell(grid, n).querySelector('.mk');
  m.className = 'mk ' + kind;
  m.textContent = text;
  pop(m, t, at, 0.35, -6);
}

// CDO 의자 (인물 뒤에 깐다. 인물과 같은 300x420 비율)
function chairSVG() {
  return `<svg viewBox="0 0 300 420" width="100%" height="100%">
    <rect x="36" y="20" width="228" height="290" rx="64" fill="#3B3F4A"/>
    <rect x="58" y="44" width="184" height="240" rx="50" fill="#4A4F5C"/>
    <rect x="0" y="236" width="44" height="100" rx="18" fill="#2B2E36"/><rect x="256" y="236" width="44" height="100" rx="18" fill="#2B2E36"/>
    <rect x="138" y="330" width="24" height="56" fill="#2B2E36"/>
    <path d="M150 384 L52 404 M150 384 L248 404 M150 384 L150 410" stroke="#2B2E36" stroke-width="14" stroke-linecap="round"/>
    <circle cx="52" cy="408" r="10" fill="#211C17"/><circle cx="248" cy="408" r="10" fill="#211C17"/><circle cx="150" cy="412" r="8" fill="#211C17"/>
  </svg>`;
}
$$('[data-chair]').forEach(el => { el.innerHTML = chairSVG(); });

// 2부 화면 모형의 마우스 커서: <div class="cursor" data-cursor>
$$('[data-cursor]').forEach(el => {
  el.innerHTML = `<svg viewBox="0 0 24 30" width="100%" height="100%"><path d="M2 2 L2 24 L8 18 L12 28 L16 26 L12 16 L20 16 Z"
    fill="#211C17" stroke="#fff" stroke-width="2" stroke-linejoin="round"/></svg>`;
});
// keys = [[시각, x, y], ...] 사이를 부드럽게 옮긴다. clicks = 누르는 시각들 (그 순간 살짝 작아진다)
function cursorAt(el, t, keys, clicks = []) {
  let [, x, y] = keys[0];
  for (let i = 1; i < keys.length; i++) {
    const [t0, x0, y0] = keys[i - 1], [t1, x1, y1] = keys[i];
    if (t >= t0) {
      const k = eo(prog(t, t0, t1 - t0));
      x = x0 + (x1 - x0) * k;
      y = y0 + (y1 - y0) * k;
    }
  }
  const press = clicks.some(c => t >= c && t < c + 0.15);
  el.style.opacity = t >= keys[0][0] ? 1 : 0;
  el.style.transform = `translate(${x}px, ${y}px) scale(${press ? 0.8 : 1})`;
}
// el의 왼쪽 위 위치를 root 기준으로 (커서를 화면 속 버튼·링크에 맞출 때. 변형(transform)과 상관없는 배치 위치)
function posIn(el, root) {
  let x = 0, y = 0;
  for (let e = el; e && e !== root; e = e.offsetParent) { x += e.offsetLeft; y += e.offsetTop; }
  return [x, y];
}
// 답이 한 줄씩 올라오는 모습: els를 at부터 gap 간격으로 차례로 띄운다
function stream(els, t, at, gap = 0.25) { els.forEach((el, i) => rise(el, t, at + i * gap, 0.25, 12)); }
