// AI 신입 길들이기 — 모든 편이 같이 쓰는 런타임
// 편마다 index.html에서 장면 마크업(#area 안의 .scene)과 SCENE 함수들을 정의하고 start(SCENE)를 부른다.
// 모든 움직임은 시간 t로만 정해지므로, 렌더러가 seek(t)로 아무 프레임이나 똑같이 다시 그릴 수 있다.

const TL = window.TIMELINE;
const $ = id => document.getElementById(id);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

// ---------- 애니메이션 도우미 ----------
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const prog = (t, at, dur) => clamp((t - at) / dur);
const eo = x => 1 - Math.pow(1 - x, 3);
const eb = x => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
function put(el, o, y = 0, s = 1, r = 0, x = 0) {
  el.style.opacity = o;
  el.style.transform = `translate(${x}px, ${y}px) scale(${s}) rotate(${r}deg)`;
}
function rise(el, t, at, dur = 0.35, dist = 40) { const k = eo(prog(t, at, dur)); put(el, k, (1 - k) * dist); }
function slide(el, t, at, dur = 0.4, dist = 120) { const k = eo(prog(t, at, dur)); put(el, k, 0, 1, 0, (1 - k) * dist); }
function pop(el, t, at, dur = 0.4, r = 0) { const k = prog(t, at, dur); put(el, clamp(k * 1.6), 0, k ? 0.6 + 0.4 * eb(k) : 0.6, r); }
function fade(el, t, at, dur = 0.3) { el.style.opacity = prog(t, at, dur); }
function hide(el, t, at, dur = 0.25) { el.style.opacity = 1 - prog(t, at, dur); }
function typeText(el, text, t, at, cps) {
  const n = Math.floor(clamp((t - at) * cps, 0, text.length));
  el.textContent = text.slice(0, n);
  return n >= text.length;
}
function meterTo(el, t, at, dur, pct) { el.style.width = eo(prog(t, at, dur)) * pct + '%'; }
function countTo(el, t, at, dur, n, fmt = v => v.toLocaleString()) { el.textContent = fmt(Math.round(eo(prog(t, at, dur)) * n)); }
const blink = t => Math.floor(t * 2.5) % 2 ? 0 : 1;
const spin = t => '◐◓◑◒'[Math.floor(t * 10) % 4];
const bob = (t, k = 1, amp = 3, f = 14) => Math.sin(t * f) * amp * k;
// 그 단어를 말하기 시작하는 시각(장면 기준). 못 찾으면 fallback
const when = (W, s, fallback = 0) => (W.find(x => x.w.includes(s)) || { t: fallback }).t;

// ---------- 화면 녹화 클립 ----------
// <canvas data-src="../rec/clips/ep07_a.mp4" width="1920" height="1080"> (lib/clip.py로 만든 클립)
// 숨긴 <video>로 탐색하고, 탐색을 마친 프레임을 캔버스에 그린다. 화면 합성 타이밍과 상관없이 정확한 프레임이 찍힌다
function initClips() {
  $$('canvas[data-src]').forEach(cv => {
    const v = document.createElement('video');
    v.muted = true;
    v.preload = 'auto';
    v.src = cv.dataset.src;
    v.style.display = 'none';
    cv.video = v;
    cv.draw = () => cv.getContext('2d').drawImage(v, 0, 0, cv.width, cv.height);
    v.addEventListener('seeked', cv.draw);
    v.addEventListener('loadeddata', cv.draw);
    document.body.appendChild(v);
  });
}
// 장면 시각 at~at+dur 동안 녹화본의 a~b초를 보여 준다. 구간이 길면 그만큼 빨리 감긴다
function clip(cv, t, at, dur, a, b) {
  const v = cv.video, want = a + (b - a) * prog(t, at, dur);
  if (Math.abs(v.currentTime - want) > 0.001) v.currentTime = want;
}
// 렌더러가 프레임마다 기다린다: 모든 클립이 탐색을 마치면 그 프레임을 그리고 끝낸다
window.settle = () => new Promise(res => {
  const t0 = performance.now(), cvs = $$('canvas[data-src]');
  const check = () => {
    if (cvs.every(c => !c.video.seeking && c.video.readyState >= 2) || performance.now() - t0 > 5000) {
      cvs.forEach(c => c.draw());
      res();
    } else requestAnimationFrame(check);
  };
  check();
});

