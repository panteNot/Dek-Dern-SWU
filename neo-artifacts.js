/* ==========================================================================
   NEO Labs — Artifacts Panel (shared module)
   --------------------------------------------------------------------------
   Slide-in right panel for code / HTML preview / markdown.
   Public API:
     window.NeoArtifacts.open({ title, lang, content, author })
     window.NeoArtifacts.close()
     window.NeoArtifacts.scan(text) -> [{ lang, content }] — fenced blocks
   ========================================================================== */
(function () {
  'use strict';
  if (window.NeoArtifacts) return;   // idempotent

  /* ---------- Fenced block parser ---------- */
  function scan(text) {
    if (!text) return [];
    const re = /```([a-zA-Z0-9+_-]*)\n([\s\S]*?)```/g;
    const out = [];
    let m;
    while ((m = re.exec(text)) !== null) {
      out.push({ lang: (m[1] || 'text').toLowerCase(), content: m[2] });
    }
    return out;
  }

  /* ---------- CSS inject ---------- */
  const CSS = `
    .neo-arts-backdrop {
      position: fixed; inset: 0; background: rgba(0,0,0,0.35);
      opacity: 0; pointer-events: none; transition: opacity .18s ease;
      z-index: 9990;
    }
    .neo-arts-backdrop.open { opacity: 1; pointer-events: auto; }

    .neo-arts-panel {
      position: fixed; top: 0; right: 0; bottom: 0;
      width: min(780px, 88vw);
      background: #0d0d14;
      border-left: 1px solid rgba(255,255,255,0.08);
      box-shadow: -20px 0 60px -10px rgba(0,0,0,0.6);
      display: flex; flex-direction: column;
      transform: translateX(100%); transition: transform .22s cubic-bezier(.3,.7,.3,1);
      z-index: 9991;
      font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: #e9e9ef;
    }
    .neo-arts-panel.open { transform: translateX(0); }

    .neo-arts-head {
      display: flex; align-items: center; gap: 10px;
      padding: 12px 16px; border-bottom: 1px solid rgba(255,255,255,0.06);
      background: rgba(255,255,255,0.02);
    }
    .neo-arts-head .na-title {
      flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis;
      white-space: nowrap; font-weight: 700; font-size: 13px; letter-spacing: .5px;
    }
    .neo-arts-head .na-meta {
      font: 500 10px/1 'JetBrains Mono', monospace;
      color: #7c7c8a; padding: 4px 8px; border: 1px solid rgba(255,255,255,0.1);
      border-radius: 999px;
    }
    .neo-arts-head button {
      background: transparent; border: 1px solid rgba(255,255,255,0.1);
      color: #d5d5dd; padding: 6px 10px; border-radius: 8px;
      font: 500 12px/1 inherit; cursor: pointer;
      display: inline-flex; align-items: center; gap: 5px;
      transition: background .12s, border-color .12s, color .12s;
    }
    .neo-arts-head button:hover { background: rgba(255,255,255,0.06); border-color: rgba(255,255,255,0.22); }
    .neo-arts-head .na-close {
      background: transparent; border: 0; color: #7c7c8a; font-size: 20px;
      padding: 4px 8px; border-radius: 8px;
    }
    .neo-arts-head .na-close:hover { background: rgba(239,68,68,0.14); color: #fca5a5; }

    .neo-arts-tabs {
      display: flex; gap: 2px; padding: 8px 12px;
      background: rgba(255,255,255,0.015);
      border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    .neo-arts-tabs button {
      background: transparent; border: 0; color: #9a9aa8;
      padding: 7px 14px; border-radius: 7px;
      font: 600 12px/1 inherit; letter-spacing: .3px; cursor: pointer;
    }
    .neo-arts-tabs button.active { background: rgba(255,255,255,0.07); color: #fff; }
    .neo-arts-tabs button:hover:not(.active) { background: rgba(255,255,255,0.04); color: #d5d5dd; }

    .neo-arts-body { flex: 1; min-height: 0; overflow: hidden; position: relative; }
    .neo-arts-view { position: absolute; inset: 0; display: none; overflow: auto; }
    .neo-arts-view.active { display: block; }

    .neo-arts-code {
      font: 13px/1.6 'JetBrains Mono', ui-monospace, Menlo, monospace;
      padding: 16px 18px; white-space: pre; color: #e9e9ef;
      tab-size: 2;
    }
    .neo-arts-md {
      padding: 20px 24px; line-height: 1.7;
    }
    .neo-arts-md h1, .neo-arts-md h2, .neo-arts-md h3 { margin: 1em 0 .4em; font-weight: 700; }
    .neo-arts-md h1 { font-size: 22px; } .neo-arts-md h2 { font-size: 18px; } .neo-arts-md h3 { font-size: 15px; }
    .neo-arts-md p  { margin: .6em 0; }
    .neo-arts-md ul, .neo-arts-md ol { margin: .6em 0 .6em 1.5em; }
    .neo-arts-md code {
      font: 12px/1 'JetBrains Mono', monospace;
      background: rgba(255,255,255,0.07); padding: 2px 6px; border-radius: 5px;
    }
    .neo-arts-md pre {
      background: #05050a; border: 1px solid rgba(255,255,255,0.06);
      padding: 12px 14px; border-radius: 10px; overflow: auto; margin: .8em 0;
    }
    .neo-arts-md pre code { background: transparent; padding: 0; }
    .neo-arts-md a { color: #a855f7; }

    .neo-arts-preview {
      width: 100%; height: 100%; border: 0; background: #fff;
    }

    .neo-arts-toast {
      position: fixed; bottom: 22px; right: 22px; z-index: 9993;
      padding: 10px 16px; background: #1a1a26; color: #e9e9ef;
      border: 1px solid rgba(255,255,255,0.1); border-radius: 10px;
      font: 500 12px/1 inherit; opacity: 0; transform: translateY(8px);
      transition: opacity .18s, transform .18s; pointer-events: none;
    }
    .neo-arts-toast.show { opacity: 1; transform: translateY(0); }

    /* Pill inside host page to trigger panel */
    .neo-arts-pill {
      display: inline-flex; align-items: center; gap: 6px;
      padding: 5px 10px; margin: 6px 6px 0 0;
      background: rgba(255,255,255,0.05); color: inherit;
      border: 1px solid rgba(255,255,255,0.1); border-radius: 999px;
      font: 600 11px/1 'JetBrains Mono', monospace; cursor: pointer;
      transition: background .12s, border-color .12s;
    }
    .neo-arts-pill:hover { background: rgba(255,255,255,0.1); border-color: currentColor; }
    .neo-arts-pill .na-p-ico { opacity: 0.8; }
  `;
  const style = document.createElement('style');
  style.id = 'neo-arts-style';
  style.textContent = CSS;
  document.head.appendChild(style);

  /* ---------- Markup ---------- */
  const backdrop = document.createElement('div');
  backdrop.className = 'neo-arts-backdrop';

  const panel = document.createElement('aside');
  panel.className = 'neo-arts-panel';
  panel.innerHTML = `
    <header class="neo-arts-head">
      <div class="na-title">Artifact</div>
      <span class="na-meta">—</span>
      <button class="na-copy" title="Copy (⌘C)"><span>Copy</span></button>
      <button class="na-download" title="Download"><span>Download</span></button>
      <button class="na-close" title="Close (Esc)">×</button>
    </header>
    <nav class="neo-arts-tabs">
      <button data-tab="code" class="active">Code</button>
      <button data-tab="preview">Preview</button>
      <button data-tab="markdown">Markdown</button>
    </nav>
    <div class="neo-arts-body">
      <div class="neo-arts-view active" data-view="code"><pre class="neo-arts-code"></pre></div>
      <div class="neo-arts-view" data-view="preview"></div>
      <div class="neo-arts-view" data-view="markdown"><div class="neo-arts-md"></div></div>
    </div>
  `;

  const toast = document.createElement('div');
  toast.className = 'neo-arts-toast';

  function mount() {
    if (!document.body) return setTimeout(mount, 30);
    document.body.appendChild(backdrop);
    document.body.appendChild(panel);
    document.body.appendChild(toast);
    bind();
  }

  /* ---------- State ---------- */
  let current = { title: 'Artifact', lang: 'text', content: '', author: '' };

  /* ---------- Helpers ---------- */
  const EXT_BY_LANG = {
    html: 'html', htm: 'html', xml: 'xml', svg: 'svg',
    js: 'js', javascript: 'js', mjs: 'js', jsx: 'jsx', ts: 'ts', tsx: 'tsx',
    py: 'py', python: 'py', rb: 'rb', go: 'go', rs: 'rs',
    css: 'css', scss: 'scss', sql: 'sql', sh: 'sh', bash: 'sh',
    json: 'json', yaml: 'yaml', yml: 'yaml', toml: 'toml',
    md: 'md', markdown: 'md', text: 'txt', '': 'txt'
  };
  function extFor(lang) { return EXT_BY_LANG[lang] || 'txt'; }
  function isHTML(lang, content) {
    if (/^(html|htm|xml|svg)$/i.test(lang)) return true;
    return /<(?:!DOCTYPE|html|body|div|section|article)/i.test(content || '');
  }
  function isMarkdown(lang) { return /^(md|markdown)$/i.test(lang); }

  function escHtml(s) {
    return String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  /* Tiny, safe-ish markdown (headings/bold/italic/code/links/lists) */
  function renderMarkdown(src) {
    let html = escHtml(src);
    html = html.replace(/```([a-zA-Z0-9+_-]*)\n([\s\S]*?)```/g,
      (_, l, code) => `<pre><code data-lang="${l}">${code}</code></pre>`);
    html = html.replace(/`([^`\n]+)`/g, '<code>$1</code>');
    html = html.replace(/^###\s+(.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^##\s+(.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^#\s+(.+)$/gm, '<h1>$1</h1>');
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener">$1</a>');
    html = html.replace(/(^|\n)- (.+?)(?=\n[^-]|\n$|$)/gs, (_, p, item) => `${p}<ul><li>${item}</li></ul>`);
    html = html.replace(/<\/ul>\s*<ul>/g, '');
    html = html.split(/\n{2,}/).map(b => /^<(h\d|ul|pre|ol)/.test(b) ? b : `<p>${b.replace(/\n/g, '<br>')}</p>`).join('\n');
    return html;
  }

  /* ---------- Render ---------- */
  function setTab(name) {
    panel.querySelectorAll('.neo-arts-tabs button').forEach(b =>
      b.classList.toggle('active', b.dataset.tab === name));
    panel.querySelectorAll('.neo-arts-view').forEach(v =>
      v.classList.toggle('active', v.dataset.view === name));
  }

  function renderAll() {
    panel.querySelector('.na-title').textContent = current.title || 'Artifact';
    const meta = current.lang + (current.author ? ` · ${current.author}` : '');
    panel.querySelector('.na-meta').textContent = meta;

    /* Code view */
    panel.querySelector('.neo-arts-code').textContent = current.content;

    /* Preview view */
    const prevView = panel.querySelector('[data-view="preview"]');
    prevView.innerHTML = '';
    if (isHTML(current.lang, current.content)) {
      const iframe = document.createElement('iframe');
      iframe.className = 'neo-arts-preview';
      iframe.setAttribute('sandbox', 'allow-scripts');   // no same-origin → can't read parent
      iframe.srcdoc = current.content;
      prevView.appendChild(iframe);
    } else {
      prevView.innerHTML = `<div style="padding:40px;color:#7c7c8a;text-align:center;">
        <div style="font-size:30px;">🔒</div>
        <div style="margin-top:10px;">Preview available only for HTML artifacts.</div>
        <div style="margin-top:4px;font-size:12px;">Current: <code>${escHtml(current.lang)}</code></div>
      </div>`;
    }

    /* Markdown view */
    const md = panel.querySelector('.neo-arts-md');
    if (isMarkdown(current.lang)) {
      md.innerHTML = renderMarkdown(current.content);
    } else {
      md.innerHTML = `<p style="color:#7c7c8a;">Not a markdown artifact. Viewing raw:</p>
                      <pre><code>${escHtml(current.content)}</code></pre>`;
    }

    /* Default tab by kind */
    setTab(isHTML(current.lang, current.content) ? 'preview'
         : isMarkdown(current.lang)               ? 'markdown'
         : 'code');
  }

  /* ---------- Open/Close ---------- */
  function open(art) {
    current = Object.assign({ title: 'Artifact', lang: 'text', content: '', author: '' }, art || {});
    renderAll();
    backdrop.classList.add('open');
    panel.classList.add('open');
  }
  function close() {
    backdrop.classList.remove('open');
    panel.classList.remove('open');
  }

  /* ---------- Events ---------- */
  function showToast(msg) {
    toast.textContent = msg;
    toast.classList.add('show');
    clearTimeout(showToast._t);
    showToast._t = setTimeout(() => toast.classList.remove('show'), 1800);
  }

  function bind() {
    backdrop.addEventListener('click', close);
    panel.querySelector('.na-close').addEventListener('click', close);
    panel.querySelectorAll('.neo-arts-tabs button').forEach(b =>
      b.addEventListener('click', () => setTab(b.dataset.tab)));
    panel.querySelector('.na-copy').addEventListener('click', async () => {
      try { await navigator.clipboard.writeText(current.content); showToast('Copied to clipboard'); }
      catch { showToast('Copy failed'); }
    });
    panel.querySelector('.na-download').addEventListener('click', () => {
      const ext = extFor(current.lang);
      const safeTitle = (current.title || 'artifact').replace(/[^\w\- ]+/g, '_').slice(0, 60);
      const blob = new Blob([current.content], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = `${safeTitle}.${ext}`;
      document.body.appendChild(a); a.click();
      setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 500);
      showToast('Downloaded');
    });
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && panel.classList.contains('open')) { e.preventDefault(); close(); }
    });
  }

  /* ---------- Public API ---------- */
  window.NeoArtifacts = { open, close, scan };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mount);
  } else {
    mount();
  }
})();
