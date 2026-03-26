/* BetScore — Match detail page */

let matchData = null;
let betChart = null;

document.addEventListener('DOMContentLoaded', async () => {
  const container = document.getElementById('match-container');
  const eventId = container.dataset.eventId;

  await loadMatch(eventId);

  // Setup tabs
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });
});

// ── Load Match ────────────────────────────────
async function loadMatch(eventId) {
  try {
    const res = await fetch(`/api/match/${eventId}`);
    matchData = await res.json();

    if (matchData.error) {
      document.getElementById('match-hero').innerHTML = `<div class="empty-state"><i class="fa-solid fa-triangle-exclamation"></i>${matchData.error}</div>`;
      return;
    }

    renderHero(matchData.summary);
    document.getElementById('tabs').style.display = 'flex';

    renderStats(matchData.statistics);
    renderBetting(matchData.betting, matchData.summary);
    renderIncidents(matchData.incidents, matchData.summary);
    renderH2H(matchData.h2h, matchData.summary);
    loadLineups(eventId);

    switchTab('stats');
  } catch (err) {
    document.getElementById('match-hero').innerHTML = `<div class="empty-state"><i class="fa-solid fa-wifi"></i>Erreur de chargement</div>`;
  }
}

// ── Render Hero ───────────────────────────────
function renderHero(s) {
  const statusClass = s.status_type === 'inprogress' ? 'status-live-badge' :
                      s.status_type === 'finished' ? 'status-finished' : 'status-notstarted';
  const statusText = s.status_type === 'inprogress' ? `<i class="fa-solid fa-circle-dot"></i> ${s.status_desc || 'En direct'}` :
                     s.status_type === 'finished' ? 'Terminé' :
                     formatDateTime(s.start_timestamp);

  const homeScore = s.home_score !== null ? s.home_score : '-';
  const awayScore = s.away_score !== null ? s.away_score : '-';

  document.getElementById('match-hero').innerHTML = `
    <div class="hero-tournament">
      <span>${s.category || ''}</span>
      ${s.category ? '<i class="fa-solid fa-angle-right"></i>' : ''}
      <strong>${s.tournament || ''}</strong>
      ${s.round ? `<span style="color:var(--text2)">· J${s.round}</span>` : ''}
    </div>
    <div class="hero-teams">
      <div class="hero-team">
        <img src="${s.home_logo}" alt="${s.home_team}" onerror="this.src='/static/img/team-default.svg'" />
        <span class="hero-team-name">${s.home_team}</span>
      </div>
      <div class="hero-score">
        <div class="hero-score-box">${homeScore} – ${awayScore}</div>
        <span class="hero-status ${statusClass}">${statusText}</span>
      </div>
      <div class="hero-team">
        <img src="${s.away_logo}" alt="${s.away_team}" onerror="this.src='/static/img/team-default.svg'" />
        <span class="hero-team-name">${s.away_team}</span>
      </div>
    </div>
  `;
  document.title = `${s.home_team} vs ${s.away_team} — BetScore`;
}

// ── Render Statistics ─────────────────────────
function renderStats(stats) {
  const periods = ['ALL', '1ST', '2ND'];
  const availablePeriods = periods.filter(p =>
    Object.keys(stats).some(k => k.startsWith(p + '_'))
  );

  const periodSel = document.getElementById('stats-periods');
  periodSel.innerHTML = '';

  availablePeriods.forEach((p, i) => {
    const btn = document.createElement('button');
    btn.className = 'period-btn' + (i === 0 ? ' active' : '');
    btn.textContent = p === 'ALL' ? 'Match entier' : p === '1ST' ? '1ère mi-temps' : '2ème mi-temps';
    btn.dataset.period = p;
    btn.addEventListener('click', () => {
      document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderStatRows(stats, p);
    });
    periodSel.appendChild(btn);
  });

  if (availablePeriods.length > 0) renderStatRows(stats, availablePeriods[0]);
  else document.getElementById('stats-content').innerHTML = '<div class="empty-state"><i class="fa-solid fa-chart-bar"></i><p>Statistiques non disponibles</p></div>';
}