// ---------- 캐릭터 ----------
const SKIN = '#F7D4B8', HAIR = '#2B2420', HOOD = '#4FD1B5';

function faceParts(mood, skin, ink) {
  const eyes = mood === 'proud'
    ? `<path d="M102 174 Q116 160 130 174" stroke="${ink}" stroke-width="7" fill="none" stroke-linecap="round"/><path d="M170 174 Q184 160 198 174" stroke="${ink}" stroke-width="7" fill="none" stroke-linecap="round"/>`
    : `<circle cx="116" cy="172" r="${mood === 'shock' ? 11 : 9}" fill="${ink}"/><circle cx="186" cy="172" r="${mood === 'shock' ? 11 : 9}" fill="${ink}"/>
       <circle cx="119" cy="168" r="3" fill="#fff"/><circle cx="189" cy="168" r="3" fill="#fff"/>`;
  const mouths = {
    smile: `<path d="M124 214 Q150 248 176 214 Z" fill="#B23A3A"/><path d="M136 230 Q150 240 164 230 Q150 225 136 230 Z" fill="#FF8C8C"/>`,
    proud: `<path d="M124 214 Q150 248 176 214 Z" fill="#B23A3A"/><path d="M136 230 Q150 240 164 230 Q150 225 136 230 Z" fill="#FF8C8C"/>`,
    grin: `<path d="M126 220 Q150 240 174 220" stroke="#8A3A2E" stroke-width="7" fill="none" stroke-linecap="round"/>`,
    oops: `<ellipse cx="150" cy="228" rx="12" ry="15" fill="#B23A3A"/>`,
    shock: `<ellipse cx="150" cy="230" rx="16" ry="20" fill="#B23A3A"/>`,
    sad: `<path d="M128 234 Q150 216 172 234" stroke="#8A3A2E" stroke-width="7" fill="none" stroke-linecap="round"/>`,
    skeptic: `<path d="M126 226 Q152 216 178 230" stroke="#8A3A2E" stroke-width="7" stroke-linecap="round" fill="none"/>`,
  };
  const sweat = (mood === 'oops' || mood === 'sad') ? `<path d="M236 112 q14 24 0 34 q-14 -10 0 -34z" fill="#7EC8F5"/>` : '';
  return eyes + (mouths[mood] || mouths.smile) + sweat;
}

// 디자이너 편의 열정이 분신: 같은 AI가 역할만 바꿔 쓴 모자와 명찰
const ROLE = {
  analyst: { badge: '분석', color: '#3D6EF0',
    hat: `<path d="M58 124 C58 -14 242 -14 242 124 Z" fill="#3D6EF0"/><path d="M200 116 Q282 110 290 130 Q244 138 200 130 Z" fill="#2F57C7"/>` },
  planner: { badge: '기획', color: '#C99A12',
    hat: `<path d="M64 112 C64 -6 236 -6 236 112 Z" fill="#FFD84D"/><path d="M150 26 L150 108" stroke="#E9BF2B" stroke-width="12"/><rect x="46" y="102" width="208" height="20" rx="10" fill="#E9BF2B"/>` },
  designer: { badge: '디자인', color: '#FF7A2F',
    hat: `<ellipse cx="138" cy="66" rx="108" ry="46" fill="#FF7A2F" transform="rotate(-10 138 66)"/><circle cx="132" cy="22" r="11" fill="#E0661E"/>` },
  copy: { badge: '카피', color: '#D9468F',
    hat: `<path d="M70 104 Q76 18 150 18 Q224 18 230 104 Z" fill="#F06BA8"/><ellipse cx="150" cy="106" rx="106" ry="16" fill="#D9468F"/>` },
  critic: { badge: '비평', color: '#E5484D',
    hat: `<path d="M92 76 Q64 30 94 4 Q98 44 124 62 Z" fill="#E5484D"/><path d="M208 76 Q236 30 206 4 Q202 44 176 62 Z" fill="#E5484D"/>` },
};

