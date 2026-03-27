/* BetScore — Index page (real GitHub data source) */

let currentDate   = null;   // ISO string of selected date
let _allScheduled = [];
let _activeTournament = 'all';

document.addEventListener('DOMContentLoaded', async () => {
  await initDatePicker();
  loadPicks();
  loadScheduled();

  document.getElementById('refresh-picks').addEventListener('click', () => {
    loadPicks();
    loadScheduled();
  });
});

// ═══════════════════════════════════════════════════
// DATE PICKER — fetches real upcoming dates
// ═══════════════════════════════════════════════════
async function initDatePicker() {
  try {
    const res   = await fetch('/api/upcoming');
    const dates = await res.json();

    const today = new Date().toISOString().slice(0,10);
    currentDate = dates[0] || today;   // default: nearest match day

    renderDateSlots(dates, today);
  } catch {
    currentDate = new Date().toISOString().slice(0,10);
    renderDateSlots([currentDate], currentDate);
  }
}

function renderDateSlots(dates, today) {
  const slots = document.getElementById('date-slots');
  slots.innerHTML = '';

  const allDates = [...new Set([today, ...dates])].sort();

  allDates.forEach(d => {
    const btn = document.createElement('button');
    btn.className = 'date-slot' + (d === currentDate ? ' active' : '');
    if (d === today) btn.classList.add('today');
    const dt = new Date(d + 'T12:00:00Z');
    btn.innerHTML = `<span class="ds-day">${dt.toLocaleDateString('fr-FR',{weekday:'short'})}</span>
                     <span class="ds-num">${dt.toLocaleDateString('fr-FR',{day:'2-digit',month:'2-digit'})}</span>`;
    if (!dates.includes(d) && d !== today) btn.classList.add('no-match');
    btn.addEventListener('click', () => {
      document.querySelectorAll('.date-slot').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentDate = d;
      loadPicks();
      loadScheduled();
    });
    slots.appendChild(btn);
  });
}

// ═══════════════════════════════════════════════════
// PICKS
// ═══════════════════════════════════════════════════
async function loadPicks() {
  const container = document.getElementById('picks-container');
  container.innerHTML = `<div class="picks-loading">
    <i class="fa-solid fa-spinner fa-spin"></i>
    <span>Calcul en cours — données réelles openfootball…</span>
  </div>`;

  const today = new Date().toISOString().slice(0,10);
  const offset = dateDiff(today, currentDate);

  try {
    const res  = await fetch(`/api/picks?day=${offset}`);
    const data = await res.json();
    renderPicks(data);
  } catch {
    container.innerHTML = `<div class="empty-state">
      <i class="fa-solid fa-wifi"></i><p>Erreur de chargement</p>
    </div>`;
  }
}