function renderStatRows(stats, period) {
  const content = document.getElementById('stats-content');
  const rows = Object.entries(stats)
    .filter(([k]) => k.startsWith(period + '_'))
    .map(([k, v]) => ({ key: k.replace(period + '_', ''), ...v }));

  if (rows.length === 0) {
    content.innerHTML = '<div class="empty-state"><i class="fa-solid fa-chart-bar"></i><p>Aucune statistique pour cette période</p></div>';
    return;
  }

  content.innerHTML = rows.map(row => {
    const hVal = parseFloat(row.home_value) || 0;
    const aVal = parseFloat(row.away_value) || 0;
    const total = hVal + aVal || 1;
    const hPct = (hVal / total * 100).toFixed(0);
    const aPct = (aVal / total * 100).toFixed(0);

    const homeDisplay = row.home || row.home_value || '0';
    const awayDisplay = row.away || row.away_value || '0';

    return `
      <div class="stat-row">
        <div class="stat-side home">
          <span class="stat-value">${homeDisplay}</span>
          <div class="stat-bar-wrap">
            <div class="stat-bar-fill" style="width:${hPct}%"></div>
          </div>
        </div>
        <div class="stat-name">${row.name || row.key}</div>
        <div class="stat-side away">
          <span class="stat-value">${awayDisplay}</span>
          <div class="stat-bar-wrap">
            <div class="stat-bar-fill" style="width:${aPct}%"></div>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

// ── Render Betting ────────────────────────────
function renderBetting(betting, summary) {
  const content = document.getElementById('betting-content');

  if (!betting || Object.keys(betting).length === 0) {
    content.innerHTML = '<div class="empty-state"><i class="fa-solid fa-chart-pie"></i><p>Analyse indisponible (match non commencé ou sans données)</p></div>';
    return;
  }

  const { home_pct, draw_pct, away_pct, signal, confidence } = betting;

  const signalLabel = signal === 'DOMICILE'
    ? `<strong style="color:var(--green)">${summary.home_team}</strong>`
    : signal === 'EXTERIEUR'
    ? `<strong style="color:var(--red)">${summary.away_team}</strong>`
    : `<strong style="color:var(--yellow)">Match Nul</strong>`;

  const bars = (pct) => {
    const filled = Math.round(pct / 20);
    return Array.from({ length: 5 }, (_, i) =>
      `<div class="signal-bar ${i < filled ? 'filled' : ''}"></div>`
    ).join('');
  };

  content.innerHTML = `
    <div class="bet-chart-wrap">
      <canvas id="betChart" height="200"></canvas>
    </div>

    <div class="betting-panel">
      <div class="bet-card bet-home ${signal === 'DOMICILE' ? 'recommended' : ''}">
        <div class="bet-label">${summary.home_team}</div>
        <div class="bet-pct">${home_pct}%</div>
        ${signal === 'DOMICILE' ? '<span class="rec-badge"><i class="fa-solid fa-star"></i> Recommandé</span>' : ''}
        <div class="confidence-bar"><div class="confidence-fill" style="width:${home_pct}%"></div></div>
      </div>
      <div class="bet-card bet-draw ${signal === 'NUL' ? 'recommended' : ''}">
        <div class="bet-label">Match Nul</div>
        <div class="bet-pct">${draw_pct}%</div>
        ${signal === 'NUL' ? '<span class="rec-badge"><i class="fa-solid fa-star"></i> Recommandé</span>' : ''}
        <div class="confidence-bar"><div class="confidence-fill" style="width:${draw_pct}%"></div></div>
      </div>
      <div class="bet-card bet-away ${signal === 'EXTERIEUR' ? 'recommended' : ''}">
        <div class="bet-label">${summary.away_team}</div>
        <div class="bet-pct">${away_pct}%</div>
        ${signal === 'EXTERIEUR' ? '<span class="rec-badge"><i class="fa-solid fa-star"></i> Recommandé</span>' : ''}
        <div class="confidence-bar"><div class="confidence-fill" style="width:${away_pct}%"></div></div>
      </div>
    </div>

    <div class="match-card" style="text-align:center; padding: 1.5rem; cursor:default;">
      <div style="font-size:0.85rem; color:var(--text2); margin-bottom:0.5rem; text-transform:uppercase; letter-spacing:0.1em;">Signal de l'algorithme</div>
      <div style="font-size:1.4rem; font-weight:800; margin-bottom:0.4rem;">Favoris : ${signalLabel}</div>
      <div style="font-size:0.9rem; color:var(--text2);">Confiance : <strong>${confidence}%</strong></div>
      <div style="display:flex; justify-content:center; gap:3px; margin-top:0.6rem;">${bars(confidence)}</div>
      <div style="margin-top:1rem; padding:0.8rem; background:rgba(210,153,34,0.08); border:1px solid rgba(210,153,34,0.3); border-radius:8px; font-size:0.8rem; color:var(--yellow);">
        <i class="fa-solid fa-triangle-exclamation"></i>
        Analyse basée sur les stats SofaScore uniquement. Le pari sportif comporte des risques.
      </div>
    </div>
  `;

  // Pie chart
  setTimeout(() => {
    const ctx = document.getElementById('betChart');
    if (!ctx) return;
    if (betChart) betChart.destroy();
    betChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: [summary.home_team, 'Nul', summary.away_team],
        datasets: [{
          data: [home_pct, draw_pct, away_pct],
          backgroundColor: ['#3fb950', '#d29922', '#f85149'],
          borderWidth: 0,
          hoverOffset: 6,
        }],
      },
      options: {
        responsive: true,
        cutout: '65%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: '#8b949e', font: { family: 'Inter', size: 12 } },
          },
          tooltip: {
            callbacks: {
              label: ctx => ` ${ctx.label}: ${ctx.parsed}%`,
            },
          },
        },
      },
    });
  }, 100);
}

// ── Render Incidents ──────────────────────────
function renderIncidents(incidents, summary) {
  const content = document.getElementById('incidents-content');

  if (!incidents || incidents.length === 0) {
    content.innerHTML = '<div class="empty-state"><i class="fa-solid fa-bolt"></i><p>Aucun incident disponible</p></div>';
    return;
  }

  const incidentTypes = {
    goal: { icon: 'fa-futbol icon-goal', dot: 'goal', label: 'But' },
    yellowCard: { icon: 'fa-square icon-yellow', dot: 'yellow-card', label: 'Carton jaune' },
    redCard: { icon: 'fa-square icon-red', dot: 'red-card', label: 'Carton rouge' },
    yellowRedCard: { icon: 'fa-square icon-red', dot: 'red-card', label: '2ème jaune' },
    substitution: { icon: 'fa-right-left icon-sub', dot: 'substitution', label: 'Remplacement' },
    varDecision: { icon: 'fa-tv', dot: '', label: 'VAR' },
    penaltyMissed: { icon: 'fa-xmark icon-red', dot: 'red-card', label: 'Pénalty manqué' },
  };

  const items = incidents
    .filter(inc => inc.incidentType !== 'period')
    .sort((a, b) => (a.time || 0) - (b.time || 0));

  if (items.length === 0) {
    content.innerHTML = '<div class="empty-state"><i class="fa-solid fa-bolt"></i><p>Aucun incident enregistré</p></div>';
    return;
  }

  const html = items.map(inc => {
    const type = incidentTypes[inc.incidentType] || { icon: 'fa-circle', dot: '', label: inc.incidentType };
    const isHome = inc.isHome;
    const player = inc.player?.name || inc.playerName || '';
    const addInfo = inc.addedTime ? `+${inc.addedTime}'` : '';
    const teamName = isHome ? summary.home_team : summary.away_team;

    return `
      <div class="incident-item">
        <div class="incident-dot ${type.dot}"></div>
        <div class="incident-card">
          <span class="incident-minute">${inc.time || '?'}'${addInfo}</span>
          <i class="fa-solid ${type.icon} incident-icon"></i>
          <div class="incident-text">
            <div class="incident-player">${player}</div>
            <div class="incident-team">${teamName} · ${type.label}</div>
          </div>
        </div>
      </div>
    `;
  }).join('');

  content.innerHTML = `<div class="incidents-timeline">${html}</div>`;
}

