# Configuration APScheduler pour mise à jour automatique
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from .chess_updater import update_all_players
from .config import UPDATE_INTERVAL_MINUTES, SCHEDULER_ENABLED

logger = logging.getLogger(__name__)

# Instance globale du scheduler
scheduler = None

def start_scheduler():
    """
    Démarre le scheduler APScheduler.
    Exécute update_all_players toutes les N minutes.
    """
    global scheduler

    if not SCHEDULER_ENABLED:
        logger.info("Scheduler disabled by config (SCHEDULER_ENABLED=false)")
        return

    scheduler = BackgroundScheduler(timezone="Europe/Paris")

    # Job : mise à jour toutes les N minutes
    scheduler.add_job(
        func=update_all_players,
        trigger=IntervalTrigger(minutes=UPDATE_INTERVAL_MINUTES),
        id='update_players_job',
        name='Update Chess.com stats for all players',
        replace_existing=True,
        max_instances=1  # Éviter les exécutions parallèles
    )

    scheduler.start()
    logger.info(f"✓ Scheduler started: update every {UPDATE_INTERVAL_MINUTES} minutes")

def stop_scheduler():
    """Arrête le scheduler proprement."""
    global scheduler
    if scheduler:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
