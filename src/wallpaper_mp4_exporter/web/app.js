const i18n = window.WallpaperMp4I18n;
const api = window.WallpaperMp4Api;
const { mediaUrl } = api;
const { localeStorageKey, normalizeLocale } = i18n;
let currentLocale = normalizeLocale(i18n.initialLocale);
let lastRenderedFiles = [];
let lastResult = null;
let lastDoctorState = 'checking';
let lastRenderedEntryCount = 0;

const form = document.getElementById('exportForm');
const sourceInput = document.getElementById('source');
const outputInput = document.getElementById('output');
const pickSourceFolder = document.getElementById('pickSourceFolder');
const pickSourceFile = document.getElementById('pickSourceFile');
const pickOutputFolder = document.getElementById('pickOutputFolder');
const scanButton = document.getElementById('scanButton');
const exportButton = document.getElementById('exportButton');
const doctorStatus = document.getElementById('doctorStatus');
const logOutput = document.getElementById('logOutput');
const jobState = document.getElementById('jobState');
const fileCount = document.getElementById('fileCount');
const fileTable = document.getElementById('fileTable');
const videoPreview = document.getElementById('videoPreview');
const exportedPicker = document.getElementById('exportedPicker');
const previewCount = document.getElementById('previewCount');
const previewPath = document.getElementById('previewPath');
const languagePicker = document.getElementById('languagePicker');
const tabButtons = Array.from(document.querySelectorAll('[data-tab-target]'));
const tabPanels = Array.from(document.querySelectorAll('.tab-panel'));


function t(key, values = {}) {
  return i18n.translate(currentLocale, key, values);
}

function setLocale(locale, options = {}) {
  currentLocale = normalizeLocale(locale);
  document.documentElement.lang = currentLocale;
  document.title = t('appTitle');
  languagePicker.value = currentLocale;
  document.querySelectorAll('[data-i18n]').forEach(element => {
    element.textContent = t(element.dataset.i18n);
  });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
    element.placeholder = t(element.dataset.i18nPlaceholder);
  });
  document.querySelectorAll('[data-tooltip-i18n]').forEach(element => {
    const text = t(element.dataset.tooltipI18n);
    element.title = text;
    element.setAttribute('aria-label', `${t('help')}: ${text}`);
  });
  languagePicker.setAttribute('aria-label', t('language'));
  previewCount.textContent = lastResult ? t('exportedCount', { count: exportedPicker.options.length }) : t('noExportedVideo');
  previewPath.textContent = lastResult && lastResult.preview_path ? previewPath.textContent : t('noPreviewHtml');
  jobState.textContent = jobState.dataset.state ? translateJobState(jobState.dataset.state) : t('idle');
  if (!logOutput.dataset.dirty) {
    logOutput.textContent = t('ready');
  }
  renderDoctorStatus();
  renderFiles(lastRenderedFiles);
  if (lastResult) {
    renderResult(lastResult);
  }
  if (options.persist) {
    localStorage.setItem(localeStorageKey, currentLocale);
    const nextPath = currentLocale === 'zh-CN' ? '/zh-CN' : '/en';
    if (location.pathname !== nextPath) {
      history.replaceState(null, '', nextPath);
    }
  }
}

function setActiveTab(panelId) {
  tabButtons.forEach(button => {
    const active = button.dataset.tabTarget === panelId;
    button.classList.toggle('active', active);
    button.setAttribute('aria-selected', active ? 'true' : 'false');
    button.tabIndex = active ? 0 : -1;
  });
  tabPanels.forEach(panel => {
    const active = panel.id === panelId;
    panel.hidden = !active;
    panel.classList.toggle('active', active);
  });
}

function initLocale() {
  const saved = localStorage.getItem(localeStorageKey);
  const pathLocale = location.pathname.toLowerCase().startsWith('/zh') ? 'zh-CN' : location.pathname.toLowerCase().startsWith('/en') ? 'en' : '';
  currentLocale = normalizeLocale(pathLocale || saved || i18n.initialLocale);
  languagePicker.addEventListener('change', () => setLocale(languagePicker.value, { persist: true }));
  setLocale(currentLocale);
}

function formPayload() {
  const data = new FormData(form);
  return {
    source: data.get('source'),
    output: data.get('output'),
    profile: data.get('profile'),
    layout: data.get('layout'),
    compatibility: data.get('compatibility'),
    key: data.get('key'),
    overwrite: Boolean(data.get('overwrite')),
    limit: Number(data.get('limit') || 0),
    locale: currentLocale
  };
}