// 열정이: kind = laptop(노트북 앞) | cheer(만세) | stand | coffee | thumb(엄지척)
// mood = smile | proud | oops | shock | sad | skeptic, role = ROLE의 키(없으면 NEW 명찰)
function yjSVG(kind = 'stand', mood = 'smile', role = '') {
  const R = ROLE[role];
  const tall = kind !== 'laptop';
  const legs = tall ? `
    <rect x="108" y="396" width="36" height="66" rx="12" fill="#3B3F4A"/><rect x="156" y="396" width="36" height="66" rx="12" fill="#3B3F4A"/>
    <ellipse cx="120" cy="466" rx="28" ry="11" fill="${HAIR}"/><ellipse cx="180" cy="466" rx="28" ry="11" fill="${HAIR}"/>` : '';
  const arm = (d, hx, hy) => `<path d="${d}" stroke="${HOOD}" stroke-width="30" stroke-linecap="round" fill="none"/><circle cx="${hx}" cy="${hy}" r="18" fill="${SKIN}"/>`;
  const arms = {
    cheer: arm('M86 318 Q44 272 36 216', 36, 206) + arm('M214 318 Q256 272 264 216', 264, 206),
    stand: arm('M74 330 Q62 370 70 400', 70, 404) + arm('M226 330 Q238 370 230 400', 230, 404),
    coffee: arm('M74 330 Q62 370 70 400', 70, 404) + arm('M222 330 Q262 340 250 300', 250, 296)
      + `<rect x="228" y="236" width="46" height="54" rx="8" fill="#fff" stroke="${HAIR}" stroke-width="5"/>
         <path d="M240 226 q-6 -12 0 -22 M256 226 q-6 -12 0 -22" stroke="#C9BBA9" stroke-width="5" fill="none" stroke-linecap="round"/>`,
    thumb: arm('M74 330 Q62 370 70 400', 70, 404) + arm('M222 330 Q262 330 256 286', 256, 280)
      + `<rect x="248" y="236" width="18" height="34" rx="9" fill="${SKIN}" stroke="#E0B08E" stroke-width="3"/>`,
  }[kind] || '';
  const laptop = kind === 'laptop' ? `
    <path d="M44 322 L256 322 L244 404 L56 404 Z" fill="#C9CED6"/><rect x="24" y="400" width="252" height="18" rx="7" fill="#9EA5B0"/>
    <circle cx="150" cy="362" r="13" fill="#fff" opacity=".75"/>
    <g class="tap" stroke="#FFB020" stroke-width="6" stroke-linecap="round">
      <path d="M30 344 l-20 -10"/><path d="M26 368 l-22 0"/><path d="M30 392 l-20 10"/>
      <path d="M270 344 l20 -10"/><path d="M274 368 l22 0"/><path d="M270 392 l20 10"/>
    </g>` : '';
  return `<svg viewBox="0 0 300 ${tall ? 480 : 420}" width="100%" height="100%">
    ${legs}
    <path d="M60 420 C60 332 95 286 150 286 C205 286 240 332 240 420 Z" fill="${HOOD}"/>
    <path d="M100 292 Q150 332 200 292 Q190 320 150 324 Q110 320 100 292 Z" fill="#36B89C"/>
    <path d="M135 320 L131 362" stroke="#fff" stroke-width="5" stroke-linecap="round"/>
    <path d="M165 320 L169 362" stroke="#fff" stroke-width="5" stroke-linecap="round"/>
    ${R ? `<rect x="164" y="350" width="72" height="32" rx="7" fill="#fff"/>
           <text x="200" y="373" font-size="19" font-weight="900" text-anchor="middle" fill="${R.color}" font-family="sans-serif">${R.badge}</text>`
        : `<rect x="176" y="352" width="48" height="28" rx="6" fill="#fff"/>
           <text x="200" y="372" font-size="16" font-weight="900" text-anchor="middle" fill="#1FB394" font-family="sans-serif">NEW</text>`}
    ${arms}
    <rect x="132" y="244" width="36" height="48" rx="12" fill="#EFC3A2"/>
    <circle cx="60" cy="170" r="18" fill="${SKIN}"/><circle cx="240" cy="170" r="18" fill="${SKIN}"/>
    <circle cx="150" cy="160" r="92" fill="${SKIN}"/>
    <path d="M54 170 C46 92 96 50 150 50 C206 50 256 92 246 170 L236 150 L226 126 L210 142 L198 116 L180 136 L166 108 L150 134 L134 108 L120 136 L102 116 L90 142 L74 126 L64 150 Z" fill="${HAIR}"/>
    <path d="M118 58 L104 24 L140 50 Z M146 52 L152 16 L168 52 Z M178 56 L206 30 L198 70 Z" fill="${HAIR}"/>
    <ellipse cx="94" cy="204" rx="16" ry="10" fill="#FF9F8A" opacity=".55"/><ellipse cx="206" cy="204" rx="16" ry="10" fill="#FF9F8A" opacity=".55"/>
    ${faceParts(mood, SKIN, HAIR)}
    <circle cx="114" cy="170" r="30" fill="#fff" fill-opacity=".25" stroke="${HAIR}" stroke-width="7"/>
    <circle cx="186" cy="170" r="30" fill="#fff" fill-opacity=".25" stroke="${HAIR}" stroke-width="7"/>
    <path d="M144 168 Q150 162 156 168" stroke="${HAIR}" stroke-width="6" fill="none"/>
    ${R ? R.hat : ''}
    ${laptop}
  </svg>`;
}

