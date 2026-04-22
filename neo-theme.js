/* ==========================================================================
   NEO Labs — Theme Toggle (shared module)
   --------------------------------------------------------------------------
   Usage: <script src="neo-theme.js?v=1"></script> — place BEFORE </body>
   (no defer needed; we set data-theme early to avoid flash)
   Storage: localStorage['neo_theme'] = 'dark' | 'light' (default 'dark')
   Public: window.NeoTheme.toggle() / .set('light'|'dark') / .get()
   ========================================================================== */
(function () {
  'use strict';

  const KEY = 'neo_theme';
  const stored = localStorage.getItem(KEY);
  const initial = stored === 'light' || stored === 'dark' ? stored : 'dark';
  document.documentElement.setAttribute('data-theme', initial);

  function injectStyles() {
    if (document.getElementById('neo-theme-style')) return;
    const css = `
      :root { color-scheme: dark; }
      html[data-theme="light"] { color-scheme: light; }
      html[data-theme="light"] {
        /* office.html pattern */
        --bg-0: #f7f8fb;
        --bg-1: #ffffff;
        --bg-2: #f1f3f7;
        --bg-3: #e6e9ef;
        /* council.html pattern */
        --bg: #f7f8fb;
        --panel: #ffffff;
        --panel-2: #f1f3f7;
        --line-strong: rgba(0,0,0,0.14);
        /* landing/brand pattern */
        --bg-deep: #f7f8fb;
        /* team.html pattern */
        --border: rgba(0,0,0,0.08);
        --card: rgba(0,0,0,0.025);
        /* shared */
        --line:   rgba(0,0,0,0.08);
        --line-2: rgba(0,0,0,0.14);
        --fg:    #141421;
        --muted: #585867;
        --dim:   #9b9ba8;
      }
      html[data-theme="light"] body {
        background:
          radial-gradient(ellipse at top left, rgba(255,107,53,0.08), transparent 55%),
          radial-gradient(ellipse at bottom right, rgba(168,85,247,0.10), transparent 55%),
          var(--bg-0, var(--bg, #f7f8fb)) !important;
      }
      html[data-theme="light"] .topbar {
        background: linear-gradient(180deg, rgba(255,255,255,0.92), rgba(241,243,247,0.92)) !important;
      }
      html[data-theme="light"] .neo-auth-badge {
        background: rgba(255,255,255,0.85) !important;
        border-color: rgba(0,0,0,0.08) !important;
        color: #141421 !important;
      }
      html[data-theme="light"] .neo-auth-menu {
        background: rgba(255,255,255,0.96) !important;
        border-color: rgba(0,0,0,0.10) !important;
        color: #141421 !important;
      }
      html[data-theme="light"] .neo-auth-menu button:hover { background: rgba(0,0,0,0.05) !important; }

      /* Floating toggle button */
      .neo-theme-fab {
        position: fixed; bottom: 16px; right: 16px; z-index: 9997;
        width: 40px; height: 40px;
        display: flex; align-items: center; justify-content: center;
        background: rgba(20, 20, 28, 0.78);
        backdrop-filter: blur(14px) saturate(140%);
        -webkit-backdrop-filter: blur(14px) saturate(140%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 50%;
        color: #e9e9ef;
        cursor: pointer;
        font-size: 16px; line-height: 1;
        transition: transform .18s ease, background .18s ease, border-color .18s ease;
        user-select: none;
      }
      .neo-theme-fab:hover { transform: translateY(-2px) rotate(-8deg); border-color: rgba(255,255,255,0.18); }
      .neo-theme-fab:active { transform: translateY(0) rotate(0deg); }
      html[data-theme="light"] .neo-theme-fab {
        background: rgba(255, 255, 255, 0.85);
        border-color: rgba(0, 0, 0, 0.08);
        color: #1a1a24;
      }
      html[data-theme="light"] .neo-theme-fab:hover { border-color: rgba(0,0,0,0.2); }
    `;
    const style = document.createElement('style');
    style.id = 'neo-theme-style';
    style.textContent = css;
    document.head.appendChild(style);
  }

  function renderFab() {
    if (document.getElementById('neo-theme-fab')) return;
    const btn = document.createElement('button');
    btn.id = 'neo-theme-fab';
    btn.className = 'neo-theme-fab';
    btn.type = 'button';
    btn.setAttribute('aria-label', 'Toggle theme');
    updateFab(btn);
    btn.addEventListener('click', () => { toggle(); updateFab(btn); });
    document.body.appendChild(btn);
  }

  function updateFab(btn) {
    const t = document.documentElement.getAttribute('data-theme');
    btn.textContent = t === 'light' ? '☀' : '☾';
    btn.title = t === 'light' ? 'Switch to dark' : 'Switch to light';
  }

  function set(mode) {
    const m = mode === 'light' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', m);
    localStorage.setItem(KEY, m);
    const fab = document.getElementById('neo-theme-fab');
    if (fab) updateFab(fab);
  }

  function toggle() {
    set(document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light');
  }

  function get() { return document.documentElement.getAttribute('data-theme') || 'dark'; }

  injectStyles();
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', renderFab);
  } else {
    renderFab();
  }

  /* cross-tab sync */
  window.addEventListener('storage', (e) => {
    if (e.key === KEY && e.newValue) set(e.newValue);
  });

  window.NeoTheme = { toggle, set, get };
})();
