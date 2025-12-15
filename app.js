// Client-only mode (sans npm) : lit `data/players.json` localement et interroge l'API publique Chess.com
const $ = sel => document.querySelector(sel);
const $status = $('#status');

function setStatus(text) { if($status) $status.textContent = text; }

// Use Chess.com stats API per player
async function fetchPlayerStats(username){
  const url = `https://api.chess.com/pub/player/${encodeURIComponent(username)}/stats`;
  const res = await fetch(url);
  if(!res.ok) return null;
  return res.json();
}

async function fetchPlayerProfile(username){
  const url = `https://api.chess.com/pub/player/${encodeURIComponent(username)}`;
  const res = await fetch(url);
  if(!res.ok) return null;
  return res.json();
}

function arrowFor(direction){
  if(direction === 'up') return `<i class="fa-solid fa-arrow-up dir up" title="monté"></i>`;
  if(direction === 'down') return `<i class="fa-solid fa-arrow-down dir down" title="descendu"></i>`;
  return `<i class="fa-solid fa-minus dir neutral" title="stable"></i>`;
}

function renderWinLossDraw(stats) {
  if (!stats) return '';
  
  const { wins, losses, draws } = stats;
  const total = wins + losses + draws;
  if (total === 0) return '';
  
  const winPct = ((wins / total) * 100).toFixed(0);
  const lossPct = ((losses / total) * 100).toFixed(0);
  const drawPct = ((draws / total) * 100).toFixed(0);
  
  // Option : Barre segmentée style Chess.com (une seule barre avec 3 couleurs)
  return `
    <div style="display:flex;flex-direction:column;gap:2px">
      <div style="display:flex;height:5px;border-radius:2px;overflow:hidden;background:#1a1a1a">
        <div style="width:${winPct}%;background:#36d399" title="${wins} victoires"></div>
        <div style="width:${drawPct}%;background:#999" title="${draws} nuls"></div>
        <div style="width:${lossPct}%;background:#ff6b6b" title="${losses} défaites"></div>
      </div>
      <div style="display:flex;justify-content:space-between;font-size:0.55rem;line-height:1;opacity:0.8">
        <span style="color:#36d399">${winPct}%</span>
        <span style="color:#999">${drawPct}%</span>
        <span style="color:#ff6b6b">${lossPct}%</span>
      </div>
    </div>
  `;
}

