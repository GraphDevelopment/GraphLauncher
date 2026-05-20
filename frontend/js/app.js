/* ============================================================
   Graph Launcher — Application
   ============================================================ */

/* ── State ──────────────────────────────────────────────── */
const S = {
  page:         'packs',
  packs:        [],
  sel:          null,
  settings:     {},
  filters:      { search: '', tags: [], status: 'all' },
  busy:         false,
  activeBtn:    null,
  updateUrl:    null,
  workshopPacks: [],
};

/* ── i18n shortcut ──────────────────────────────────────── */
function t(key, vars) { return I18n.t(key, vars); }

/* ── Spinner SVG snippet ────────────────────────────────── */
const SPIN_SVG = `<span class="btn-spinner"></span>`;

/* ── Button loading helpers ─────────────────────────────── */
function btnLoad(btn, label) {
  if (!btn) return;
  btn._saved = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `${SPIN_SVG}${label || ''}`;
}
function btnReset(btn) {
  if (!btn) return;
  btn.disabled = false;
  if (btn._saved !== undefined) btn.innerHTML = btn._saved;
}

/* ── pywebview event bridge ─────────────────────────────── */
window.__pyEvent = function(type, data) {
  switch (type) {
    case 'operation-start':
      openProgressModal(data.title || 'Opération en cours');
      break;
    case 'progress':
      setProgress(data.percent, data.message);
      break;
    case 'operation-end':
      closeModal();
      S.busy = false;
      btnReset(S.activeBtn);
      S.activeBtn = null;
      if (data.success === false) {
        toast(data.error || t('toast_operation_failed'), 'error');
      } else {
        const n = data.files_copied ?? data.deleted;
        toast(n != null ? t('toast_files_n', { n }) : t('toast_operation_done'), 'success');
        if (S.page === 'packs')    refreshPacks();
        if (S.page === 'workshop') { toast(t('toast_download_ok'), 'success'); refreshPacks(); }
        if (S.page === 'settings') loadSettings();
      }
      break;
  }
};

/* ── Router ─────────────────────────────────────────────── */
function navigate(page) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const el = document.getElementById('page-' + page);
  if (el) el.classList.add('active');
  const nav = document.querySelector(`.nav-item[data-page="${page}"]`);
  if (nav) nav.classList.add('active');
  S.page = page;
  if (page === 'packs')    refreshPacks();
  if (page === 'settings') loadSettings();
  if (page === 'workshop') refreshWorkshop();
}

/* ══════════════════════════════════════════════════════════
   PACKS PAGE
══════════════════════════════════════════════════════════ */

async function refreshPacks() {
  const btn = document.querySelector('[onclick="refreshPacks()"]');
  btnLoad(btn, 'Scan…');
  showSkeletons();
  const r = await Api.scanPacks();
  btnReset(btn);

  if (!r || r.success === false) {
    S.packs = [];
    renderPacks([]);
    setText('empty-title', t('toast_no_packs_dir'));
    setText('empty-desc', r?.error || '');
    return;
  }
  S.packs = r.packs || [];
  renderFiltered();
  updateStats();

  const n = S.packs.length;
  toast(t('toast_packs_n', { n }), 'info');
}

function renderFiltered() {
  const { search, tags, status } = S.filters;
  const filtered = S.packs.filter(p => {
    if (search && !p.name.toLowerCase().includes(search.toLowerCase())) return false;
    if (status === 'installed'     && !p.installed)  return false;
    if (status === 'not-installed' &&  p.installed)  return false;
    if (tags.length && !tags.some(t => p.tags.includes(t))) return false;
    return true;
  });
  renderPacks(filtered);
}

function renderPacks(list) {
  const grid  = $('packs-grid');
  const empty = $('empty-state');
  grid.innerHTML = '';
  if (!list.length) {
    grid.style.display = 'none';
    empty.style.display = 'flex';
    return;
  }
  grid.style.display = 'grid';
  empty.style.display = 'none';
  list.forEach(p => grid.appendChild(buildCard(p)));
}

