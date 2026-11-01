from fastapi import APIRouter, HTTPException, Body
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from app.services.db_service import DBService

router = APIRouter(prefix="/api/profile", tags=["User Profile Persistence"])


class SaveProfileRequest(BaseModel):
    candidate_name: Optional[str] = "Candidate"
    primary_title: Optional[str] = "Software Engineer"
    experience_years: Optional[float] = 2.0
    skills: Optional[List[str]] = None
    suggested_titles: Optional[List[str]] = None
    keywords: Optional[str] = None
    location_1: Optional[str] = None
    location_2: Optional[str] = None
    location_3: Optional[str] = None
    experience_level: Optional[str] = "mid_senior"
    min_match_percentage: Optional[float] = 55.0
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None


@router.get("/saved")
async def get_saved_profile():
    """
    Retrieve stored user profile, resume details, and Telegram credentials from SQLite database.
    Allows pre-filling the dashboard on login/load so user does not have to repeat inputs.
    """
    profile = DBService.get_user_profile(user_id=1)
    if not profile:
        return {
            "has_saved_profile": False,
            "message": "No profile saved yet. Upload a resume or save settings to initialize."
        }
    return {
        "has_saved_profile": True,
        "profile": profile
    }


@router.post("/save")
async def save_profile_settings(req: SaveProfileRequest):
    """
    Persist or update user profile, target keywords, locations, experience level,
    and Telegram credentials in the SQLite database.
    """
    try:
        updated = DBService.save_user_profile(req.model_dump(exclude_unset=True), user_id=1)
        return {
            "success": True,
            "message": "User profile and settings saved successfully to SQLite database.",
            "profile": updated
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save profile: {str(e)}")