// 김기획: mood = skeptic | shock | grin | facepalm | proud
function bossSVG(mood = 'skeptic') {
  const skin = '#F1C7A6', hair = '#3E3A38';
  const brows = mood === 'shock'
    ? `<path d="M92 120 L132 112" stroke="${hair}" stroke-width="9" stroke-linecap="round"/><path d="M168 112 L208 120" stroke="${hair}" stroke-width="9" stroke-linecap="round"/>`
    : `<path d="M90 134 L132 124" stroke="${hair}" stroke-width="9" stroke-linecap="round"/><path d="M168 118 L210 130" stroke="${hair}" stroke-width="9" stroke-linecap="round"/>`;
  const face = mood === 'facepalm'
    ? `<path d="M126 228 Q150 220 174 228" stroke="#8A3A2E" stroke-width="7" stroke-linecap="round" fill="none"/>
       <path d="M150 420 L150 330 Q120 300 120 250" stroke="#34425E" stroke-width="34" stroke-linecap="round" fill="none"/>
       <ellipse cx="146" cy="172" rx="62" ry="36" fill="#E9B997"/>
       <path d="M100 160 L190 156 M98 176 L192 174 M104 192 L186 192" stroke="#D49C78" stroke-width="4" stroke-linecap="round"/>`
    : `<rect x="84" y="146" width="58" height="42" rx="10" fill="#fff" fill-opacity=".3" stroke="${hair}" stroke-width="6"/>
       <rect x="158" y="146" width="58" height="42" rx="10" fill="#fff" fill-opacity=".3" stroke="${hair}" stroke-width="6"/>
       <path d="M142 162 L158 162" stroke="${hair}" stroke-width="6"/>
       <circle cx="114" cy="168" r="${mood === 'shock' ? 9 : 7}" fill="${hair}"/><circle cx="186" cy="166" r="${mood === 'shock' ? 9 : 7}" fill="${hair}"/>
       ${{ shock: `<ellipse cx="152" cy="230" rx="15" ry="19" fill="#8A3A2E"/>`,
           grin: `<path d="M124 220 Q152 246 180 220" stroke="#8A3A2E" stroke-width="7" stroke-linecap="round" fill="none"/>`,
           proud: `<path d="M124 216 Q152 250 180 216 Z" fill="#8A3A2E"/>` }[mood]
         || `<path d="M126 226 Q152 216 178 230" stroke="#8A3A2E" stroke-width="7" stroke-linecap="round" fill="none"/>`}`;
  return `<svg viewBox="0 0 300 420" width="100%" height="100%">
    <path d="M50 420 C50 332 90 288 150 288 C210 288 250 332 250 420 Z" fill="#34425E"/>
    <path d="M116 290 L150 344 L184 290 Z" fill="#fff"/>
    <path d="M150 304 L141 344 L150 400 L159 344 Z" fill="#E0663A"/>
    <rect x="132" y="246" width="36" height="48" rx="12" fill="#E9B997"/>
    <circle cx="60" cy="172" r="18" fill="${skin}"/><circle cx="240" cy="172" r="18" fill="${skin}"/>
    <circle cx="150" cy="162" r="92" fill="${skin}"/>
    <path d="M56 160 C50 90 96 54 152 54 C210 54 252 92 244 160 C238 128 226 110 206 102 C176 94 126 96 100 108 C82 118 66 134 56 160 Z" fill="${hair}"/>
    <path d="M56 160 C56 142 60 130 66 122 L70 160 Z" fill="#A39D97"/><path d="M244 160 C244 142 240 130 234 122 L230 160 Z" fill="#A39D97"/>
    ${brows}
    ${face}
  </svg>`;
}

