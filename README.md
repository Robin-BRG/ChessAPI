# Chess.com Leaderboard API

Application Flask pour gérer un classement Chess.com intégré avec Slack.

## 📁 Structure du projet

```
ChessAPI/
├── README.md              # Cette documentation
├── requirements.txt       # Dépendances Python
├── api_server.py         # Serveur Flask principal
├── app/                  # Modules internes
│   ├── __init__.py
│   ├── config.py         # Configuration centralisée
│   ├── chess_api.py      # Wrapper API Chess.com
│   ├── chess_updater.py  # Logique de mise à jour automatique
│   └── scheduler.py      # Configuration APScheduler
├── static/               # Frontend (HTML/CSS/JS)
│   ├── index.html        # Page web du classement
│   ├── app.js            # Logique frontend
│   └── styles.css        # Styles CSS
└── data/                 # Données
    └── players.json      # Base de données des joueurs
```

## 🚀 Installation

### 1. Cloner le projet
```bash
cd /path/to/your/server
git clone <repository-url> ChessAPI
cd ChessAPI
```

### 2. Installer les dépendances Python
```bash
pip install -r requirements.txt
```

### 3. Configurer les variables d'environnement

#### Variables requises
- **`SLACK_BOT_TOKEN`** : Token Slack pour récupérer les informations des utilisateurs

#### Variables optionnelles (avec valeurs par défaut)
- **`UPDATE_INTERVAL_MINUTES`** : Intervalle de mise à jour automatique (défaut: 5)
- **`RATE_LIMIT_DELAY_SECONDS`** : Délai entre chaque joueur lors de la mise à jour (défaut: 1.0)
- **`SCHEDULER_ENABLED`** : Activer/désactiver le scheduler (défaut: true)

**Linux/Mac :**
```bash
export SLACK_BOT_TOKEN='xoxb-votre-token-slack'
export UPDATE_INTERVAL_MINUTES=5
export SCHEDULER_ENABLED=true
```

**Windows PowerShell :**
```powershell
$env:SLACK_BOT_TOKEN='xoxb-votre-token-slack'
$env:UPDATE_INTERVAL_MINUTES=5
$env:SCHEDULER_ENABLED='true'
```

**Windows CMD :**
```cmd
set SLACK_BOT_TOKEN=xoxb-votre-token-slack
set UPDATE_INTERVAL_MINUTES=5
set SCHEDULER_ENABLED=true
```

> ⚠️ **Important** : Ne jamais commiter le token dans le code !

### 4. Démarrer le serveur
```bash
python api_server.py
```

Le serveur démarre sur `http://0.0.0.0:5000`

## 🔌 Routes API

### Frontend
- **`GET /`** - Page web du classement (HTML)
- **`GET /static/<path>`** - Fichiers statiques (CSS, JS, images)
- **`GET /data/<path>`** - Fichiers de données (JSON)

### API - Gestion des joueurs
- **`POST /api/players`** - Mettre à jour la liste complète des joueurs
  - Body : `[{joueur1}, {joueur2}, ...]`
  - Retourne : `{"message": "players.json updated", "count": N}`

- **`POST /api/refresh`** - Déclencher manuellement la mise à jour de tous les joueurs
  - Récupère les derniers scores depuis Chess.com pour tous les joueurs
  - Utile pour tests et debug
  - Retourne : `{"success": true, "updated": N, "errors": N, "removed": N, "total": N}`

### API - Commandes Slack
- **`POST /slack/chessadd`** - Ajouter un joueur via Slack
  - Form data :
    - `text` : `<username_chess> <promo> <classe>`
    - `user_id` : ID Slack de l'utilisateur
  - Exemple : `magnuscarlsen 2027 A`
  - Retourne : Informations du joueur ajouté avec debug info
  - **Note** : Empêche l'ajout de plusieurs pseudos pour le même utilisateur (basé sur firstName + lastName)

- **`POST /slack/chessdelete`** - Supprimer son compte via Slack
  - Form data :
    - `user_id` : ID Slack de l'utilisateur
  - Supprime le compte associé au firstName + lastName de l'utilisateur
  - Retourne : Message de confirmation ou erreur

## 📱 Configuration Slack

### 1. Créer une Slack App
1. Allez sur https://api.slack.com/apps
2. Créez une nouvelle app
3. Notez le **Bot Token** (commence par `xoxb-`)

### 2. Configurer les permissions (Scopes)
Dans **OAuth & Permissions** > **Bot Token Scopes**, ajoutez :
- `users:read` - Pour récupérer le prénom/nom des utilisateurs

### 3. Créer les Slash Commands
Dans **Slash Commands**, créez deux commandes :

**Commande 1 : Ajouter un compte**
- **Command** : `/chessadd`
- **Request URL** : `https://votre-serveur.com/slack/chessadd`
- **Short Description** : Ajouter mon compte Chess.com au classement
- **Usage Hint** : `<username_chess> <promo> <classe>`

**Commande 2 : Supprimer un compte**
- **Command** : `/chessdelete`
- **Request URL** : `https://votre-serveur.com/slack/chessdelete`
- **Short Description** : Supprimer mon compte du classement
- **Usage Hint** : (aucun paramètre requis)

### 4. Installer l'app dans votre workspace
Dans **Install App**, cliquez sur "Install to Workspace"

## 📊 Format des données