// ── Render H2H ────────────────────────────────
function renderH2H(h2h, summary) {
  const content = document.getElementById('h2h-content');

  const events = h2h?.events || h2h?.teamDuel?.events || [];

  if (events.length === 0) {
    content.innerHTML = '<div class="empty-state"><i class="fa-solid fa-arrows-left-right"></i><p>Aucune confrontation directe disponible</p></div>';
    return;
  }

  let homeWins = 0, awayWins = 0, draws = 0;

  const matchHtml = events.slice(0, 10).map(e => {
    const hs = e.homeScore?.current ?? '-';
    const as = e.awayScore?.current ?? '-';
    const d = new Date((e.startTimestamp || 0) * 1000);
    const dateStr = d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' });

    if (hs > as) homeWins++;
    else if (as > hs) awayWins++;
    else if (hs === as && hs !== '-') draws++;

    const homeTeam = e.homeTeam?.name || '?';
    const awayTeam = e.awayTeam?.name || '?';

    return `
      <div class="h2h-match">
        <span class="h2h-home">${homeTeam}</span>
        <span class="h2h-score">${hs} – ${as}</span>
        <span class="h2h-away">${awayTeam}</span>
        <span class="h2h-date" style="grid-column:1/-1;text-align:center">${dateStr}</span>
      </div>
    `;
  }).join('');

  content.innerHTML = `
    <div class="h2h-summary">
      <div class="h2h-team-wins home">
        <div style="font-size:0.8rem;color:var(--text2);margin-bottom:0.3rem">${summary.home_team}</div>
        <div class="wins-num">${homeWins}</div>
        <div style="font-size:0.8rem;color:var(--text2)">victoires</div>
      </div>
      <div class="h2h-draws">
        <div class="draws-label">Nuls</div>
        <div class="draws-num">${draws}</div>
      </div>
      <div class="h2h-team-wins away">
        <div style="font-size:0.8rem;color:var(--text2);margin-bottom:0.3rem">${summary.away_team}</div>
        <div class="wins-num">${awayWins}</div>
        <div style="font-size:0.8rem;color:var(--text2)">victoires</div>
      </div>
    </div>
    <div class="h2h-list">${matchHtml}</div>
  `;
}

