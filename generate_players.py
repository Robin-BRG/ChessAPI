import json
import random
from datetime import datetime

# Vrais joueurs du top 100 Chess.com
top_players = [
    ("Hikaru", "Nakamura", "GMHikaru"),
    ("Magnus", "Carlsen", "MagnusCarlsen"),
    ("Fabiano", "Caruana", "FabianoCaruana"),
    ("Wesley", "So", "Wesley_So"),
    ("Daniel", "Naroditsky", "DanielNaroditsky"),
    ("Levon", "Aronian", "LevonAronian"),
    ("Ian", "Nepomniachtchi", "lachesisQ"),
    ("Anish", "Giri", "AnishGiri"),
    ("Maxime", "Vachier-Lagrave", "MVL"),
    ("Alireza", "Firouzja", "Firouzja2003"),
    ("Viswanathan", "Anand", "viditchess"),
    ("Teimour", "Radjabov", "Teimour"),
    ("Shakhriyar", "Mamedyarov", "mishanp"),
    ("Vladimir", "Kramnik", "VladimirKramnik"),
    ("Alexander", "Grischuk", "Grischuk"),
    ("Sergey", "Karjakin", "SergeyKarjakin"),
    ("Richard", "Rapport", "RichardRapport"),
    ("Jan-Krzysztof", "Duda", "Polish_fighter3000"),
    ("Pentala", "Harikrishna", "Harikrishna"),
    ("David", "Navara", "DavidNavara"),
    ("Sam", "Shankland", "SamShankland"),
    ("Jeffery", "Xiong", "JefferyXiong"),
    ("Samuel", "Sevian", "SamuelSevian"),
    ("Parham", "Maghsoodloo", "parham"),
    ("Matthias", "Bluebaum", "Msb2"),
    ("Daniil", "Dubov", "DanielDubov"),
    ("Peter", "Svidler", "Svish"),
    ("Vladislav", "Artemiev", "Sibelephant"),
    ("Dmitry", "Andreikin", "AndreikinD"),
    ("Radoslaw", "Wojtaszek", "radekw"),
    ("David", "Anton", "DavidAntonGuijarro"),
    ("Vidit", "Gujrathi", "viditgujrathi"),
    ("Etienne", "Bacrot", "EtienneBacrot"),
    ("Nikita", "Vitiugov", "vitik"),
    ("Liviu-Dieter", "Nisipeanu", "Nisipeanu"),
    ("Wang", "Hao", "WangHao"),
    ("Yu", "Yangyi", "YuYangyi"),
    ("Bassem", "Amin", "BassemAmin"),
    ("Michael", "Adams", "MickyAdams"),
    ("Luke", "McShane", "LukeMcShane"),
    ("Gawain", "Jones", "GawainJones"),
    ("Romain", "Edouard", "RomainEdouard"),
    ("Jules", "Moussard", "JulesMoussard"),
    ("Christian", "Bauer", "ChristianBauer"),
    ("Tigran", "Gharamian", "TigranGharamian"),
    ("Robert", "Hovhannisyan", "RobertHovhannisyan"),
    ("Alexei", "Shirov", "AlexeiShirov"),
    ("Evgeny", "Bareev", "EvgenyBareev"),
    ("Boris", "Gelfand", "BorisGelfand"),
    ("Judit", "Polgar", "JuditPolgar"),
    ("Susan", "Polgar", "SusanPolgar"),
    ("Anna", "Muzychuk", "AnnaMuzychuk"),
    ("Mariya", "Muzychuk", "MariyaMuzychuk"),
]

# Charger les joueurs existants
with open('data/players.json', 'r', encoding='utf-8') as f:
    players = json.load(f)

print(f"Joueurs existants: {len(players)}")

# Ajouter 53 nouveaux joueurs
promos = ["2025", "2026", "2027", "2028", "2029"]
classes = ["A", "B", "C", "D"]
today = datetime.now().date().isoformat()

for i, (first_name, last_name, username) in enumerate(top_players[:53]):
    rapid_current = random.randint(800, 2800)
    rapid_best = rapid_current + random.randint(0, 200)
    blitz_current = rapid_current + random.randint(-300, 300)
    blitz_best = blitz_current + random.randint(0, 150)

    # Générer historique avec variation réaliste
    history = []
    base = rapid_current
    for _ in range(7):
        variation = random.randint(-30, 30)
        history.append(max(400, min(3000, base + variation)))
        base = history[-1]

    player = {
        "username": username,
        "firstName": first_name,
        "lastName": last_name,
        "promo": random.choice(promos),
        "class": random.choice(classes),
        "previousRank": len(players) + i + 1,
        "rapid": {
            "current": rapid_current,
            "best": rapid_best
        },
        "blitz": {
            "current": blitz_current,
            "best": blitz_best
        },
        "history7days": history,
        "lastHistoryUpdate": today,
        "stats": {
            "wins": random.randint(50, 500),
            "losses": random.randint(30, 400),
            "draws": random.randint(10, 100)
        },
        "avatar": f"https://images.chesscomfiles.com/uploads/v1/user/{random.randint(1000000, 9999999)}.{random.choice(['jpeg', 'png'])}"
    }

    players.append(player)

# Sauvegarder
with open('data/players.json', 'w', encoding='utf-8') as f:
    json.dump(players, f, indent=2, ensure_ascii=False)

print(f"Total joueurs: {len(players)}")
print("✓ 53 joueurs ajoutés avec succès!")