// 나머지 인물: sian(디자이너 최시안) | tag(퍼블리셔 박태그) | owner(모닝빵 사장님) | junior(사람 신입, 사원증)
const PEOPLE = {
  sian: {
    skin: '#F5D0B5', neck: '#E9BC9C', top: '#FF9A5C', ink: '#3B2A22',
    back: `<path d="M48 170 C42 88 96 50 150 50 C204 50 258 88 252 170 L256 252 Q254 266 238 266 L62 266 Q46 266 44 252 Z" fill="#5A3A2A"/>`,
    collar: `<path d="M114 292 Q150 320 186 292" stroke="#E07B3D" stroke-width="9" fill="none" stroke-linecap="round"/>`,
    hair: `<path d="M56 160 C52 88 100 54 150 54 C200 54 248 88 244 160 L236 136 L64 136 Z" fill="#5A3A2A"/>`,
    extra: `<g transform="rotate(-32 246 140)"><rect x="238" y="96" width="14" height="84" rx="3" fill="#FFD84D"/><path d="M238 180 L245 198 L252 180 Z" fill="#F1C7A6"/><rect x="238" y="92" width="14" height="10" fill="#FF8C8C"/></g>
            <circle cx="60" cy="194" r="7" fill="#FFD84D"/><circle cx="240" cy="194" r="7" fill="#FFD84D"/>`,
  },
  tag: {
    skin: '#EDC2A0', neck: '#E0B08E', top: '#7D8794', ink: '#1F1B18',
    collar: `<path d="M100 292 Q150 334 200 292 Q190 322 150 326 Q110 322 100 292 Z" fill="#69727E"/>`,
    hair: `<path d="M56 158 C50 86 100 52 154 52 C210 52 252 92 244 158 C236 120 214 100 186 96 C160 112 120 116 92 112 C76 122 64 138 56 158 Z" fill="#1F1B18"/>`,
    glasses: `<rect x="86" y="148" width="56" height="40" rx="8" fill="#fff" fill-opacity=".25" stroke="#1F1B18" stroke-width="7"/>
              <rect x="158" y="148" width="56" height="40" rx="8" fill="#fff" fill-opacity=".25" stroke="#1F1B18" stroke-width="7"/>
              <path d="M142 164 L158 164" stroke="#1F1B18" stroke-width="6"/>`,
    neckExtra: `<path d="M84 300 Q150 362 216 300" stroke="#2B2420" stroke-width="12" fill="none"/>
                <rect x="64" y="284" width="38" height="48" rx="12" fill="#2B2420"/><rect x="198" y="284" width="38" height="48" rx="12" fill="#2B2420"/>`,
  },
  owner: {
    skin: '#F3CBA8', neck: '#E6B793', top: '#FFFFFF', ink: '#3B2A22',
    collar: `<path d="M98 420 L98 334 Q150 316 202 334 L202 420 Z" fill="#B5835A"/>
             <path d="M112 330 L104 300 M188 330 L196 300" stroke="#B5835A" stroke-width="8" stroke-linecap="round"/>
             <rect x="128" y="360" width="44" height="30" rx="6" fill="#9A6C47"/>`,
    hair: `<path d="M58 168 C58 146 64 132 72 124 L78 168 Z" fill="#8C8076"/><path d="M242 168 C242 146 236 132 228 124 L222 168 Z" fill="#8C8076"/>
           <path d="M84 112 C58 74 98 30 130 50 C140 18 182 18 188 50 C218 30 252 74 220 112 Z" fill="#fff" stroke="#E6DCCF" stroke-width="4"/>
           <rect x="86" y="98" width="132" height="38" rx="8" fill="#fff" stroke="#E6DCCF" stroke-width="4"/>`,
    extra: `<path d="M118 206 Q150 194 182 206 Q166 218 150 209 Q134 218 118 206 Z" fill="#6B4E3A"/>`,
  },
  junior: {
    skin: '#F6D2B6', neck: '#EABD9C', top: '#9AA6B8', ink: '#2B2420',
    collar: `<path d="M116 292 L150 330 L184 292" stroke="#fff" stroke-width="10" fill="none" stroke-linejoin="round"/>`,
    neckExtra: `<path d="M126 300 L150 360 L174 300" stroke="#3D6EF0" stroke-width="6" fill="none"/>
                <rect x="130" y="356" width="40" height="52" rx="6" fill="#fff" stroke="#3D6EF0" stroke-width="4"/>
                <rect x="138" y="366" width="24" height="14" rx="3" fill="#C9D6F5"/>`,
    hair: `<path d="M56 164 C46 84 102 46 152 50 C206 50 254 86 244 164 C238 132 222 108 196 100 C170 92 116 92 94 108 C74 120 62 138 56 164 Z" fill="#2B2420"/>`,
  },
};

