/* BetScore — Index page JS */

let currentSport = 'football';
let currentDay   = 0;

document.addEventListener('DOMContentLoaded', () => {
  setupSportButtons();
  setupDayButtons();
  loadAll();

  document.getElementById('refresh-picks').addEventListener('click', loadPicks);
  document.getElementById('refresh-live').addEventListener('click', loadLive);
});

function loadAll() {
  loadPicks();
  loadLive();
  loadScheduled();
}

// ── Sports ───────────────────────────────────
function setupSportButtons() {
  document.querySelectorAll('.sport-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.sport-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentSport = btn.dataset.sport;
      loadAll();
    });
  });
}

// ── Day ──────────────────────────────────────
function setupDayButtons() {
  document.querySelectorAll('.day-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.day-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentDay = parseInt(btn.dataset.day);
      loadAll();
    });
  });
}

// ═══════════════════════════════════════════════════
// PICKS
// ═══════════════════════════════════════════════════
async function loadPicks() {
  const container = document.getElementById('picks-container');
  container.innerHTML = `<div class="picks-loading">
    <i class="fa-solid fa-spinner fa-spin"></i>
    <span>Analyse statistique en cours…</span>
  </div>`;

  try {
    const res  = await fetch(`/api/picks?sport=${currentSport}&day=${currentDay}`);
    const data = await res.json();
    renderPicks(data);
  } catch {
    container.innerHTML = `<div class="empty-state">
      <i class="fa-solid fa-wifi"></i>
      <p>Erreur de connexion à l'API</p>
    </div>`;
  }
}

function confClass(c) {
  if (c >= 75) return 'high';
  if (c >= 65) return 'medium';
  return 'low';
}

function renderPicks(data) {
  const container = document.getElementById('picks-container');
  const picks      = data.picks || [];
  const analyzed   = data.total_matches_analyzed || 0;

  document.getElementById('picks-count').textContent = picks.length;

  if (picks.length === 0) {
    container.innerHTML = `<div class="empty-state">
      <i class="fa-solid fa-magnifying-glass"></i>
      <p>Aucun pari avec une confiance suffisante aujourd'hui (${analyzed} matchs analysés)</p>
    </div>`;
    return;
  }

  const grid = document.createElement('div');
  grid.className = 'picks-grid';

  picks.forEach((pick, idx) => {
    const cc    = confClass(pick.confidence);
    const card  = document.createElement('div');
    card.className = 'pick-card';
    card.dataset.conf = cc;
    card.addEventListener('click', () => window.location.href = `/match/${pick.match_id}`);

    const hf = pick.home_form || {};
    const af = pick.away_form || {};
    const startTime = pick.start_ts ? formatTime(pick.start_ts) : '—';

    const expGoalsHtml = pick.exp_goals
      ? `<span class="exp-goals-chip"><i class="fa-solid fa-bolt"></i> ${pick.exp_goals} buts attendus</span>`
      : '';

    // Rank badge
    const rankColors = ['#f1c40f','#bdc3c7','#cd7f32'];
    const rankBadge = idx < 3
      ? `<span style="position:absolute;top:8px;left:8px;font-size:.8rem;font-weight:800;color:${rankColors[idx]};">#${idx+1}</span>`
      : '';

    card.innerHTML = `
      ${rankBadge}
      <span class="pick-ribbon ribbon-${cc}">${pick.confidence}%</span>

      <div class="pick-header">
        <span class="pick-market-icon">${pick.icon || '⚽'}</span>
        <div>
          <div class="pick-market-name">${pick.market}</div>
          <div class="pick-tournament">
            <i class="fa-solid fa-trophy" style="font-size:.65rem"></i>
            ${pick.tournament} · ${startTime}
          </div>
        </div>
      </div>

      <div class="pick-match">
        <div class="pick-team-logos">
          <img src="${pick.home_logo}" alt="${pick.home_team}"
               onerror="this.src='/static/img/team-default.svg'" />
          <span class="pick-vs">VS</span>
          <img src="${pick.away_logo}" alt="${pick.away_team}"
               onerror="this.src='/static/img/team-default.svg'" />
        </div>
        <div class="pick-match-name">${pick.home_team} — ${pick.away_team}</div>
      </div>

      <div class="pick-confidence">
        <div class="conf-header">
          <span class="conf-label">Confiance algorithmique</span>
          <span class="conf-value ${cc}">${pick.confidence}%</span>
        </div>
        <div class="conf-bar-track">
          <div class="conf-bar-fill fill-${cc}" style="width:${pick.confidence}%"></div>
        </div>
      </div>

      <div class="pick-stats">
        ${hf.avg_scored !== undefined ? `
          <div class="mini-stat">
            <span class="ms-label">${pick.home_team.split(' ').pop()} buts/m</span>
            <span class="ms-value">${hf.avg_scored}</span>
          </div>` : ''}
        ${af.avg_scored !== undefined ? `
          <div class="mini-stat">
            <span class="ms-label">${pick.away_team.split(' ').pop()} buts/m</span>
            <span class="ms-value">${af.avg_scored}</span>
          </div>` : ''}
        ${hf.over25_rate_pct !== undefined ? `
          <div class="mini-stat">
            <span class="ms-label">Over 2.5 (dom.)</span>
            <span class="ms-value">${hf.over25_rate_pct}%</span>
          </div>` : ''}
        ${expGoalsHtml}
      </div>
    `;

    grid.appendChild(card);
  });

  container.innerHTML = `
    <p style="color:var(--text2);font-size:.83rem;margin-bottom:1rem;">
      <i class="fa-solid fa-circle-info"></i>
      ${analyzed} matchs analysés · ${picks.length} opportunités sélectionnées
    </p>
  `;
  container.appendChild(grid);
}

