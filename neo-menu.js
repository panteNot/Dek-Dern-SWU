/* ============================================================
   NEO Labs — Hamburger Navigation Menu (☰)
   Touch-friendly fullscreen drawer. Companion to ⌘K for users
   who can't / don't want to use keyboard shortcuts.
   Usage: <script src="neo-menu.js" defer></script>
   ============================================================ */
(function () {
  'use strict';

  const IS_MAC = /Mac|iPhone|iPad|iPod/i.test(navigator.platform || navigator.userAgent || '');

  // Flat list of groups → items. Each item: {icon, label, sub?, href? or run?}
  const GROUPS = [
    {
      title: 'Pages',
      items: [
        { icon: '◆', label: 'Office',         sub: 'หน้าทำงานหลัก',            href: 'neo-labs-office.html' },
        { icon: '◆', label: 'Agent Council',  sub: '3 agents ตอบพร้อมกัน',      href: 'neo-labs-council.html' },
        { icon: '📈', label: 'Admin',         sub: 'Analytics & audit log',    href: 'neo-labs-admin.html' },
        { icon: '⚙',  label: 'Settings',      sub: 'Profile, memory, export',  href: 'neo-labs-settings.html' },
        { icon: '◇', label: 'Team Playground', sub: 'Pixel robot showcase',     href: 'neo-labs-team.html' },
      ],
    },
    {
      // Views only make sense on the Office page — the custom event there
      // switches the current tab instead of navigating away.
      title: 'Office Views',
      items: [
        { icon: '📜', label: 'History', sub: 'Task history (persistent)',     run: () => view('history') },
        { icon: '📁', label: 'Files',   sub: 'Workspace file browser',        run: () => view('files') },
        { icon: '⌨',  label: 'Editor',  sub: 'Monaco code editor',            run: () => view('editor') },
        { icon: '🎨', label: 'Canvas',  sub: 'Whiteboard / freeform draw',    run: () => view('canvas') },
        { icon: '🌐', label: '3D Viewer', sub: 'Model / scene preview',       run: () => view('viewer3d') },
      ],
    },
    {
      title: 'Agents',
      items: [
        { icon: '🟠', label: 'NEO',   sub: 'CEO / Main',             run: () => call('neo') },
        { icon: '🟢', label: 'ATLAS', sub: 'Chief of Staff / PM',    run: () => call('atlas') },
        { icon: '🟣', label: 'NOVA',  sub: 'Research',               run: () => call('nova') },
        { icon: '🩷', label: 'LUNA',  sub: 'UX/UI Designer',         run: () => call('luna') },
        { icon: '🟢', label: 'PIXEL', sub: 'Slide Maker',            run: () => call('pixel') },
        { icon: '🟡', label: 'SAGE',  sub: 'Study Tutor',            run: () => call('sage') },
        { icon: '🔴', label: 'REX',   sub: "Devil's Advocate",       run: () => call('rex') },
        { icon: '🔵', label: 'BYTE',  sub: 'Code Reviewer',          run: () => call('byte') },
        { icon: '⚪', label: 'QUILL', sub: 'Copywriter',             run: () => call('quill') },
      ],
    },
    {
      title: 'Actions',
      items: [
        { icon: (IS_MAC ? '⌘' : '⌃'), label: 'Command Palette',
          sub: (IS_MAC ? '⌘K' : 'Ctrl+K') + ' — search anything',
          run: () => { close(); if (window.NeoCmdK) window.NeoCmdK.open(); } },
        { icon: '☾', label: 'Toggle theme',  sub: 'Dark / light mode',
          run: () => { if (window.NeoTheme) window.NeoTheme.toggle(); } },
        { icon: '↓', label: 'Export chat',   sub: 'ดาวน์โหลดเป็น Markdown',
          run: () => exportMD() },
        { icon: '↗', label: 'Log out',       sub: 'ออกจาก NEO Labs',
          run: () => logout() },
      ],
    },
  ];

  function call(id) {
    close();
    window.dispatchEvent(new CustomEvent('neo:agent', { detail: { id } }));
  }
  function view(name) {
    close();
    // If we're on office page, the listener there will switchView.
    // Otherwise navigate to office and carry the view as a query param
    // (office page could optionally read ?view= on load — not wired yet).
    if (/neo-labs-office\.html$/.test(location.pathname) || location.pathname === '/' || location.pathname.endsWith('/neo-labs-office.html')) {
      window.dispatchEvent(new CustomEvent('neo:view', { detail: { view: name } }));
    } else {
      window.location.href = 'neo-labs-office.html?view=' + encodeURIComponent(name);
    }
  }
  function exportMD() {
    close();
    const c = document.getElementById('exportBtn');
    const o = document.getElementById('exportAllBtn');
    if (c) c.click(); else if (o) o.click();
    else alert('หน้านี้ยังไม่มี export');
  }
  function logout() {
    try { localStorage.removeItem('neo_user'); } catch (_) {}
    window.location.href = 'neo-labs-login.html';
  }

  const CSS = `
  .neo-mb-fab {
    position: fixed; top: 14px; left: 14px;
    width: 40px; height: 40px; border-radius: 10px;
    background: rgba(20,20,30,0.72);
    border: 1px solid rgba(255,255,255,0.1);
    color: #f0f0f0; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px; line-height: 1;
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    z-index: 9998;
    transition: opacity .18s, transform .15s, background .15s;
  }
  .neo-mb-fab:hover { background: rgba(255,107,53,0.2); transform: scale(1.05); }
  .neo-mb-fab:active { transform: scale(0.95); }
  /* Hide when the office conversations slide-in panel is open, so it doesn't
     overlap the drawer header. Class is toggled by the observer below, and
     :has() gives a no-JS fallback on modern browsers. */
  .neo-mb-fab.hide-for-panel { opacity: 0; pointer-events: none; transform: scale(.8); }
  body:has(.conv-panel.open) .neo-mb-fab { opacity: 0; pointer-events: none; transform: scale(.8); }

  .neo-mb-backdrop {
    position: fixed; inset: 0;
    background: rgba(0,0,0,0.5);
    backdrop-filter: blur(4px);
    -webkit-backdrop-filter: blur(4px);
    z-index: 9999;
    opacity: 0; pointer-events: none;
    transition: opacity .2s;
  }
  .neo-mb-backdrop.open { opacity: 1; pointer-events: auto; }

  .neo-mb-drawer {
    position: fixed; top: 0; left: 0; bottom: 0;
    width: min(380px, 88vw);
    background: #0a0a12;
    border-right: 1px solid rgba(255,255,255,0.08);
    transform: translateX(-100%);
    transition: transform .25s cubic-bezier(.2,.8,.2,1);
    z-index: 10000;
    display: flex; flex-direction: column;
    font-family: 'Inter', 'Noto Sans Thai', system-ui, sans-serif;
    color: #e8e8e8;
    overflow: hidden;
  }
  .neo-mb-drawer.open { transform: translateX(0); }

  .neo-mb-head {
    display: flex; align-items: center; justify-content: space-between;
    padding: 18px 20px;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    flex-shrink: 0;
  }
  .neo-mb-brand {
    display: flex; align-items: center; gap: 10px;
    font-weight: 800; font-size: 18px; letter-spacing: 1px;
  }
  .neo-mb-brand .dot {
    width: 10px; height: 10px; border-radius: 50%;
    background: #ff6b35;
    box-shadow: 0 0 10px #ff6b35;
  }
  .neo-mb-close {
    background: none; border: none; color: #aaa;
    font-size: 22px; cursor: pointer; padding: 4px 10px;
    border-radius: 8px; line-height: 1;
  }
  .neo-mb-close:hover { background: rgba(255,255,255,0.08); color: #fff; }

  .neo-mb-body {
    flex: 1; overflow-y: auto;
    padding: 8px 0 24px;
  }
  .neo-mb-group-title {
    padding: 14px 20px 6px;
    font-size: 11px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 1.5px;
    color: #666;
  }
  .neo-mb-item {
    display: flex; align-items: center; gap: 14px;
    padding: 14px 20px;
    cursor: pointer;
    transition: background .12s;
    border-left: 3px solid transparent;
    text-decoration: none; color: inherit;
  }
  .neo-mb-item:hover {
    background: rgba(255,107,53,0.08);
    border-left-color: #ff6b35;
  }
  .neo-mb-item:active { background: rgba(255,107,53,0.15); }
  .neo-mb-icon {
    width: 28px; text-align: center;
    font-size: 18px; flex-shrink: 0;
  }
  .neo-mb-text { flex: 1; min-width: 0; }
  .neo-mb-label {
    font-size: 15px; font-weight: 600;
    line-height: 1.2;
  }
  .neo-mb-sub {
    font-size: 12px; color: #888;
    margin-top: 2px;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }
  .neo-mb-chev {
    color: #555; font-size: 16px; flex-shrink: 0;
  }

  html[data-theme="light"] .neo-mb-fab { background: rgba(255,255,255,0.85); color: #222; border-color: rgba(0,0,0,0.1); }
  html[data-theme="light"] .neo-mb-drawer { background: #fafafa; color: #222; }
  html[data-theme="light"] .neo-mb-head { border-bottom-color: rgba(0,0,0,0.08); }
  html[data-theme="light"] .neo-mb-close:hover { background: rgba(0,0,0,0.06); color: #000; }
  html[data-theme="light"] .neo-mb-item:hover { background: rgba(255,107,53,0.1); }
  html[data-theme="light"] .neo-mb-sub { color: #666; }
  html[data-theme="light"] .neo-mb-group-title { color: #888; }
  `;

  function injectStyle() {
    if (document.getElementById('neo-mb-style')) return;
    const s = document.createElement('style');
    s.id = 'neo-mb-style';
    s.textContent = CSS;
    document.head.appendChild(s);
  }

  function build() {
    injectStyle();
    const fab = document.createElement('button');
    fab.className = 'neo-mb-fab';
    fab.id = 'neoMenuFab';
    fab.setAttribute('aria-label', 'Open menu');
    fab.title = 'Menu';
    fab.textContent = '☰';

    const backdrop = document.createElement('div');
    backdrop.className = 'neo-mb-backdrop';

    const drawer = document.createElement('aside');
    drawer.className = 'neo-mb-drawer';
    drawer.setAttribute('role', 'dialog');
    drawer.setAttribute('aria-label', 'Navigation menu');

    let bodyHTML = '';
    for (const g of GROUPS) {
      bodyHTML += `<div class="neo-mb-group-title">${g.title}</div>`;
      for (const it of g.items) {
        const chev = it.href ? '›' : '';
        const tag = it.href ? 'a' : 'button';
        const attr = it.href ? `href="${it.href}"` : 'type="button"';
        bodyHTML += `
          <${tag} class="neo-mb-item" ${attr} data-group="${g.title}" data-label="${it.label}">
            <span class="neo-mb-icon">${it.icon}</span>
            <span class="neo-mb-text">
              <div class="neo-mb-label">${it.label}</div>
              <div class="neo-mb-sub">${it.sub || ''}</div>
            </span>
            <span class="neo-mb-chev">${chev}</span>
          </${tag}>`;
      }
    }

    drawer.innerHTML = `
      <div class="neo-mb-head">
        <div class="neo-mb-brand"><span class="dot"></span>NEO LABS</div>
        <button class="neo-mb-close" aria-label="Close menu">✕</button>
      </div>
      <div class="neo-mb-body">${bodyHTML}</div>
    `;

    document.body.appendChild(fab);
    document.body.appendChild(backdrop);
    document.body.appendChild(drawer);

    // Wire up item clicks (only `run` handlers — href already navigates natively)
    const items = drawer.querySelectorAll('.neo-mb-item');
    items.forEach((el) => {
      const group = el.dataset.group;
      const label = el.dataset.label;
      const grp = GROUPS.find((g) => g.title === group);
      const it = grp && grp.items.find((i) => i.label === label);
      if (it && typeof it.run === 'function') {
        el.addEventListener('click', (e) => { e.preventDefault(); it.run(); });
      } else if (it && it.href) {
        // let native <a> handle it, close first for snappy feel
        el.addEventListener('click', () => close());
      }
    });

    return { fab, backdrop, drawer };
  }

  const dom = build();

  function open()  {
    dom.backdrop.classList.add('open');
    dom.drawer.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
  function close() {
    dom.backdrop.classList.remove('open');
    dom.drawer.classList.remove('open');
    document.body.style.overflow = '';
  }
  function toggle() {
    if (dom.drawer.classList.contains('open')) close(); else open();
  }

  dom.fab.addEventListener('click', toggle);
  dom.backdrop.addEventListener('click', close);
  dom.drawer.querySelector('.neo-mb-close').addEventListener('click', close);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && dom.drawer.classList.contains('open')) close();
  });

  window.NeoMenu = { open, close, toggle };

  // Observe `.conv-panel` open-state on the office page so the ☰ FAB
  // ducks out of the way whenever the conversations drawer is visible.
  function watchConvPanel() {
    const panel = document.querySelector('.conv-panel');
    if (!panel) return;
    const sync = () => {
      dom.fab.classList.toggle('hide-for-panel', panel.classList.contains('open'));
    };
    sync();
    new MutationObserver(sync).observe(panel, { attributes: true, attributeFilter: ['class'] });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', watchConvPanel);
  } else {
    watchConvPanel();
  }
})();
