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

// Calculer la classe (B1, B2, B3, M1, M2) à partir de l'année de promo
function calculateClass(promoYear) {
  if (!promoYear || promoYear === '—') return '—';

  const currentYear = new Date().getFullYear();
  const yearsUntilGraduation = parseInt(promoYear) - currentYear;

  if (yearsUntilGraduation >= 5) return 'B1';
  if (yearsUntilGraduation === 4) return 'B2';
  if (yearsUntilGraduation === 3) return 'B3';
  if (yearsUntilGraduation === 2) return 'M1';
  if (yearsUntilGraduation === 1) return 'M2';
  if (yearsUntilGraduation <= 0) return 'Diplômé';

  return '—';
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

    // IMPORTANT: Trier les joueurs par score Rapid décroissant
    players.sort((a, b) => ((b.rapid?.current || 0) - (a.rapid?.current || 0)));

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
    const calculatedClass = calculateClass(p.promo);
    // Ajouter la lettre de classe (A, B, C, etc.) en majuscule si elle existe
    const classLetter = p.class ? p.class.toUpperCase().trim() : '';
    const fullClass = classLetter ? `${calculatedClass} ${classLetter}` : calculatedClass;
    const badgeClass = `class-badge badge-${calculatedClass}`;

    // Afficher firstName + lastName s'ils existent, sinon username
    const displayName = (p.firstName && p.lastName)
      ? `${p.firstName} ${p.lastName}`
      : p.username;

    const wrapper = document.createElement('div');
    wrapper.className = `podium-wrapper rank-${rankNum}`;
    const defaultAvatar = 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + p.username;
    const avatarUrl = p.avatar || defaultAvatar;
    wrapper.innerHTML = `
      <img class="podium-avatar-top" src="${avatarUrl}" alt="${p.username}" onerror="this.src='${defaultAvatar}'" />
      <div class="podium-card">
        <div class="podium-medal">${medals[i]}</div>
        <div class="podium-bottom">
          <div style="display: flex; align-items: center; gap: 0.3rem; justify-content: center; flex-wrap: wrap;">
            <div class="podium-name">${displayName}</div>
            <span class="${badgeClass}" style="font-size: 0.65rem; padding: 2px 5px;">${fullClass}</span>
          </div>
          <div class="podium-score">
            <div class="score-group">
              <svg class="score-icon rapid-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M11.97 14.63C11.07 14.63 10.1 13.9 10.47 12.4L11.5 8H12.5L13.53 12.37C13.9 13.9 12.9 14.64 11.96 14.64L11.97 14.63ZM12 22.5C6.77 22.5 2.5 18.23 2.5 13C2.5 7.77 6.77 3.5 12 3.5C17.23 3.5 21.5 7.77 21.5 13C21.5 18.23 17.23 22.5 12 22.5ZM12 19.5C16 19.5 18.5 17 18.5 13C18.5 9 16 6.5 12 6.5C8 6.5 5.5 9 5.5 13C5.5 17 8 19.5 12 19.5ZM10.5 5.23V1H13.5V5.23H10.5ZM15.5 2H8.5C8.5 0.3 8.93 0 12 0C15.07 0 15.5 0.3 15.5 2Z"/></svg>
              <span class="score-value">${p.rapid?.current ?? '—'}</span>
              <span class="score-best">(${p.rapid?.best ?? '—'})</span>
            </div>
            <div class="score-group">
              <svg class="score-icon blitz-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M5.77002 15C4.74002 15 4.40002 14.6 4.57002 13.6L6.10002 3.4C6.27002 2.4 6.73002 2 7.77002 2H13.57C14.6 2 14.9 2.4 14.64 3.37L11.41 15H5.77002ZM18.83 9C19.86 9 20.03 9.33 19.4 10.13L9.73002 22.86C8.50002 24.49 8.13002 24.33 8.46002 22.29L10.66 8.99L18.83 9Z"/></svg>
              <span class="score-value">${p.blitz?.current ?? '—'}</span>
              <span class="score-best">(${p.blitz?.best ?? '—'})</span>
            </div>
          </div>
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

  // Toujours afficher exactement 25 lignes par colonne (50 total - 3 podium = 47, réparti en 25 + 22)
  const ROWS_PER_COL = 25;
  const col1Players = remaining.slice(0, ROWS_PER_COL); // ranks 4-28 (25 joueurs max)
  const col2Players = remaining.slice(ROWS_PER_COL, ROWS_PER_COL * 2); // ranks 29-53 (25 joueurs max)

  function renderRow(p, i, startRank) {
    const tr = document.createElement('tr');
    const rankNum = startRank + i;

    // Si pas de joueur, créer une ligne vide
    if (!p) {
      tr.innerHTML = `
        <td style="width:50px">${rankNum}</td>
        <td><div class="user-cell"><span class="muted" style="font-size:0.75rem">—</span></div></td>
        <td style="width:80px"><span class="muted">—</span></td>
        <td style="width:120px"><span class="muted">—</span></td>
        <td style="width:90px"></td>
        <td style="width:100px"></td>
      `;
      return tr;
    }

    const promo = p.promo || '—';
    const calculatedClass = calculateClass(p.promo);
    // Ajouter la lettre de classe (A, B, C, etc.) en majuscule si elle existe
    const classLetter = p.class ? p.class.toUpperCase().trim() : '';
    const fullClass = classLetter ? `${calculatedClass} ${classLetter}` : calculatedClass;
    const badgeClass = `class-badge badge-${calculatedClass}`;
    const defaultAvatar = 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + p.username;

    tr.innerHTML = `
      <td style="width:50px">${arrowFor(p.direction)} ${rankNum}</td>
      <td>
        <div class="user-cell">
          <img class="avatar" src="${p.avatar || defaultAvatar}" alt="${p.username}" onerror="this.src='${defaultAvatar}'" />
          <div>
            <span class="username">${p.username}</span>
            <div class="muted">${p.firstName} ${p.lastName}</div>
          </div>
        </div>
      </td>
      <td style="width:80px">
        <span class="${badgeClass}">
          ${fullClass}
        </span>
      </td>
      <td style="width:180px">
        <div class="score-container">
          <div class="score-row">
            <svg class="score-icon rapid-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M11.97 14.63C11.07 14.63 10.1 13.9 10.47 12.4L11.5 8H12.5L13.53 12.37C13.9 13.9 12.9 14.64 11.96 14.64L11.97 14.63ZM12 22.5C6.77 22.5 2.5 18.23 2.5 13C2.5 7.77 6.77 3.5 12 3.5C17.23 3.5 21.5 7.77 21.5 13C21.5 18.23 17.23 22.5 12 22.5ZM12 19.5C16 19.5 18.5 17 18.5 13C18.5 9 16 6.5 12 6.5C8 6.5 5.5 9 5.5 13C5.5 17 8 19.5 12 19.5ZM10.5 5.23V1H13.5V5.23H10.5ZM15.5 2H8.5C8.5 0.3 8.93 0 12 0C15.07 0 15.5 0.3 15.5 2Z"/></svg>
            <strong>${p.rapid?.current ?? '—'}</strong>
            <span class="muted" style="font-size:0.7rem">(${p.rapid?.best ?? '—'})</span>
          </div>
          <div class="score-row">
            <svg class="score-icon blitz-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M5.77002 15C4.74002 15 4.40002 14.6 4.57002 13.6L6.10002 3.4C6.27002 2.4 6.73002 2 7.77002 2H13.57C14.6 2 14.9 2.4 14.64 3.37L11.41 15H5.77002ZM18.83 9C19.86 9 20.03 9.33 19.4 10.13L9.73002 22.86C8.50002 24.49 8.13002 24.33 8.46002 22.29L10.66 8.99L18.83 9Z"/></svg>
            <strong>${p.blitz?.current ?? '—'}</strong>
            <span class="muted" style="font-size:0.7rem">(${p.blitz?.best ?? '—'})</span>
          </div>
        </div>
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

  // Remplir la colonne 1 (toujours 25 lignes)
  for (let i = 0; i < ROWS_PER_COL; i++) {
    tbody1.appendChild(renderRow(col1Players[i], i, 4));
  }

  // Remplir la colonne 2 (toujours 25 lignes)
  for (let i = 0; i < ROWS_PER_COL; i++) {
    tbody2.appendChild(renderRow(col2Players[i], i, 4 + ROWS_PER_COL));
  }
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
