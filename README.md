# Chess.com Leaderboard API

Application Flask pour gérer un classement Chess.com intégré avec Slack.

## Structure du projet

```
ChessAPI/
├── api_server.py         # Serveur Flask principal
├── app/                  # Modules internes
│   ├── config.py         # Configuration centralisée
│   ├── chess_api.py      # Wrapper API Chess.com
│   ├── chess_updater.py  # Logique de mise à jour automatique
│   └── scheduler.py      # Configuration APScheduler
├── static/               # Frontend (HTML/CSS/JS)
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── data/
│   └── players.json      # Base de données des joueurs
└── requirements.txt
```

## Installation

```bash
git clone https://github.com/Robin-BRG/ChessAPI.git
cd ChessAPI
pip install -r requirements.txt
```

### Variables d'environnement

**Requises:**
- `SLACK_BOT_TOKEN` - Token Slack pour récupérer les informations utilisateurs

**Optionnelles:**
- `UPDATE_INTERVAL_MINUTES` (défaut: 5)
- `RATE_LIMIT_DELAY_SECONDS` (défaut: 1.0)
- `SCHEDULER_ENABLED` (défaut: true)

```bash
export SLACK_BOT_TOKEN='xoxb-votre-token'
python api_server.py
```

Serveur: `http://localhost:5000`

## Routes API

### Frontend
- `GET /` - Page web du classement
- `GET /static/<path>` - Fichiers statiques
- `GET /data/<path>` - Fichiers de données

### Gestion des joueurs
- `POST /api/players` - Mettre à jour la liste complète
- `POST /api/refresh` - Déclencher mise à jour manuelle

### Commandes Slack
- `POST /slack/chessadd` - Ajouter un joueur
  - Paramètres: `<username_chess> <promo> <classe>`
  - Exemple: `/chessadd magnuscarlsen 2027 A`

- `POST /slack/chessdelete` - Supprimer son compte
  - Aucun paramètre requis

## Format des données

```json
{
  "username": "magnuscarlsen",
  "firstName": "Magnus",
  "lastName": "Carlsen",
  "promo": "2027",
  "class": "A",
  "previousRank": 0,
  "rapid": {
    "current": 2941,
    "best": 2977
  },
  "blitz": {
    "current": 3200,
    "best": 3250
  },
  "history7days": [2900, 2920, 2935, 2941, 2945, 2940, 2941],
  "lastHistoryUpdate": "2025-01-15",
  "stats": {
    "wins": 107,
    "losses": 26,
    "draws": 95
  },
  "avatar": "https://images.chesscomfiles.com/..."
}
```

### Mise à jour automatique

- Fréquence: Toutes les 5 minutes (configurable)
- Horaires: Lundi-Vendredi, 6h-00h uniquement
- Suppression auto des promos expirées (année < année actuelle)
- Rate limiting: 1 seconde entre chaque joueur
- Historique: 1 valeur par jour, 7 jours max

### Calcul de la classe

| Années restantes | Classe |
|------------------|--------|
| 5+ ans           | B1     |
| 4 ans            | B2     |
| 3 ans            | B3     |
| 2 ans            | M1     |
| 1 an             | M2     |
| Passé            | Diplômé|

## Utilisation

### Commandes Slack

Ajouter un compte:
```
/chessadd magnuscarlsen 2027 A
```

Supprimer un compte:
```
/chessdelete
```

### Interface Web

Accédez à `http://localhost:5000` pour:
- Voir le podium (Top 3)
- Consulter le classement complet (50 joueurs max)
- Visualiser l'historique sur 7 jours
- Afficher les statistiques W/L/D

Le classement est basé sur le score Rapid. Le score Blitz est affiché à titre indicatif.
