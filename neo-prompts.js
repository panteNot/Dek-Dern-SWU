/* ============================================================
   NEO Labs — Prompt Library
   Usage: <script src="neo-prompts.js" defer></script>
   Stores prompts in localStorage (key: neo_prompt_library_v1).
   Exposes: window.NeoPrompts.{open, close, insert}
   ============================================================ */
(function () {
  'use strict';

  const LS_KEY = 'neo_prompt_library_v1';

  const DEFAULTS = [
    { id: p('d1'), cat: 'Code',    title: 'Review this code',     body: 'ช่วย review code นี้ให้หน่อย — หา bug, security issue, performance problem, และ style ที่ไม่สอดคล้อง:\n\n```\n<paste code here>\n```', ts: Date.now() },
    { id: p('d2'), cat: 'Code',    title: 'Explain this error',   body: 'ผมเจอ error นี้ — ช่วยอธิบายว่าหมายความว่าอะไร เกิดจากอะไร และวิธีแก้:\n\n```\n<paste error here>\n```', ts: Date.now() },
    { id: p('d3'), cat: 'Writing', title: 'Social caption IG',    body: 'เขียน caption สำหรับ Instagram — หัวข้อ: <topic> — tone: <casual/professional/funny> — ยาวประมาณ 3 ประโยค + emojis + hashtags 5 ตัว', ts: Date.now() },
    { id: p('d4'), cat: 'Writing', title: 'Tweet thread',         body: 'เขียน tweet thread 5 tweets เรื่อง <topic> — hook strong, each tweet ≤ 280 chars, last tweet = CTA', ts: Date.now() },
    { id: p('d5'), cat: 'Learn',   title: 'Explain like I\'m new', body: 'อธิบายเรื่อง <topic> แบบที่ผมเพิ่งเริ่มรู้จัก — ใช้ analogy จากชีวิตประจำวัน, 3 bullet points หลัก, จบด้วย "เหมือน..."', ts: Date.now() },
    { id: p('d6'), cat: 'Learn',   title: 'Make flashcards',      body: 'ทำ flashcards (Q → A) จากเนื้อหานี้ — เอา 10 concept ที่สำคัญที่สุด — format: **Q:** ... / **A:** ...\n\n<paste notes>', ts: Date.now() },
    { id: p('d7'), cat: 'Ideas',   title: 'Stress test this idea', body: 'ช่วย stress test ไอเดียนี้ — หาจุดอ่อน, edge case, สมมติฐานที่อาจผิด:\n\n<describe idea>', ts: Date.now() },
    { id: p('d8'), cat: 'Ideas',   title: 'Brainstorm 10 angles', body: 'ช่วย brainstorm 10 มุมมองที่แตกต่างกันสำหรับ <problem> — แต่ละ angle 1-2 ประโยค — เรียงจาก conventional → weird', ts: Date.now() },
  ];

  function p(prefix) { return prefix + '_' + Math.random().toString(36).slice(2, 9); }
  function uid() { return 'p_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 7); }

  function load() {
    try {
      const raw = localStorage.getItem(LS_KEY);
      if (!raw) {
        localStorage.setItem(LS_KEY, JSON.stringify(DEFAULTS));
        return [...DEFAULTS];
      }
      return JSON.parse(raw);
    } catch { return [...DEFAULTS]; }
  }
  function save(list) { localStorage.setItem(LS_KEY, JSON.stringify(list)); }

  const CSS = `
    #neo-pl-fab {
      position: fixed; right: 20px; bottom: 80px; z-index: 998;
      width: 44px; height: 44px; border-radius: 50%;
      background: linear-gradient(135deg, #ff6b35, #ec4899);
      border: none; color: white; font-size: 18px; cursor: pointer;
      box-shadow: 0 8px 24px rgba(255,107,53,0.3);
      transition: transform .15s;
    }
    #neo-pl-fab:hover { transform: scale(1.08); }
    #neo-pl-drawer {
      position: fixed; top: 0; right: 0; bottom: 0;
      width: min(440px, 92vw); z-index: 9999;
      background: #0d0d17;
      border-left: 1px solid rgba(255,255,255,0.08);
      transform: translateX(100%); transition: transform .25s ease;
      display: flex; flex-direction: column;
      font-family: 'Prompt', system-ui, sans-serif; color: #e8e8f0;
      box-shadow: -10px 0 40px rgba(0,0,0,0.4);
    }
    #neo-pl-drawer.open { transform: translateX(0); }
    .neo-pl-head {
      padding: 16px 20px; border-bottom: 1px solid rgba(255,255,255,0.07);
      display: flex; align-items: center; justify-content: space-between;
    }
    .neo-pl-title {
      font-family: 'JetBrains Mono', monospace; font-weight: 900;
      font-size: 13px; letter-spacing: 2px;
      background: linear-gradient(90deg, #ff6b35, #ec4899);
      -webkit-background-clip: text; background-clip: text; color: transparent;
    }
    .neo-pl-head-actions { display: flex; gap: 6px; }
    .neo-pl-icon-btn {
      background: transparent; border: 1px solid rgba(255,255,255,0.12);
      color: #c0c0cc; font-size: 12px; cursor: pointer;
      padding: 5px 10px; border-radius: 6px;
      transition: all .15s;
    }
    .neo-pl-icon-btn:hover { border-color: #ff6b35; color: #ff6b35; }
    .neo-pl-tools {
      padding: 12px 20px; display: flex; gap: 8px; align-items: center;
      border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    .neo-pl-search {
      flex: 1; padding: 8px 10px; border-radius: 6px;
      background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1);
      color: #e8e8f0; font: 12px/1 system-ui, sans-serif; outline: none;
    }
    .neo-pl-search:focus { border-color: #ff6b35; }
    .neo-pl-cat {
      background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
      color: #c0c0cc; padding: 7px 10px; border-radius: 6px;
      font: 11px/1 system-ui, sans-serif;
    }
    .neo-pl-list { flex: 1; overflow-y: auto; padding: 8px 16px 40px; }
    .neo-pl-empty {
      padding: 40px 20px; text-align: center; color: #7b7b8c; font-size: 12px;
    }
    .neo-pl-card {
      background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
      border-radius: 10px; padding: 12px 14px; margin-bottom: 10px;
      cursor: pointer; transition: all .15s;
      position: relative;
    }
    .neo-pl-card:hover {
      border-color: rgba(255,107,53,0.4);
      background: rgba(255,107,53,0.04);
    }
    .neo-pl-card-cat {
      display: inline-block; padding: 2px 8px;
      background: rgba(255,107,53,0.15); color: #ff6b35;
      font: 9px/1.4 'JetBrains Mono', monospace; font-weight: 700;
      letter-spacing: 1px; text-transform: uppercase;
      border-radius: 10px; margin-bottom: 6px;
    }
    .neo-pl-card-title {
      font-size: 13px; font-weight: 600; color: #e8e8f0;
      margin-bottom: 4px; padding-right: 50px;
    }
    .neo-pl-card-body {
      font-size: 11px; color: #8a8a99; line-height: 1.4;
      display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
      overflow: hidden;
    }
    .neo-pl-card-actions {
      position: absolute; top: 10px; right: 10px;
      display: flex; gap: 4px; opacity: 0; transition: opacity .15s;
    }
    .neo-pl-card:hover .neo-pl-card-actions { opacity: 1; }
    .neo-pl-card-action {
      background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.1);
      color: #c0c0cc; width: 24px; height: 24px; border-radius: 5px;
      cursor: pointer; font-size: 11px; display: grid; place-items: center;
    }
    .neo-pl-card-action:hover { border-color: #ff6b35; color: #ff6b35; }

    /* Edit modal */
    #neo-pl-editor {
      position: fixed; inset: 0; z-index: 10001;
      background: rgba(7,7,13,0.82); backdrop-filter: blur(4px);
      display: none; align-items: center; justify-content: center;
    }
    #neo-pl-editor.open { display: flex; }
    .neo-pl-editor-box {
      width: min(540px, 92vw); background: #0d0d17;
      border: 1px solid rgba(255,255,255,0.12); border-radius: 14px;
      padding: 22px 24px;
    }
    .neo-pl-editor-title {
      font-family: 'JetBrains Mono', monospace; font-weight: 700;
      font-size: 12px; letter-spacing: 2px; color: #ff6b35;
      margin-bottom: 16px;
    }
    .neo-pl-field { margin-bottom: 12px; }
    .neo-pl-label {
      display: block; font-size: 10px; letter-spacing: 1.5px;
      color: #7b7b8c; margin-bottom: 4px; text-transform: uppercase;
    }
    .neo-pl-inp {
      width: 100%; padding: 9px 12px; border-radius: 6px;
      background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.12);
      color: #e8e8f0; font: 13px/1.4 system-ui, sans-serif; outline: none;
      font-family: inherit;
    }
    .neo-pl-inp:focus { border-color: #ff6b35; }
    textarea.neo-pl-inp {
      min-height: 160px; resize: vertical;
      font-family: 'JetBrains Mono', monospace; font-size: 12px;
    }
    .neo-pl-editor-btns {
      display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px;
    }
    .neo-pl-btn {
      padding: 8px 16px; border-radius: 6px; border: none;
      font: 12px/1 system-ui, sans-serif; font-weight: 600; cursor: pointer;
    }
    .neo-pl-btn.primary { background: linear-gradient(135deg, #ff6b35, #ec4899); color: #fff; }
    .neo-pl-btn.ghost  { background: transparent; color: #c0c0cc; border: 1px solid rgba(255,255,255,0.12); }
    .neo-pl-btn:hover { filter: brightness(1.1); }

    html[data-theme="light"] #neo-pl-drawer { background: #fff; color: #0f0f1a; border-left-color: rgba(0,0,0,0.08); }
    html[data-theme="light"] .neo-pl-card { background: #f8f8fb; border-color: rgba(0,0,0,0.06); }
    html[data-theme="light"] .neo-pl-card-title { color: #0f0f1a; }
    html[data-theme="light"] .neo-pl-editor-box { background: #fff; color: #0f0f1a; }
    html[data-theme="light"] .neo-pl-inp { background: #f1f1f7; color: #0f0f1a; }
  `;

  function injectStyle() {
    if (document.getElementById('neo-pl-style')) return;
    const s = document.createElement('style');
    s.id = 'neo-pl-style'; s.textContent = CSS;
    document.head.appendChild(s);
  }

  function escapeHtml(str) {
    return String(str ?? '').replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  }

  let items = [];
  let filter = { q: '', cat: '' };
  let drawer = null, editor = null, editingId = null;

  function render() {
    if (drawer) return;
    drawer = document.createElement('aside');
    drawer.id = 'neo-pl-drawer';
    drawer.innerHTML = `
      <div class="neo-pl-head">
        <div class="neo-pl-title">📌 PROMPT LIBRARY</div>
        <div class="neo-pl-head-actions">
          <button class="neo-pl-icon-btn" data-act="new">+ NEW</button>
          <button class="neo-pl-icon-btn" data-act="export" title="Export JSON">⬇</button>
          <button class="neo-pl-icon-btn" data-act="import" title="Import JSON">⬆</button>
          <button class="neo-pl-icon-btn" data-act="close">×</button>
        </div>
      </div>
      <div class="neo-pl-tools">
        <input class="neo-pl-search" id="neo-pl-search-inp" placeholder="🔍 ค้นหา…" autocomplete="off" />
        <select class="neo-pl-cat" id="neo-pl-cat-sel"></select>
      </div>
      <div class="neo-pl-list" id="neo-pl-list"></div>
      <input type="file" id="neo-pl-import-file" accept="application/json" style="display:none;" />
    `;
    document.body.appendChild(drawer);

    drawer.querySelector('[data-act="close"]').addEventListener('click', close);
    drawer.querySelector('[data-act="new"]').addEventListener('click', () => openEditor(null));
    drawer.querySelector('[data-act="export"]').addEventListener('click', exportJson);
    drawer.querySelector('[data-act="import"]').addEventListener('click', () => drawer.querySelector('#neo-pl-import-file').click());
    drawer.querySelector('#neo-pl-import-file').addEventListener('change', importJson);
    drawer.querySelector('#neo-pl-search-inp').addEventListener('input', (e) => { filter.q = e.target.value; renderList(); });
    drawer.querySelector('#neo-pl-cat-sel').addEventListener('change', (e) => { filter.cat = e.target.value; renderList(); });
    drawer.querySelector('#neo-pl-list').addEventListener('click', onListClick);

    renderEditor();
  }

  function renderEditor() {
    if (editor) return;
    editor = document.createElement('div');
    editor.id = 'neo-pl-editor';
    editor.innerHTML = `
      <div class="neo-pl-editor-box" role="dialog" aria-label="Edit prompt">
        <div class="neo-pl-editor-title" id="neo-pl-editor-heading">NEW PROMPT</div>
        <div class="neo-pl-field">
          <label class="neo-pl-label">Title</label>
          <input class="neo-pl-inp" id="neo-pl-ed-title" />
        </div>
        <div class="neo-pl-field">
          <label class="neo-pl-label">Category</label>
          <input class="neo-pl-inp" id="neo-pl-ed-cat" placeholder="Code / Writing / Learn / Ideas / …" />
        </div>
        <div class="neo-pl-field">
          <label class="neo-pl-label">Prompt Body</label>
          <textarea class="neo-pl-inp" id="neo-pl-ed-body"></textarea>
        </div>
        <div class="neo-pl-editor-btns">
          <button class="neo-pl-btn ghost" data-act="cancel">ยกเลิก</button>
          <button class="neo-pl-btn ghost" data-act="del" id="neo-pl-ed-del" style="color:#ef4444; display:none;">ลบ</button>
          <button class="neo-pl-btn primary" data-act="save">บันทึก</button>
        </div>
      </div>
    `;
    document.body.appendChild(editor);
    editor.addEventListener('click', (e) => { if (e.target === editor) closeEditor(); });
    editor.querySelector('[data-act="cancel"]').addEventListener('click', closeEditor);
    editor.querySelector('[data-act="save"]').addEventListener('click', saveFromEditor);
    editor.querySelector('[data-act="del"]').addEventListener('click', delFromEditor);
  }

  function openEditor(id) {
    editingId = id;
    const delBtn = editor.querySelector('#neo-pl-ed-del');
    if (id) {
      const it = items.find(x => x.id === id);
      if (!it) return;
      editor.querySelector('#neo-pl-editor-heading').textContent = 'EDIT PROMPT';
      editor.querySelector('#neo-pl-ed-title').value = it.title;
      editor.querySelector('#neo-pl-ed-cat').value   = it.cat || '';
      editor.querySelector('#neo-pl-ed-body').value  = it.body;
      delBtn.style.display = 'inline-block';
    } else {
      editor.querySelector('#neo-pl-editor-heading').textContent = 'NEW PROMPT';
      editor.querySelector('#neo-pl-ed-title').value = '';
      editor.querySelector('#neo-pl-ed-cat').value   = '';
      editor.querySelector('#neo-pl-ed-body').value  = '';
      delBtn.style.display = 'none';
    }
    editor.classList.add('open');
    editor.querySelector('#neo-pl-ed-title').focus();
  }
  function closeEditor() { editor?.classList.remove('open'); editingId = null; }

  function saveFromEditor() {
    const title = editor.querySelector('#neo-pl-ed-title').value.trim();
    const cat   = editor.querySelector('#neo-pl-ed-cat').value.trim() || 'General';
    const body  = editor.querySelector('#neo-pl-ed-body').value.trim();
    if (!title || !body) { alert('ต้องมี title + body'); return; }
    if (editingId) {
      const i = items.findIndex(x => x.id === editingId);
      if (i >= 0) items[i] = { ...items[i], title, cat, body };
    } else {
      items.unshift({ id: uid(), title, cat, body, ts: Date.now() });
    }
    save(items); renderList(); closeEditor();
  }
  function delFromEditor() {
    if (!editingId) return;
    if (!confirm('ลบ prompt นี้?')) return;
    items = items.filter(x => x.id !== editingId);
    save(items); renderList(); closeEditor();
  }

  function exportJson() {
    const blob = new Blob([JSON.stringify(items, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `neo-prompts-${new Date().toISOString().slice(0,10)}.json`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function importJson(e) {
    const file = e.target.files[0];
    if (!file) return;
    const r = new FileReader();
    r.onload = () => {
      try {
        const data = JSON.parse(r.result);
        if (!Array.isArray(data)) throw new Error('must be array');
        const cleaned = data.filter(x => x && x.title && x.body)
                            .map(x => ({ id: x.id || uid(), title: x.title, cat: x.cat || 'Imported', body: x.body, ts: x.ts || Date.now() }));
        items = [...cleaned, ...items];
        save(items); renderList();
        alert(`Imported ${cleaned.length} prompts`);
      } catch (err) { alert('Import failed: ' + err.message); }
    };
    r.readAsText(file);
    e.target.value = '';
  }

  function renderCats() {
    const sel = drawer.querySelector('#neo-pl-cat-sel');
    const cats = ['all', ...Array.from(new Set(items.map(x => x.cat || 'General'))).sort()];
    const cur = filter.cat || 'all';
    sel.innerHTML = cats.map(c => `<option value="${c === 'all' ? '' : escapeHtml(c)}" ${(c==='all'?'':c) === filter.cat ? 'selected' : ''}>${c === 'all' ? 'ทุกหมวด' : escapeHtml(c)}</option>`).join('');
  }

  function renderList() {
    renderCats();
    const list = drawer.querySelector('#neo-pl-list');
    const q = filter.q.trim().toLowerCase();
    let filtered = items;
    if (q) filtered = filtered.filter(x => (x.title + ' ' + x.body + ' ' + (x.cat||'')).toLowerCase().includes(q));
    if (filter.cat) filtered = filtered.filter(x => (x.cat || 'General') === filter.cat);
    if (!filtered.length) {
      list.innerHTML = '<div class="neo-pl-empty">ไม่พบ prompt — ลอง + NEW ดู</div>';
      return;
    }
    list.innerHTML = filtered.map(x => `
      <div class="neo-pl-card" data-id="${x.id}">
        <div class="neo-pl-card-cat">${escapeHtml(x.cat || 'General')}</div>
        <div class="neo-pl-card-title">${escapeHtml(x.title)}</div>
        <div class="neo-pl-card-body">${escapeHtml(x.body)}</div>
        <div class="neo-pl-card-actions">
          <button class="neo-pl-card-action" data-act="edit" title="Edit">✎</button>
          <button class="neo-pl-card-action" data-act="copy" title="Copy">⎘</button>
        </div>
      </div>
    `).join('');
  }

  function onListClick(e) {
    const actBtn = e.target.closest('.neo-pl-card-action');
    const card   = e.target.closest('.neo-pl-card');
    if (!card) return;
    const id = card.dataset.id;
    const it = items.find(x => x.id === id);
    if (!it) return;
    if (actBtn) {
      e.stopPropagation();
      if (actBtn.dataset.act === 'edit') openEditor(id);
      else if (actBtn.dataset.act === 'copy') {
        navigator.clipboard?.writeText(it.body);
        actBtn.textContent = '✓';
        setTimeout(() => { actBtn.textContent = '⎘'; }, 1200);
      }
      return;
    }
    insert(it.body);
    close();
  }

  function insert(text) {
    const targets = ['cmd', 'composerInput', 'msgInput', 'input'];
    for (const id of targets) {
      const el = document.getElementById(id);
      if (el && (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT')) {
        el.value = text;
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.focus();
        return true;
      }
    }
    navigator.clipboard?.writeText(text);
    alert('ไม่เจอ input box — copy ไป clipboard แล้ว');
    return false;
  }

  function addFab() {
    if (document.getElementById('neo-pl-fab')) return;
    injectStyle();  // FAB styles live in CSS block — must inject before append or button renders invisible
    const b = document.createElement('button');
    b.id = 'neo-pl-fab';
    b.title = 'Prompt Library';
    b.textContent = '📌';
    b.addEventListener('click', open);
    document.body.appendChild(b);
  }

  function open() {
    items = load();
    injectStyle();
    render();
    renderList();
    drawer.classList.add('open');
  }
  function close() { drawer?.classList.remove('open'); }

  /* Esc closes drawer (but not if editor open — editor owns Esc then) */
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    if (editor?.classList.contains('open')) { closeEditor(); return; }
    if (drawer?.classList.contains('open')) close();
  });

  /* Init on load */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addFab);
  } else {
    addFab();
  }

  window.NeoPrompts = { open, close, insert };
})();
