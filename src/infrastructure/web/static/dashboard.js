document.addEventListener('DOMContentLoaded', () => {
  // Resolution table: show more
  const showMore = document.getElementById('resolution-show-more');
  if (showMore) {
    showMore.addEventListener('click', () => {
      document.querySelectorAll('.resolution-extra').forEach(r => r.classList.remove('resolution-extra'));
      showMore.style.display = 'none';
    });
  }

  // Transcodings pagination
  const pagination = document.querySelector('.pagination');
  if (pagination) {
    pagination.addEventListener('click', async (e) => {
      const btn = e.target.closest('[data-page]');
      if (!btn || btn.disabled) return;

      const page = parseInt(btn.dataset.page, 10);
      const res = await fetch(`/api/transcodings?page=${page}`);
      if (!res.ok) return;
      const data = await res.json();

      renderTranscodingsTable(data.transcodings);
      renderPagination(data.page, data.total_pages);
    });
  }

  // Search toggle
  const searchToggle = document.getElementById('transcodings-search-toggle');
  const searchBar = document.getElementById('transcodings-search-bar');
  const searchInput = document.getElementById('transcodings-search-input');

  if (searchToggle && searchBar && searchInput) {
    searchToggle.addEventListener('click', () => {
      const isOpen = !searchBar.hidden;
      if (isOpen) {
        searchBar.hidden = true;
        searchToggle.classList.remove('search-toggle--active');
        searchInput.value = '';
        _restoreNormalView();
      } else {
        searchBar.hidden = false;
        searchToggle.classList.add('search-toggle--active');
        searchInput.focus();
      }
    });

    let _searchTimer;
    searchInput.addEventListener('input', () => {
      clearTimeout(_searchTimer);
      const val = searchInput.value.trim();
      if (val.length < 3) {
        _restoreNormalView();
        return;
      }
      _searchTimer = setTimeout(async () => {
        const res = await fetch(`/api/transcodings/search?path=${encodeURIComponent(val)}`);
        if (!res.ok) return;
        const data = await res.json();
        _renderSearchIntoTable(data.results);
      }, 300);
    });
  }

  // Unified click delegation on transcodings table
  const transcodingsTbody = document.getElementById('transcodings-tbody');
  if (transcodingsTbody) {
    transcodingsTbody.addEventListener('click', (e) => {
      const btn = e.target.closest('.btn-retranscode');
      if (btn) {
        handleRetranscode(btn.dataset.path, btn);
        return;
      }
      const row = e.target.closest('tr[data-path]');
      if (row) _openDetail(row);
    });
  }

  // Detail dialog close
  const detailClose = document.getElementById('detail-close-btn');
  if (detailClose) {
    detailClose.addEventListener('click', () => {
      document.getElementById('transcoding-detail-dialog').close();
    });
  }
  const detailDialog = document.getElementById('transcoding-detail-dialog');
  if (detailDialog) {
    detailDialog.addEventListener('click', (e) => {
      if (e.target === detailDialog) detailDialog.close();
    });
  }
});

