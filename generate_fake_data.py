"""
Génère des données fake pour tester le leaderboard avec des courbes variées
"""

import json
import random
from pathlib import Path

JSON_PATH = Path(__file__).parent / "data" / "players.json"

def generate_varied_history(base_score):
    """Génère un historique 7 jours avec patterns variés"""
    patterns = [
        # Forte hausse progressive
        lambda b: [b - 80, b - 60, b - 40, b - 20, b - 10, b - 5, b],
        # Forte baisse progressive
        lambda b: [b + 80, b + 60, b + 40, b + 20, b + 10, b + 5, b],
        # Volatil en V (baisse puis remontée)
        lambda b: [b, b - 30, b - 50, b - 60, b - 40, b - 20, b],
        # Volatil en montagne (hausse puis baisse)
        lambda b: [b, b + 30, b + 50, b + 60, b + 40, b + 20, b],
        # Quasi stagnant avec micro variations
        lambda b: [b - 2, b + 1, b - 1, b, b + 2, b - 1, b],
        # Escalier montant
        lambda b: [b - 70, b - 60, b - 45, b - 30, b - 20, b - 10, b],
        # Escalier descendant
        lambda b: [b + 70, b + 60, b + 45, b + 30, b + 20, b + 10, b],
        # Zig-zag violent
        lambda b: [b, b + 40, b - 20, b + 30, b - 40, b + 10, b],
        # Chute brutale récente
        lambda b: [b + 50, b + 48, b + 45, b + 40, b + 10, b + 5, b],
        # Hausse brutale récente
        lambda b: [b - 50, b - 48, b - 45, b - 40, b - 10, b - 5, b],
    ]
    
    pattern = random.choice(patterns)
    return [max(100, score) for score in pattern(base_score)]

def generate_win_loss_draw():
    """Génère des stats W/L/D réalistes"""
    total = random.randint(50, 500)
    win_rate = random.uniform(0.35, 0.65)
    draw_rate = random.uniform(0.15, 0.35)
    
    wins = int(total * win_rate)
    draws = int(total * draw_rate)
    losses = total - wins - draws
    
    return {"wins": wins, "losses": losses, "draws": draws}