### Structure de `players.json`
```json
[
  {
    "username": "magnuscarlsen",
    "firstName": "Magnus",
    "lastName": "Carlsen",
    "promo": "2027",
    "class": "A",
    "previousRank": 0,
    "current": 2941,
    "best": 2977,
    "history7days": [2900, 2920, 2935, 2941, 2945, 2940, 2941],
    "lastHistoryUpdate": "2025-01-15",
    "stats": {
      "wins": 107,
      "losses": 26,
      "draws": 95
    },
    "avatar": "https://images.chesscomfiles.com/..."
  }
]
```

**Notes sur les champs :**
- `history7days` : Historique des scores sur **7 jours réels** (1 valeur par jour)
- `lastHistoryUpdate` : Date (YYYY-MM-DD) de la dernière mise à jour de history7days
- La mise à jour automatique n'ajoute à `history7days` qu'**une fois par jour** maximum

### Calcul automatique de la classe
La classe (B1, B2, B3, M1, M2) est calculée automatiquement à partir de l'année de promo :

| Années restantes | Classe |
|------------------|--------|
| 5+ ans           | B1     |
| 4 ans            | B2     |
| 3 ans            | B3     |
| 2 ans            | M1     |
| 1 an             | M2     |
| Passé            | Diplômé|

**Exemple** : En 2025, si promo = 2027 → 2 ans restants → **M1**

### Mise à jour automatique des scores

Le serveur met à jour automatiquement les scores de TOUS les joueurs depuis Chess.com :

#### Fonctionnement
- **Fréquence** : Toutes les 5 minutes (configurable via `UPDATE_INTERVAL_MINUTES`)
- **Horaires** : Lundi-Vendredi, 6h-00h uniquement (économie ressources)
- **Données mises à jour** : current, best, stats (W/L/D), avatar, history7days, previousRank

#### Suppression automatique
Les joueurs dont la promo est dépassée (année < année actuelle) sont automatiquement supprimés :
- **Exemple** : En 2026, tous les joueurs avec promo 2025 ou moins sont supprimés
- **Raison** : Nettoyer les diplômés du classement

#### Rate limiting
- Délai de 1 seconde entre chaque joueur (configurable via `RATE_LIMIT_DELAY_SECONDS`)
- Respecte les limites de l'API Chess.com (300 requêtes/minute)

#### Désactivation
Pour désactiver la mise à jour automatique (tests, développement) :
```bash
export SCHEDULER_ENABLED=false
```

## 🎮 Utilisation

### Via Slack

**Ajouter votre compte :**
```
/chessadd magnuscarlsen 2027 A
```
Cela va :
1. Récupérer votre prénom/nom depuis Slack
2. Vérifier que vous n'avez pas déjà un compte (1 compte max par personne)
3. Récupérer les stats Chess.com (rating **Rapid**, W/L/D, avatar)
4. Calculer la classe automatiquement (ex: M1 pour promo 2027)
5. Ajouter la lettre de classe (A, B, C...)
6. Sauvegarder dans `data/players.json`

**Supprimer votre compte :**
```
/chessdelete
```
Supprime votre compte du classement (identifié par votre prénom/nom Slack)

### Via Web
Accédez à `http://votre-serveur.com` pour voir :
- 🥇 Podium (Top 3) avec photos et badges
- 📊 Classement complet (jusqu'à 50 joueurs)
- 📈 Historique des scores (7 jours)
- 📊 Statistiques W/L/D
- 🔄 Rafraîchissement automatique toutes les 5 minutes

## 🔧 Déploiement

### Sur votre serveur

1. **Installer Python 3.8+**
2. **Cloner et configurer le projet** (voir Installation ci-dessus)
3. **Configurer le token Slack** en variable d'environnement persistante
4. **Exposer les routes** :
   - Route principale : `/` (frontend)
   - Route Slack : `/slack/addchessaccount` (doit être accessible publiquement)
5. **Démarrer le serveur** :
   ```bash
   python api_server.py
   ```

### Avec un reverse proxy (nginx/apache)
Configurez un reverse proxy pour rediriger vers `localhost:5000`

**Exemple nginx :**
```nginx
location / {
    proxy_pass http://localhost:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### En production (recommandé)
Utilisez un serveur WSGI comme **Gunicorn** :
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 api_server:app
```

## 🐛 Dépannage

### Le token Slack ne fonctionne pas
- Vérifiez que `SLACK_BOT_TOKEN` est bien défini : `echo $SLACK_BOT_TOKEN`
- Vérifiez que le scope `users:read` est ajouté dans l'app Slack
- Réinstallez l'app dans votre workspace après avoir ajouté le scope

### Les noms ne s'affichent pas
Le serveur récupère `real_name` depuis Slack et le divise en prénom/nom. Si vide, le username Chess.com s'affiche.

### Les photos ne s'affichent pas
L'API Chess.com doit retourner un champ `avatar`. Si absent, une image générée automatiquement est utilisée.

### Le classement n'est pas trié
Le frontend trie automatiquement par score décroissant. Vérifiez la console JavaScript pour les erreurs.

## 📝 Notes importantes

- Les scores sont en mode **Rapid** (priorité), puis Blitz, puis Daily
- Le classement se rafraîchit automatiquement toutes les 5 minutes
- Maximum 50 joueurs affichés
- Les données sont stockées dans `data/players.json` (fichier JSON simple)

## 🔐 Sécurité

- ⚠️ Ne jamais commiter le token Slack dans le code
- ⚠️ Utiliser HTTPS en production
- ⚠️ Restreindre l'accès à l'endpoint `/api/players` si nécessaire

## 📞 Support

Pour toute question sur le déploiement ou la configuration, contactez le développeur.
