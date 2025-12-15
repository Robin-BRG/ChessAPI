import express from 'express';
import cors from 'cors';
import fetch from 'node-fetch';
import fs from 'fs/promises';
import path from 'path';

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || 3000;
const DATA_PATH = path.join(process.cwd(), 'data', 'players.json');

// Simple in-memory cache to avoid hammering Chess.com during quick reloads
const cache = {
  ratings: {
    // key: category -> { timestamp, data }
  },
  profiles: {
    // username -> { timestamp, data }
  }
};
const CACHE_TTL = 15 * 1000; // 15 seconds

function mapCategoryToStatKey(category){
  switch(category){
    case 'live_blitz':
    case 'blitz': return 'chess_blitz';
    case 'live_rapid':
    case 'rapid': return 'chess_rapid';
    case 'bullet': return 'chess_bullet';
    case 'daily': return 'chess_daily';
    case 'puzzle_rush': return 'tactics';
    default: return 'chess_blitz';
  }
}

async function readPlayers(){
  const raw = await fs.readFile(DATA_PATH, 'utf8');
  return JSON.parse(raw);
}

async function fetchPlayerStats(username){
  const url = `https://api.chess.com/pub/player/${encodeURIComponent(username)}/stats`;
  const res = await fetch(url);
  if(!res.ok) return null;
  return res.json();
}

async function fetchPlayerProfile(username){
  // simple cache per username
  const cached = cache.profiles[username];
  const now = Date.now();
  if(cached && (now - cached.timestamp) < (60 * 1000)){
    return cached.data;
  }

  const url = `https://api.chess.com/pub/player/${encodeURIComponent(username)}`;
  const res = await fetch(url);
  if(!res.ok) return null;
  const data = await res.json();
  cache.profiles[username] = { timestamp: now, data };
  return data;
}

app.get('/api/players', async (req, res) => {
  try{
    const players = await readPlayers();
    res.json(players);
  }catch(e){
    res.status(500).json({ error: e.message });
  }
});

// Returns players augmented with current and best rating for selected category
app.get('/api/ratings', async (req, res) => {
  const category = req.query.category || 'blitz';
  const statKey = mapCategoryToStatKey(category);

  // cache key by category
  const cacheEntry = cache.ratings[category];
  if(cacheEntry && (Date.now() - cacheEntry.timestamp) < CACHE_TTL){
    return res.json(cacheEntry.data);
  }

  try{
    const players = await readPlayers();

    // For each player, fetch stats and extract rating
    const promises = players.map(async p => {
      const [stats, profile] = await Promise.all([
        fetchPlayerStats(p.username).catch(()=>null),
        fetchPlayerProfile(p.username).catch(()=>null)
      ]);

      let current = null, best = null;
      if(stats && stats[statKey]){
        const entry = stats[statKey];
        current = entry.last?.rating ?? entry.rating ?? null;
        best = entry.best?.rating ?? null;
      }

      const avatar = profile?.avatar ?? null;

      // compare with lastScores from DB, if present
      const lastKnown = (p.lastScores && (p.lastScores[category] ?? p.lastScores[statKey])) ?? null;
      let direction = 'neutral';
      if(lastKnown != null && current != null){
        if(current > lastKnown) direction = 'up';
        else if(current < lastKnown) direction = 'down';
      }

      return {
        username: p.username,
        firstName: p.firstName,
        lastName: p.lastName,
        class: p.class,
        best: best,
        current: current,
        lastKnown: lastKnown,
        direction,
        avatar
      };
    });

    const results = await Promise.all(promises);

    // sort by current desc (nulls go to bottom)
    results.sort((a,b)=> (b.current ?? -Infinity) - (a.current ?? -Infinity));

    cache.ratings[category] = { timestamp: Date.now(), data: results };

    res.json(results);
  }catch(e){
    res.status(500).json({ error: e.message });
  }
});

// Serve static frontend files for convenience
app.use(express.static(process.cwd()));

app.listen(PORT, ()=>{
  console.log(`Server started on http://localhost:${PORT}`);
});
