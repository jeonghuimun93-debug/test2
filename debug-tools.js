/* ────────────────────────────────────────────────────────────────────────
 * Debug Tools — 시연/개발용 토글 패널
 *
 * 화면에서 직접 특정 기능의 노출 여부를 끄고 켤 수 있는 디버그 팝업.
 * 헤더 우측 디버그 버튼을 누르면 팝업이 뜨고, 그 안의 스위치로 기능을 토글한다.
 * 상태는 localStorage에 저장되어 새로고침 후에도 유지된다.
 *
 * ▶ 새 디버그 기능 추가 방법
 *   아래 DEBUG_TOGGLES 배열에 항목을 하나 추가하면 팝업에 스위치가 자동 생성된다.
 *   { key, label, desc, default, apply(enabled) }
 *     - key     : localStorage 저장 키(고유)
 *     - label   : 스위치 제목
 *     - desc    : 설명(작은 글씨, 생략 가능)
 *     - default : 기본 상태(boolean)
 *     - apply   : 상태가 바뀔 때 실행될 함수. enabled(boolean)를 받는다.
 * ──────────────────────────────────────────────────────────────────────── */
(function () {
  'use strict';

  var STORAGE_KEY = 'debugToggles';

  // ── 토글 레지스트리 ─────────────────────────────────────────────────
  var DEBUG_TOGGLES = [
    {
      key: 'emailFeature',
      label: '메일 발송 기능',
      desc: '개인정보 이슈로 기본 비활성화. 시연 시에만 켜세요.',
      default: false,
      apply: function (enabled) {
        // 메일 발송 관련 UI 전체를 inline display로 강제 토글한다.
        // (켜짐: display 비워 원래 d-none/flex 로직에 맡김 / 꺼짐: none으로 강제 숨김)
        ['mailSendNavBtn', 'sp3', 'sl2', 'sec-send'].forEach(function (id) {
          var el = document.getElementById(id);
          if (el) el.style.display = enabled ? '' : 'none';
        });

        // 기능을 끌 때, 현재 메일 발송(step3) 화면이라면 결과(step2)로 되돌린다.
        var send = document.getElementById('sec-send');
        if (!enabled && send && !send.classList.contains('d-none')) {
          if (typeof window.goStep === 'function') window.goStep(2);
        }
      },
    },
  ];

  // ── 상태 영속화 ─────────────────────────────────────────────────────
  function loadState() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
    } catch (e) {
      return {};
    }
  }
  function saveState(state) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (e) {}
  }
  function isEnabled(state, toggle) {
    return toggle.key in state ? !!state[toggle.key] : !!toggle.default;
  }

  // ── 스타일 주입 ─────────────────────────────────────────────────────
  function injectStyles() {
    if (document.getElementById('debug-tools-style')) return;
    var css = [
      '#debugBtn{display:inline-flex;align-items:center;gap:6px;background:rgba(255,255,255,0.14);',
      'color:#fff;border:1px solid rgba(255,255,255,0.35);border-radius:8px;padding:5px 12px;',
      'font-size:0.78rem;font-weight:600;cursor:pointer;transition:background 0.15s;}',
      '#debugBtn:hover{background:rgba(255,255,255,0.28);}',
      '#debugOverlay{position:fixed;inset:0;z-index:1090;display:none;}',
      '#debugOverlay.open{display:block;}',
      '#debugPanel{position:fixed;top:64px;right:16px;width:320px;max-width:calc(100vw - 32px);',
      'background:#fff;border-radius:14px;box-shadow:0 10px 40px rgba(0,0,0,0.28);',
      'z-index:1100;overflow:hidden;font-family:inherit;}',
      '#debugPanel .dbg-head{background:#1428A0;color:#fff;padding:12px 16px;display:flex;',
      'align-items:center;justify-content:space-between;}',
      '#debugPanel .dbg-head .t{font-size:0.9rem;font-weight:700;display:flex;align-items:center;gap:7px;}',
      '#debugPanel .dbg-head .x{background:none;border:none;color:#fff;font-size:1.1rem;cursor:pointer;line-height:1;opacity:0.85;}',
      '#debugPanel .dbg-head .x:hover{opacity:1;}',
      '#debugPanel .dbg-body{padding:8px 16px 14px;max-height:60vh;overflow-y:auto;}',
      '.dbg-row{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;padding:12px 0;border-bottom:1px solid #F1F3F8;}',
      '.dbg-row:last-child{border-bottom:none;}',
      '.dbg-row .lbl{font-size:0.84rem;font-weight:600;color:#1f2937;}',
      '.dbg-row .desc{font-size:0.72rem;color:#9CA3AF;margin-top:3px;line-height:1.4;}',
      '.dbg-sw{position:relative;flex-shrink:0;width:42px;height:24px;border-radius:99px;background:#D1D5DB;',
      'border:none;cursor:pointer;transition:background 0.18s;margin-top:2px;}',
      '.dbg-sw::after{content:"";position:absolute;top:2px;left:2px;width:20px;height:20px;border-radius:50%;',
      'background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.3);transition:transform 0.18s;}',
      '.dbg-sw.on{background:#1428A0;}',
      '.dbg-sw.on::after{transform:translateX(18px);}',
      '#debugPanel .dbg-foot{padding:8px 16px;background:#F8F9FC;font-size:0.68rem;color:#9CA3AF;text-align:center;}',
    ].join('');
    var style = document.createElement('style');
    style.id = 'debug-tools-style';
    style.textContent = css;
    document.head.appendChild(style);
  }

  // ── 토글 적용 ───────────────────────────────────────────────────────
  function applyAll(state) {
    DEBUG_TOGGLES.forEach(function (t) {
      try {
        t.apply(isEnabled(state, t));
      } catch (e) {
        console.warn('[debug-tools] apply 실패:', t.key, e);
      }
    });
  }

  // ── 팝업/버튼 생성 ──────────────────────────────────────────────────
  function build() {
    injectStyles();
    var state = loadState();

    // 헤더 버튼
    var mount = document.getElementById('debugMount');
    if (!mount) {
      mount = document.createElement('div');
      document.body.appendChild(mount);
    }
    var btn = document.createElement('button');
    btn.id = 'debugBtn';
    btn.type = 'button';
    btn.innerHTML = '<i class="bi bi-bug-fill"></i><span>Debug</span>';
    mount.appendChild(btn);

    // 오버레이(바깥 클릭 시 닫힘) + 패널
    var overlay = document.createElement('div');
    overlay.id = 'debugOverlay';
    overlay.innerHTML =
      '<div id="debugPanel" role="dialog" aria-label="Debug Tools">' +
      '  <div class="dbg-head">' +
      '    <span class="t"><i class="bi bi-tools"></i>Debug Tools</span>' +
      '    <button class="x" type="button" aria-label="닫기">&times;</button>' +
      '  </div>' +
      '  <div class="dbg-body" id="debugBody"></div>' +
      '  <div class="dbg-foot">시연/개발용 · 배포 시 기본값 유지</div>' +
      '</div>';
    document.body.appendChild(overlay);

    var panel = overlay.querySelector('#debugPanel');
    var body = overlay.querySelector('#debugBody');

    // 토글 행 렌더
    DEBUG_TOGGLES.forEach(function (t) {
      var row = document.createElement('div');
      row.className = 'dbg-row';
      var enabled = isEnabled(state, t);
      row.innerHTML =
        '<div><div class="lbl">' + t.label + '</div>' +
        (t.desc ? '<div class="desc">' + t.desc + '</div>' : '') +
        '</div>' +
        '<button class="dbg-sw' + (enabled ? ' on' : '') + '" type="button" role="switch" aria-checked="' + enabled + '"></button>';
      var sw = row.querySelector('.dbg-sw');
      sw.addEventListener('click', function () {
        var cur = loadState();
        var next = !isEnabled(cur, t);
        cur[t.key] = next;
        saveState(cur);
        sw.classList.toggle('on', next);
        sw.setAttribute('aria-checked', next);
        try {
          t.apply(next);
        } catch (e) {
          console.warn('[debug-tools] apply 실패:', t.key, e);
        }
      });
      body.appendChild(row);
    });

    // 열기/닫기
    function open() { overlay.classList.add('open'); }
    function close() { overlay.classList.remove('open'); }
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      overlay.classList.contains('open') ? close() : open();
    });
    overlay.addEventListener('click', close); // 바깥(오버레이) 클릭 시 닫힘
    panel.addEventListener('click', function (e) { e.stopPropagation(); });
    overlay.querySelector('.x').addEventListener('click', close);
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') close();
    });

    // 초기 상태 적용
    applyAll(state);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', build);
  } else {
    build();
  }
})();
