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

function renderTranscodingsTable(transcodings) {
  const tbody = document.getElementById('transcodings-tbody');
  if (!tbody) return;
  if (transcodings.length === 0) {
    tbody.innerHTML = '<tr class="table-empty"><td colspan="4">No transcodings yet</td></tr>';
    return;
  }
  tbody.innerHTML = transcodings.map(t => `
    <tr>
      <td class="cell-status">${statusIcon(t.status)}</td>
      <td class="cell-path" title="${esc(t.original_video_path)}">${esc(t.original_video_path)}</td>
      <td>${esc(t.transcoded_video_codec || '—')}</td>
      <td>${esc(t.transcoded_video_resolution || '—')}</td>
    </tr>
  `).join('');
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
