import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DB_FILE = DATA_DIR / "jobfit.db"


class DBService:
    """
    Lightweight SQLite Database Service to persist user profile,
    uploaded resume data, search preferences, and Telegram credentials.
    Ensures users never have to repeat the same setup steps when reloading.
    """

    @classmethod
    def get_connection(cls) -> sqlite3.Connection:
        os.makedirs(DATA_DIR, exist_ok=True)
        conn = sqlite3.connect(str(DB_FILE))
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def init_db(cls):
        """Create sqlite tables if not exists."""
        with cls.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_profile (
                    id INTEGER PRIMARY KEY,
                    candidate_name TEXT,
                    primary_title TEXT,
                    experience_years REAL DEFAULT 2.0,
                    skills_json TEXT DEFAULT '[]',
                    suggested_titles_json TEXT DEFAULT '[]',
                    resume_filename TEXT,
                    resume_text TEXT,
                    keywords TEXT,
                    location_1 TEXT,
                    location_2 TEXT,
                    location_3 TEXT,
                    experience_level TEXT DEFAULT 'mid_senior',
                    min_match_percentage REAL DEFAULT 55.0,
                    telegram_bot_token TEXT,
                    telegram_chat_id TEXT,
                    updated_at TEXT
                );
            """)
            conn.commit()

    @classmethod
    def get_user_profile(cls, user_id: int = 1) -> Optional[Dict[str, Any]]:
        """Retrieve persisted user profile and credentials."""
        cls.init_db()
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_profile WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if not row:
                return None

            try:
                skills = json.loads(row["skills_json"] or "[]")
            except Exception:
                skills = []

            try:
                suggested_titles = json.loads(row["suggested_titles_json"] or "[]")
            except Exception:
                suggested_titles = []

            locs = [
                row["location_1"] or "",
                row["location_2"] or "",
                row["location_3"] or ""
            ]
            valid_locs = [l.strip() for l in locs if l and l.strip()]

            return {
                "id": row["id"],
                "candidate_name": row["candidate_name"] or "Candidate",
                "primary_title": row["primary_title"] or "Software Engineer",
                "experience_years": row["experience_years"] if row["experience_years"] is not None else 2.0,
                "skills": skills,
                "suggested_titles": suggested_titles,
                "resume_filename": row["resume_filename"] or "",
                "resume_text": row["resume_text"] or "",
                "has_resume": bool(row["resume_text"] and row["resume_text"].strip()),
                "keywords": row["keywords"] or "Python FastAPI Developer",
                "location_1": row["location_1"] or "Remote",
                "location_2": row["location_2"] or "",
                "location_3": row["location_3"] or "",
                "locations": valid_locs,
                "experience_level": row["experience_level"] or "mid_senior",
                "min_match_percentage": row["min_match_percentage"] if row["min_match_percentage"] is not None else 55.0,
                "telegram_bot_token": row["telegram_bot_token"] or "",
                "telegram_chat_id": row["telegram_chat_id"] or "",
                "updated_at": row["updated_at"] or ""
            }

    @classmethod
    def save_user_profile(cls, data: Dict[str, Any], user_id: int = 1) -> Dict[str, Any]:
        """Upsert user profile and credentials, preserving existing values if omitted."""
        cls.init_db()
        existing = cls.get_user_profile(user_id) or {}

        # Merge new data with existing data
        candidate_name = data.get("candidate_name") or existing.get("candidate_name") or "Candidate"
        primary_title = data.get("primary_title") or existing.get("primary_title") or "Software Engineer"
        experience_years = data.get("experience_years") if data.get("experience_years") is not None else existing.get("experience_years", 2.0)

        skills = data.get("skills") if data.get("skills") is not None else existing.get("skills", [])
        suggested_titles = data.get("suggested_titles") if data.get("suggested_titles") is not None else existing.get("suggested_titles", [])

        resume_filename = data.get("resume_filename") or existing.get("resume_filename") or ""
        resume_text = data.get("resume_text") or existing.get("resume_text") or ""

        keywords = data.get("keywords") or existing.get("keywords") or "Python FastAPI Developer"
        location_1 = data.get("location_1") if data.get("location_1") is not None else existing.get("location_1", "Remote")
        location_2 = data.get("location_2") if data.get("location_2") is not None else existing.get("location_2", "")
        location_3 = data.get("location_3") if data.get("location_3") is not None else existing.get("location_3", "")

        experience_level = data.get("experience_level") or existing.get("experience_level") or "mid_senior"
        min_match = data.get("min_match_percentage") if data.get("min_match_percentage") is not None else existing.get("min_match_percentage", 55.0)

        tg_token = data.get("telegram_bot_token") if data.get("telegram_bot_token") is not None else existing.get("telegram_bot_token", "")
        tg_chat = data.get("telegram_chat_id") if data.get("telegram_chat_id") is not None else existing.get("telegram_chat_id", "")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with cls.get_connection() as conn:
            conn.execute("""
                INSERT INTO user_profile (
                    id, candidate_name, primary_title, experience_years,
                    skills_json, suggested_titles_json, resume_filename, resume_text,
                    keywords, location_1, location_2, location_3,
                    experience_level, min_match_percentage,
                    telegram_bot_token, telegram_chat_id, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    candidate_name=excluded.candidate_name,
                    primary_title=excluded.primary_title,
                    experience_years=excluded.experience_years,
                    skills_json=excluded.skills_json,
                    suggested_titles_json=excluded.suggested_titles_json,
                    resume_filename=excluded.resume_filename,
                    resume_text=excluded.resume_text,
                    keywords=excluded.keywords,
                    location_1=excluded.location_1,
                    location_2=excluded.location_2,
                    location_3=excluded.location_3,
                    experience_level=excluded.experience_level,
                    min_match_percentage=excluded.min_match_percentage,
                    telegram_bot_token=excluded.telegram_bot_token,
                    telegram_chat_id=excluded.telegram_chat_id,
                    updated_at=excluded.updated_at;
            """, (
                user_id,
                candidate_name,
                primary_title,
                float(experience_years),
                json.dumps(skills),
                json.dumps(suggested_titles),
                resume_filename,
                resume_text,
                keywords,
                location_1,
                location_2,
                location_3,
                experience_level,
                float(min_match),
                tg_token,
                tg_chat,
                now_str
            ))
            conn.commit()

        # Also sync to .env file if tokens are updated
        if tg_token or tg_chat:
            cls.update_env_file(tg_token, tg_chat)

        return cls.get_user_profile(user_id)

    @classmethod
    def update_env_file(cls, token: Optional[str] = None, chat_id: Optional[str] = None):
        """Update TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env file."""
        env_path = DATA_DIR.parent / ".env"
        if not env_path.exists():
            return
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            new_lines = []
            for line in lines:
                if token and line.startswith("TELEGRAM_BOT_TOKEN="):
                    new_lines.append(f"TELEGRAM_BOT_TOKEN={token.strip()}\n")
                elif chat_id and line.startswith("TELEGRAM_CHAT_ID="):
                    new_lines.append(f"TELEGRAM_CHAT_ID={chat_id.strip()}\n")
                else:
                    new_lines.append(line)

            with open(env_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
        except Exception as e:
            print(f"[DBService] Warning: Could not update .env: {e}")
