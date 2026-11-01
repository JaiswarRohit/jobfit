from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional, List
from app.services.resume_service import ResumeService
from app.services.watcher_service import WatcherService
from app.services.db_service import DBService
from app.config import settings

router = APIRouter(prefix="/api/watcher", tags=["Background Job Watcher"])


@router.get("/status")
async def get_watcher_status():
    """Get the current running status and statistics of the background watcher."""
    return WatcherService.get_status()


@router.post("/start")
async def start_background_watcher(
    file: Optional[UploadFile] = File(None),
    resume_text: Optional[str] = Form(None),
    candidate_name: Optional[str] = Form("Candidate"),
    keywords: Optional[str] = Form(None),
    location_1: Optional[str] = Form(None),
    location_2: Optional[str] = Form(None),
    location_3: Optional[str] = Form(None),
    location: Optional[str] = Form(""),
    min_match_percentage: float = Form(55.0),
    interval_minutes: float = Form(5.0),
    experience_level: Optional[str] = Form("all"),
    telegram_bot_token: Optional[str] = Form(None),
    telegram_chat_id: Optional[str] = Form(None)
):
    """
    Start the autonomous 24/7 background watcher.
    It runs periodically on the server, monitors LinkedIn, and automatically
    sends newly detected matching jobs to your Telegram bot.
    """
    # 1. Parse Profile
    extracted_text = ""
    if file and hasattr(file, "filename") and file.filename:
        content = await file.read()
        fname = file.filename.lower()
        if fname.endswith(".pdf"):
            extracted_text = ResumeService.extract_text_from_pdf(content)
        elif fname.endswith(".docx"):
            extracted_text = ResumeService.extract_text_from_docx(content)
        elif fname.endswith(".txt"):
            extracted_text = content.decode("utf-8", errors="ignore")
    elif resume_text and resume_text.strip():
        extracted_text = resume_text.strip()
    else:
        # Check if we already have saved profile in config
        existing_status = WatcherService.get_status()
        if existing_status.get("config"):
            pass
        else:
            extracted_text = (
                "Senior Python Developer with 4 years of experience building scalable backend APIs. "
                "Skilled in Python, FastAPI, Docker, PostgreSQL, Redis, REST API, Git, CI/CD, and AWS."
            )

    if extracted_text:
        profile = ResumeService.parse_profile(extracted_text, name=candidate_name)
    else:
        # Fallback profile
        profile = ResumeService.parse_profile("Python FastAPI Developer", name=candidate_name)

    # 2. Collect up to 3 optional locations
    target_locations = []
    for loc_cand in [location_1, location_2, location_3]:
        if loc_cand and isinstance(loc_cand, str) and loc_cand.strip():
            target_locations.append(loc_cand.strip())

    if not target_locations and location and isinstance(location, str):
        parts = [p.strip() for p in location.split(",") if p.strip()]
        target_locations = parts[:3]

    search_keywords = keywords or (f"{profile.title} " + " ".join(profile.skills[:2])).strip()
    if not search_keywords.strip():
        search_keywords = settings.DEFAULT_JOB_KEYWORDS

    tg_token = (telegram_bot_token.strip() if telegram_bot_token else None) or settings.TELEGRAM_BOT_TOKEN
    tg_chat = (telegram_chat_id.strip() if telegram_chat_id else None) or settings.TELEGRAM_CHAT_ID

    if not tg_token or not tg_chat:
        raise HTTPException(
            status_code=400,
            detail="Telegram Bot Token and Chat ID are required for the background watcher to send you new jobs."
        )

    config = {
        "profile": profile.model_dump(),
        "keywords": search_keywords,
        "locations": target_locations,
        "experience_level": experience_level or "all",
        "min_match_percentage": min_match_percentage,
        "interval_minutes": max(1.0, interval_minutes),
        "telegram_bot_token": tg_token,
        "telegram_chat_id": tg_chat
    }

    # Save to SQLite so user settings are remembered
    DBService.save_user_profile({
        "candidate_name": profile.name,
        "primary_title": profile.title,
        "experience_years": profile.experience_years,
        "skills": profile.skills,
        "suggested_titles": profile.suggested_titles,
        "resume_text": extracted_text,
        "keywords": search_keywords,
        "location_1": location_1,
        "location_2": location_2,
        "location_3": location_3,
        "experience_level": experience_level or "all",
        "min_match_percentage": min_match_percentage,
        "telegram_bot_token": tg_token,
        "telegram_chat_id": tg_chat
    }, user_id=1)

    result = await WatcherService.start(config)
    return {
        "success": True,
        "message": f"Autonomous Background Watcher started! Checking LinkedIn every {interval_minutes} minutes.",
        "watcher_status": result
    }


@router.post("/stop")
async def stop_background_watcher():
    """Stop the background watcher."""
    result = await WatcherService.stop()
    return {
        "success": True,
        "message": "Background Watcher stopped.",
        "watcher_status": result
    }
