/* ============================================================
   NEO Labs — Keyboard Shortcuts Overlay
   Usage: <script src="neo-shortcuts.js" defer></script>
   Press `?` anywhere (not in inputs) to open.
   ============================================================ */
(function () {
  'use strict';

  // OS-aware: show the modifier the user actually presses.
  const IS_MAC = /Mac|iPhone|iPad|iPod/i.test(navigator.platform || navigator.userAgent || '');
  const MOD = IS_MAC ? '⌘' : 'Ctrl';

  const SHORTCUTS = [
    { group: 'Navigation', items: [
      { keys: [MOD, 'K'], desc: 'Open command palette' },
      { keys: [MOD, 'H'], desc: 'Toggle conversations panel' },
      { keys: ['Esc'], desc: 'Close any panel / modal' },
      { keys: ['?'], desc: 'Show this cheatsheet' },
    ]},
    { group: 'Chat', items: [
      { keys: ['Enter'], desc: 'Send message' },
      { keys: ['Shift', 'Enter'], desc: 'New line in message' },
      { keys: [MOD, 'E'], desc: 'Export current conversation to Markdown' },
      { keys: [MOD, '/'], desc: 'Focus message input' },
    ]},
    { group: 'Office / Council', items: [
      { keys: ['🎭', 'TEAM'], desc: 'Toggle multi-agent orchestration (topbar)' },
      { keys: ['📈'], desc: 'Open admin analytics (topbar)' },
      { keys: ['💬'], desc: 'Open conversation history (topbar)' },
    ]},
    { group: 'Theme', items: [
      { keys: ['☾/☀'], desc: 'Toggle dark / light theme (bottom-right FAB)' },
    ]},
  ];

  const CSS = `
    #neo-sc-backdrop {
      position: fixed; inset: 0; z-index: 10000;
      background: rgba(7,7,13,0.82); backdrop-filter: blur(6px);
      display: none; align-items: center; justify-content: center;
      animation: neoScFade .15s ease-out;
    }
    #neo-sc-backdrop.open { display: flex; }
    @keyframes neoScFade { from{opacity:0} to{opacity:1} }
    .neo-sc-modal {
      width: min(620px, 92vw); max-height: 82vh; overflow-y: auto;
      background: #0d0d17; border: 1px solid rgba(255,255,255,0.12);
      border-radius: 16px; padding: 24px 28px;
      box-shadow: 0 20px 60px rgba(0,0,0,0.5);
      font-family: 'Prompt', system-ui, sans-serif; color: #e8e8f0;
    }
    .neo-sc-head {
      display: flex; align-items: center; justify-content: space-between;
      margin-bottom: 18px; padding-bottom: 14px;
      border-bottom: 1px solid rgba(255,255,255,0.07);
    }
    .neo-sc-title {
      font-family: 'JetBrains Mono', monospace; font-weight: 900;
      font-size: 14px; letter-spacing: 2px;
      background: linear-gradient(90deg, #ff6b35, #ec4899, #a855f7);
      -webkit-background-clip: text; background-clip: text; color: transparent;
    }
    .neo-sc-close {
      background: transparent; border: none; color: #7b7b8c;
      font-size: 20px; cursor: pointer; padding: 4px 10px; border-radius: 6px;
    }
    .neo-sc-close:hover { background: rgba(255,255,255,0.06); color: #e8e8f0; }
    .neo-sc-group { margin-bottom: 18px; }
    .neo-sc-group-title {
      font-size: 10px; letter-spacing: 2px; color: #7b7b8c;
      text-transform: uppercase; margin-bottom: 8px; font-weight: 700;
    }
    .neo-sc-row {
      display: flex; justify-content: space-between; align-items: center;
      padding: 8px 0; border-bottom: 1px dashed rgba(255,255,255,0.04);
      font-size: 13px;
    }
    .neo-sc-row:last-child { border-bottom: none; }
    .neo-sc-desc { color: #c0c0cc; }
    .neo-sc-keys { display: flex; gap: 5px; }
    .neo-sc-kbd {
      background: #1c1c2e; border: 1px solid rgba(255,255,255,0.12);
      border-radius: 5px; padding: 3px 8px;
      font-family: 'JetBrains Mono', monospace; font-size: 11px;
      color: #ff6b35; font-weight: 600; min-width: 22px; text-align: center;
    }
    html[data-theme="light"] .neo-sc-modal {
      background: #fff; color: #0f0f1a; border-color: rgba(0,0,0,0.1);
    }
    html[data-theme="light"] .neo-sc-kbd {
      background: #f1f1f7; color: #ff6b35; border-color: rgba(0,0,0,0.1);
    }
    html[data-theme="light"] .neo-sc-desc { color: #1a1a2e; }
  `;

  function injectStyle() {
    if (document.getElementById('neo-sc-style')) return;
    const s = document.createElement('style');
    s.id = 'neo-sc-style'; s.textContent = CSS;
    document.head.appendChild(s);
  }

  function render() {
    const backdrop = document.createElement('div');
    backdrop.id = 'neo-sc-backdrop';
    backdrop.innerHTML = `
      <div class="neo-sc-modal" role="dialog" aria-label="Keyboard shortcuts">
        <div class="neo-sc-head">
          <div class="neo-sc-title">⌨ KEYBOARD SHORTCUTS</div>
          <button class="neo-sc-close" aria-label="Close">×</button>
        </div>
        ${SHORTCUTS.map(g => `
          <div class="neo-sc-group">
            <div class="neo-sc-group-title">${g.group}</div>
            ${g.items.map(it => `
              <div class="neo-sc-row">
                <div class="neo-sc-desc">${it.desc}</div>
                <div class="neo-sc-keys">${it.keys.map(k => `<span class="neo-sc-kbd">${k}</span>`).join('')}</div>
              </div>
            `).join('')}
          </div>
        `).join('')}
      </div>
    `;
    backdrop.addEventListener('click', (e) => { if (e.target === backdrop) close(); });
    backdrop.querySelector('.neo-sc-close').addEventListener('click', close);
    document.body.appendChild(backdrop);
    return backdrop;
  }

  let el = null;
  function open()  { injectStyle(); el = el || render(); el.classList.add('open'); }
  function close() { if (el) el.classList.remove('open'); }

  document.addEventListener('keydown', (e) => {
    if (e.key === '?' && !isTypingTarget(e.target)) {
      e.preventDefault(); open();
    } else if (e.key === 'Escape' && el?.classList.contains('open')) {
      close();
    }
  });

  function isTypingTarget(t) {
    if (!t) return false;
    const tag = t.tagName;
    return tag === 'INPUT' || tag === 'TEXTAREA' || t.isContentEditable;
  }

  window.NeoShortcuts = { open, close };
})();