# Noms français fictifs pour l'école
fake_players = [
    {"firstName": "Alexandre", "lastName": "Dubois", "promo": "M1", "class": "A"},
    {"firstName": "Sophie", "lastName": "Martin", "promo": "B2", "class": "B"},
    {"firstName": "Lucas", "lastName": "Bernard", "promo": "M2", "class": "C"},
    {"firstName": "Emma", "lastName": "Petit", "promo": "B1", "class": "A"},
    {"firstName": "Thomas", "lastName": "Durand", "promo": "B3", "class": "D"},
    {"firstName": "Léa", "lastName": "Moreau", "promo": "M1", "class": "B"},
    {"firstName": "Hugo", "lastName": "Laurent", "promo": "B2", "class": "A"},
    {"firstName": "Chloé", "lastName": "Simon", "promo": "M2", "class": "C"},
    {"firstName": "Nathan", "lastName": "Michel", "promo": "B1", "class": "D"},
    {"firstName": "Camille", "lastName": "Lefebvre", "promo": "B3", "class": "A"},
    {"firstName": "Antoine", "lastName": "Leroy", "promo": "M1", "class": "C"},
    {"firstName": "Julie", "lastName": "Roux", "promo": "B2", "class": "B"},
    {"firstName": "Mathis", "lastName": "David", "promo": "M2", "class": "D"},
    {"firstName": "Sarah", "lastName": "Bertrand", "promo": "B1", "class": "A"},
    {"firstName": "Maxime", "lastName": "Morel", "promo": "B3", "class": "C"},
    {"firstName": "Clara", "lastName": "Fournier", "promo": "M1", "class": "B"},
    {"firstName": "Louis", "lastName": "Girard", "promo": "B2", "class": "D"},
    {"firstName": "Inès", "lastName": "Bonnet", "promo": "M2", "class": "A"},
    {"firstName": "Théo", "lastName": "Dupont", "promo": "B1", "class": "C"},
    {"firstName": "Manon", "lastName": "Lambert", "promo": "B3", "class": "B"},
    {"firstName": "Arthur", "lastName": "Fontaine", "promo": "M1", "class": "D"},
    {"firstName": "Jade", "lastName": "Rousseau", "promo": "B2", "class": "A"},
    {"firstName": "Gabriel", "lastName": "Vincent", "promo": "M2", "class": "C"},
    {"firstName": "Lola", "lastName": "Muller", "promo": "B1", "class": "B"},
    {"firstName": "Raphaël", "lastName": "Lefevre", "promo": "B3", "class": "D"},
    {"firstName": "Louise", "lastName": "Meyer", "promo": "M1", "class": "A"},
    {"firstName": "Tom", "lastName": "Denis", "promo": "B2", "class": "C"},
    {"firstName": "Zoé", "lastName": "Gauthier", "promo": "M2", "class": "B"},
    {"firstName": "Enzo", "lastName": "Robert", "promo": "B1", "class": "D"},
    {"firstName": "Anaïs", "lastName": "Blanc", "promo": "B3", "class": "A"},
    {"firstName": "Noah", "lastName": "Garnier", "promo": "M1", "class": "C"},
    {"firstName": "Eva", "lastName": "Faure", "promo": "B2", "class": "B"},
    {"firstName": "Adam", "lastName": "Andre", "promo": "M2", "class": "D"},
    {"firstName": "Lina", "lastName": "Mercier", "promo": "B1", "class": "A"},
    {"firstName": "Jules", "lastName": "Blanc", "promo": "B3", "class": "C"},
    {"firstName": "Mila", "lastName": "Gauthier", "promo": "M1", "class": "B"},
    {"firstName": "Ethan", "lastName": "Perrin", "promo": "B2", "class": "D"},
    {"firstName": "Lily", "lastName": "Morin", "promo": "M2", "class": "A"},
    {"firstName": "Paul", "lastName": "Robin", "promo": "B1", "class": "C"},
    {"firstName": "Alice", "lastName": "Clement", "promo": "B3", "class": "B"},
    {"firstName": "Baptiste", "lastName": "Masson", "promo": "M1", "class": "D"},
    {"firstName": "Rose", "lastName": "Sanchez", "promo": "B2", "class": "A"},
    {"firstName": "Victor", "lastName": "Giraud", "promo": "M2", "class": "C"},
    {"firstName": "Nina", "lastName": "Nicolas", "promo": "B1", "class": "B"},
    {"firstName": "Oscar", "lastName": "Blanchard", "promo": "B3", "class": "D"},
    {"firstName": "Juliette", "lastName": "Renard", "promo": "M1", "class": "A"},
    {"firstName": "Timéo", "lastName": "Leclerc", "promo": "B2", "class": "C"},
    {"firstName": "Romane", "lastName": "Barbier", "promo": "M2", "class": "B"},
    {"firstName": "Maël", "lastName": "Arnaud", "promo": "B1", "class": "D"},
    {"firstName": "Margaux", "lastName": "Martinez", "promo": "B3", "class": "A"},
]

def main():
    print("🎲 Génération de données fake pour tests...")
    
    players = []
    base_scores = sorted([random.randint(1800, 3000) for _ in range(50)], reverse=True)
    
    for i, (player, score) in enumerate(zip(fake_players, base_scores)):
        username = f"{player['firstName'].lower()}{player['lastName'].lower()}{random.randint(100,999)}"
        
        players.append({
            "username": username,
            "firstName": player["firstName"],
            "lastName": player["lastName"],
            "promo": player["promo"],
            "class": player["class"],
            "previousRank": random.randint(1, 50),  # Rank précédent aléatoire
            "current": score,
            "best": score + random.randint(10, 150),
            "history7days": generate_varied_history(score),
            "stats": generate_win_loss_draw()
        })
    
    save_path = JSON_PATH
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(players, f, indent=2, ensure_ascii=False)
    
    print(f"✅ {len(players)} joueurs fake générés dans {save_path}")
    print("📊 Courbes variées: hausse, baisse, volatilité, stagnation...")

if __name__ == "__main__":
    main()
