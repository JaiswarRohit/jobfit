from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional, List
from app.schemas.profile import UserProfile
from app.schemas.job import JobPost
from app.schemas.telegram import TelegramSendResponse
from app.services.resume_service import ResumeService
from app.services.linkedin_service import LinkedInService
from app.services.matching_service import MatchingService
from app.services.telegram_service import TelegramService
from app.services.db_service import DBService
from app.config import settings

router = APIRouter(prefix="/api/pipeline", tags=["End-to-End Pipeline"])


@router.post("/run")
async def run_full_pipeline(
    file: Optional[UploadFile] = File(None),
    resume_text: Optional[str] = Form(None),
    candidate_name: Optional[str] = Form("Candidate"),
    keywords: Optional[str] = Form(None),
    location: Optional[str] = Form(""),
    location_1: Optional[str] = Form(None),
    location_2: Optional[str] = Form(None),
    location_3: Optional[str] = Form(None),
    min_match_percentage: float = Form(55.0),
    max_jobs_to_scan: Optional[int] = Form(0),
    top_n_to_telegram: Optional[int] = Form(0),
    experience_level: Optional[str] = Form("all"),
    sort_by: Optional[str] = Form("recent"),
    telegram_bot_token: Optional[str] = Form(None),
    telegram_chat_id: Optional[str] = Form(None),
    already_sent_ids: Optional[str] = Form(None),
    send_telegram: bool = Form(True)
):
    """
    Complete Autonomous Pipeline (No Limit & Auto-Send):
    1. Parse Resume (from file or text)
    2. Search LinkedIn for matching active jobs (Unlimited / All Available, Filtered by Experience, Newest First)
    3. Calculate match percentage & select jobs meeting the threshold
    4. Automatically send ALL matching jobs directly to Telegram Bot in newest-first priority!
    """
    # Step 1: Extract Profile (Supports uploaded file, text, or saved DB profile)
    saved_profile = DBService.get_user_profile(user_id=1)
    extracted_text = ""
    resume_file_name = ""

    if file and hasattr(file, "filename") and file.filename:
        content = await file.read()
        fname = file.filename.lower()
        resume_file_name = file.filename
        if fname.endswith(".pdf"):
            extracted_text = ResumeService.extract_text_from_pdf(content)
        elif fname.endswith(".docx"):
            extracted_text = ResumeService.extract_text_from_docx(content)
        elif fname.endswith(".txt"):
            extracted_text = content.decode("utf-8", errors="ignore")
    elif resume_text and resume_text.strip():
        extracted_text = resume_text.strip()
    elif saved_profile and saved_profile.get("resume_text"):
        extracted_text = saved_profile["resume_text"]
        resume_file_name = saved_profile.get("resume_filename", "")
    else:
        # Sensible sample profile if user runs without resume
        extracted_text = (
            "Senior Python Developer with 4 years of experience building scalable backend APIs. "
            "Skilled in Python, FastAPI, Docker, PostgreSQL, Redis, REST API, Git, CI/CD, and AWS."
        )

    resolved_name = candidate_name
    if (not resolved_name or resolved_name == "Candidate") and saved_profile and saved_profile.get("candidate_name"):
        resolved_name = saved_profile["candidate_name"]

    profile = ResumeService.parse_profile(extracted_text, name=resolved_name)

    # Search keywords default to user target title or skills
    search_keywords = keywords or (f"{profile.title} " + " ".join(profile.skills[:2])).strip()
    if not search_keywords.strip():
        search_keywords = settings.DEFAULT_JOB_KEYWORDS

    # Collect up to 3 locations (NOT mandatory: empty means worldwide/any)
    target_locations: List[str] = []
    for loc_cand in [location_1, location_2, location_3]:
        if loc_cand and isinstance(loc_cand, str) and loc_cand.strip():
            target_locations.append(loc_cand.strip())

    if not target_locations and location and isinstance(location, str):
        parts = [p.strip() for p in location.split(",") if p.strip()]
        target_locations = parts[:3]

    # Step 2: Search LinkedIn Jobs (Supports Unlimited, 3 Locations, Experience filter, Newest First)
    limit_val = max_jobs_to_scan if (isinstance(max_jobs_to_scan, int) and max_jobs_to_scan > 0) else None
    exp_str = experience_level if isinstance(experience_level, str) else "all"
    sort_str = sort_by if isinstance(sort_by, str) else "recent"

    jobs = await LinkedInService.search_jobs(
        keywords=search_keywords,
        locations=target_locations,
        limit=limit_val,
        experience_level=exp_str,
        sort_by=sort_str
    )

    # Step 3: Match & Rank Jobs (Newest jobs are top priority)
    ranked_results = MatchingService.rank_jobs_by_match(
        profile=profile,
        jobs=jobs,
        min_match_percentage=min_match_percentage,
        sort_by=sort_str,
        experience_level=exp_str
    )

    # Normalize Telegram credentials
    tg_token_str = telegram_bot_token if isinstance(telegram_bot_token, str) else None
    tg_chat_str = telegram_chat_id if isinstance(telegram_chat_id, str) else None

    # Auto-persist user settings and credentials to SQLite so user never has to re-enter them
    DBService.save_user_profile({
        "candidate_name": profile.name,
        "primary_title": profile.title,
        "experience_years": profile.experience_years,
        "skills": profile.skills,
        "suggested_titles": profile.suggested_titles,
        "resume_filename": resume_file_name or (saved_profile.get("resume_filename") if saved_profile else ""),
        "resume_text": extracted_text,
        "keywords": search_keywords,
        "location_1": location_1,
        "location_2": location_2,
        "location_3": location_3,
        "experience_level": exp_str,
        "min_match_percentage": min_match_percentage,
        "telegram_bot_token": tg_token_str,
        "telegram_chat_id": tg_chat_str
    }, user_id=1)

    # Step 4: Dispatch ALL Matching Jobs to Telegram if enabled
    telegram_dispatch = None

    tg_token = (tg_token_str.strip() if tg_token_str else None) or settings.TELEGRAM_BOT_TOKEN
    tg_chat = (tg_chat_str.strip() if tg_chat_str else None) or settings.TELEGRAM_CHAT_ID

    # Deliver all matched jobs without limit if top_n is omitted or <= 0
    deliver_all = not (isinstance(top_n_to_telegram, int) and top_n_to_telegram > 0)

    # Filter out already sent job IDs to prevent duplicate alerts during auto-refresh
    sent_ids_set = set()
    if already_sent_ids and isinstance(already_sent_ids, str):
        sent_ids_set = set(x.strip() for x in already_sent_ids.split(",") if x.strip())

    jobs_to_dispatch = [r for r in ranked_results if r.job.id not in sent_ids_set]

    if send_telegram and tg_token and tg_chat and jobs_to_dispatch:
        sent_count, errors = await TelegramService.send_matching_jobs(
            jobs=jobs_to_dispatch,
            bot_token=tg_token,
            chat_id=tg_chat,
            top_n=None if deliver_all else top_n_to_telegram
        )
        telegram_dispatch = {
            "sent_to_telegram": sent_count > 0,
            "jobs_sent_count": sent_count,
            "new_jobs_found": len(jobs_to_dispatch),
            "total_qualified": len(ranked_results),
            "errors": errors
        }
    else:
        telegram_dispatch = {
            "sent_to_telegram": False,
            "jobs_sent_count": 0,
            "new_jobs_found": len(jobs_to_dispatch),
            "total_qualified": len(ranked_results),
            "notice": "All matching jobs were already sent or no new postings met the threshold." if sent_ids_set else "Telegram credentials not provided."
        }

    return {
        "success": True,
        "candidate": {
            "name": profile.name,
            "title": profile.title,
            "experience_years": profile.experience_years,
            "skills": profile.skills,
            "suggested_titles": profile.suggested_titles,
        },
        "search_parameters": {
            "keywords": search_keywords,
            "locations": target_locations if target_locations else ["Worldwide / Any"],
            "experience_level": exp_str,
            "sort_by": sort_str,
            "total_scanned": len(jobs),
            "qualified_count": len(ranked_results)
        },
        "all_ranked_results": ranked_results,
        "telegram_status": telegram_dispatch
    }
