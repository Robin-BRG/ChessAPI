# Wrapper réutilisable pour l'API Chess.com
import requests
import logging
from .config import CHESS_API_BASE_URL, CHESS_API_TIMEOUT, CHESS_API_HEADERS

logger = logging.getLogger(__name__)

def fetch_player_profile(username):
    """
    Récupère le profil Chess.com (avatar).

    Args:
        username: Username Chess.com

    Returns:
        dict avec les données du profil ou None en cas d'erreur
    """
    try:
        url = f'{CHESS_API_BASE_URL}/{username}'
        resp = requests.get(url, timeout=CHESS_API_TIMEOUT, headers=CHESS_API_HEADERS)
        if resp.status_code == 200:
            return resp.json()
        logger.warning(f"Profile API failed for {username}: {resp.status_code}")
        return None
    except Exception as e:
        logger.error(f"Exception fetching profile for {username}: {e}")
        return None

def fetch_player_stats(username):
    """
    Récupère les stats Chess.com pour un joueur (Rapid ET Blitz).

    Args:
        username: Username Chess.com

    Returns:
        dict avec {rapid{current, best}, blitz{current, best}, stats{wins/losses/draws}, avatar}
        ou None en cas d'erreur
    """
    result = {
        "rapid": {"current": 0, "best": 0},
        "blitz": {"current": 0, "best": 0},
        "stats": {"wins": 0, "losses": 0, "draws": 0},
        "avatar": ""
    }

    # 1. Récupérer avatar
    profile = fetch_player_profile(username)
    if profile:
        result["avatar"] = profile.get('avatar', '')

    # 2. Récupérer stats
    try:
        url = f'{CHESS_API_BASE_URL}/{username}/stats'
        resp = requests.get(url, timeout=CHESS_API_TIMEOUT, headers=CHESS_API_HEADERS)
        if resp.status_code == 200:
            stats = resp.json()

            # Rapid
            rapid_data = stats.get('chess_rapid', {})
            result["rapid"]["current"] = rapid_data.get('last', {}).get('rating', 0)
            result["rapid"]["best"] = rapid_data.get('best', {}).get('rating', 0)

            # Blitz
            blitz_data = stats.get('chess_blitz', {})
            result["blitz"]["current"] = blitz_data.get('last', {}).get('rating', 0)
            result["blitz"]["best"] = blitz_data.get('best', {}).get('rating', 0)

            # Stats W/L/D (priorité Rapid > Blitz)
            record = rapid_data.get('record') or blitz_data.get('record') or {}

            result["stats"] = {
                "wins": record.get('win', 0),
                "losses": record.get('loss', 0),
                "draws": record.get('draw', 0)
            }

            return result
        else:
            logger.warning(f"Stats API failed for {username}: {resp.status_code}")
            return None

    except Exception as e:
        logger.error(f"Exception fetching stats for {username}: {e}")
        return None
