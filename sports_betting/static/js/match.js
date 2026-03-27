/* BetScore — Match detail page */

let betChart = null;

document.addEventListener('DOMContentLoaded', async () => {
  const eventId = document.getElementById('match-container').dataset.eventId;
  await loadMatch(eventId);
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });
});

// ── Load match ────────────────────────────────
async function loadMatch(eventId) {
  try {
    const res  = await fetch(`/api/match/${eventId}`);
    const data = await res.json();
    if (data.error) {
      document.getElementById('match-hero').innerHTML =
        `<div class="empty-state"><i class="fa-solid fa-triangle-exclamation"></i>${data.error}</div>`;
      return;
    }
    renderHero(data.summary);
    document.getElementById('tabs').style.display = 'flex';

    renderBettingTab(data.betting, data.summary);
    renderStats(data.statistics);
    renderIncidents(data.incidents, data.summary);
    renderH2H(data.h2h, data.summary);
    loadLineups(eventId);
  } catch {
    document.getElementById('match-hero').innerHTML =
      `<div class="empty-state"><i class="fa-solid fa-wifi"></i>Erreur de chargement</div>`;
  }
}

// ── Hero ──────────────────────────────────────
function renderHero(s) {
  const statusClass = s.status_type === 'inprogress' ? 'status-live-badge' :
                      s.status_type === 'finished'   ? 'status-finished' : 'status-notstarted';
  const statusText  = s.status_type === 'inprogress' ? `<i class="fa-solid fa-circle-dot"></i> ${s.status_desc || 'En direct'}` :
                      s.status_type === 'finished'   ? 'Terminé' : formatDateTime(s.start_timestamp);

  const hs = s.home_score !== null ? s.home_score : '–';
  const as = s.away_score !== null ? s.away_score : '–';

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
        <div class="hero-score-box">${hs} – ${as}</div>
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

// ═══════════════════════════════════════════════════
// BETTING TAB (main analysis)
// ═══════════════════════════════════════════════════
function renderBettingTab(betting, summary) {
  const content = document.getElementById('betting-content');
  if (!betting || Object.keys(betting).length === 0) {
    content.innerHTML = `<div class="empty-state" style="margin-top:2rem;">
      <i class="fa-solid fa-chart-pie"></i>
      <p>Analyse indisponible — les données de forme ne sont pas encore disponibles</p>
    </div>`;
    return;
  }

  const hf = betting.home_form || {};
  const af = betting.away_form || {};

  let html = '';

  // ── Form cards ─────────────────────────────
  html += `<h3 class="betting-section-title"><i class="fa-solid fa-chart-line accent-icon"></i> Forme récente (${hf.matches || '?'} matchs)</h3>`;
  html += `<div class="form-grid">
    ${formCard(summary.home_team, hf)}
    ${formCard(summary.away_team, af)}
  </div>`;

  // ── Market rows ────────────────────────────
  const markets = [];
  if (betting.over25) markets.push(betting.over25);
  if (betting.over15) markets.push(betting.over15);
  if (betting.btts)   markets.push(betting.btts);
  if (betting.x12 && betting.x12.length) markets.push(betting.x12[0]); // best 1X2

  markets.sort((a, b) => b.confidence - a.confidence);
  const best = markets[0];

  html += `<h3 class="betting-section-title"><i class="fa-solid fa-fire accent-icon"></i> Analyse par marché</h3>`;

  markets.forEach(m => {
    const isTop  = m === best;
    const cc     = confClass(m.confidence);
    const factors = (m.factors || []).map(f => f).join(' · ');
    html += `
      <div class="market-row ${isTop ? 'top-pick' : ''}">
        <span class="market-icon">${m.icon || '⚽'}</span>
        <div>
          <div class="market-name">
            ${m.market}
            ${isTop ? '<span style="font-size:.75rem;color:var(--green);margin-left:.5rem;">⭐ Meilleur pari</span>' : ''}
          </div>
          <div class="market-factors">${factors}</div>
        </div>
        <div class="market-conf">
          <div class="mc-pct ${cc}">${m.confidence}%</div>
          <div class="mc-label">confiance</div>
        </div>
      </div>
    `;
  });

  // ── Doughnut chart ─────────────────────────
  if (betting.x12 && betting.x12.length >= 3) {
    const x12 = betting.x12;
    html += `<h3 class="betting-section-title" style="margin-top:2rem;">
      <i class="fa-solid fa-chart-pie accent-icon"></i> Probabilités 1X2</h3>`;
    html += `<div class="bet-chart-wrap"><canvas id="betChart" height="220"></canvas></div>`;

    const best1x2 = x12[0];
    html += `<div style="text-align:center;margin-bottom:1rem;">
      Favori : <strong>${best1x2.market}</strong>
      <span class="pick-ribbon ribbon-${confClass(best1x2.confidence)}" style="position:static;display:inline-block;margin-left:.5rem">
        ${best1x2.confidence}%
      </span>
    </div>`;
  }

  // ── Disclaimer ─────────────────────────────
  html += `<div class="disclaimer">
    <i class="fa-solid fa-triangle-exclamation" style="margin-top:.1rem"></i>
    <span>Analyse basée sur les statistiques SofaScore (loi de Poisson, forme sur 8 matchs).
    Le pari sportif comporte des risques. Jouez de manière responsable.</span>
  </div>`;

  content.innerHTML = html;

  // Draw chart after DOM update
  if (betting.x12 && betting.x12.length >= 3) {
    setTimeout(() => drawX12Chart(betting.x12, summary), 80);
  }
}

function formCard(teamName, f) {
  if (!f || Object.keys(f).length === 0) return `<div class="form-card"><p style="color:var(--text2)">Données indisponibles</p></div>`;

  const dots = (f.form_str || []).map(r =>
    `<span class="form-dot dot-${r}">${r}</span>`
  ).join('');

  return `
    <div class="form-card">
      <div class="form-card-title">${teamName}</div>
      <div class="form-dots">${dots}</div>
      <div class="stat-mini-grid">
        <div class="stat-mini-item">
          <div class="sm-label">Buts marqués/m</div>
          <div class="sm-val sm-green">${f.avg_scored}</div>
        </div>
        <div class="stat-mini-item">
          <div class="sm-label">Buts encaissés/m</div>
          <div class="sm-val sm-red">${f.avg_conceded}</div>
        </div>
        <div class="stat-mini-item">
          <div class="sm-label">Over 2.5</div>
          <div class="sm-val sm-blue">${f.over25_rate_pct}%</div>
        </div>
        <div class="stat-mini-item">
          <div class="sm-label">BTTS</div>
          <div class="sm-val sm-blue">${f.btts_rate_pct}%</div>
        </div>
        <div class="stat-mini-item">
          <div class="sm-label">Win rate</div>
          <div class="sm-val">${f.win_rate_pct}%</div>
        </div>
        <div class="stat-mini-item">
          <div class="sm-label">Clean sheets</div>
          <div class="sm-val">${f.clean_sheet_pct}%</div>
        </div>
      </div>
    </div>
  `;
}

function drawX12Chart(x12, summary) {
  const ctx = document.getElementById('betChart');
  if (!ctx) return;
  if (betChart) betChart.destroy();

  const sorted = [...x12].sort((a, b) => {
    const order = ['home_win', 'draw', 'away_win'];
    return order.indexOf(a.market_key) - order.indexOf(b.market_key);
  });

  betChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: sorted.map(m => m.market),
      datasets: [{
        data:            sorted.map(m => m.confidence),
        backgroundColor: ['#3fb950', '#d29922', '#f85149'],
        borderWidth: 0,
        hoverOffset: 8,
      }],
    },
    options: {
      responsive: true, cutout: '60%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: '#8b949e', font: { family: 'Inter', size: 12 }, padding: 16 },
        },
        tooltip: {
          callbacks: { label: ctx => ` ${ctx.label}: ${ctx.parsed.toFixed(1)}%` },
        },
      },
    },
  });
}

