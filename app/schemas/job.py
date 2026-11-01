from pydantic import BaseModel, Field
from typing import List, Optional


class JobPost(BaseModel):
    id: str
    title: str
    company: str
    location: str
    url: str
    posted_date: Optional[str] = "Recently"
    posted_age_hours: Optional[float] = 24.0
    experience_level: Optional[str] = "Mid-Senior"
    description: Optional[str] = ""
    source: str = "LinkedIn"


class JobMatchResult(BaseModel):
    job: JobPost
    match_percentage: float = Field(..., description="Calculated profile match percentage 0-100%")
    selection_probability: str = Field(..., description="'High', 'Moderate', or 'Low' chance of resume selection")
    matching_skills: List[str] = Field(default_factory=list, description="Skills present in both resume and job")
    missing_skills: List[str] = Field(default_factory=list, description="Key skills requested by job but missing in profile")
    match_summary: str = Field(..., description="Concise rationale for match rating and selection likelihood")
    selection_tips: List[str] = Field(default_factory=list, description="Actionable tips to maximize interview chances")