// ── Load Lineups ──────────────────────────────
async function loadLineups(eventId) {
  try {
    const res = await fetch(`/api/match/${eventId}/lineups`);
    const data = await res.json();
    renderLineups(data);
  } catch {
    document.getElementById('lineups-content').innerHTML =
      '<div class="empty-state"><i class="fa-solid fa-users"></i><p>Compositions non disponibles</p></div>';
  }
}

function renderLineups(data) {
  const content = document.getElementById('lineups-content');

  const home = data.home;
  const away = data.away;

  if (!home && !away) {
    content.innerHTML = '<div class="empty-state"><i class="fa-solid fa-users"></i><p>Compositions non disponibles</p></div>';
    return;
  }

  const renderTeam = (team, side) => {
    if (!team) return `<div class="lineup-team"><div class="lineup-header">Composition non disponible</div></div>`;

    const players = team.players || [];
    const starters = players.filter(p => !p.substitute);
    const subs = players.filter(p => p.substitute);

    const playerHtml = (p) => `
      <div class="player-item">
        <span class="player-number">${p.player?.jerseyNumber || p.jerseyNumber || '#'}</span>
        <span class="player-name">${p.player?.name || p.name || ''}</span>
        <span class="player-pos">${p.position || ''}</span>
      </div>
    `;

    return `
      <div class="lineup-team">
        <div class="lineup-header">
          <span>${team.name || side}</span>
          <span class="lineup-formation">${team.formation || ''}</span>
        </div>
        <div class="lineup-players">
          ${starters.map(playerHtml).join('')}
          ${subs.length ? `<div class="substitutes-title">Remplaçants</div>${subs.map(playerHtml).join('')}` : ''}
        </div>
      </div>
    `;
  };

  content.innerHTML = `
    <div class="lineups-container">
      ${renderTeam(home, 'Domicile')}
      ${renderTeam(away, 'Extérieur')}
    </div>
  `;
}

// ── Tab Switching ─────────────────────────────
function switchTab(name) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === name));
  document.querySelectorAll('.tab-content').forEach(c => {
    c.classList.toggle('active', c.id === `tab-${name}`);
    c.style.display = c.id === `tab-${name}` ? 'block' : 'none';
  });
}

// ── Utils ─────────────────────────────────────
function formatDateTime(ts) {
  if (!ts) return '';
  const d = new Date(ts * 1000);
  return d.toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
}