function confClass(c) {
  if (c >= 75) return 'high';
  if (c >= 65) return 'medium';
  return 'low';
}

// ── Statistics tab ────────────────────────────
function renderStats(stats) {
  const periods = ['ALL', '1ST', '2ND'].filter(p =>
    Object.keys(stats).some(k => k.startsWith(p + '_'))
  );

  const sel = document.getElementById('stats-periods');
  sel.innerHTML = '';

  if (periods.length === 0) {
    document.getElementById('stats-content').innerHTML =
      '<div class="empty-state"><i class="fa-solid fa-chart-bar"></i><p>Statistiques non disponibles</p></div>';
    return;
  }

  periods.forEach((p, i) => {
    const btn = document.createElement('button');
    btn.className = 'period-btn' + (i === 0 ? ' active' : '');
    btn.textContent = p === 'ALL' ? 'Match entier' : p === '1ST' ? '1ère MT' : '2ème MT';
    btn.dataset.period = p;
    btn.addEventListener('click', () => {
      document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderStatRows(stats, p);
    });
    sel.appendChild(btn);
  });

  renderStatRows(stats, periods[0]);
}

function renderStatRows(stats, period) {
  const content = document.getElementById('stats-content');
  const rows    = Object.entries(stats)
    .filter(([k]) => k.startsWith(period + '_'))
    .map(([k, v]) => ({ key: k.replace(period + '_', ''), ...v }));

  if (!rows.length) {
    content.innerHTML = '<div class="empty-state"><i class="fa-solid fa-chart-bar"></i><p>Aucune stat pour cette période</p></div>';
    return;
  }

  content.innerHTML = rows.map(row => {
    const hv   = parseFloat(row.home_value) || 0;
    const av   = parseFloat(row.away_value) || 0;
    const tot  = hv + av || 1;
    const hPct = (hv / tot * 100).toFixed(0);
    const aPct = (av / tot * 100).toFixed(0);
    return `
      <div class="stat-row">
        <div class="stat-side home">
          <span class="stat-value">${row.home || row.home_value || '0'}</span>
          <div class="stat-bar-wrap"><div class="stat-bar-fill" style="width:${hPct}%"></div></div>
        </div>
        <div class="stat-name">${row.name || row.key}</div>
        <div class="stat-side away">
          <span class="stat-value">${row.away || row.away_value || '0'}</span>
          <div class="stat-bar-wrap"><div class="stat-bar-fill" style="width:${aPct}%"></div></div>
        </div>
      </div>`;
  }).join('');
}

