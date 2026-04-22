/* ==========================================================================
   NEO Labs — Auth Guard + User Header (shared module)
   --------------------------------------------------------------------------
   What it does:
     1. Guard — runs immediately. If no valid session → redirect to login.html
     2. Session expiry — reject session older than MAX_AGE_DAYS
     3. User Header — floating top-right card with avatar + name + logout
     4. Logout hook — window.NeoAuth.logout()
   Usage:
     <script src="neo-auth.js?v=1"></script>   (NO defer — must run first!)
   ========================================================================== */
(function () {
  'use strict';

  const STORAGE_KEY   = 'neo_user';
  const LOGIN_URL     = 'neo-labs-login.html';
  const MAX_AGE_DAYS  = 7;
  const MAX_AGE_MS    = MAX_AGE_DAYS * 24 * 60 * 60 * 1000;

  /* ---------- 1. Guard ---------- */
  function readSession() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      const u = JSON.parse(raw);
      if (!u || !u.email || !u.ts) return null;
      if (Date.now() - u.ts > MAX_AGE_MS) return null;  // expired
      /* Google sessions MUST carry the raw JWT — older sessions predating
         the auth middleware won't work against backend. Treat as stale. */
      if (u.provider === 'google' && !u.token) return null;
      /* Google JWT itself expires in 1h — re-login if past that. */
      if (u.exp && Date.now() / 1000 > u.exp) return null;
      return u;
    } catch { return null; }
  }

  function redirectToLogin(reason) {
    // Preserve return URL so login can bounce back
    const here = encodeURIComponent(location.pathname + location.search);
    location.replace(`${LOGIN_URL}?from=${here}${reason ? '&r=' + reason : ''}`);
  }

  const user = readSession();
  if (!user) {
    redirectToLogin(localStorage.getItem(STORAGE_KEY) ? 'expired' : 'noauth');
    return;  // stop executing — browser is navigating away
  }

  /* ---------- 2. Logout ---------- */
  function logout() {
    localStorage.removeItem(STORAGE_KEY);
    location.replace(LOGIN_URL + '?r=logout');
  }

  /* ---------- 3. User Header UI ---------- */
  function injectHeaderStyles() {
    if (document.getElementById('neo-auth-style')) return;
    const css = `
      .neo-auth-badge {
        position: fixed; top: 16px; right: 16px; z-index: 9998;
        display: flex; align-items: center; gap: 10px;
        padding: 6px 12px 6px 6px;
        background: rgba(20, 20, 28, 0.78);
        backdrop-filter: blur(14px) saturate(140%);
        -webkit-backdrop-filter: blur(14px) saturate(140%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 999px;
        font: 500 13px/1 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: #e9e9ef; cursor: pointer;
        transition: transform .15s ease, background .15s ease, border-color .15s ease;
        user-select: none;
      }
      .neo-auth-badge:hover { background: rgba(30, 30, 42, 0.92); border-color: rgba(255,255,255,0.16); transform: translateY(-1px); }
      .neo-auth-badge img {
        width: 28px; height: 28px; border-radius: 50%;
        border: 1.5px solid rgba(255,255,255,0.18); object-fit: cover;
      }
      .neo-auth-badge .neo-auth-initials {
        width: 28px; height: 28px; border-radius: 50%;
        background: linear-gradient(135deg, #ff6b35, #a855f7);
        color: #fff; font-weight: 700; font-size: 12px;
        display: flex; align-items: center; justify-content: center;
        border: 1.5px solid rgba(255,255,255,0.18);
      }
      .neo-auth-badge .neo-auth-name { white-space: nowrap; max-width: 120px; overflow: hidden; text-overflow: ellipsis; }
      .neo-auth-badge .neo-auth-caret { opacity: 0.55; font-size: 10px; margin-left: 2px; }

      .neo-auth-menu {
        position: fixed; top: 58px; right: 16px; z-index: 9999;
        min-width: 220px; padding: 8px;
        background: rgba(18, 18, 26, 0.95);
        backdrop-filter: blur(20px) saturate(160%);
        -webkit-backdrop-filter: blur(20px) saturate(160%);
        border: 1px solid rgba(255, 255, 255, 0.10);
        border-radius: 14px;
        box-shadow: 0 20px 60px -10px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.04) inset;
        font: 500 13px/1.2 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: #e9e9ef; opacity: 0; transform: translateY(-6px) scale(.98);
        pointer-events: none; transition: opacity .15s ease, transform .15s ease;
      }
      .neo-auth-menu.open { opacity: 1; transform: translateY(0) scale(1); pointer-events: auto; }
      .neo-auth-menu .neo-auth-head { padding: 10px 12px 12px; border-bottom: 1px solid rgba(255,255,255,0.06); margin-bottom: 6px; }
      .neo-auth-menu .neo-auth-head .nn { font-weight: 700; font-size: 14px; margin-bottom: 3px; }
      .neo-auth-menu .neo-auth-head .ne { opacity: 0.6; font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      .neo-auth-menu button {
        width: 100%; text-align: left; background: transparent; border: 0;
        padding: 9px 12px; border-radius: 8px; color: inherit; cursor: pointer;
        font: inherit; display: flex; align-items: center; gap: 10px;
      }
      .neo-auth-menu button:hover { background: rgba(255,255,255,0.06); }
      .neo-auth-menu button.danger:hover { background: rgba(239, 68, 68, 0.12); color: #fca5a5; }
      .neo-auth-menu .ico { width: 16px; opacity: 0.7; text-align: center; }
    `;
    const style = document.createElement('style');
    style.id = 'neo-auth-style';
    style.textContent = css;
    document.head.appendChild(style);
  }

  function initials(name) {
    return (name || '?').trim().split(/\s+/).slice(0, 2).map(s => s[0].toUpperCase()).join('');
  }

  function renderHeader() {
    if (document.getElementById('neo-auth-badge')) return;
    injectHeaderStyles();

    const badge = document.createElement('div');
    badge.id = 'neo-auth-badge';
    badge.className = 'neo-auth-badge';
    const avatar = user.picture
      ? `<img src="${user.picture}" alt="" onerror="this.replaceWith(Object.assign(document.createElement('div'),{className:'neo-auth-initials',textContent:'${initials(user.name || user.email)}'}))">`
      : `<div class="neo-auth-initials">${initials(user.name || user.email)}</div>`;
    badge.innerHTML = `${avatar}<span class="neo-auth-name">${escapeHtml(user.name || user.email)}</span><span class="neo-auth-caret">▼</span>`;

    const menu = document.createElement('div');
    menu.id = 'neo-auth-menu';
    menu.className = 'neo-auth-menu';
    menu.innerHTML = `
      <div class="neo-auth-head">
        <div class="nn">${escapeHtml(user.name || 'User')}</div>
        <div class="ne">${escapeHtml(user.email)}</div>
      </div>
      <button id="neo-auth-cmdk"><span class="ico">⌘</span><span>Command Palette</span></button>
      <button class="danger" id="neo-auth-logout"><span class="ico">⎋</span><span>Logout</span></button>
    `;

    document.body.appendChild(badge);
    document.body.appendChild(menu);

    function toggle(open) {
      const isOpen = open ?? !menu.classList.contains('open');
      menu.classList.toggle('open', isOpen);
    }
    badge.addEventListener('click', (e) => { e.stopPropagation(); toggle(); });
    document.addEventListener('click', (e) => {
      if (!menu.contains(e.target) && e.target !== badge) toggle(false);
    });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') toggle(false); });

    menu.querySelector('#neo-auth-logout').addEventListener('click', logout);
    menu.querySelector('#neo-auth-cmdk').addEventListener('click', () => {
      toggle(false);
      if (window.NeoCmdK) window.NeoCmdK.open();
    });
  }

  function escapeHtml(s) {
    return String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  /* DOM may not be ready yet because guard runs before defer'd scripts */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', renderHeader);
  } else {
    renderHeader();
  }

  /* ---------- 4. Auto-attach Authorization header on all fetch() calls ---------- */
  // Covers every API call to same-origin /chat, /log, /files/*, /gen3d, etc.
  // Skips external URLs + login page calls.
  const _origFetch = window.fetch.bind(window);
  window.fetch = async function (input, init) {
    let sameOrigin = false;
    try {
      const url = typeof input === 'string' ? input : (input && input.url) || '';
      sameOrigin = url.startsWith('/') || url.startsWith(location.origin) || !/^https?:\/\//.test(url);
      if (sameOrigin && user.token) {
        init = init || {};
        const headers = new Headers(init.headers || (typeof input !== 'string' ? input.headers : undefined));
        if (!headers.has('Authorization')) headers.set('Authorization', 'Bearer ' + user.token);
        init.headers = headers;
      }
    } catch {}
    const res = await _origFetch(input, init);
    /* Auto-handle expired/invalid tokens from backend */
    if (sameOrigin && res.status === 401) {
      localStorage.removeItem(STORAGE_KEY);
      redirectToLogin('expired');
    }
    return res;
  };

  /* ---------- 5. Public API ---------- */
  window.NeoAuth = {
    user,
    logout,
    isAuthed: () => !!readSession(),
    token: () => user.token,
  };

  /* ---------- 6. Listen for cross-tab logout ---------- */
  window.addEventListener('storage', (e) => {
    if (e.key === STORAGE_KEY && !e.newValue) redirectToLogin('logout');
  });
})();