function sparkline(data) {
  if (!data || data.length < 2) return '';
  
  const width = 70;
  const height = 20;
  const padding = 2;
  
  // Trouver le score moyen pour définir une plage fixe autour
  const avg = data.reduce((a, b) => a + b, 0) / data.length;
  const minData = Math.min(...data);
  const maxData = Math.max(...data);
  const dataRange = maxData - minData;
  
  // Utiliser une plage fixe basée sur la variation (min 100 points pour voir les détails)
  const fixedRange = Math.max(dataRange * 2, 100);
  const centerValue = avg;
  const min = centerValue - fixedRange / 2;
  const max = centerValue + fixedRange / 2;
  
  const points = data.map((val, i) => {
    const x = padding + (i / (data.length - 1)) * (width - padding * 2);
    // Clamp la valeur entre min et max pour éviter débordements
    const clampedVal = Math.max(min, Math.min(max, val));
    const y = height - padding - ((clampedVal - min) / (max - min)) * (height - padding * 2);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');
  
  // Calculer la différence entre premier et dernier jour
  const diff = data[data.length - 1] - data[0];
  const percentChange = (diff / data[0]) * 100;
  
  // 3 niveaux: gain majeur (>2%), stagnant (-2% à +2%), perte (<-2%)
  let color;
  if (percentChange > 2) {
    color = '#36d399'; // vert - gain majeur
  } else if (percentChange < -2) {
    color = '#ff6b6b'; // rouge - perte
  } else {
    color = '#ff9f1c'; // orange - stagnant/minime
  }
  
  return `<svg width="${width}" height="${height}" class="sparkline">
    <polyline points="${points}" fill="none" stroke="${color}" stroke-width="1.5" />
  </svg>`;
}

// No longer needed - promo and class are separate fields in DB
// Kept for compatibility but not used
function parseClass(cls){
  if(!cls) return { promo: '—', letter: '' };
  const parts = String(cls).trim().toUpperCase().split(/\s+/);
  const promo = parts[0] || '—';
  const letter = parts[1] || '';
  return { promo, letter };
}

async function loadClientOnly(limit){
  setStatus('Chargement…');
  try{
    // Charger le JSON (mis à jour quotidiennement par update_leaderboard.py)
    const playersRes = await fetch('data/players.json?t=' + Date.now()); // cache buster
    if(!playersRes.ok) throw new Error('Impossible de lire data/players.json');
    let players = await playersRes.json();
    
    // Le JSON contient déjà: current, best, history7days, previousRank
    // Plus besoin d'appeler l'API Chess.com !
    
    // Calculer la direction des flèches
    players.forEach((p, idx) => {
      const currentRank = idx + 1;
      if(p.previousRank == null){
        p.direction = 'neutral';
      } else if(currentRank < p.previousRank){
        p.direction = 'up'; // rank amélioré (nombre plus petit = meilleur)
      } else if(currentRank > p.previousRank){
        p.direction = 'down';
      } else {
        p.direction = 'neutral';
      }
    });

    render(players.slice(0, 50));
    setLastUpdated(new Date());
    
  }catch(err){
    console.error('Erreur:', err);
    setStatus('Erreur de chargement');
  }
}

// Fonction pour mettre à jour l'historique des 7 derniers jours
async function updateDailyHistory(players) {
  const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
  const lastUpdate = localStorage.getItem('lastHistoryUpdate');
  
  // Ne mettre à jour qu'une fois par jour
  if (lastUpdate === today) return;
  
  try {
    // Récupérer la BD actuelle
    const response = await fetch('data/players.json?t=' + Date.now());
    const dbPlayers = await response.json();
    
    // Pour chaque joueur, mettre à jour son historique
    const updatedPlayers = dbPlayers.map(dbPlayer => {
      const current = players.find(p => p.username === dbPlayer.username);
      if (!current) return dbPlayer;
      
      let history = dbPlayer.history7days || [];
      
      // Ajouter le score actuel
      history.push(current.current || 0);
      
      // Garder seulement les 7 derniers jours
      if (history.length > 7) {
        history = history.slice(-7);
      }
      
      return {
        ...dbPlayer,
        history7days: history,
        previousRank: players.indexOf(current) + 1 // Mettre à jour previousRank
      };
    });
    
    // Sauvegarder dans localStorage (en attendant un vrai backend)
    localStorage.setItem('playersHistory', JSON.stringify(updatedPlayers));
    localStorage.setItem('lastHistoryUpdate', today);
    
    console.log('Historique mis à jour pour le', today);
  } catch(err) {
    console.error('Erreur mise à jour historique:', err);
  }
}

// Charger l'historique depuis localStorage si disponible
function loadHistoryFromCache() {
  const cached = localStorage.getItem('playersHistory');
  return cached ? JSON.parse(cached) : null;
}

// Fonction pour mettre à jour l'historique des 7 derniers jours
async function updateDailyHistory(players) {
  const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
  const lastUpdate = localStorage.getItem('lastHistoryUpdate');
  
  // Ne mettre à jour qu'une fois par jour
  if (lastUpdate === today) return;
  
  try {
    // Récupérer la BD actuelle
    const response = await fetch('data/players.json?t=' + Date.now());
    const dbPlayers = await response.json();
    
    // Pour chaque joueur, mettre à jour son historique
    const updatedPlayers = dbPlayers.map(dbPlayer => {
      const current = players.find(p => p.username === dbPlayer.username);
      if (!current) return dbPlayer;
      
      let history = dbPlayer.history7days || [];
      
      // Ajouter le score actuel
      history.push(current.current || 0);
      
      // Garder seulement les 7 derniers jours
      if (history.length > 7) {
        history = history.slice(-7);
      }
      
      return {
        ...dbPlayer,
        history7days: history,
        previousRank: players.indexOf(current) + 1 // Mettre à jour previousRank
      };
    });
    
    // Sauvegarder dans localStorage (en attendant un vrai backend)
    localStorage.setItem('playersHistory', JSON.stringify(updatedPlayers));
    localStorage.setItem('lastHistoryUpdate', today);
    
    console.log('📈 Historique mis à jour pour le', today);
  } catch(err) {
    console.error('Erreur mise à jour historique:', err);
  }
}

// Charger l'historique depuis localStorage si disponible
function loadHistoryFromCache() {
  const cached = localStorage.getItem('playersHistory');
  return cached ? JSON.parse(cached) : null;
}

// Auto-refresh every N ms and show countdown
const REFRESH_INTERVAL = 5 * 60 * 1000; // 5 minutes
let refreshTimer = null;
let countdownInterval = null;

function startAutoRefresh(){
  stopAutoRefresh();
  let nextAt = Date.now() + REFRESH_INTERVAL;
  updateRefreshButton(nextAt - Date.now());
  countdownInterval = setInterval(()=>{
    const remaining = nextAt - Date.now();
    if(remaining <= 0){
      // trigger immediate refresh
      loadClientOnly(50);
      nextAt = Date.now() + REFRESH_INTERVAL;
    }
    updateRefreshButton(Math.max(0, nextAt - Date.now()));
  }, 1000);
}

function stopAutoRefresh(){
  if(countdownInterval) { clearInterval(countdownInterval); countdownInterval = null; }
}

function updateRefreshButton(ms){
  const btn = document.getElementById('next-refresh');
  if(!btn) return;
  const s = Math.floor(ms/1000);
  const mm = String(Math.floor(s/60)).padStart(2,'0');
  const ss = String(s % 60).padStart(2,'0');
  btn.textContent = `Prochaine maj dans ${mm}:${ss}`;
}

function setLastUpdated(d){
  const el = document.getElementById('last-updated');
  if(!el) return;
  const s = d.toLocaleString();
  el.textContent = `Dernière maj : ${s}`;
}

function render(players){
  console.log('Rendering players:', players); // Debug
  
  // Render podium (top 3)
  const podiumDiv = document.getElementById('podium');
  const top3 = players.slice(0, 3);
  podiumDiv.innerHTML = '';
  
  top3.forEach((p, i) => {
    const rankNum = i + 1;
    const medals = ['🥇', '🥈', '🥉'];
    const promo = p.promo || '—';
    const letter = p.class || '';
    const badgeClass = `class-badge badge-${promo}`;
    
    const wrapper = document.createElement('div');
    wrapper.className = `podium-wrapper rank-${rankNum}`;
    const avatarUrl = p.avatar || 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + p.username;
    wrapper.innerHTML = `
      <img class="podium-avatar-top" src="${avatarUrl}" alt="${p.username}" />
      <div class="podium-card">
        <div class="podium-medal">${medals[i]}</div>
        <div class="podium-bottom">
          <div class="podium-name">${p.firstName} ${p.lastName}</div>
          <div class="podium-score">${p.current ?? '—'}</div>
        </div>
      </div>
    `;
    podiumDiv.appendChild(wrapper);
  });
  
  // Render tables in 2 columns (ranks 4-50 split into 4-28 and 29-53)
  const tbody1 = document.querySelector('#leaders-col1 tbody');
  const tbody2 = document.querySelector('#leaders-col2 tbody');
  tbody1.innerHTML = '';
  tbody2.innerHTML = '';
  
  const remaining = players.slice(3, 50); // skip top 3, take next 47
  const col1Players = remaining.slice(0, 25); // ranks 4-28
  const col2Players = remaining.slice(25, 50); // ranks 29-53
  
  function renderRow(p, i, startRank) {
    const tr = document.createElement('tr');
    const rankNum = startRank + i;
    const promo = p.promo || '—';
    const letter = p.class || '';
    const badgeClass = `class-badge badge-${promo}`;
    
    tr.innerHTML = `
      <td style="width:50px">${arrowFor(p.direction)} ${rankNum}</td>
      <td>
        <div class="user-cell">
          <img class="avatar" src="${p.avatar || 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + p.username}" alt="${p.username}" />
          <div>
            <span class="username">${p.username}</span>
            <div class="muted">${p.firstName} ${p.lastName}</div>
          </div>
        </div>
      </td>
      <td style="width:80px">
        <span class="${badgeClass}">
          ${promo}${letter ? ' <span class="promo-in-badge">' + letter + '</span>' : ''}
        </span>
      </td>
      <td style="width:120px">
        ${p.current ? `
          <div>
            <strong>${p.current}</strong>
            <span class="muted" style="font-size:0.7rem">(${p.best ?? '—'})</span>
          </div>
        ` : '<span class="muted" style="font-size:0.75rem">N/A</span>'}
      </td>
      <td style="width:90px">
        ${p.history7days ? sparkline(p.history7days) : ''}
      </td>
      <td style="width:100px">
        ${p.stats ? renderWinLossDraw(p.stats) : '<span class="muted" style="font-size:0.7rem">N/A</span>'}
      </td>
    `;
    return tr;
  }
  
  col1Players.forEach((p, i) => tbody1.appendChild(renderRow(p, i, 4)));
  col2Players.forEach((p, i) => tbody2.appendChild(renderRow(p, i, 29)));
}

// Note: 'load' button removed — use the refresh button instead.

// Auto load default on open
window.addEventListener('load', ()=>{
  const limit = 50;
  loadClientOnly(limit).then(()=>{
    // start auto-refresh countdown after first successful load
    startAutoRefresh();
  });
});

// clicking the refresh button triggers immediate refresh and restarts countdown
document.addEventListener('click', (e)=>{
  const btn = e.target.closest && e.target.closest('#next-refresh');
  if(!btn) return;
  loadClientOnly(50).then(()=>{
    startAutoRefresh();
  });
});