// ── Incidents ─────────────────────────────────
function renderIncidents(incidents, summary) {
  const content = document.getElementById('incidents-content');
  if (!incidents || !incidents.length) {
    content.innerHTML = '<div class="empty-state"><i class="fa-solid fa-bolt"></i><p>Aucun incident disponible</p></div>';
    return;
  }

  const typeMap = {
    goal:          { icon: 'fa-futbol icon-goal',   dot: 'goal',         label: 'But' },
    yellowCard:    { icon: 'fa-square icon-yellow',  dot: 'yellow-card',  label: 'Carton jaune' },
    redCard:       { icon: 'fa-square icon-red',     dot: 'red-card',     label: 'Carton rouge' },
    yellowRedCard: { icon: 'fa-square icon-red',     dot: 'red-card',     label: '2ème jaune' },
    substitution:  { icon: 'fa-right-left icon-sub', dot: 'substitution', label: 'Remplacement' },
    varDecision:   { icon: 'fa-tv',                  dot: '',             label: 'VAR' },
    penaltyMissed: { icon: 'fa-xmark icon-red',      dot: 'red-card',     label: 'Pénalty manqué' },
  };

  const items = incidents
    .filter(i => i.incidentType !== 'period')
    .sort((a, b) => (a.time || 0) - (b.time || 0));

  const html = items.map(inc => {
    const t    = typeMap[inc.incidentType] || { icon: 'fa-circle', dot: '', label: inc.incidentType };
    const team = inc.isHome ? summary.home_team : summary.away_team;
    const pl   = inc.player?.name || '';
    const add  = inc.addedTime ? `+${inc.addedTime}'` : '';
    return `
      <div class="incident-item">
        <div class="incident-dot ${t.dot}"></div>
        <div class="incident-card">
          <span class="incident-minute">${inc.time || '?'}'${add}</span>
          <i class="fa-solid ${t.icon} incident-icon"></i>
          <div class="incident-text">
            <div class="incident-player">${pl}</div>
            <div class="incident-team">${team} · ${t.label}</div>
          </div>
        </div>
      </div>`;
  }).join('');

  content.innerHTML = `<div class="incidents-timeline">${html}</div>`;
}