function renderPicks(data) {
  const container = document.getElementById('picks-container');
  const picks     = data.picks || [];

  // Source badge
  const sb = document.getElementById('source-badge');
  if (data.source === 'openfootball/github') {
    sb.innerHTML = '<i class="fa-solid fa-database"></i> Données réelles';
    sb.className = 'source-badge real';
  } else if (data.source === 'demo') {
    sb.innerHTML = '<i class="fa-solid fa-flask"></i> Données démo';
    sb.className = 'source-badge demo';
  }

  document.getElementById('picks-count').textContent = picks.length;

  if (picks.length === 0) {
    const note = data.note || '';
    container.innerHTML = `<div class="empty-state">
      <i class="fa-solid fa-magnifying-glass"></i>
      <p>Aucun pari ≥ 60% de confiance (${data.total_matches_analyzed || 0} matchs analysés)</p>
      ${note ? `<p style="margin-top:.5rem;color:var(--accent);font-size:.85rem">${note}</p>` : ''}
    </div>`;
    return;
  }

  if (data.note) {
    container.innerHTML = `<div style="background:rgba(88,166,255,.08);border:1px solid rgba(88,166,255,.3);
      border-radius:8px;padding:.7rem 1rem;font-size:.85rem;color:var(--accent);margin-bottom:1rem;">
      <i class="fa-solid fa-circle-info"></i> ${data.note}
    </div>`;
  } else {
    container.innerHTML = '';
  }

  const matchDate = picks[0]?.start_ts
    ? new Date(picks[0].start_ts * 1000).toLocaleDateString('fr-FR',{weekday:'long',day:'2-digit',month:'long'})
    : '';

  if (matchDate) {
    container.insertAdjacentHTML('beforeend',
      `<p style="color:var(--text2);font-size:.83rem;margin-bottom:1rem">
        <i class="fa-regular fa-calendar"></i> <strong>${matchDate}</strong> ·
        ${data.total_matches_analyzed} matchs analysés · ${picks.length} opportunités sélectionnées ·
        Source : <em>${data.source || 'GitHub'}</em>
      </p>`);
  }

  const grid = document.createElement('div');
  grid.className = 'picks-grid';

  picks.forEach((pick, idx) => {
    const cc    = confClass(pick.confidence);
    const card  = document.createElement('div');
    card.className = 'pick-card';
    card.dataset.conf = cc;
    card.addEventListener('click', () => {
      if (pick.match_id) window.location.href = `/match/${pick.match_id}`;
    });

    const rankColors = ['#f1c40f','#bdc3c7','#cd7f32', '#888'];
    const hf  = pick.home_form || {};
    const af  = pick.away_form || {};
    const analysis = pick.analysis || {};
    const time = pick.start_ts ? new Date(pick.start_ts*1000).toLocaleTimeString('fr-FR',{hour:'2-digit',minute:'2-digit'}) : '';

    const statsRow = [
      hf.avg_scored !== undefined ? `<div class="mini-stat"><span class="ms-label">${shortName(pick.home_team)} sc/m</span><span class="ms-value" style="color:var(--green)">${hf.avg_scored}</span></div>` : '',
      af.avg_scored !== undefined ? `<div class="mini-stat"><span class="ms-label">${shortName(pick.away_team)} sc/m</span><span class="ms-value" style="color:var(--green)">${af.avg_scored}</span></div>` : '',
      hf.over25_rate_pct !== undefined ? `<div class="mini-stat"><span class="ms-label">O2.5 dom.</span><span class="ms-value" style="color:var(--accent)">${hf.over25_rate_pct}%</span></div>` : '',
      af.over25_rate_pct !== undefined ? `<div class="mini-stat"><span class="ms-label">O2.5 ext.</span><span class="ms-value" style="color:var(--accent)">${af.over25_rate_pct}%</span></div>` : '',
      analysis.lam ? `<span class="exp-goals-chip"><i class="fa-solid fa-bolt"></i> λ = ${analysis.lam}</span>` : '',
    ].filter(Boolean).join('');

    const formDots = (form) => (form || []).map(r =>
      `<span class="fd-${r.toLowerCase()}">${r}</span>`).join('');

    card.innerHTML = `
      <span style="position:absolute;top:8px;left:10px;font-size:.82rem;font-weight:800;color:${rankColors[idx]||'#888'}">#${idx+1}</span>
      <span class="pick-ribbon ribbon-${cc}">${pick.confidence}%</span>

      <div class="pick-header">
        <span class="pick-market-icon">${pick.icon || '⚽'}</span>
        <div>
          <div class="pick-market-name">${pick.market}</div>
          <div class="pick-tournament">
            ${pick.flag || ''} ${pick.tournament || ''} · ${time}
          </div>
        </div>
      </div>

      <div class="pick-vs-row">
        <div class="pick-team-col">
          <div class="pick-team-name">${pick.home_team}</div>
          <div class="pick-form">${formDots(hf.form_str)}</div>
          <div class="pick-team-stat">${hf.avg_scored ?? '—'} sc · ${hf.avg_conceded ?? '—'} en</div>
        </div>
        <div class="pick-separator">VS</div>
        <div class="pick-team-col right">
          <div class="pick-team-name">${pick.away_team}</div>
          <div class="pick-form">${formDots(af.form_str)}</div>
          <div class="pick-team-stat">${af.avg_scored ?? '—'} sc · ${af.avg_conceded ?? '—'} en</div>
        </div>
      </div>

      <div class="pick-confidence">
        <div class="conf-header">
          <span class="conf-label">Confiance</span>
          <span class="conf-value ${cc}">${pick.confidence}%</span>
        </div>
        <div class="conf-bar-track">
          <div class="conf-bar-fill fill-${cc}" style="width:${pick.confidence}%"></div>
        </div>
      </div>

      <div class="pick-multi-stats">
        ${analysis.over25 !== undefined ? `<div class="ms2"><span>O 2.5</span><strong>${analysis.over25}%</strong></div>` : ''}
        ${analysis.btts   !== undefined ? `<div class="ms2"><span>BTTS</span><strong>${analysis.btts}%</strong></div>` : ''}
        ${analysis.over15 !== undefined ? `<div class="ms2"><span>O 1.5</span><strong>${analysis.over15}%</strong></div>` : ''}
        ${analysis.lam    !== undefined ? `<div class="ms2"><span>λ buts</span><strong>${analysis.lam}</strong></div>` : ''}
      </div>
    `;
    grid.appendChild(card);
  });

  container.appendChild(grid);
}