function esc(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

const STATUS_ICON = {
  completed:   { icon: 'i-check-circle', cls: 'status-icon--completed' },
  failed:      { icon: 'i-x-circle',     cls: 'status-icon--failed' },
  in_progress: { icon: 'i-zap',          cls: 'status-icon--in-progress' },
  pending:     { icon: 'i-clock',        cls: 'status-icon--pending' },
};

function statusIcon(status) {
  const s = STATUS_ICON[status] || { icon: 'i-minus-circle', cls: 'status-icon--muted' };
  return `<svg class="icon icon-sm ${s.cls}"><use href="/static/icons.svg#${s.icon}"/></svg>`;
}

const RETRANSCODE_ELIGIBLE = new Set(['completed', 'failed']);

function _labels() {
  const el = document.getElementById('js-labels');
  return el ? el.dataset : {};
}

function retranscodeBtn(path) {
  const labels = _labels();
  return `<button class="btn-retranscode" data-path="${esc(path)}" title="${esc(labels.forceButton || '')}">
    <svg class="icon icon-sm"><use href="/static/icons.svg#i-rotate-ccw"/></svg>
  </button>`;
}

function renderTranscodingsTable(transcodings) {
  const tbody = document.getElementById('transcodings-tbody');
  if (!tbody) return;
  if (transcodings.length === 0) {
    const msg = tbody.dataset.emptyMessage || 'No transcodings yet';
    tbody.innerHTML = `<tr class="table-empty"><td colspan="5">${msg}</td></tr>`;
    return;
  }
  tbody.innerHTML = transcodings.map(t => `
    <tr class="row-clickable" data-path="${esc(t.original_video_path)}" data-status="${esc(t.status)}" data-codec="${esc(t.transcoded_video_codec || '')}" data-resolution="${esc(t.transcoded_video_resolution || '')}">
      <td class="cell-status">${statusIcon(t.status)}</td>
      <td class="cell-path" title="${esc(t.original_video_path)}">${esc(_basename(t.original_video_path))}</td>
      <td class="col-codec">${esc(t.transcoded_video_codec || '—')}</td>
      <td>${esc(t.transcoded_video_resolution || '—')}</td>
      <td class="cell-action">${RETRANSCODE_ELIGIBLE.has(t.status) ? retranscodeBtn(t.original_video_path) : ''}</td>
    </tr>
  `).join('');
}

function _renderSearchIntoTable(results) {
  const tbody = document.getElementById('transcodings-tbody');
  if (!tbody) return;
  const pagination = document.querySelector('.pagination');
  if (pagination) pagination.hidden = true;
  if (results.length === 0) {
    const msg = tbody.dataset.emptyMessage || 'No transcodings yet';
    tbody.innerHTML = `<tr class="table-empty"><td colspan="5">${msg}</td></tr>`;
    return;
  }
  tbody.innerHTML = results.map(t => `
    <tr class="row-clickable" data-path="${esc(t.original_video_path)}" data-status="${esc(t.status)}" data-codec="${esc(t.transcoded_video_codec || '')}" data-resolution="${esc(t.transcoded_video_resolution || '')}">
      <td class="cell-status">${statusIcon(t.status)}</td>
      <td class="cell-path" title="${esc(t.original_video_path)}">${esc(_basename(t.original_video_path))}</td>
      <td class="col-codec">${esc(t.transcoded_video_codec || '—')}</td>
      <td>${esc(t.transcoded_video_resolution || '—')}</td>
      <td class="cell-action">${RETRANSCODE_ELIGIBLE.has(t.status) ? retranscodeBtn(t.original_video_path) : ''}</td>
    </tr>
  `).join('');
}

async function _restoreNormalView() {
  const res = await fetch('/api/transcodings?page=1');
  if (!res.ok) return;
  const data = await res.json();
  renderTranscodingsTable(data.transcodings);
  renderPagination(data.page, data.total_pages);
  const pagination = document.querySelector('.pagination');
  if (pagination) pagination.hidden = data.total_pages <= 1;
}

function renderPagination(page, totalPages) {
  const info = document.querySelector('.page-info');
  if (info) info.textContent = `${page} / ${totalPages}`;

  const [prevBtn, nextBtn] = document.querySelectorAll('button[data-page]');
  if (prevBtn) {
    prevBtn.dataset.page = page - 1;
    prevBtn.disabled = page <= 1;
  }
  if (nextBtn) {
    nextBtn.dataset.page = page + 1;
    nextBtn.disabled = page >= totalPages;
  }
}

async function handleRetranscode(path, buttonEl) {
  const labels = _labels();
  buttonEl.disabled = true;
  buttonEl.classList.add('btn-retranscode--loading');

  let res;
  try {
    res = await fetch('/api/transcodings/retranscode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ original_video_path: path }),
    });
  } catch (_) {
    buttonEl.disabled = false;
    buttonEl.classList.remove('btn-retranscode--loading');
    _flashError(buttonEl, labels.error);
    return;
  }

  buttonEl.classList.remove('btn-retranscode--loading');

  if (res.ok) {
    // Update the matching table row (works from both inline button and detail dialog)
    const escapedPath = path.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
    const tableRow = document.querySelector(`#transcodings-tbody tr[data-path="${escapedPath}"]`);
    if (tableRow) {
      tableRow.querySelector('.cell-status').innerHTML = statusIcon('pending');
      tableRow.dataset.status = 'pending';
      const tableBtn = tableRow.querySelector('.cell-action .btn-retranscode');
      if (tableBtn) tableBtn.remove();
    }
    buttonEl.remove();
    const dialog = document.getElementById('transcoding-detail-dialog');
    if (dialog && dialog.open) dialog.close();
    refreshBreakdown();
  } else {
    buttonEl.disabled = false;
    const msg = res.status === 409 ? labels.notEligible : labels.error;
    _flashError(buttonEl, msg);
  }
}

async function refreshBreakdown() {
  const res = await fetch('/api/stats');
  if (!res.ok) return;
  const stats = await res.json();
  const sc = stats.status_counts;

  _setKpi('kpi-completed', sc.completed, []);
  _setKpi('kpi-failed',    sc.failed,    sc.failed    > 0 ? ['c-danger']  : []);
  _setKpi('kpi-pending',   sc.pending,   sc.pending   > 0 ? ['c-warning'] : []);
  _setKpi('kpi-in-progress', sc.in_progress, sc.in_progress > 0 ? ['c-info'] : []);

  const rate = stats.success_rate;
  const rateCls = rate >= 90 ? 'c-success' : rate < 70 ? 'c-danger' : 'c-warning';
  _setKpi('kpi-success-rate', rate.toFixed(1) + '%', [rateCls]);
}

function _setKpi(id, value, colorClasses) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = value;
  ['c-success', 'c-danger', 'c-warning', 'c-info'].forEach(c => el.classList.remove(c));
  colorClasses.forEach(c => el.classList.add(c));
}

function _flashError(buttonEl, message) {
  buttonEl.classList.add('btn-retranscode--error');
  if (message) buttonEl.title = message;
  setTimeout(() => buttonEl.classList.remove('btn-retranscode--error'), 2500);
}

function _basename(path) {
  return path.split('/').filter(Boolean).pop() || path;
}

function _openDetail(tr) {
  const path = tr.dataset.path;
  const status = tr.dataset.status;
  const codec = tr.dataset.codec;
  const resolution = tr.dataset.resolution;
  const labels = _labels();

  document.getElementById('detail-status-icon').innerHTML = statusIcon(status);
  document.getElementById('detail-filename').textContent = _basename(path);
  document.getElementById('detail-path').textContent = path;
  document.getElementById('detail-codec').textContent = codec || '—';
  document.getElementById('detail-resolution').textContent = resolution || '—';

  const footer = document.getElementById('detail-dialog-footer');
  if (RETRANSCODE_ELIGIBLE.has(status)) {
    footer.innerHTML = `<button class="btn-retranscode btn-retranscode--labeled" data-path="${esc(path)}">
      <svg class="icon icon-sm"><use href="/static/icons.svg#i-rotate-ccw"/></svg>
      ${esc(labels.forceButton || '')}
    </button>`;
    footer.querySelector('.btn-retranscode').addEventListener('click', (e) => {
      handleRetranscode(path, e.currentTarget);
    });
  } else {
    footer.innerHTML = '';
  }

  document.getElementById('transcoding-detail-dialog').showModal();
}