// ── H2H ──────────────────────────────────────
function renderH2H(h2h, summary) {
  const content = document.getElementById('h2h-content');
  const events  = h2h?.events || h2h?.teamDuel?.events || [];

  if (!events.length) {
    content.innerHTML = '<div class="empty-state"><i class="fa-solid fa-arrows-left-right"></i><p>Aucune confrontation disponible</p></div>';
    return;
  }

  let hw = 0, aw = 0, dr = 0;
  const rows = events.slice(0, 10).map(e => {
    const hs = e.homeScore?.current ?? '-';
    const as = e.awayScore?.current ?? '-';
    if (hs > as) hw++; else if (as > hs) aw++; else if (hs !== '-') dr++;
    const dt = new Date((e.startTimestamp || 0) * 1000)
      .toLocaleDateString('fr-FR', { day:'2-digit', month:'2-digit', year:'numeric' });
    return `
      <div class="h2h-match">
        <span class="h2h-home">${e.homeTeam?.name || '?'}</span>
        <span class="h2h-score">${hs} – ${as}</span>
        <span class="h2h-away">${e.awayTeam?.name || '?'}</span>
        <span class="h2h-date" style="grid-column:1/-1;text-align:center">${dt}</span>
      </div>`;
  }).join('');

  content.innerHTML = `
    <div class="h2h-summary">
      <div class="h2h-team-wins home">
        <div style="font-size:.8rem;color:var(--text2);margin-bottom:.3rem">${summary.home_team}</div>
        <div class="wins-num">${hw}</div>
        <div style="font-size:.8rem;color:var(--text2)">victoires</div>
      </div>
      <div class="h2h-draws">
        <div class="draws-label">Nuls</div>
        <div class="draws-num">${dr}</div>
      </div>
      <div class="h2h-team-wins away">
        <div style="font-size:.8rem;color:var(--text2);margin-bottom:.3rem">${summary.away_team}</div>
        <div class="wins-num">${aw}</div>
        <div style="font-size:.8rem;color:var(--text2)">victoires</div>
      </div>
    </div>
    <div class="h2h-list">${rows}</div>`;
}

// ── Lineups ───────────────────────────────────
async function loadLineups(eventId) {
  try {
    const res  = await fetch(`/api/match/${eventId}/lineups`);
    const data = await res.json();
    renderLineups(data);
  } catch {
    document.getElementById('lineups-content').innerHTML =
      '<div class="empty-state"><i class="fa-solid fa-users"></i><p>Compositions indisponibles</p></div>';
  }
}

function renderLineups(data) {
  const content = document.getElementById('lineups-content');
  const home = data.home, away = data.away;
  if (!home && !away) {
    content.innerHTML = '<div class="empty-state"><i class="fa-solid fa-users"></i><p>Compositions indisponibles</p></div>';
    return;
  }

  const renderTeam = team => {
    if (!team) return `<div class="lineup-team"><div class="lineup-header">Indisponible</div></div>`;
    const starters = (team.players || []).filter(p => !p.substitute);
    const subs     = (team.players || []).filter(p => p.substitute);
    const pl = p => `
      <div class="player-item">
        <span class="player-number">${p.player?.jerseyNumber || '#'}</span>
        <span class="player-name">${p.player?.name || ''}</span>
        <span class="player-pos">${p.position || ''}</span>
      </div>`;
    return `
      <div class="lineup-team">
        <div class="lineup-header">
          <span>${team.name || ''}</span>
          <span class="lineup-formation">${team.formation || ''}</span>
        </div>
        <div class="lineup-players">
          ${starters.map(pl).join('')}
          ${subs.length ? `<div class="substitutes-title">Remplaçants</div>${subs.map(pl).join('')}` : ''}
        </div>
      </div>`;
  };

  content.innerHTML = `<div class="lineups-container">${renderTeam(home)}${renderTeam(away)}</div>`;
}

// ── Tab switching ─────────────────────────────
function switchTab(name) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === name));
  document.querySelectorAll('.tab-content').forEach(c => {
    const active = c.id === `tab-${name}`;
    c.classList.toggle('active', active);
    c.style.display = active ? 'block' : 'none';
  });
}

// ── Utils ─────────────────────────────────────
function formatDateTime(ts) {
  if (!ts) return '';
  return new Date(ts * 1000).toLocaleString('fr-FR', { day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit' });
}
