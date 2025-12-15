# Chess.com Leaderboard

Système de leaderboard pour suivre les classements Chess.com avec historique sur 7 jours.

## 📁 Architecture

### Système à 2 composantes :

1. **Script Python** (`update_leaderboard.py`) - Mise à jour quotidienne
   - Se lance tous les jours à 6h du matin
   - Récupère les profils depuis Chess.com API (limite 300 appels/minute)
   - Calcule le nouveau classement
   - Met à jour `previousRank` pour les flèches
   - Maintient l'historique sur 7 jours
   - Sauvegarde dans `data/players.json`

2. **Interface HTML/JS** - Affichage en temps réel
   - Lit simplement le JSON (ultra rapide)
   - Pas d'appels API depuis le navigateur
   - Auto-refresh toutes les 5 minutes
   - Affiche podium + tableau 2 colonnes
   - Sparklines avec historique 7 jours

## 🚀 Installation

### 1. Configuration de la tâche planifiée

Exécute en tant qu'administrateur :

```powershell
cd C:\Users\robin\Code\ChessAPI
.\setup_scheduled_task.ps1
```

Cela crée une tâche Windows qui lance `update_leaderboard.py` tous les jours à 6h.

### 2. Test manuel du script

Pour tester sans attendre 6h du matin :

```powershell
py -3 update_leaderboard.py
```

### 3. Lancer le serveur web

```powershell
py -3 -m http.server 8000
```

Puis ouvre : http://localhost:8000

## 📝 Gestion des joueurs

### Ajouter un joueur

Édite `data/players.json` et ajoute :

```json
{
  "username": "username_chesscom",
  "firstName": "Prénom",
  "lastName": "Nom",
  "promo": "B1",
  "class": "A",
  "previousRank": 99,
  "history7days": [],
  "current": null,
  "best": null
}
```

**Champs :**
- `username` : identifiant Chess.com exact
- `promo` : B1/B2/B3/M1/M2
- `class` : A/B/C/D
- `previousRank` : rang précédent (sera mis à jour auto)
- `history7days` : historique 7 jours (sera rempli auto)

### Limites API Chess.com

- **300 appels/minute max**
- Le script gère automatiquement le rate limiting
- Pour >250 joueurs, le script fait des pauses de 60s

## 🧪 Tests avec données fake

Pour tester le rendu sans appeler Chess.com :

1. Édite `data/players.json`
2. Remplis manuellement `current`, `best`, `history7days`
3. Varie les `previousRank` pour voir les flèches bouger
4. Recharge la page

**Exemple de données fake :**

```json
{
  "username": "test_player",
  "firstName": "Test",
  "lastName": "Player",
  "promo": "B1",
  "class": "A",
  "previousRank": 5,
  "history7days": [2900, 2920, 2910, 2950, 2940, 2960, 2980],
  "current": 2980,
  "best": 3050
}
```

## 📊 Fonctionnalités

- ✅ Podium visuel pour top 3
- ✅ Tableau 2 colonnes (ranks 4-50)
- ✅ Badges promo/classe colorés
- ✅ Flèches de progression (↑↓=)
- ✅ Sparklines 7 jours avec couleurs :
  - 🟢 Vert : progression >2%
  - 🟠 Orange : stable (-2% à +2%)
  - 🔴 Rouge : baisse <-2%
- ✅ Auto-refresh toutes les 5 minutes
- ✅ Design ultra-compact (tout tient sans scroll)

## 🛠️ Commandes utiles

### Tester la tâche planifiée maintenant

```powershell
Start-ScheduledTask -TaskName "ChessLeaderboardUpdate"
```

### Voir les infos de la dernière exécution

```powershell
Get-ScheduledTaskInfo -TaskName "ChessLeaderboardUpdate"
```

### Désactiver la tâche planifiée

```powershell
Disable-ScheduledTask -TaskName "ChessLeaderboardUpdate"
```

### Supprimer la tâche planifiée

```powershell
Unregister-ScheduledTask -TaskName "ChessLeaderboardUpdate"
```

## 📈 Workflow quotidien

```
06:00 → Tâche Windows se lance
      → update_leaderboard.py s'exécute
      → Récupère les profils Chess.com (respects rate limits)
      → Calcule nouveau classement
      → Met à jour previousRank
      → Ajoute scores à history7days
      → Sauvegarde players.json
      
Toute la journée → HTML lit players.json
                 → Rafraîchit toutes les 5 min
                 → Affichage instantané (pas d'API calls)
```

## 🐛 Troubleshooting

**Problème : Joueurs avec "Pas de données"**
- Vérifie que le username Chess.com est exact
- Teste manuellement : https://api.chess.com/pub/player/USERNAME/stats
- Certains comptes privés ne retournent rien

**Problème : Tâche planifiée ne se lance pas**
- Vérifie dans Planificateur de tâches Windows
- Assure-toi que le chemin Python est correct
- Regarde les logs dans l'historique de la tâche

**Problème : Rate limit dépassé**
- Le script pause automatiquement à 300 calls/min
- Pour >300 joueurs, utilise plusieurs runs dans la journée
