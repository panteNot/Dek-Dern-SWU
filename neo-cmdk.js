/* ============================================================
   NEO Labs — Command Palette (⌘K)
   Self-contained: styles + markup injected on first use.
   Usage: <script src="neo-cmdk.js" defer></script>
   ============================================================ */
(function () {
  'use strict';

  /* ----- OS-AWARE MODIFIER LABEL --------------------------
     Mac users see "⌘K", Windows/Linux see "Ctrl+K".
     Functionality (metaKey || ctrlKey) already works on both. */
  const IS_MAC = /Mac|iPhone|iPad|iPod/i.test(navigator.platform || navigator.userAgent || '');
  const MOD = IS_MAC ? '⌘' : 'Ctrl+';
  const MOD_LABEL = IS_MAC ? '⌘K' : 'Ctrl+K';

  /* ----- ACTION REGISTRY ---------------------------------- */
  const ACTIONS = [
    /* --- Pages --- */
    { group: 'Pages', id: 'p-office',   label: 'Office — Dashboard',        hint: 'go',  icon: '◆', run: () => nav('neo-labs-office.html') },
    { group: 'Pages', id: 'p-council',  label: 'Agent Council — Parallel',  hint: 'go',  icon: '◆', run: () => nav('neo-labs-council.html') },
    { group: 'Pages', id: 'p-admin',    label: 'Admin — Analytics & Audit', hint: 'go',  icon: '📈', run: () => nav('neo-labs-admin.html') },
    { group: 'Pages', id: 'p-settings', label: 'Settings — Profile & Data', hint: 'go',  icon: '⚙', run: () => nav('neo-labs-settings.html') },
    { group: 'Pages', id: 'p-team',     label: 'Team Playground',           hint: 'go',  icon: '◇', run: () => nav('neo-labs-team.html') },
    { group: 'Pages', id: 'p-brand',    label: 'Brand Guidelines',          hint: 'go',  icon: '◇', run: () => nav('neo-labs-brand.html') },
    { group: 'Pages', id: 'p-landing',  label: 'Landing Page',              hint: 'go',  icon: '◇', run: () => nav('neo-labs-landing.html') },
    { group: 'Pages', id: 'p-login',    label: 'Login Page',                hint: 'go',  icon: '◇', run: () => nav('neo-labs-login.html') },
    { group: 'Pages', id: 'p-logo',     label: 'Logo Explorations',         hint: 'go',  icon: '◇', run: () => nav('neo-labs-logo.html') },

    /* --- Agents --- (fires 'neo:agent' event; handler decides what happens) */
    { group: 'Agents', id: 'a-neo',   label: 'NEO — CEO / Main',             hint: 'call', icon: '🟠', color: '#ff6b35', run: () => call('neo') },
    { group: 'Agents', id: 'a-atlas', label: 'ATLAS — Chief of Staff / PM',  hint: 'call', icon: '🟢', color: '#14b8a6', run: () => call('atlas') },
    { group: 'Agents', id: 'a-nova',  label: 'NOVA — Research Intelligence', hint: 'call', icon: '🟣', color: '#a855f7', run: () => call('nova') },
    { group: 'Agents', id: 'a-luna',  label: 'LUNA — UX/UI Designer',        hint: 'call', icon: '🩷', color: '#ec4899', run: () => call('luna') },
    { group: 'Agents', id: 'a-pixel', label: 'PIXEL — Slide Maker',          hint: 'call', icon: '🟢', color: '#22c55e', run: () => call('pixel') },
    { group: 'Agents', id: 'a-sage',  label: 'SAGE — Study Tutor',           hint: 'call', icon: '🟡', color: '#eab308', run: () => call('sage') },
    { group: 'Agents', id: 'a-rex',   label: 'REX — Devil\'s Advocate',      hint: 'call', icon: '🔴', color: '#ef4444', run: () => call('rex') },
    { group: 'Agents', id: 'a-byte',  label: 'BYTE — Code Reviewer',         hint: 'call', icon: '🔵', color: '#3b82f6', run: () => call('byte') },
    { group: 'Agents', id: 'a-quill', label: 'QUILL — Copywriter',           hint: 'call', icon: '⚪', color: '#e5e5e5', run: () => call('quill') },

    /* --- Actions --- */
    { group: 'Actions', id: 'x-shortcuts', label: 'Show keyboard shortcuts', hint: '?', icon: '⌨', run: () => { if (window.NeoShortcuts) window.NeoShortcuts.open(); else toast('Shortcuts ยังไม่พร้อม'); } },
    { group: 'Actions', id: 'x-prompts', label: 'Open Prompt Library', hint: '', icon: '📌', run: () => { if (window.NeoPrompts) window.NeoPrompts.open(); else toast('Prompt Library ยังไม่พร้อม (หน้านี้ไม่มี)'); } },
    { group: 'Actions', id: 'x-export',  label: 'Export conversation → Markdown', hint: '', icon: '↓', run: () => exportMD() },
    { group: 'Actions', id: 'x-theme',   label: 'Toggle theme (dark / light)', hint: '',  icon: '☾', run: () => toggleTheme() },
    { group: 'Actions', id: 'x-logout',  label: 'Log out',               hint: '⎋', icon: '↗', run: () => logout() },
    { group: 'Actions', id: 'x-reload',  label: 'Reload page',           hint: MOD + 'R', icon: '↻', run: () => location.reload() },
    { group: 'Actions', id: 'x-copyurl', label: 'Copy current URL',      hint: '',  icon: '⎘', run: () => copyUrl() },
    { group: 'Actions', id: 'x-home',    label: 'Back to office',        hint: '',  icon: '⌂', run: () => nav('neo-labs-office.html') },
  ];

  function toggleTheme() {
    if (window.NeoTheme) { window.NeoTheme.toggle(); toast('Theme: ' + window.NeoTheme.get()); }
    else toast('Theme module not loaded');
  }

  function exportMD() {
    /* try council exporter first, then office history exporter */
    const councilBtn = document.getElementById('exportBtn');
    const officeBtn  = document.getElementById('exportAllBtn');
    if (councilBtn) { councilBtn.click(); return; }
    if (officeBtn)  { officeBtn.click(); return; }
    toast('หน้านี้ยังไม่มี export');
  }

  function nav(href) { window.location.href = href; }
  function call(id)  {
    /* fire custom event — any page can listen & respond */
    window.dispatchEvent(new CustomEvent('neo:agent', { detail: { id } }));
    toast(`เรียก ${id.toUpperCase()} แล้ว`);
  }
  function logout() {
    try { localStorage.removeItem('neo_user'); } catch (_) {}
    window.location.href = 'neo-labs-login.html';
  }
  async function copyUrl() {
    try {
      await navigator.clipboard.writeText(location.href);
      toast('Copied URL');
    } catch (_) { toast('Copy failed'); }
  }

  /* ----- STYLES ------------------------------------------- */
  const CSS = `
  .cmdk-root * { box-sizing: border-box; }
  .cmdk-backdrop {
    position: fixed; inset: 0;
    background: rgba(6,6,10,0.72);
    backdrop-filter: blur(6px);
    -webkit-backdrop-filter: blur(6px);
    display: none;
    z-index: 99999;
    align-items: flex-start;
    justify-content: center;
    padding-top: 14vh;
    animation: cmdkFade .15s ease-out;
  }
  .cmdk-backdrop.open { display: flex; }
  @keyframes cmdkFade { from { opacity: 0 } to { opacity: 1 } }
  @keyframes cmdkPop  { from { transform: translateY(-6px) scale(.98); opacity: 0 } to { transform: none; opacity: 1 } }

  .cmdk-panel {
    width: min(640px, 92%);
    background: #0d0d17;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    box-shadow: 0 30px 60px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,107,53,0.08);
    overflow: hidden;
    font-family: 'Inter', 'Noto Sans Thai', system-ui, sans-serif;
    color: #e8e8e8;
    animation: cmdkPop .18s cubic-bezier(.2,.8,.2,1);
  }
  .cmdk-search {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 18px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
  }
  .cmdk-search .icon {
    color: #8a8a98;
    font-size: 16px;
    font-family: 'Courier New', monospace;
  }
  .cmdk-search input {
    flex: 1;
    background: transparent;
    border: 0;
    outline: 0;
    color: #e8e8e8;
    font-size: 15px;
    font-family: inherit;
  }
  .cmdk-search input::placeholder { color: #5a5a68; }
  .cmdk-search .kbd {
    font-family: 'Courier New', monospace;
    font-size: 10px;
    letter-spacing: 1px;
    padding: 3px 6px;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 4px;
    color: #8a8a98;
    background: rgba(255,255,255,0.03);
  }

  .cmdk-list {
    max-height: 52vh;
    overflow-y: auto;
    padding: 6px;
  }
  .cmdk-list::-webkit-scrollbar { width: 6px; }
  .cmdk-list::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 3px; }

  .cmdk-group {
    padding: 8px 12px 4px;
    font-family: 'Courier New', monospace;
    font-size: 10px;
    letter-spacing: 2px;
    color: #5a5a68;
    text-transform: uppercase;
  }
  .cmdk-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 9px 12px;
    border-radius: 8px;
    cursor: pointer;
    transition: background .08s ease;
  }
  .cmdk-item:hover, .cmdk-item.active {
    background: rgba(255,107,53,0.12);
  }
  .cmdk-item.active {
    box-shadow: inset 0 0 0 1px rgba(255,107,53,0.25);
  }
  .cmdk-item .ico {
    width: 24px; height: 24px;
    display: flex; align-items: center; justify-content: center;
    font-size: 13px;
    color: #c7c7d0;
    background: rgba(255,255,255,0.04);
    border-radius: 6px;
    flex-shrink: 0;
  }
  .cmdk-item[data-color] .ico { color: var(--ic); background: color-mix(in srgb, var(--ic) 12%, transparent); }
  .cmdk-item .label { flex: 1; font-size: 14px; color: #e8e8e8; }
  .cmdk-item .hint {
    font-family: 'Courier New', monospace;
    font-size: 10px;
    color: #5a5a68;
    letter-spacing: 1px;
  }

  .cmdk-empty {
    padding: 32px 18px;
    text-align: center;
    color: #5a5a68;
    font-size: 13px;
  }

  .cmdk-foot {
    display: flex;
    justify-content: space-between;
    padding: 8px 16px;
    border-top: 1px solid rgba(255,255,255,0.06);
    font-family: 'Courier New', monospace;
    font-size: 10px;
    letter-spacing: 1px;
    color: #5a5a68;
  }
  .cmdk-foot .key {
    padding: 2px 5px;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 3px;
    margin-right: 4px;
    color: #8a8a98;
  }

  .cmdk-toast {
    position: fixed;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%) translateY(20px);
    background: #0d0d17;
    color: #e8e8e8;
    padding: 10px 16px;
    border: 1px solid rgba(255,107,53,0.3);
    border-radius: 8px;
    font-size: 13px;
    font-family: 'Inter', system-ui, sans-serif;
    z-index: 99998;
    opacity: 0;
    transition: opacity .2s, transform .2s;
    pointer-events: none;
  }
  .cmdk-toast.show {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
  `;

  /* ----- MARKUP ------------------------------------------- */
  function build() {
    const style = document.createElement('style');
    style.textContent = CSS;
    document.head.appendChild(style);

    const root = document.createElement('div');
    root.className = 'cmdk-root';
    root.innerHTML = `
      <div class="cmdk-backdrop" id="cmdkBack">
        <div class="cmdk-panel" role="dialog" aria-label="Command Palette">
          <div class="cmdk-search">
            <span class="icon">${IS_MAC ? '⌘' : '⌃'}</span>
            <input id="cmdkInput" type="text" placeholder="Type a command or search… (${MOD_LABEL})" autocomplete="off" spellcheck="false" />
            <span class="kbd">ESC</span>
          </div>
          <div class="cmdk-list" id="cmdkList"></div>
          <div class="cmdk-foot">
            <div><span class="key">↑↓</span>navigate  <span class="key">↵</span>select</div>
            <div><span class="key">${MOD_LABEL}</span>toggle</div>
          </div>
        </div>
      </div>
      <div class="cmdk-toast" id="cmdkToast"></div>
    `;
    document.body.appendChild(root);
    return {
      back:  root.querySelector('#cmdkBack'),
      input: root.querySelector('#cmdkInput'),
      list:  root.querySelector('#cmdkList'),
      toast: root.querySelector('#cmdkToast'),
    };
  }

  const dom = build();
  let filtered = [...ACTIONS];
  let activeIdx = 0;

  /* ----- RENDER ------------------------------------------- */
  function render() {
    dom.list.innerHTML = '';
    if (filtered.length === 0) {
      dom.list.innerHTML = `<div class="cmdk-empty">ไม่พบคำสั่งที่ตรง — ลอง "office", "neo", "logout"</div>`;
      return;
    }
    let lastGroup = null;
    filtered.forEach((a, i) => {
      if (a.group !== lastGroup) {
        const g = document.createElement('div');
        g.className = 'cmdk-group';
        g.textContent = a.group;
        dom.list.appendChild(g);
        lastGroup = a.group;
      }
      const row = document.createElement('div');
      row.className = 'cmdk-item' + (i === activeIdx ? ' active' : '');
      row.dataset.idx = i;
      if (a.color) { row.dataset.color = '1'; row.style.setProperty('--ic', a.color); }
      row.innerHTML = `
        <div class="ico">${a.icon || '·'}</div>
        <div class="label"></div>
        <div class="hint">${a.hint || ''}</div>
      `;
      row.querySelector('.label').textContent = a.label;
      row.addEventListener('click', () => exec(i));
      row.addEventListener('mousemove', () => {
        if (activeIdx !== i) { activeIdx = i; render(); }
      });
      dom.list.appendChild(row);
    });
    /* scroll active into view */
    const active = dom.list.querySelector('.cmdk-item.active');
    if (active) active.scrollIntoView({ block: 'nearest' });
  }

  /* ----- FILTER ------------------------------------------- */
  function filter(q) {
    q = q.trim().toLowerCase();
    if (!q) { filtered = [...ACTIONS]; activeIdx = 0; render(); return; }
    filtered = ACTIONS.filter(a => {
      const hay = (a.label + ' ' + a.group + ' ' + a.id).toLowerCase();
      return q.split(/\s+/).every(tok => hay.includes(tok));
    });
    activeIdx = 0;
    render();
  }

  /* ----- OPEN/CLOSE --------------------------------------- */
  function open() {
    dom.back.classList.add('open');
    dom.input.value = '';
    filter('');
    setTimeout(() => dom.input.focus(), 30);
  }
  function close() { dom.back.classList.remove('open'); }
  function toggle() { dom.back.classList.contains('open') ? close() : open(); }

  function exec(idx) {
    const a = filtered[idx];
    if (!a) return;
    close();
    setTimeout(() => a.run(), 80);
  }

  /* ----- TOAST (used by actions) -------------------------- */
  let toastTimer;
  function toast(msg) {
    dom.toast.textContent = msg;
    dom.toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => dom.toast.classList.remove('show'), 2200);
  }

  /* ----- EVENTS ------------------------------------------- */
  document.addEventListener('keydown', (e) => {
    /* ⌘K / Ctrl+K toggle */
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      toggle();
      return;
    }
    if (!dom.back.classList.contains('open')) return;

    if (e.key === 'Escape') { e.preventDefault(); close(); }
    else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (activeIdx < filtered.length - 1) { activeIdx++; render(); }
    }
    else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (activeIdx > 0) { activeIdx--; render(); }
    }
    else if (e.key === 'Enter') {
      e.preventDefault();
      exec(activeIdx);
    }
  });

  dom.input.addEventListener('input', (e) => filter(e.target.value));
  dom.back.addEventListener('click', (e) => {
    if (e.target === dom.back) close();
  });

  /* ----- PUBLIC API --------------------------------------- */
  window.NeoCmdK = {
    open, close, toggle, toast,
    register(action) { ACTIONS.push(action); },
  };

  /* ----- FIRST-TIME HINT (shows for 5s on first page load) */
  if (!sessionStorage.getItem('neo_cmdk_seen')) {
    sessionStorage.setItem('neo_cmdk_seen', '1');
    setTimeout(() => toast(MOD_LABEL + ' เปิด Command Palette'), 800);
  }
})();
