import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Set, List
from app.schemas.profile import UserProfile
from app.schemas.job import JobMatchResult
from app.services.linkedin_service import LinkedInService
from app.services.matching_service import MatchingService
from app.services.telegram_service import TelegramService

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
CONFIG_FILE = DATA_DIR / "watcher_config.json"
SENT_JOBS_FILE = DATA_DIR / "sent_jobs.json"


class WatcherService:
    _task: Optional[asyncio.Task] = None
    _is_running: bool = False
    _config: Optional[Dict[str, Any]] = None
    _sent_job_ids: Set[str] = set()
    _stats: Dict[str, Any] = {
        "status": "stopped",
        "total_checks": 0,
        "total_jobs_sent": 0,
        "last_check_time": None,
        "last_new_jobs_found": 0,
        "started_at": None,
        "recent_jobs": []
    }

    @classmethod
    def initialize(cls):
        """Load persisted state on startup."""
        os.makedirs(DATA_DIR, exist_ok=True)
        # Load sent jobs
        if SENT_JOBS_FILE.exists():
            try:
                with open(SENT_JOBS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cls._sent_job_ids = set(data)
            except Exception as e:
                print(f"[WatcherService] Failed to load sent jobs: {e}")

        # Load saved config
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cls._config = json.load(f)
            except Exception as e:
                print(f"[WatcherService] Failed to load watcher config: {e}")

    @classmethod
    def is_running(cls) -> bool:
        return cls._is_running and cls._task is not None and not cls._task.done()

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Return real-time status of the background watcher."""
        return {
            "is_running": cls.is_running(),
            "status": "running" if cls.is_running() else "stopped",
            "stats": cls._stats,
            "config": {
                "keywords": cls._config.get("keywords") if cls._config else "",
                "locations": cls._config.get("locations", []) if cls._config else [],
                "candidate_title": cls._config.get("profile", {}).get("title", "") if cls._config else "",
                "interval_minutes": cls._config.get("interval_minutes", 10) if cls._config else 10,
                "min_match_percentage": cls._config.get("min_match_percentage", 55.0) if cls._config else 55.0,
                "telegram_configured": bool(cls._config.get("telegram_bot_token") and cls._config.get("telegram_chat_id")) if cls._config else False
            } if cls._config else None,
            "total_sent_jobs_tracked": len(cls._sent_job_ids)
        }

    @classmethod
    async def start(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """Start or restart the background watcher task."""
        if cls.is_running():
            await cls.stop()

        cls._config = config
        cls._is_running = True
        cls._stats["status"] = "running"
        cls._stats["started_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Save config to disk
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"[WatcherService] Failed to save config: {e}")

        # Send activation alert to Telegram
        tg_token = config.get("telegram_bot_token")
        tg_chat = config.get("telegram_chat_id")
        keywords = config.get("keywords", "Matching Roles")
        interval_min = config.get("interval_minutes", 10)
        locations_str = ", ".join(config.get("locations", [])) or "Worldwide / Remote"

        if tg_token and tg_chat:
            try:
                activation_msg = (
                    "🟢 <b>JobFit AI • 24/7 Background Watcher Activated!</b>\n\n"
                    f"🎯 <b>Target Keywords:</b> {keywords}\n"
                    f"📍 <b>Locations:</b> {locations_str}\n"
                    f"⏱️ <b>Check Frequency:</b> Every {interval_min} minutes\n\n"
                    "<i>I will continuously monitor LinkedIn in the background. As soon as a NEW matching job is posted, you will receive an instant alert here!</i>"
                )
                import httpx
                url = TelegramService.BASE_URL.format(token=tg_token, method="sendMessage")
                async with httpx.AsyncClient(timeout=10.0) as client:
                    await client.post(url, json={
                        "chat_id": tg_chat,
                        "text": activation_msg,
                        "parse_mode": "HTML"
                    })
            except Exception as e:
                print(f"[WatcherService] Activation ping error: {e}")

        # Launch the autonomous background task
        cls._task = asyncio.create_task(cls._worker_loop())
        return cls.get_status()

    @classmethod
    async def stop(cls) -> Dict[str, Any]:
        """Stop the background watcher."""
        cls._is_running = False
        cls._stats["status"] = "stopped"

        if cls._task:
            cls._task.cancel()
            try:
                await cls._task
            except asyncio.CancelledError:
                pass
            cls._task = None

        # Send stop alert to Telegram if configured
        if cls._config:
            tg_token = cls._config.get("telegram_bot_token")
            tg_chat = cls._config.get("telegram_chat_id")
            if tg_token and tg_chat:
                try:
                    import httpx
                    url = TelegramService.BASE_URL.format(token=tg_token, method="sendMessage")
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        await client.post(url, json={
                            "chat_id": tg_chat,
                            "text": "🛑 <b>JobFit AI • Background Watcher Stopped.</b>\nYou can reactivate it anytime from the dashboard.",
                            "parse_mode": "HTML"
                        })
                except Exception:
                    pass

        return cls.get_status()

    @classmethod
    async def _worker_loop(cls):
        """Continuous background execution loop."""
        print("[WatcherService] [RUNNING] Background watcher loop started.")
        while cls._is_running:
            try:
                await cls._perform_scan()
            except Exception as e:
                print(f"[WatcherService] Worker cycle error: {e}")

            # Sleep until next check interval
            interval_min = cls._config.get("interval_minutes", 10) if cls._config else 10
            interval_sec = max(60, int(interval_min * 60))
            
            try:
                await asyncio.sleep(interval_sec)
            except asyncio.CancelledError:
                break

        print("[WatcherService] [STOPPED] Background watcher loop exited.")

    @classmethod
    async def _perform_scan(cls):
        """Scrape LinkedIn, find new matching jobs, and deliver to Telegram."""
        if not cls._config:
            return

        profile_data = cls._config.get("profile")
        if not profile_data:
            return

        profile = UserProfile(**profile_data)
        keywords = cls._config.get("keywords") or profile.title
        locations = cls._config.get("locations", [])
        min_match = float(cls._config.get("min_match_percentage", 55.0))
        tg_token = cls._config.get("telegram_bot_token")
        tg_chat = cls._config.get("telegram_chat_id")

        exp_level = cls._config.get("experience_level", "all")

        cls._stats["total_checks"] += 1
        cls._stats["last_check_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"[WatcherService] Check #{cls._stats['total_checks']} for '{keywords}' (Exp: {exp_level})...")

        # 1. Search LinkedIn (All Available / Unlimited, Filtered by Experience, Newest First)
        jobs = await LinkedInService.search_jobs(
            keywords=keywords,
            locations=locations,
            limit=None,
            experience_level=exp_level,
            sort_by="recent"
        )

        # 2. Match & Rank against candidate profile (Newest first)
        ranked_jobs = MatchingService.rank_jobs_by_match(
            profile=profile,
            jobs=jobs,
            min_match_percentage=min_match,
            sort_by="recent",
            experience_level=exp_level
        )

        # 3. Filter for brand NEW jobs only (not previously sent)
        new_jobs = [r for r in ranked_jobs if r.job.id not in cls._sent_job_ids]
        cls._stats["last_new_jobs_found"] = len(new_jobs)

        print(f"[WatcherService] Scanned {len(jobs)} jobs. Found {len(ranked_jobs)} qualified, {len(new_jobs)} are brand NEW.")

        if new_jobs and tg_token and tg_chat:
            # Deliver new jobs to Telegram
            sent_count, errors = await TelegramService.send_matching_jobs(
                jobs=new_jobs,
                bot_token=tg_token,
                chat_id=tg_chat,
                top_n=None  # Send all newly discovered matches
            )

            # Record newly sent IDs to prevent duplicate notifications
            for item in new_jobs:
                cls._sent_job_ids.add(item.job.id)

            cls._stats["total_jobs_sent"] += sent_count

            # Keep top recent jobs in memory for UI status preview
            cls._stats["recent_jobs"] = [
                {
                    "title": j.job.title,
                    "company": j.job.company,
                    "match": j.match_percentage,
                    "time": datetime.now().strftime("%H:%M")
                }
                for j in new_jobs[:5]
            ]

            # Persist sent jobs database to disk
            try:
                with open(SENT_JOBS_FILE, "w", encoding="utf-8") as f:
                    json.dump(list(cls._sent_job_ids), f)
            except Exception as e:
                print(f"[WatcherService] Failed to persist sent jobs: {e}")
