# Configuration centralisée pour ChessAPI
import os
from pathlib import Path
import threading

# Chemins
BASE_DIR = Path(__file__).parent.parent  # Remonter au dossier racine (ChessAPI/)
JSON_PATH = BASE_DIR / "data" / "players.json"

# Lock pour protéger l'accès concurrent à players.json
PLAYERS_JSON_LOCK = threading.Lock()

# Slack
SLACK_BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN')

# Chess.com API
CHESS_API_BASE_URL = "https://api.chess.com/pub/player"
CHESS_API_TIMEOUT = 5
CHESS_API_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# Scheduler
UPDATE_INTERVAL_MINUTES = int(os.environ.get('UPDATE_INTERVAL_MINUTES', 5))
RATE_LIMIT_DELAY_SECONDS = float(os.environ.get('RATE_LIMIT_DELAY_SECONDS', 1.0))

# Horaires de fonctionnement
SCHEDULER_ENABLED = os.environ.get('SCHEDULER_ENABLED', 'true').lower() == 'true'
WORKING_DAYS = [0, 1, 2, 3, 4]  # Lundi-Vendredi (0=lundi, 6=dimanche)
START_HOUR = 6   # 6h du matin
END_HOUR = 0     # Minuit (00h)
