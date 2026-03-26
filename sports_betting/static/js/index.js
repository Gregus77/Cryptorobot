/* BetScore — Index page */

let currentSport = 'football';
let currentDay = 0;
let liveInterval = null;

// ── Init ──────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  setupSportButtons();
  setupDayButtons();
  loadLive();
  loadScheduled();

  document.getElementById('refresh-live').addEventListener('click', loadLive);

  // Auto-refresh live every 30s
  liveInterval = setInterval(loadLive, 30000);
});

// ── Sport Buttons ─────────────────────────────
function setupSportButtons() {
  document.querySelectorAll('.sport-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.sport-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentSport = btn.dataset.sport;
      loadLive();
      loadScheduled();
    });
  });
}

// ── Day Buttons ───────────────────────────────
function setupDayButtons() {
  document.querySelectorAll('.day-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.day-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentDay = parseInt(btn.dataset.day);
      loadScheduled();
    });
  });
}

// ── Load Live ─────────────────────────────────
async function loadLive() {
  const container = document.getElementById('live-matches');
  container.innerHTML = '<div class="loading-card"><i class="fa-solid fa-spinner fa-spin"></i> Chargement...</div>';
  try {
    const res = await fetch(`/api/live?sport=${currentSport}`);
    const events = await res.json();
    document.getElementById('live-count').textContent = events.length;
    renderMatches(container, events, true);
  } catch {
    container.innerHTML = '<div class="empty-state"><i class="fa-solid fa-wifi"></i>Erreur de connexion</div>';
  }
}

// ── Load Scheduled ────────────────────────────
async function loadScheduled() {
  const container = document.getElementById('scheduled-matches');
  container.innerHTML = '<div class="loading-card"><i class="fa-solid fa-spinner fa-spin"></i> Chargement...</div>';
  try {
    const res = await fetch(`/api/scheduled?sport=${currentSport}&day=${currentDay}`);
    const events = await res.json();
    document.getElementById('scheduled-count').textContent = events.length;
    buildTournamentFilter(events);
    renderMatches(container, events, false);
  } catch {
    container.innerHTML = '<div class="empty-state"><i class="fa-solid fa-wifi"></i>Erreur de connexion</div>';
  }
}

// ── Tournament Filter ─────────────────────────
let activeTournament = 'all';

function buildTournamentFilter(events) {
  const wrap = document.getElementById('tournament-filter');
  const tournaments = [...new Set(events.map(e => e.tournament).filter(Boolean))].slice(0, 12);

  wrap.innerHTML = '';
  const allBtn = document.createElement('button');
  allBtn.className = 'filter-chip' + (activeTournament === 'all' ? ' active' : '');
  allBtn.textContent = 'Tous';
  allBtn.addEventListener('click', () => setTournamentFilter('all', events));
  wrap.appendChild(allBtn);

  tournaments.forEach(t => {
    const btn = document.createElement('button');
    btn.className = 'filter-chip' + (activeTournament === t ? ' active' : '');
    btn.textContent = t;
    btn.addEventListener('click', () => setTournamentFilter(t, events));
    wrap.appendChild(btn);
  });
}

function setTournamentFilter(name, events) {
  activeTournament = name;
  document.querySelectorAll('.filter-chip').forEach(b => {
    b.classList.toggle('active', b.textContent === (name === 'all' ? 'Tous' : name));
  });
  const filtered = name === 'all' ? events : events.filter(e => e.tournament === name);
  renderMatches(document.getElementById('scheduled-matches'), filtered, false);
}

// ── Render Matches ────────────────────────────
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

    const statusType = e.status_type || 'notstarted';
    const isLiveMatch = statusType === 'inprogress';
    const isFinished = statusType === 'finished';

    let statusHtml = '';
    if (isLiveMatch) {
      statusHtml = `<span class="status-live">${e.status_desc || 'En direct'}</span>`;
    } else if (isFinished) {
      statusHtml = `<span style="color:var(--text2);font-size:0.8rem">Terminé</span>`;
    } else {
      statusHtml = `<span style="color:var(--text2);font-size:0.8rem">${formatTime(e.start_timestamp)}</span>`;
    }

    const homeScore = e.home_score !== undefined && e.home_score !== null ? e.home_score : '-';
    const awayScore = e.away_score !== undefined && e.away_score !== null ? e.away_score : '-';

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
          <span class="score-box">${homeScore} - ${awayScore}</span>
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
  const d = new Date(ts * 1000);
  return d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
}