// ═══════════════════════════════════════════════════
// SCHEDULED MATCHES
// ═══════════════════════════════════════════════════
async function loadScheduled() {
  const container = document.getElementById('scheduled-matches');
  container.innerHTML = '<div class="loading-card"><i class="fa-solid fa-spinner fa-spin"></i></div>';

  const today  = new Date().toISOString().slice(0,10);
  const offset = dateDiff(today, currentDate);

  try {
    const res    = await fetch(`/api/scheduled?day=${offset}`);
    _allScheduled = await res.json();
    document.getElementById('scheduled-count').textContent = _allScheduled.length;
    buildFilter(_allScheduled);
    renderMatches(container, _allScheduled);
  } catch {
    container.innerHTML = '<div class="empty-state"><i class="fa-solid fa-wifi"></i><p>Erreur</p></div>';
  }
}

function buildFilter(events) {
  const wrap  = document.getElementById('tournament-filter');
  const tours = [...new Set(events.map(e => e.tournament).filter(Boolean))].slice(0,15);
  wrap.innerHTML = '';
  const all = [['Tous','all'], ...tours.map(t=>[t,t])];
  all.forEach(([label,val]) => {
    const btn = document.createElement('button');
    btn.className = 'filter-chip' + (_activeTournament===val?' active':'');
    btn.textContent = label;
    btn.addEventListener('click',()=>{
      _activeTournament = val;
      wrap.querySelectorAll('.filter-chip').forEach(b=>b.classList.remove('active'));
      btn.classList.add('active');
      const f = val==='all' ? _allScheduled : _allScheduled.filter(e=>e.tournament===val);
      renderMatches(document.getElementById('scheduled-matches'), f);
    });
    wrap.appendChild(btn);
  });
}

function renderMatches(container, events) {
  if (!events || !events.length) {
    container.innerHTML = `<div class="empty-state">
      <i class="fa-solid fa-calendar-xmark"></i>
      <p>Aucun match ce jour (pause internationale ?)</p>
    </div>`;
    return;
  }
  container.innerHTML = '';
  events.forEach(e => {
    const card = document.createElement('div');
    card.className = 'match-card';
    card.addEventListener('click', () => {
      if (e.id) window.location.href = `/match/${e.id}`;
    });

    const time = e.start_timestamp ? new Date(e.start_timestamp*1000)
      .toLocaleTimeString('fr-FR',{hour:'2-digit',minute:'2-digit'}) : '';

    card.innerHTML = `
      <div class="card-meta">
        <span class="tournament">${e.country_flag||''} ${e.tournament||''}</span>
        <span style="color:var(--text2);font-size:.8rem">${time}</span>
      </div>
      <div class="match-teams">
        <div class="team">
          <img src="${e.home_logo}" alt="${e.home_team}" onerror="this.src='/static/img/team-default.svg'"/>
          <span class="team-name">${e.home_team}</span>
        </div>
        <div class="match-score">
          <span class="score-box">– vs –</span>
          <span class="score-time">${e.round||''}</span>
        </div>
        <div class="team">
          <img src="${e.away_logo}" alt="${e.away_team}" onerror="this.src='/static/img/team-default.svg'"/>
          <span class="team-name">${e.away_team}</span>
        </div>
      </div>`;
    container.appendChild(card);
  });
}

// ── Utils ─────────────────────────────────────────
function confClass(c) {
  if (c >= 80) return 'high';
  if (c >= 65) return 'medium';
  return 'low';
}

function shortName(n) {
  if (!n) return '';
  const parts = n.split(' ');
  return parts[parts.length-1];
}

function dateDiff(from, to) {
  return Math.round((new Date(to+' 12:00') - new Date(from+' 12:00')) / 86400000);
}
