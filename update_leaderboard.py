"""
Script pour mettre à jour le leaderboard Chess.com
- Récupère les profils depuis Chess.com API (limite 300/min)
- Calcule le nouveau classement
- Met à jour previousRank
- Garde l'historique 7 jours
- Sauvegarde dans players.json

Usage: py -3 update_leaderboard.py
"""

import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
JSON_PATH = Path(__file__).parent / "data" / "players.json"
CHESS_COM_API = "https://api.chess.com/pub/player"
RATE_LIMIT_PER_MINUTE = 300
BATCH_SIZE = 250  # Pour rester sous 300/min, on traite par lots

def load_players():
    """Charge la liste des joueurs depuis le JSON"""
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_players(players):
    """Sauvegarde la liste mise à jour dans le JSON"""
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(players, f, indent=2, ensure_ascii=False)
    print(f"✅ {len(players)} joueurs sauvegardés dans {JSON_PATH}")

def fetch_chess_com_rating(username):
    """Récupère le rating rapid depuis Chess.com"""
    try:
        url = f"{CHESS_COM_API}/{username}/stats"
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 ChessLeaderboard/1.0'
        })
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            rapid = data.get('chess_rapid', {})
            current = rapid.get('last', {}).get('rating')
            best = rapid.get('best', {}).get('rating')
            
            return {
                'current': current,
                'best': best,
                'success': current is not None
            }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"  ⚠️  {username}: profil introuvable")
        else:
            print(f"  ⚠️  {username}: erreur HTTP {e.code}")
        return {'current': None, 'best': None, 'success': False}
    except Exception as e:
        print(f"  ⚠️  {username}: {str(e)}")
        return {'current': None, 'best': None, 'success': False}

def fetch_all_ratings(players):
    """Récupère les ratings pour tous les joueurs avec rate limiting"""
    total = len(players)
    print(f"\n🔄 Récupération des ratings pour {total} joueurs...")
    
    updated_players = []
    start_time = time.time()
    calls_this_minute = 0
    minute_start = time.time()
    
    for i, player in enumerate(players, 1):
        # Rate limiting: max 300 calls par minute
        if calls_this_minute >= RATE_LIMIT_PER_MINUTE:
            elapsed = time.time() - minute_start
            if elapsed < 60:
                sleep_time = 60 - elapsed
                print(f"  ⏳ Rate limit: pause de {sleep_time:.1f}s...")
                time.sleep(sleep_time)
            calls_this_minute = 0
            minute_start = time.time()
        
        username = player['username']
        print(f"  [{i}/{total}] {username}...", end=' ')
        
        rating_data = fetch_chess_com_rating(username)
        calls_this_minute += 1
        
        if rating_data['success']:
            player['current'] = rating_data['current']
            player['best'] = rating_data['best']
            print(f"✓ {rating_data['current']}")
        else:
            # Garde les anciennes valeurs si échec
            print(f"✗ (garde ancienne valeur)")
        
        updated_players.append(player)
        
        # Petit délai entre chaque appel pour être gentil
        time.sleep(0.2)
    
    elapsed = time.time() - start_time
    print(f"\n✅ Récupération terminée en {elapsed:.1f}s")
    
    return updated_players

def update_rankings(players):
    """
    Met à jour le classement:
    1. Sauvegarde les ranks actuels comme previousRank
    2. Trie par score
    3. Assigne les nouveaux ranks
    4. Met à jour l'historique 7 jours
    """
    print("\n📊 Mise à jour du classement...")
    
    # Créer un mapping username -> ancien rank (avant tri)
    old_ranks = {}
    for i, p in enumerate(players, 1):
        old_ranks[p['username']] = i
    
    # Trier par score décroissant (les joueurs sans score en fin)
    players_sorted = sorted(
        players,
        key=lambda p: p.get('current') or 0,
        reverse=True
    )
    
    # Mettre à jour les ranks et l'historique
    today_score = {}
    for i, player in enumerate(players_sorted, 1):
        username = player['username']
        
        # previousRank = l'ancien rank avant ce tri
        player['previousRank'] = old_ranks.get(username, i)
        
        # Historique 7 jours
        current_score = player.get('current')
        if current_score:
            history = player.get('history7days', [])
            
            # Ajouter le score d'aujourd'hui
            history.append(current_score)
            
            # Garder seulement les 7 derniers jours
            if len(history) > 7:
                history = history[-7:]
            
            player['history7days'] = history
        
        # Debug info
        direction = ""
        if player['previousRank'] > i:
            direction = f"↑ (+{player['previousRank'] - i})"
        elif player['previousRank'] < i:
            direction = f"↓ (-{i - player['previousRank']})"
        else:
            direction = "="
        
        current_score = player.get('current')
        score_str = str(current_score) if current_score else 'N/A'
        print(f"  #{i:2d} {player['firstName']:12s} {player['lastName']:15s} "
              f"{score_str:>4s}  {direction}")
    
    print(f"\n✅ Classement mis à jour")
    return players_sorted

def main():
    """Point d'entrée principal"""
    print("=" * 60)
    print("🏆 Mise à jour du leaderboard Chess.com")
    print("=" * 60)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Charger les joueurs
    players = load_players()
    print(f"📂 {len(players)} joueurs chargés depuis {JSON_PATH}")
    
    # 2. Récupérer les ratings depuis Chess.com
    players = fetch_all_ratings(players)
    
    # 3. Mettre à jour le classement
    players = update_rankings(players)
    
    # 4. Sauvegarder
    save_players(players)
    
    print("\n" + "=" * 60)
    print("✨ Mise à jour terminée avec succès!")
    print("=" * 60)

if __name__ == "__main__":
    main()
