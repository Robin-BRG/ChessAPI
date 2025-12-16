# Logique métier de mise à jour des joueurs
import json
import logging
import time
from datetime import datetime
from pathlib import Path
import shutil
from .chess_api import fetch_player_stats
from .config import JSON_PATH, RATE_LIMIT_DELAY_SECONDS, WORKING_DAYS, START_HOUR, PLAYERS_JSON_LOCK

logger = logging.getLogger(__name__)

def should_run_update():
    """
    Vérifie si la mise à jour doit s'exécuter selon les horaires.
    Retourne True si on est lundi-vendredi entre 6h et minuit.
    """
    now = datetime.now()

    # Vérifier jour de la semaine (0=lundi, 6=dimanche)
    if now.weekday() not in WORKING_DAYS:
        logger.info(f"Update skipped: weekend (day={now.weekday()})")
        return False

    # Vérifier heure (6h-00h = 6h-23h59)
    hour = now.hour
    if hour < START_HOUR:  # Avant 6h du matin
        logger.info(f"Update skipped: before start hour (hour={hour})")
        return False

    return True

def remove_expired_promos(players):
    """
    Supprime les joueurs diplômés (promo <= année actuelle).
    Seuls les étudiants avec promo > année actuelle sont gardés.

    Args:
        players: Liste des joueurs

    Returns:
        tuple: (liste filtrée, nombre de suppressions)
    """
    current_year = datetime.now().year
    initial_count = len(players)

    filtered = [
        p for p in players
        if p.get('promo', '').isdigit() and int(p['promo']) > current_year
    ]

    removed_count = initial_count - len(filtered)
    if removed_count > 0:
        removed_usernames = [
            p['username'] for p in players
            if p not in filtered
        ]
        logger.info(f"Removed {removed_count} expired players: {removed_usernames}")

    return filtered, removed_count

def update_player_rank(players):
    """
    Trie les joueurs par score Rapid décroissant et met à jour previousRank.

    Args:
        players: Liste des joueurs

    Returns:
        Liste triée
    """
    # Trier par score Rapid décroissant
    sorted_players = sorted(players, key=lambda x: x.get('rapid', {}).get('current', 0), reverse=True)

    # Sauvegarder les rangs actuels dans previousRank
    for idx, player in enumerate(sorted_players):
        player['previousRank'] = idx + 1

    return sorted_players

def update_history_7days(player, new_current):
    """
    Met à jour history7days en ajoutant new_current SEULEMENT si on est un nouveau jour.
    Cela permet d'avoir un vrai historique de 7 jours (et non les 7 dernières mises à jour).

    Args:
        player: Dictionnaire du joueur
        new_current: Nouveau score actuel

    Returns:
        Joueur modifié
    """
    today = datetime.now().date().isoformat()  # YYYY-MM-DD
    last_update = player.get('lastHistoryUpdate', '')

    # Ne mettre à jour que si on est un nouveau jour
    if last_update == today:
        logger.debug(f"History already updated today for {player.get('username')}")
        return player

    history = player.get('history7days', [])
    history.append(new_current)

    # Garder seulement les 7 derniers jours
    if len(history) > 7:
        history = history[-7:]

    player['history7days'] = history
    player['lastHistoryUpdate'] = today
    logger.info(f"Updated history for {player.get('username')}: added {new_current} for {today}")
    return player

def update_all_players():
    """
    Fonction principale de mise à jour :
    1. Vérifier horaires
    2. Charger players.json
    3. Supprimer promos expirées
    4. Mettre à jour previousRank
    5. Récupérer nouvelles stats Chess.com (avec rate limiting)
    6. Mettre à jour history7days
    7. Re-trier
    8. Sauvegarder atomiquement

    Returns:
        dict avec résumé de l'opération
    """
    logger.info("=== Starting update_all_players ===")

    # 1. Vérifier horaires
    if not should_run_update():
        return {"success": False, "message": "Outside working hours"}

    # SECTION CRITIQUE: Protéger toute la mise à jour avec le lock
    with PLAYERS_JSON_LOCK:
        # 2. Charger données actuelles
        try:
            with open(JSON_PATH, 'r', encoding='utf-8') as f:
                players = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load players.json: {e}")
            return {"success": False, "error": str(e)}

        initial_count = len(players)
        logger.info(f"Loaded {initial_count} players")

        # 3. Supprimer promos expirées
        players, removed_count = remove_expired_promos(players)

        # 4. Mettre à jour previousRank (avant récupération nouvelles stats)
        players = update_player_rank(players)

        # 5. Récupérer nouvelles stats Chess.com
        success_count = 0
        error_count = 0

        for idx, player in enumerate(players):
            username = player.get('username')
            if not username:
                continue

            logger.info(f"Updating {username} ({idx+1}/{len(players)})")

            # Rate limiting
            if idx > 0:
                time.sleep(RATE_LIMIT_DELAY_SECONDS)

            # Récupérer nouvelles stats
            new_stats = fetch_player_stats(username)

            if new_stats:
                # Mettre à jour seulement si récupération réussie
                player['rapid'] = new_stats['rapid']
                player['blitz'] = new_stats['blitz']

                # Garder le meilleur score rapid historique
                if 'rapid' in player and 'best' in player['rapid']:
                    player['rapid']['best'] = max(player['rapid'].get('best', 0), new_stats['rapid']['best'])

                # Garder le meilleur score blitz historique
                if 'blitz' in player and 'best' in player['blitz']:
                    player['blitz']['best'] = max(player['blitz'].get('best', 0), new_stats['blitz']['best'])

                player['stats'] = new_stats['stats']
                if new_stats['avatar']:
                    player['avatar'] = new_stats['avatar']

                # Mettre à jour history (basé sur Rapid)
                player = update_history_7days(player, new_stats['rapid']['current'])

                success_count += 1
            else:
                # Conserver anciennes stats en cas d'erreur
                logger.warning(f"Failed to update {username}, keeping old stats")
                error_count += 1

        # 6. Re-trier après mises à jour (par score Rapid)
        players = sorted(players, key=lambda x: x.get('rapid', {}).get('current', 0), reverse=True)

        # 7. Sauvegarder atomiquement (temp file + rename)
        if success_count > 0:
            try:
                temp_path = JSON_PATH.with_suffix('.json.tmp')
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(players, f, indent=2, ensure_ascii=False)

                # Rename atomique
                if temp_path.exists():
                    shutil.move(str(temp_path), str(JSON_PATH))

                logger.info(f"✓ Update complete: {success_count} success, {error_count} errors, {removed_count} removed")
                return {
                    "success": True,
                    "updated": success_count,
                    "errors": error_count,
                    "removed": removed_count,
                    "total": len(players)
                }
            except Exception as e:
                logger.error(f"Failed to save players.json: {e}")
                return {"success": False, "error": str(e)}
        else:
            logger.error("No successful updates, not saving file")
            return {"success": False, "message": "No successful updates"}