// ═══════════════════════════════════════════════════
// LIVE
// ═══════════════════════════════════════════════════
async function loadLive() {
  const container = document.getElementById('live-matches');
  container.innerHTML = '<div class="loading-card"><i class="fa-solid fa-spinner fa-spin"></i></div>';
  try {
    const res    = await fetch(`/api/live?sport=${currentSport}`);
    const events = await res.json();
    document.getElementById('live-count').textContent = events.length;
    renderMatches(container, events, true);
  } catch {
    container.innerHTML = '<div class="empty-state"><i class="fa-solid fa-wifi"></i><p>Erreur</p></div>';
  }
}

// ═══════════════════════════════════════════════════
// SCHEDULED
// ═══════════════════════════════════════════════════
let _allScheduled = [];
let _activeTournament = 'all';

async function loadScheduled() {
  const container = document.getElementById('scheduled-matches');
  container.innerHTML = '<div class="loading-card"><i class="fa-solid fa-spinner fa-spin"></i></div>';
  try {
    const res    = await fetch(`/api/scheduled?sport=${currentSport}&day=${currentDay}`);
    _allScheduled = await res.json();
    document.getElementById('scheduled-count').textContent = _allScheduled.length;
    buildFilter(_allScheduled);
    renderMatches(container, _allScheduled, false);
  } catch {
    container.innerHTML = '<div class="empty-state"><i class="fa-solid fa-wifi"></i><p>Erreur</p></div>';
  }
}

function buildFilter(events) {
  const wrap = document.getElementById('tournament-filter');
  const tours = [...new Set(events.map(e => e.tournament).filter(Boolean))].slice(0, 12);
  wrap.innerHTML = '';

  [['Tous', 'all'], ...tours.map(t => [t, t])].forEach(([label, val]) => {
    const btn = document.createElement('button');
    btn.className = 'filter-chip' + (_activeTournament === val ? ' active' : '');
    btn.textContent = label;
    btn.addEventListener('click', () => {
      _activeTournament = val;
      document.querySelectorAll('.filter-chip').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const filtered = val === 'all' ? _allScheduled : _allScheduled.filter(e => e.tournament === val);
      renderMatches(document.getElementById('scheduled-matches'), filtered, false);
    });
    wrap.appendChild(btn);
  });
}

// ═══════════════════════════════════════════════════
// Render match cards
// ═══════════════════════════════════════════════════
function renderMatches(container, events, isLive) {
  if (!events || events.length === 0) {
    container.innerHTML = `<div class="empty-state">
      <i class="fa-solid fa-calendar-xmark"></i>
      <p>Aucun match ${isLive ? 'en direct' : 'programmé'}</p>
    </div>`;
    return;
  }
  container.innerHTML = '';
  events.forEach(e => {
    const card = document.createElement('div');
    card.className = 'match-card' + (isLive ? ' live' : '');
    card.addEventListener('click', () => window.location.href = `/match/${e.id}`);

    const statusType    = e.status_type || 'notstarted';
    const isLiveNow     = statusType === 'inprogress';
    const isFinished    = statusType === 'finished';

    let statusHtml = '';
    if (isLiveNow)   statusHtml = `<span class="status-live">${e.status_desc || 'En direct'}</span>`;
    else if (isFinished) statusHtml = `<span style="color:var(--text2);font-size:.8rem">Terminé</span>`;
    else             statusHtml = `<span style="color:var(--text2);font-size:.8rem">${formatTime(e.start_timestamp)}</span>`;

    const hs = e.home_score !== null && e.home_score !== undefined ? e.home_score : '-';
    const as = e.away_score !== null && e.away_score !== undefined ? e.away_score : '-';

    card.innerHTML = `
      <div class="card-meta">
        <span class="tournament">${e.tournament || ''}</span>
        ${statusHtml}
      </div>
      <div class="match-teams">
        <div class="team">
          <img src="${e.home_logo}" alt="${e.home_team}" onerror="this.src='/static/img/team-default.svg'" />
          <span class="team-name">${e.home_team}</span>
        </div>
        <div class="match-score">
          <span class="score-box">${hs} – ${as}</span>
          <span class="score-time">${e.round ? 'J' + e.round : ''}</span>
        </div>
        <div class="team">
          <img src="${e.away_logo}" alt="${e.away_team}" onerror="this.src='/static/img/team-default.svg'" />
          <span class="team-name">${e.away_team}</span>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

// ── Utils ─────────────────────────────────────
function formatTime(ts) {
  if (!ts) return '';
  return new Date(ts * 1000).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
}