function buildCard(pack) {
  const el = document.createElement('div');
  el.className = 'pack-card' + (S.sel?.name === pack.name ? ' selected' : '');
  el.dataset.name = pack.name;

  const tags = (pack.tags || []).map(t => {
    const cls = t.replace(/\s+/g, '-');
    return `<span class="tag t-${cls}">${t}</span>`;
  }).join('') || `<span style="font-size:11px;color:var(--text3)">Aucun tag détecté</span>`;

  el.innerHTML = `
    <div class="card-top">
      <div style="min-width:0">
        <div class="card-name">${esc(pack.name)}</div>
        <div class="card-path">${esc(pack.path)}</div>
      </div>
      <span class="status-badge ${pack.installed ? 'on' : 'off'}">${pack.installed ? 'Installé' : 'Non installé'}</span>
    </div>
    <div class="tags-row">${tags}</div>
    <div class="card-actions" id="act-${esc(pack.name)}">
      ${buildCardButtons(pack)}
    </div>`;

  el.addEventListener('click', e => {
    if (e.target.closest('.btn')) return;
    S.sel = pack;
    document.querySelectorAll('.pack-card').forEach(c =>
      c.classList.toggle('selected', c.dataset.name === pack.name));
  });
  return el;
}

function buildCardButtons(pack) {
  const ico = {
    install: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>`,
    trash:   `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>`,
    folder:  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>`,
  };
  return `
    <button class="btn btn-primary btn-sm" onclick="doInstall(${jsStr(pack.path)},this)">
      ${ico.install} Installer
    </button>
    ${pack.installed ? `
    <button class="btn btn-danger btn-sm" onclick="doUninstall(${jsStr(pack.name)},this)">
      ${ico.trash} Désinstaller
    </button>` : ''}
    <button class="btn btn-ghost btn-sm" onclick="doOpenFolder(${jsStr(pack.path)},this)">
      ${ico.folder} Ouvrir
    </button>`;
}

function showSkeletons() {
  const grid = $('packs-grid');
  grid.innerHTML = '';
  grid.style.display = 'grid';
  $('empty-state').style.display = 'none';
  for (let i = 0; i < 6; i++) {
    const c = document.createElement('div');
    c.className = 'pack-card';
    c.style.cssText = 'pointer-events:none; min-height:130px;';
    c.innerHTML = `
      <div class="card-top" style="margin-bottom:10px">
        <div style="flex:1;display:flex;flex-direction:column;gap:7px">
          <div class="skeleton" style="height:13px;width:55%"></div>
          <div class="skeleton" style="height:10px;width:75%"></div>
        </div>
        <div class="skeleton" style="height:18px;width:62px;border-radius:3px"></div>
      </div>
      <div style="display:flex;gap:5px;margin-bottom:12px">
        <div class="skeleton" style="height:16px;width:48px;border-radius:3px"></div>
        <div class="skeleton" style="height:16px;width:60px;border-radius:3px"></div>
      </div>
      <div style="display:flex;gap:5px">
        <div class="skeleton" style="height:28px;width:78px;border-radius:5px"></div>
        <div class="skeleton" style="height:28px;width:68px;border-radius:5px"></div>
      </div>`;
    grid.appendChild(c);
  }
}

function updateStats() {
  const t = S.packs.length;
  const i = S.packs.filter(p => p.installed).length;
  setText('stat-total',     t);
  setText('stat-installed', i);
  setText('stat-pending',   t - i);
}

/* Filters */
function onSearch(val) { S.filters.search = val; renderFiltered(); }

function setStatusFilter(v) {
  S.filters.status = v;
  document.querySelectorAll('[data-status]').forEach(el =>
    el.classList.toggle('active', el.dataset.status === v));
  renderFiltered();
}

function toggleTag(tag) {
  const idx = S.filters.tags.indexOf(tag);
  if (idx > -1) S.filters.tags.splice(idx, 1);
  else S.filters.tags.push(tag);
  document.querySelectorAll('[data-tag]').forEach(el =>
    el.classList.toggle('active', S.filters.tags.includes(el.dataset.tag)));
  renderFiltered();
}

/* ── Pack actions ───────────────────────────────────────── */

async function doInstall(path, btn) {
  if (S.busy) { toast(t('toast_busy'), 'warning'); return; }
  S.busy = true;
  btnLoad(btn, t('installing'));
  const r = await Api.installPack(path);
  if (r?.success === false) {
    S.busy = false;
    btnReset(btn);
    toast(r.error || t('toast_operation_failed'), 'error');
  } else {
    toast(t('toast_install_started'), 'info');
  }
}

