"""
Version de test rapide avec seulement 3 joueurs
"""
import json
from pathlib import Path
import urllib.request

JSON_PATH = Path(__file__).parent / "data" / "players.json"

def fetch_rating(username):
    """Récupère le rating rapid depuis Chess.com"""
    try:
        url = f"https://api.chess.com/pub/player/{username}/stats"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            rapid = data.get('chess_rapid', {})
            current = rapid.get('last', {}).get('rating')
            best = rapid.get('best', {}).get('rating')
            return {'current': current, 'best': best, 'success': current is not None}
    except Exception as e:
        print(f"  ⚠️  {username}: {str(e)}")
        return {'current': None, 'best': None, 'success': False}

# Charger
with open(JSON_PATH, 'r', encoding='utf-8') as f:
    players = json.load(f)

print(f"📂 {len(players)} joueurs dans le JSON")
print("\n🧪 TEST avec les 3 premiers joueurs:\n")

# Tester les 3 premiers
for i, p in enumerate(players[:3], 1):
    username = p['username']
    print(f"[{i}/3] {username}...", end=' ')
    result = fetch_rating(username)
    if result['success']:
        print(f"✓ {result['current']}")
        p['current'] = result['current']
        p['best'] = result['best']
        # Ajouter à l'historique
        history = p.get('history7days', [])
        history.append(result['current'])
        if len(history) > 7:
            history = history[-7:]
        p['history7days'] = history
    else:
        print(f"✗")

print(f"\n✅ Mise à jour terminée")
print("\nAperçu des 3 premiers:")
for p in players[:3]:
    print(f"  {p['firstName']} {p['lastName']}: {p.get('current', 'N/A')} (history: {len(p.get('history7days', []))} jours)")