function setLog(lines) {
  logOutput.dataset.dirty = 'true';
  logOutput.textContent = Array.isArray(lines) ? lines.join('\n') : String(lines || '');
  logOutput.scrollTop = logOutput.scrollHeight;
}

async function pickPath(kind, input) {
  setLog(t('pickingPath'));
  try {
    const result = await api.request('/api/pick-path', {
      method: 'POST',
      body: JSON.stringify({ kind, locale: currentLocale })
    });
    if (result.path) {
      input.value = result.path;
      setLog(result.path);
    } else {
      setLog(t('pathPickerCanceled'));
    }
  } catch (error) {
    setLog(t('pathPickerFailed', { message: error.message }));
  }
}

async function loadDefaults() {
  try {
    const defaults = await api.request('/api/defaults');
    if (!sourceInput.value && defaults.source) {
      sourceInput.value = defaults.source;
    }
    if (!outputInput.value && defaults.output) {
      outputInput.value = defaults.output;
    }
    if (!sourceInput.value && !defaults.source && !logOutput.dataset.dirty) {
      logOutput.textContent = t('noDefaultSource');
    }
  } catch (_error) {
    if (!outputInput.value) {
      outputInput.value = 'exports';
    }
  }
}

function renderFiles(items) {
  lastRenderedFiles = items || [];
  fileCount.textContent = t('found', { count: lastRenderedFiles.length });
  if (!lastRenderedFiles.length) {
    fileTable.innerHTML = `<div class="empty">${escapeHtml(lastResult ? t('noMatches') : t('emptyScan'))}</div>`;
    return;
  }
  fileTable.innerHTML = `
    <table>
      <thead>
        <tr><th>ID</th><th>${escapeHtml(t('name'))}</th><th>${escapeHtml(t('video'))}</th><th>${escapeHtml(t('cover'))}</th><th>${escapeHtml(t('current'))}</th></tr>
      </thead>
      <tbody>
        ${lastRenderedFiles.map(item => `
          <tr>
            <td>${escapeHtml(item.id)}</td>
            <td>${escapeHtml(item.title || '')}</td>
            <td class="path">${escapeHtml(item.video)}</td>
            <td class="path">${escapeHtml(item.cover || '')}</td>
            <td>${item.current ? escapeHtml(t('yes')) : ''}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

function renderResult(result, options = {}) {
  lastResult = result;
  const entries = (result && result.entries) || [];
  const playable = entries.filter(entry => entry.output_video);
  const previousValue = exportedPicker.value;
  let selectedValue = '';
  if (options.selectLatest && playable.length) {
    selectedValue = playable[playable.length - 1].output_video;
  } else if (playable.some(entry => entry.output_video === previousValue)) {
    selectedValue = previousValue;
  } else {
    const preferred = playable.find(entry => entry.current) || playable[0];
    selectedValue = preferred ? preferred.output_video : '';
  }

  exportedPicker.innerHTML = '';
  exportedPicker.disabled = playable.length === 0;
  previewCount.textContent = t('exportedCount', { count: playable.length });

  playable.forEach(entry => {
    const option = document.createElement('option');
    option.value = entry.output_video;
    option.dataset.cover = entry.cover || '';
    option.textContent = `${entry.title || entry.id} · ${entry.video_codec || t('fallbackVideo')}`;
    exportedPicker.appendChild(option);
  });
  exportedPicker.value = selectedValue;
  updatePreview();

  if (result && result.preview_path) {
    previewPath.innerHTML = `<a class="link-path" href="file://${escapeAttribute(result.preview_path)}" target="_blank" rel="noreferrer">${escapeHtml(result.preview_path)}</a>`;
  } else {
    previewPath.textContent = t('noPreviewHtml');
  }

  renderFiles(entries.map(entry => ({
    id: entry.id,
    title: entry.title,
    video: entry.output_video,
    cover: entry.cover,
    current: entry.current
  })));
}

function updatePreview() {
  const option = exportedPicker.options[exportedPicker.selectedIndex];
  if (!option) {
    videoPreview.removeAttribute('src');
    videoPreview.removeAttribute('poster');
    videoPreview.load();
    return;
  }
  const nextSrc = mediaUrl(option.value);
  if (option.dataset.cover) {
    videoPreview.poster = mediaUrl(option.dataset.cover);
  } else {
    videoPreview.removeAttribute('poster');
  }
  if (videoPreview.getAttribute('src') !== nextSrc) {
    videoPreview.src = nextSrc;
    videoPreview.load();
  }
}

async function checkDoctor() {
  try {
    const data = await api.request('/api/doctor');
    if (!data.ffmpeg || !data.ffprobe) {
      lastDoctorState = 'missing';
    } else if (!data.cryptography) {
      lastDoctorState = 'aes-missing';
    } else {
      lastDoctorState = 'ready';
    }
  } catch (error) {
    lastDoctorState = 'failed';
  }
  renderDoctorStatus();
}

function renderDoctorStatus() {
  const status = {
    checking: { className: '', label: t('checkingTools') },
    ready: { className: 'ok', label: t('ffmpegReady') },
    missing: { className: 'bad', label: t('ffmpegMissing') },
    'aes-missing': { className: 'bad', label: t('aesMissing') },
    failed: { className: 'bad', label: t('toolCheckFailed') }
  }[lastDoctorState];
  doctorStatus.innerHTML = `<span class="dot ${status.className}"></span><span>${escapeHtml(status.label)}</span>`;
}

async function scanSource() {
  scanButton.disabled = true;
  setActiveTab('logPanel');
  setLog(t('scanning'));
  try {
    const payload = formPayload();
    const data = await api.request('/api/scan', {
      method: 'POST',
      body: JSON.stringify({
        source: payload.source,
        layout: payload.layout,
        limit: payload.limit
      })
    });
    renderFiles(data.candidates || []);
    setLog(t('layoutFound', { layout: data.layout, count: (data.candidates || []).length }));
  } catch (error) {
    setLog(error.message);
  } finally {
    scanButton.disabled = false;
  }
}

async function startExport(event) {
  event.preventDefault();
  exportButton.disabled = true;
  scanButton.disabled = true;
  lastResult = null;
  lastRenderedEntryCount = 0;
  setActiveTab('logPanel');
  jobState.dataset.state = 'starting';
  jobState.textContent = t('starting');
  setLog(t('startingExport'));
  try {
    const data = await api.request('/api/export', {
      method: 'POST',
      body: JSON.stringify(formPayload())
    });
    await pollJob(data.job_id);
  } catch (error) {
    jobState.dataset.state = 'failed';
    jobState.textContent = t('failed');
    setLog(error.message);
  } finally {
    exportButton.disabled = false;
    scanButton.disabled = false;
  }
}

async function pollJob(jobId) {
  while (true) {
    const job = await api.request(`/api/jobs/${jobId}`);
    jobState.dataset.state = job.status;
    jobState.textContent = translateJobState(job.status);
    setLog(job.logs || []);
    const entryCount = resultEntryCount(job.result);
    if (entryCount > 0) {
      renderResult(job.result, { selectLatest: entryCount !== lastRenderedEntryCount });
      lastRenderedEntryCount = entryCount;
    }
    if (job.status === 'done' || job.status === 'done-with-failures') {
      renderResult(job.result);
      lastRenderedEntryCount = resultEntryCount(job.result);
      setActiveTab('previewPanel');
      return;
    }
    if (job.status === 'failed') {
      throw new Error(job.error || t('exportFailed'));
    }
    await new Promise(resolve => setTimeout(resolve, 850));
  }
}

function resultEntryCount(result) {
  return ((result && result.entries) || []).filter(entry => entry.output_video).length;
}

function translateJobState(status) {
  return {
    running: t('running'),
    starting: t('starting'),
    done: t('done'),
    'done-with-failures': t('doneWithFailures'),
    failed: t('failed')
  }[status] || status;
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function escapeAttribute(value) {
  return encodeURI(String(value ?? '')).replaceAll('"', '%22');
}

scanButton.addEventListener('click', scanSource);
form.addEventListener('submit', startExport);
exportedPicker.addEventListener('change', updatePreview);
tabButtons.forEach(button => button.addEventListener('click', () => setActiveTab(button.dataset.tabTarget)));
pickSourceFolder.addEventListener('click', () => pickPath('directory', sourceInput));
pickSourceFile.addEventListener('click', () => pickPath('file', sourceInput));
pickOutputFolder.addEventListener('click', () => pickPath('output', outputInput));
initLocale();
loadDefaults();
checkDoctor();