async function doUninstall(name, btn) {
  confirm2(
    t('confirm_uninstall_title'),
    t('confirm_uninstall_desc', { name }),
    'red',
    async () => {
      if (S.busy) return;
      S.busy = true;
      btnLoad(btn, t('uninstalling'));
      const r = await Api.uninstallPack(name);
      if (r?.success === false) {
        S.busy = false;
        btnReset(btn);
        toast(r.error || t('toast_operation_failed'), 'error');
      } else {
        toast(t('toast_uninstall_started'), 'info');
      }
    }
  );
}

async function doOpenFolder(path, btn) {
  btnLoad(btn, '');
  await Api.openFolder(path);
  btnReset(btn);
}

async function confirmClean(target, btn) {
  const isFM = target === 'fivem';
  confirm2(
    isFM ? t('confirm_clean_fivem_title') : t('confirm_clean_gtav_title'),
    isFM ? t('confirm_clean_fivem_desc')  : t('confirm_clean_gtav_desc'),
    'amber',
    async () => {
      if (S.busy) return;
      S.busy = true;
      S.activeBtn = btn;
      btnLoad(btn, t('cleaning'));
      if (isFM) await Api.cleanFivem();
      else      await Api.cleanGtav();
    }
  );
}

/* ══════════════════════════════════════════════════════════
   SETTINGS PAGE
══════════════════════════════════════════════════════════ */

async function loadSettings() {
  const s = await Api.getSettings();
  if (!s) return;
  S.settings = s;
  setVal('packs-dir',  s.packs_dir        || '');
  setVal('fivem-exe',  s.fivem_exe        || '');
  setVal('fivem-data', s.fivem_data_dir   || '');
  setVal('gtav-dir',   s.gtav_dir         || '');

  const bs = await Api.getBaselineStatus();
  const el = $('baseline-status');
  if (el) el.innerHTML = bs?.exists
    ? `<span style="color:var(--green)">${t('baseline_ok', { n: (bs.file_count||0).toLocaleString() })}</span>`
    : `<span style="color:var(--text3)">${t('baseline_none')}</span>`;
}

async function saveSettings() {
  const btn = document.querySelector('[onclick="saveSettings()"]');
  btnLoad(btn, t('saving'));
  const s = {
    packs_dir:      getVal('packs-dir'),
    fivem_exe:      getVal('fivem-exe'),
    fivem_data_dir: getVal('fivem-data'),
    gtav_dir:       getVal('gtav-dir'),
    first_run:      false,
  };
  const r = await Api.saveSettings(s);
  btnReset(btn);
  if (r?.success !== false) toast(t('toast_settings_saved'), 'success');
  else                      toast(r?.error || t('toast_operation_failed'), 'error');
}

async function browsePacksDir() {
  const btn = event.currentTarget;
  btnLoad(btn, '');
  const r = await Api.selectFolder();
  btnReset(btn);
  if (r?.success && r.path) {
    setVal('packs-dir', r.path);
    toast(t('toast_folder_selected'), 'info');
  }
}

async function browseFivemExe() {
  const btn = event.currentTarget;
  btnLoad(btn, '');
  const r = await Api.selectFivemExe();
  if (!r?.success || !r.path) { btnReset(btn); return; }

  setVal('fivem-exe', r.path);
  const hint = $('fivem-hint');
  if (hint) { hint.textContent = t('valid_checking'); hint.className = 'form-hint'; }

  const v = await Api.validateFivem(r.path);
  btnReset(btn);

  if (hint) {
    hint.textContent = v.valid
      ? t('valid_fivem_ok', { dir: v.data_dir || '' })
      : v.error || t('toast_invalid_path');
    hint.className = 'form-hint ' + (v.valid ? 'ok' : 'err');
  }
  if (v.valid && v.data_dir) {
    setVal('fivem-data', v.data_dir);
    toast(t('toast_fivem_ok'), 'success');
  } else {
    toast(v.error || t('toast_operation_failed'), 'error');
  }
}

async function browseGtavDir() {
  const btn = event.currentTarget;
  btnLoad(btn, '');
  const r = await Api.selectFolder();
  if (!r?.success || !r.path) { btnReset(btn); return; }

  setVal('gtav-dir', r.path);
  const hint = $('gtav-hint');
  if (hint) { hint.textContent = t('valid_checking_gtav'); hint.className = 'form-hint'; }

  const v = await Api.validateGtav(r.path);
  btnReset(btn);

  if (hint) {
    hint.textContent = v.valid ? t('valid_gtav_ok') : v.error || t('toast_invalid_path');
    hint.className   = 'form-hint ' + (v.valid ? 'ok' : 'err');
  }
  if (v.valid) toast(t('toast_gtav_ok'), 'success');
  else         toast(v.error || t('toast_operation_failed'), 'error');
}

