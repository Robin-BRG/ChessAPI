import logging
from flask import Flask, request, jsonify, send_from_directory
import json
from pathlib import Path
import requests
import os
import threading

# Imports des modules app/
from app.scheduler import start_scheduler, stop_scheduler
from app.chess_updater import update_all_players
from app.chess_api import fetch_player_stats
from app.config import JSON_PATH, SLACK_BOT_TOKEN, PLAYERS_JSON_LOCK

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Servir le site web (HTML)
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# Servir les fichiers statiques (CSS, JS, images)
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# Servir les données JSON pour le frontend
@app.route('/data/<path:path>')
def serve_data(path):
    return send_from_directory('data', path)

# API pour update complet (POST liste de joueurs)
@app.route('/api/players', methods=['POST'])
def update_players():
    try:
        data = request.get_json()
        if not isinstance(data, list):
            return jsonify({"error": "Payload must be a list of players."}), 400
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return jsonify({"message": "players.json updated", "count": len(data)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API pour déclencher manuellement la mise à jour
@app.route('/api/refresh', methods=['POST'])
def manual_refresh():
    """Déclenche manuellement la mise à jour de tous les joueurs (utile pour tests)."""
    logger.info("Manual refresh triggered via /api/refresh")
    result = update_all_players()

    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 500

# Helper pour envoyer une réponse différée à Slack
def send_delayed_response(response_url, message):
    """Envoie un message via response_url de Slack."""
    try:
        requests.post(response_url, json={"text": message, "response_type": "ephemeral"})
    except Exception as e:
        logger.error(f"Failed to send delayed response: {e}")

# Fonction worker pour ajouter un compte en arrière-plan
def add_chess_account_worker(text, user_id, response_url):
    """Fait le travail d'ajout de compte et envoie le résultat via response_url."""
    parts = text.split()
    pseudo = parts[0].strip() if len(parts) > 0 else ''
    promo = parts[1].strip() if len(parts) > 1 else ''
    classe = parts[2].strip().upper() if len(parts) > 2 else ''

    # Récupérer firstName + lastName depuis Slack
    first_name = ''
    last_name = ''

    if user_id:
        slack_token = SLACK_BOT_TOKEN
        if not slack_token:
            send_delayed_response(response_url, "❌ Erreur: SLACK_BOT_TOKEN non configuré.")
            return

        try:
            resp = requests.get(
                'https://slack.com/api/users.info',
                params={'user': user_id},
                headers={'Authorization': f'Bearer {slack_token}'}
            )
            if resp.status_code == 200 and resp.json().get('ok'):
                profile = resp.json()['user']['profile']
                first_name = profile.get('first_name', '')
                last_name = profile.get('last_name', '')

                if not first_name and not last_name:
                    real_name = profile.get('real_name', '')
                    if real_name:
                        parts_name = real_name.split(' ', 1)
                        first_name = parts_name[0] if len(parts_name) > 0 else ''
                        last_name = parts_name[1] if len(parts_name) > 1 else ''
        except Exception as e:
            logger.error(f"Exception fetching Slack user info: {e}")

    if not pseudo:
        send_delayed_response(response_url, "❌ Aucun pseudo fourni.")
        return

    # Récupérer les stats Chess.com AVANT de prendre le lock (pour éviter de bloquer trop longtemps)
    new_stats = fetch_player_stats(pseudo)
    if not new_stats:
        send_delayed_response(response_url, f"❌ Impossible de récupérer les stats Chess.com pour {pseudo}.")
        return

    rapid_current = new_stats['rapid']['current']
    history7days = [rapid_current] * 7

    from datetime import datetime
    today = datetime.now().date().isoformat()

    joueur = {
        "username": pseudo,
        "firstName": first_name,
        "lastName": last_name,
        "promo": promo,
        "class": classe,
        "previousRank": 0,
        "rapid": new_stats['rapid'],
        "blitz": new_stats['blitz'],
        "history7days": history7days,
        "lastHistoryUpdate": today,
        "stats": new_stats['stats'],
        "avatar": new_stats['avatar']
    }

    # SECTION CRITIQUE: Protégée par lock
    with PLAYERS_JSON_LOCK:
        try:
            with open(JSON_PATH, 'r', encoding='utf-8') as f:
                players = json.load(f)
        except Exception:
            players = []

        # Vérifier si déjà présent (username)
        if any(isinstance(p, dict) and p.get('username') == pseudo for p in players):
            send_delayed_response(response_url, f"❌ Le pseudo {pseudo} existe déjà.")
            return

        # Vérifier si firstName + lastName existe déjà
        if first_name and last_name:
            if any(isinstance(p, dict) and
                   p.get('firstName', '').lower() == first_name.lower() and
                   p.get('lastName', '').lower() == last_name.lower()
                   for p in players):
                send_delayed_response(response_url, f"❌ Un compte existe déjà pour {first_name} {last_name}. Vous ne pouvez avoir qu'un seul pseudo.")
                return

        # Ajouter le joueur
        players.append(joueur)

        # Sauvegarder
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(players, f, indent=2, ensure_ascii=False)

    logger.info(f"Added account for {first_name} {last_name} - username: {pseudo}, rapid: {joueur['rapid']['current']}, blitz: {joueur['blitz']['current']}")

    send_delayed_response(response_url, f"✅ Ton compte a été ajouté au classement!\n🎮 Pseudo: {pseudo}\n⚡ Rapid: {joueur['rapid']['current']} | Blitz: {joueur['blitz']['current']}")

# Route Slack pour ajouter un compte
@app.route('/slack/chessadd', methods=['POST'])
def add_chess_account():
    """Répond immédiatement et traite la demande en arrière-plan."""
    text = request.form.get('text', '').strip()
    user_id = request.form.get('user_id', '').strip()
    response_url = request.form.get('response_url', '')

    # Lancer le traitement en arrière-plan
    thread = threading.Thread(target=add_chess_account_worker, args=(text, user_id, response_url))
    thread.daemon = True
    thread.start()

    # Réponse immédiate pour éviter le timeout Slack
    return "⏳ Ajout en cours... Tu recevras une confirmation dans quelques secondes.", 200

# Fonction worker pour supprimer un compte en arrière-plan
def delete_chess_account_worker(user_id, response_url):
    """Fait le travail de suppression et envoie le résultat via response_url."""
    first_name = ''
    last_name = ''

    slack_token = SLACK_BOT_TOKEN
    if not slack_token:
        send_delayed_response(response_url, "❌ Erreur: SLACK_BOT_TOKEN non configuré.")
        return

    try:
        resp = requests.get(
            'https://slack.com/api/users.info',
            params={'user': user_id},
            headers={'Authorization': f'Bearer {slack_token}'}
        )
        if resp.status_code == 200 and resp.json().get('ok'):
            profile = resp.json()['user']['profile']
            first_name = profile.get('first_name', '')
            last_name = profile.get('last_name', '')

            if not first_name and not last_name:
                real_name = profile.get('real_name', '')
                if real_name:
                    parts = real_name.split(' ', 1)
                    first_name = parts[0] if len(parts) > 0 else ''
                    last_name = parts[1] if len(parts) > 1 else ''
        else:
            send_delayed_response(response_url, f"❌ Erreur API Slack: {resp.json().get('error', 'unknown')}")
            return
    except Exception as e:
        logger.error(f"Exception fetching Slack user info: {e}")
        send_delayed_response(response_url, f"❌ Erreur lors de la récupération des infos Slack.")
        return

    if not first_name or not last_name:
        send_delayed_response(response_url, "❌ Impossible de récupérer votre prénom/nom depuis Slack.")
        return

    # SECTION CRITIQUE: Protégée par lock
    with PLAYERS_JSON_LOCK:
        try:
            with open(JSON_PATH, 'r', encoding='utf-8') as f:
                players = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load players.json: {e}")
            send_delayed_response(response_url, "❌ Erreur de chargement des données.")
            return

        # Chercher et supprimer le joueur
        initial_count = len(players)
        players = [
            p for p in players
            if not (isinstance(p, dict) and
                    p.get('firstName', '').lower() == first_name.lower() and
                    p.get('lastName', '').lower() == last_name.lower())
        ]

        if len(players) == initial_count:
            send_delayed_response(response_url, f"❌ Aucun compte trouvé pour {first_name} {last_name}.")
            return

        # Sauvegarder
        try:
            with open(JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(players, f, indent=2, ensure_ascii=False)

            removed_count = initial_count - len(players)
            logger.info(f"Deleted account for {first_name} {last_name} ({removed_count} removed)")

            send_delayed_response(response_url, "✅ Ton compte a été supprimé du classement Chess.com!")
        except Exception as e:
            logger.error(f"Failed to save players.json: {e}")
            send_delayed_response(response_url, "❌ Erreur de sauvegarde.")

# Route Slack pour supprimer un compte
@app.route('/slack/chessdelete', methods=['POST'])
def delete_chess_account():
    """Répond immédiatement et traite la suppression en arrière-plan."""
    user_id = request.form.get('user_id', '').strip()
    response_url = request.form.get('response_url', '')

    if not user_id:
        return "❌ Erreur: user_id manquant.", 200

    # Lancer le traitement en arrière-plan
    thread = threading.Thread(target=delete_chess_account_worker, args=(user_id, response_url))
    thread.daemon = True
    thread.start()

    # Réponse immédiate pour éviter le timeout Slack
    return "⏳ Suppression en cours... Tu recevras une confirmation dans quelques secondes.", 200

if __name__ == "__main__":
    # Démarrer le scheduler pour mise à jour automatique
    start_scheduler()

    try:
        app.run(host="0.0.0.0", port=5000, debug=True)
    finally:
        # Arrêter proprement le scheduler à la fin
        stop_scheduler()
