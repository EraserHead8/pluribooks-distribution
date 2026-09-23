const APP_ID = 'app.polka';
const FEEDS = 'https://raw.githubusercontent.com/EraserHead8/pluribooks-distribution/main/releases';
const SHA256 = /^(?!0{64}$)[0-9a-f]{64}$/;

function formatSize(bytes) {
  return `${(bytes / 1024 / 1024).toFixed(1)} МиБ`;
}

function formatDate(iso) {
  const parsed = new Date(iso);
  return Number.isNaN(parsed.valueOf())
    ? 'Дата не указана'
    : new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' }).format(parsed);
}

function isRelease(release) {
  if (!release || !Number.isSafeInteger(release.versionCode) || release.versionCode < 1 ||
      typeof release.versionName !== 'string' || !SHA256.test(release.apk?.sha256 || '') ||
      !Number.isSafeInteger(release.apk?.sizeBytes) || release.apk.sizeBytes < 1 ||
      !Number.isSafeInteger(release.minSdk) || !Array.isArray(release.notes)) return false;
  try {
    const url = new URL(release.apk.url);
    return url.protocol === 'https:' && url.hostname === 'github.com' &&
      /^\/EraserHead8\/pluribooks-distribution\/releases\/download\/[^/]+\/[^/]+\.apk$/.test(url.pathname);
  } catch { return false; }
}

async function getJson(path) {
  const response = await fetch(path, { cache: 'no-store' });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

function renderNotes(selector, notes) {
  const list = document.querySelector(selector);
  list.replaceChildren(...notes.slice(0, 6).map(note => {
    const item = document.createElement('li');
    item.textContent = note;
    return item;
  }));
  list.hidden = notes.length === 0;
}

async function loadChannel(channel) {
  try {
    const feed = await getJson(`${FEEDS}/${channel}.json`);
    if (feed.schemaVersion !== 1 || feed.channel !== channel || feed.applicationId !== APP_ID ||
        (feed.release !== null && !isRelease(feed.release))) throw new Error('Invalid release feed');
    if (feed.release === null) return;
    const release = feed.release;
    const download = document.querySelector(`#${channel}-download`);
    download.href = release.apk.url;
    download.hidden = false;
    document.querySelector(`#${channel}-heading`).textContent =
      `${channel === 'stable' ? 'Стабильная' : 'Тестовая'} версия ${release.versionName}`;
    document.querySelector(`#${channel}-status`).textContent = `Опубликована ${formatDate(release.publishedAt)}`;
    if (channel === 'preview') {
      renderNotes('#preview-notes', release.notes);
      document.querySelector('#preview-size').textContent = formatSize(release.apk.sizeBytes);
      document.querySelector('#preview-sha').textContent = release.apk.sha256;
    }
  } catch {
    document.querySelector(`#${channel}-status`).textContent =
      'Сведения о выпуске временно недоступны. Не скачивайте APK по непроверенным ссылкам.';
  }
}

async function loadHistory(channel, selector) {
  const root = document.querySelector(selector);
  try {
    const history = await getJson(`${FEEDS}/${channel === 'stable' ? 'versions' : 'preview-versions'}.json`);
    if (history.schemaVersion !== 1 || history.channel !== channel || !Array.isArray(history.versions))
      throw new Error('Invalid history');
    if (history.versions.length === 0) return;
    root.replaceChildren(...history.versions.slice(0, 10).map(version => {
      const article = document.createElement('article');
      article.className = 'version-item';
      const left = document.createElement('div');
      const name = document.createElement('div');
      name.className = 'version-name';
      name.textContent = `v${version.versionName}`;
      const date = document.createElement('div');
      date.className = 'version-date';
      date.textContent = formatDate(version.publishedAt);
      left.append(name, date);
      const notes = document.createElement('ul');
      (Array.isArray(version.notes) ? version.notes : []).slice(0, 4).forEach(note => {
        const item = document.createElement('li');
        item.textContent = note;
        notes.append(item);
      });
      article.append(left, notes);
      try {
        const url = new URL(version.releaseUrl);
        if (url.protocol === 'https:' && url.hostname === 'github.com') {
          const link = document.createElement('a');
          link.href = url.href;
          link.textContent = 'Выпуск ↗';
          article.append(link);
        }
      } catch { /* An invalid link is not rendered. */ }
      return article;
    }));
  } catch {
    root.textContent = 'История версий временно недоступна.';
  }
}

loadChannel('preview');
loadChannel('stable');
loadHistory('preview', '#preview-version-list');
loadHistory('stable', '#stable-version-list');