async function createBaseline() {
  if (!getVal('gtav-dir')) {
    toast(t('toast_need_gtav'), 'error');
    return;
  }
  confirm2(
    t('confirm_baseline_title'),
    t('confirm_baseline_desc'),
    'blue',
    async () => {
      if (S.busy) return;
      S.busy = true;
      await Api.createGtavBaseline();
    }
  );
}

/* ══════════════════════════════════════════════════════════
   TUTORIAL PAGE
══════════════════════════════════════════════════════════ */

function initTutorial() {
  const ITEMS = [
    {
      title: 'Fonctionnement général',
      body: `<p>Le launcher scanne votre dossier de packs et détecte automatiquement chaque sous-dossier.
             Les tags (<strong>MODS</strong>, <strong>CITIZEN</strong>, <strong>PLUGIN</strong>,
             <strong>RESHADE</strong>, <strong>ENB</strong>, <strong>SOUND PACK</strong>) sont identifiés
             selon le contenu de chaque pack.</p>`,
    },
    {
      title: 'Configuration initiale',
      body: `<ul>
               <li>Allez dans <strong>Paramètres</strong></li>
               <li>Définissez le dossier contenant vos packs graphiques</li>
               <li>Sélectionnez <code>FiveM.exe</code> — le launcher détecte <code>FiveM.app</code> (ou <code>FiveM Application Data</code>) automatiquement</li>
               <li>Sélectionnez le dossier racine de <strong>GTA V</strong></li>
             </ul>`,
    },
    {
      title: 'Installer un pack',
      body: `<p>Cliquez sur <strong>Installer</strong>. Le launcher analyse le contenu et copie :</p>
             <ul>
               <li><code>mods/</code> → <code>FiveM.app/mods/</code></li>
               <li><code>plugins/</code> → <code>FiveM.app/plugins/</code></li>
               <li><code>citizen/</code> → <code>FiveM.app/citizen/</code></li>
               <li><code>pack son/</code>, <code>audio/</code> → fichiers <code>.rpf</code> dans <code>GTA V/x64/audio/sfx/</code></li>
               <li><code>fivem/</code> → contenu entier dans <code>FiveM.app/</code></li>
               <li><code>gta5/</code>, <code>gta/</code> → contenu entier dans la racine GTA V</li>
             </ul>
             <p>Une sauvegarde automatique est créée dans <code>data/backups/</code> avant chaque installation.</p>`,
    },
    {
      title: 'Nettoyage FiveM',
      body: `<p>Supprime les dossiers <code>mods/</code>, <code>plugins/</code>, les fichiers ReShade et
             tous les fichiers trackés par le launcher. Le cache graphique est également vidé.</p>`,
    },
    {
      title: 'Nettoyage GTA V sécurisé',
      body: `<p>Avant de nettoyer GTA V, créez une <strong>baseline</strong> dans les Paramètres.
             Elle enregistre le hash SHA256 de chaque fichier officiel.</p>
             <p>Lors du nettoyage, seuls les fichiers <strong>absents de la baseline</strong> ou identifiés comme
             mods connus (<code>.asi</code>, <code>ScriptHookV.dll</code>, ReShade, ENB…) sont supprimés.</p>`,
    },
    {
      title: 'Erreurs fréquentes',
      body: `<p><strong>FiveM Application Data introuvable</strong> — Sélectionnez directement <code>FiveM.exe</code>.
             Le launcher cherche <code>FiveM.app</code> ou <code>FiveM Application Data</code> dans le même dossier.
             Assurez-vous que FiveM a déjà été lancé au moins une fois.</p>
             <p><strong>Dossier GTA V invalide</strong> — Le chemin doit contenir
             <code>GTA5.exe</code>, <code>GTAVLauncher.exe</code>, <code>x64b.rpf</code> et <code>x64v.rpf</code>.</p>
             <p><strong>Une opération est déjà en cours</strong> — Attendez la fin avant de relancer.</p>`,
    },
  ];

  const container = $('tutorial-accordions');
  if (!container) return;

  const chevron = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>`;

  container.innerHTML = ITEMS.map(item => `
    <div class="accordion">
      <div class="acc-header" onclick="toggleAcc(this)">
        <span class="acc-title">${esc(item.title)}</span>
        <span class="acc-chevron">${chevron}</span>
      </div>
      <div class="acc-body">${item.body}</div>
    </div>`).join('');
}

function toggleAcc(header) {
  const open = header.classList.contains('open');
  document.querySelectorAll('.acc-header.open').forEach(h => {
    h.classList.remove('open');
    h.nextElementSibling.classList.remove('open');
  });
  if (!open) {
    header.classList.add('open');
    header.nextElementSibling.classList.add('open');
  }
}

/* ══════════════════════════════════════════════════════════
   MODAL SYSTEM
══════════════════════════════════════════════════════════ */

function openProgressModal(title) {
  setText('prog-title', title);
  setText('prog-message', 'Initialisation…');
  $('prog-fill').style.width = '0%';
  setText('prog-pct', '0%');
  openModal('modal-progress');
}

function setProgress(pct, msg) {
  $('prog-fill').style.width = pct + '%';
  setText('prog-pct',     pct + '%');
  setText('prog-message', msg || '');
}

function confirm2(title, desc, color, cb) {
  setText('confirm-title', title);
  setText('confirm-desc',  desc);
  $('confirm-ico').className = 'modal-ico ' + color;
  $('confirm-ok').onclick = () => { closeModal(); cb(); };
  openModal('modal-confirm');
}

function openModal(id) {
  document.querySelectorAll('.modal').forEach(m => m.style.display = 'none');
  const m = $(id);
  if (m) m.style.display = 'block';
  $('modal-overlay').classList.add('open');
}

function closeModal() {
  $('modal-overlay').classList.remove('open');
  const iframe = $('video-iframe');
  if (iframe) iframe.src = '';
}

function onOverlayClick(e) {
  if (e.target === $('modal-overlay') && !S.busy) closeModal();
}

/* ══════════════════════════════════════════════════════════
   TOAST — pill from bottom-center
══════════════════════════════════════════════════════════ */

const TOAST_ICO = {
  success: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`,
  error:   `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`,
  warning: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
  info:    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
};