function personSVG(who, mood = 'grin') {
  const P = PEOPLE[who];
  return `<svg viewBox="0 0 300 420" width="100%" height="100%">
    ${P.back || ''}
    <path d="M56 420 C56 332 92 288 150 288 C208 288 244 332 244 420 Z" fill="${P.top}" ${P.top === '#FFFFFF' ? 'stroke="#E6DCCF" stroke-width="4"' : ''}/>
    ${P.collar || ''}
    <rect x="132" y="246" width="36" height="48" rx="12" fill="${P.neck}"/>
    ${P.neckExtra || ''}
    <circle cx="60" cy="172" r="18" fill="${P.skin}"/><circle cx="240" cy="172" r="18" fill="${P.skin}"/>
    <circle cx="150" cy="162" r="92" fill="${P.skin}"/>
    ${P.hair}
    <ellipse cx="96" cy="204" rx="15" ry="9" fill="#FF9F8A" opacity=".45"/><ellipse cx="204" cy="204" rx="15" ry="9" fill="#FF9F8A" opacity=".45"/>
    ${faceParts(mood, P.skin, P.ink)}
    ${P.glasses || ''}
    ${P.extra || ''}
  </svg>`;
}

// ---------- 아이콘 ----------
const ICON = {
  mag: c => `<svg viewBox="0 0 46 46" width="100%" height="100%"><circle cx="19" cy="19" r="13" fill="none" stroke="${c}" stroke-width="6"/><path d="M29 29 L41 41" stroke="${c}" stroke-width="7" stroke-linecap="round"/></svg>`,
  folder: c => `<svg viewBox="0 0 48 40" width="100%" height="100%"><path d="M3 8 Q3 4 7 4 L18 4 L22 9 L41 9 Q45 9 45 13 L45 33 Q45 37 41 37 L7 37 Q3 37 3 33 Z" fill="${c}"/></svg>`,
  file: c => `<svg viewBox="0 0 40 48" width="100%" height="100%"><path d="M4 4 L26 4 L36 14 L36 44 L4 44 Z" fill="#fff" stroke="${c}" stroke-width="4" stroke-linejoin="round"/><path d="M26 4 L26 14 L36 14" fill="none" stroke="${c}" stroke-width="4"/></svg>`,
  lock: c => `<svg viewBox="0 0 44 50" width="100%" height="100%"><rect x="4" y="22" width="36" height="25" rx="6" fill="${c}"/><path d="M12 22 L12 15 Q12 5 22 5 Q32 5 32 15 L32 22" fill="none" stroke="${c}" stroke-width="6"/></svg>`,
  key: c => `<svg viewBox="0 0 60 30" width="100%" height="100%"><circle cx="14" cy="15" r="11" fill="none" stroke="${c}" stroke-width="6"/><path d="M25 15 L56 15 M46 15 L46 25 M54 15 L54 23" stroke="${c}" stroke-width="6" stroke-linecap="round"/></svg>`,
  save: c => `<svg viewBox="0 0 44 44" width="100%" height="100%"><path d="M4 4 L34 4 L40 10 L40 40 L4 40 Z" fill="${c}"/><rect x="11" y="4" width="18" height="11" fill="#fff"/><rect x="10" y="24" width="24" height="16" rx="2" fill="#fff"/></svg>`,
  warn: c => `<svg viewBox="0 0 48 44" width="100%" height="100%"><path d="M24 3 L46 41 L2 41 Z" fill="${c}" stroke-linejoin="round"/><rect x="21.5" y="15" width="5" height="14" rx="2" fill="#fff"/><circle cx="24" cy="34" r="3" fill="#fff"/></svg>`,
  check: c => `<svg viewBox="0 0 44 44" width="100%" height="100%"><circle cx="22" cy="22" r="20" fill="${c}"/><path d="M12 22 L19 29 L32 15" stroke="#fff" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  x: c => `<svg viewBox="0 0 44 44" width="100%" height="100%"><circle cx="22" cy="22" r="20" fill="${c}"/><path d="M14 14 L30 30 M30 14 L14 30" stroke="#fff" stroke-width="5" stroke-linecap="round"/></svg>`,
  trash: c => `<svg viewBox="0 0 40 46" width="100%" height="100%"><rect x="4" y="8" width="32" height="5" rx="2" fill="${c}"/><rect x="14" y="3" width="12" height="6" rx="2" fill="${c}"/><path d="M8 15 L32 15 L29 43 L11 43 Z" fill="${c}"/></svg>`,
  cloud: c => `<svg viewBox="0 0 60 40" width="100%" height="100%"><path d="M16 36 Q4 36 4 26 Q4 16 15 16 Q18 4 31 4 Q44 4 46 17 Q56 18 56 27 Q56 36 46 36 Z" fill="${c}"/></svg>`,
};

// ---------- 가상 빵집 사이트 미리보기 ----------
// A/B/C: 새 시안 세 가지, broken: 폰에서 깨진 A, old: 2016년식 옛 사이트
const SITE = {
  A: { bg: '#FFF8F1', hero: 'linear-gradient(135deg,#FFB27A,#FF7A2F)', tile: '#FFE1CC', btn: '#FF7A2F', ink: '#3B2A22', copy: '매일 아침<br>굽는 빵' },
  B: { bg: '#F3FFFB', hero: 'linear-gradient(135deg,#5ED9BE,#1FB394)', tile: '#D3F3EA', btn: '#1FB394', ink: '#123D34', copy: '갓 구운 빵,<br>우리 동네 빵집' },
  C: { bg: '#FBF7F2', hero: 'linear-gradient(135deg,#5A4E44,#211C17)', tile: '#EADFD1', btn: '#211C17', ink: '#211C17', copy: '모닝빵<br>since 2012' },
};
function siteMock(v, btnStyle = '') {
  if (v === 'old') {
    return `<div class="site" style="background:#fff;color:#333;font-family:Gulim,'Times New Roman',serif">
      <div style="background:#8A8A8A;color:#fff;font-size:calc(18px*var(--s));padding:calc(10px*var(--s));font-weight:bold">MORNING BREAD 모닝빵</div>
      <div style="display:flex;gap:calc(8px*var(--s));padding:calc(8px*var(--s))">
        <div style="width:30%;background:#EEE;font-size:calc(12px*var(--s));line-height:1.8;padding:calc(6px*var(--s));color:#1a0dab;text-decoration:underline">홈<br>소개<br>메뉴<br>주문</div>
        <div style="flex:1;font-size:calc(12px*var(--s));line-height:1.7">어서오세요! 모닝빵입니다.<br>신선한 빵을 매일 굽습니다.<br>전화: 02-000-1234</div>
      </div>
      <div style="margin:calc(8px*var(--s));height:34%;background:#D8D2C8"></div>
      <div style="font-size:calc(10px*var(--s));color:#999;padding:calc(8px*var(--s))">Copyright 2016 morningbread. All rights reserved.</div>
    </div>`;
  }
  const S = SITE[v === 'broken' ? 'A' : v];
  return `<div class="site${v === 'broken' ? ' broken' : ''}" style="background:${S.bg};color:${S.ink}">
    <div class="nav">모닝빵<div><span>메뉴</span><span>오시는 길</span><span>주문</span></div></div>
    <div class="hero" style="background:${S.hero}">${S.copy}</div>
    <div class="row"><div style="background:${S.tile}"></div><div style="background:${S.tile}"></div><div style="background:${S.tile}"></div></div>
    <div class="btn" style="background:${S.btn};${btnStyle}">단체주문 문의</div>
  </div>`;
}

// ---------- 공통 화면: 상단, 자막 ----------
function buildChrome() {
  const stage = $('stage');
  const m = TL.meta;
  stage.insertAdjacentHTML('afterbegin', `
    <div class="abs" id="series"><span>${m.series} · EP${m.ep}</span></div>
    <div class="abs disp" id="title">${m.title}</div>
    <div class="abs" id="ladder"></div>`);
  stage.insertAdjacentHTML('beforeend', `<div class="abs" id="capwrap"><div id="cap"></div></div>`);
  const h = m.header || {};
  if (h.chips) {
    const size = h.size ? `font-size:${h.size}px;padding:7px 16px;` : '';
    $('ladder').innerHTML = h.chips.map((c, i) =>
      `<div class="chip${i === h.on ? ' on' : ''}" style="--c:${h.color || 'var(--ink)'};${size}">${c}</div>`).join('<div class="sep">›</div>');
  }
  document.body.insertAdjacentHTML('beforeend', `<button id="play" type="button">▶ 미리보기 재생</button>
    <audio id="audio" src="audio/narration.wav" preload="auto"></audio>`);
}

function fitTitle() {
  const el = $('title');
  let size = 84;
  while (el.scrollWidth > 1000 && size > 40) { size -= 2; el.style.fontSize = size + 'px'; }
}

function fillArt() {
  // <div data-char="yj:laptop:smile">, <div data-char="yj:stand:smile:critic">, <div data-char="boss:shock">,
  // <div data-char="person:sian:grin">, <span data-icon="mag:#3D6EF0">
  $$('[data-char]').forEach(el => {
    const [who, a, b, c] = el.dataset.char.split(':');
    el.innerHTML = who === 'yj' ? yjSVG(a, b, c) : who === 'boss' ? bossSVG(a) : personSVG(a, b);
  });
  $$('[data-icon]').forEach(el => {
    const [name, color] = el.dataset.icon.split(':');
    el.innerHTML = ICON[name](color || '#211C17');
  });
  $$('[data-site]').forEach(el => {
    const [v, s] = el.dataset.site.split(':');
    el.style.setProperty('--s', s || 1);
    el.insertAdjacentHTML('beforeend', siteMock(v));
  });
}

let capShown = null;
function caption(t) {
  const c = TL.captions.find(c => t >= c.start && t < c.end), el = $('cap');
  if (!c) { el.style.opacity = 0; return; }
  if (capShown !== c) { el.innerHTML = c.html; capShown = c; }
  el.style.opacity = 1;
  el.style.transform = `scale(${0.9 + 0.1 * eo(prog(t, c.start, 0.16))})`;
}

let SCENES = {};
function seek(t) {
  TL.scenes.forEach((sc, i) => {
    const el = $(sc.id), lt = t - sc.start, d = sc.end - sc.start;
    if (lt < 0 || lt > d) { el.style.visibility = 'hidden'; return; }
    const fin = eo(prog(lt, 0, 0.3)), fout = i === TL.scenes.length - 1 ? 1 : 1 - prog(lt, d - 0.25, 0.25);
    el.style.visibility = 'visible';
    el.style.opacity = Math.min(fin, fout);
    el.style.transform = `translateY(${(1 - fin) * 30}px)`;
    SCENES[sc.id](lt, d, sc.marks, sc.words);
  });
  caption(t);
}
window.seek = seek;

function start(scenes) {
  SCENES = scenes;
  buildChrome();
  fillArt();
  initClips();
  const params = new URLSearchParams(location.search);
  if (params.has('render')) {
    document.body.classList.add('render');
  } else {
    const fit = () => { const s = Math.min(innerWidth / 1080, innerHeight / 1920); $('viewport').style.transform = `translate(-50%, -50%) scale(${s})`; };
    fit();
    addEventListener('resize', fit);
    let playing = false, t0 = 0;
    const loop = now => {
      if (!playing) return;
      const a = $('audio');
      const t = !a.paused && a.readyState >= 2 ? a.currentTime : (now - t0) / 1000;
      if (t >= TL.total) { seek(TL.total - 0.001); playing = false; $('play').textContent = '↻ 다시 재생'; $('play').style.display = ''; return; }
      seek(t);
      requestAnimationFrame(loop);
    };
    $('play').onclick = () => {
      const a = $('audio');
      a.currentTime = 0;
      a.play().catch(() => {});
      t0 = performance.now();
      playing = true;
      $('play').style.display = 'none';
      requestAnimationFrame(loop);
    };
  }
  // 글꼴과 이미지(디자이너 편의 실제 시안 PNG)가 모두 준비된 뒤에 첫 프레임을 그린다
  const loaded = v => new Promise(r => v.readyState >= 2 ? r() : v.addEventListener('loadeddata', r, { once: true }));
  Promise.all([document.fonts.ready, ...$$('img').map(img => img.decode().catch(() => {})), ...$$('video').map(loaded)])
    .then(() => { fitTitle(); seek(Number(params.get('t') || 0)); window.READY = true; });
}