function toast(msg, type = 'info', dur = 3500) {
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `
    <div class="toast-ico">${TOAST_ICO[type] || TOAST_ICO.info}</div>
    <div class="toast-body">
      <span class="toast-msg">${esc(msg)}</span>
    </div>`;
  const wrap = $('toast-wrap');
  wrap.insertBefore(el, wrap.firstChild);
  setTimeout(() => {
    el.classList.add('out');
    setTimeout(() => el.remove(), 220);
  }, dur);
}

/* ══════════════════════════════════════════════════════════
   HELPERS
══════════════════════════════════════════════════════════ */

function $   (id)  { return document.getElementById(id); }
function esc (s)   { return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function jsStr(s)  { return "'" + String(s).replace(/\\/g,'\\\\').replace(/'/g,"\\'") + "'"; }
function setText(id, v) { const e = $(id); if (e) e.textContent = v; }
function setVal (id, v) { const e = $(id); if (e) e.value = v; }
function getVal (id)    { const e = $(id); return e ? e.value.trim() : ''; }

/* ══════════════════════════════════════════════════════════
   VIDEO PREVIEW
══════════════════════════════════════════════════════════ */

function getYouTubeId(url) {
  try {
    const u = new URL(url);
    if (u.hostname === 'youtu.be') return u.pathname.slice(1);
    return u.searchParams.get('v') || '';
  } catch { return ''; }
}

function showVideoPreview(youtubeUrl, title) {
  const id = getYouTubeId(youtubeUrl);
  if (!id) return;
  setText('video-title', title || '');
  $('video-iframe').src = `https://www.youtube-nocookie.com/embed/${id}?autoplay=1&rel=0`;
  openModal('modal-video');
}

/* ══════════════════════════════════════════════════════════
   WORKSHOP
══════════════════════════════════════════════════════════ */

async function refreshWorkshop() {
  const btn = document.querySelector('[onclick="refreshWorkshop()"]');
  btnLoad(btn, '');
  $('ws-grid').innerHTML = '';
  $('ws-empty').style.display = 'none';

  const r = await Api.getWorkshopPacks();
  btnReset(btn);

  if (!r?.success || !r.packs?.length) {
    $('ws-empty').style.display = 'flex';
    if (!r?.success) {
      setText('ws-empty-title', t('workshop_error') || 'Erreur');
      setText('ws-empty-desc', r?.error || t('toast_workshop_error'));
    }
    return;
  }

  S.workshopPacks = r.packs;
  const grid = $('ws-grid');
  r.packs.forEach(p => grid.appendChild(buildWsCard(p)));
}

function buildWsCard(pack) {
  const el = document.createElement('div');
  el.className = 'ws-card';

  const img = pack.preview_url
    ? `<img class="ws-card-img" src="${esc(pack.preview_url)}" alt="" onerror="this.parentNode.innerHTML=wsImgPh()">`
    : `<div class="ws-card-img-ph">${wsImgPh()}</div>`;

  const tags = (pack.tags || []).map(tg => {
    const cls = tg.replace(/\s+/g, '-');
    return `<span class="tag t-${cls}">${tg}</span>`;
  }).join('');

  el.innerHTML = `
    ${img}
    <div class="ws-card-body">
      <div class="ws-card-name">${esc(pack.name)}</div>
      <div class="ws-card-author">${esc(pack.author || '')}${pack.version ? ' · v' + esc(pack.version) : ''}</div>
      ${pack.description ? `<div class="ws-card-desc">${esc(pack.description)}</div>` : ''}
      <div class="tags-row">${tags}</div>
      <div class="ws-card-meta">
        ${pack.size_mb ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg><span>${pack.size_mb} Mo</span>` : ''}
        ${pack.downloads ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg><span>${pack.downloads.toLocaleString()}</span>` : ''}
      </div>
      <div class="ws-card-actions">
        ${pack.youtube_url ? `
        <button class="btn btn-ghost btn-sm" onclick="showVideoPreview(${jsStr(pack.youtube_url)},${jsStr(pack.name)})">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/></svg>
          <span data-i18n="btn_preview">${t('btn_preview')}</span>
        </button>` : ''}
        <button class="btn btn-primary btn-sm" onclick="doDownloadWsPack(${jsStr(pack.download_url)},${jsStr(pack.name)},this)">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          <span data-i18n="btn_download">${t('btn_download')}</span>
        </button>
      </div>
    </div>`;
  return el;
}

function wsImgPh() {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>`;
}

async function doDownloadWsPack(url, name, btn) {
  if (S.busy) { toast(t('toast_busy'), 'warning'); return; }
  const packs_dir = S.settings.packs_dir;
  if (!packs_dir) { toast(t('toast_no_packs_dir_ws'), 'error'); return; }

  confirm2(
    t('confirm_download_title'),
    t('confirm_download_desc', { name }),
    'blue',
    async () => {
      if (S.busy) return;
      S.busy = true;
      S.activeBtn = btn;
      btnLoad(btn, t('downloading'));
      await Api.downloadWorkshopPack(url, name);
    }
  );
}

/* ══════════════════════════════════════════════════════════
   AUTO-UPDATE
══════════════════════════════════════════════════════════ */

async function checkUpdate() {
  const r = await Api.checkForUpdate();
  if (r?.has_update && r.latest) {
    S.updateUrl = r.url;
    setText('update-msg', t('update_msg', { version: r.latest }));
    $('update-banner').style.display = 'flex';
  }
}

function openUpdateUrl() {
  if (S.updateUrl) Api.openFolder(S.updateUrl);
}

function dismissUpdateBanner() {
  $('update-banner').style.display = 'none';
}

/* ══════════════════════════════════════════════════════════
   LANGUAGE
══════════════════════════════════════════════════════════ */

function onLangChange(lang) {
  I18n.setLang(lang);
  S.settings.language = lang;
  Api.saveSettings({ ...S.settings, language: lang });
  toast(t('toast_lang_changed'), 'info');
}

/* ══════════════════════════════════════════════════════════
   INIT
══════════════════════════════════════════════════════════ */

async function initApp() {
  const s = await Api.getSettings();
  S.settings = s || {};

  // Init i18n — use saved language or auto-detect
  I18n.init(s?.language || null);

  // Sync language selector
  const langSel = $('lang-select');
  if (langSel) langSel.value = I18n.locale();

  initTutorial();

  if (!s || s.first_run) {
    navigate('settings');
    toast(t('toast_configure_first'), 'info', 6000);
  } else {
    navigate('packs');
  }

  // Check for updates in background (non-blocking)
  checkUpdate();

  const loader = $('app-loading');
  if (loader) {
    loader.classList.add('out');
    setTimeout(() => loader.remove(), 380);
  }
}

function onReady() { initApp(); }

if (window.pywebview) {
  onReady();
} else {
  window.addEventListener('pywebviewready', onReady);
}
