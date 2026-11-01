from pydantic import BaseModel, Field
from typing import List, Optional


class UserProfile(BaseModel):
    name: Optional[str] = Field(default="Candidate", description="Name of the applicant")
    title: Optional[str] = Field(default="Software Engineer", description="Current or target job title")
    skills: List[str] = Field(default_factory=list, description="Extracted technical and professional skills")
    experience_years: Optional[float] = Field(default=0.0, description="Estimated years of professional experience")
    suggested_titles: List[str] = Field(default_factory=list, description="3 to 4 recommended target job titles inferred from resume")
    summary: Optional[str] = Field(default="", description="Executive summary or bio")
    raw_text: str = Field(default="", description="Full extracted text from resume or input")


class ProfileInputRequest(BaseModel):
    name: Optional[str] = "Candidate"
    title: Optional[str] = "Python Developer"
    skills: List[str] = []
    experience_years: Optional[float] = 2.0
    summary: Optional[str] = ""
    resume_text: Optional[str] = ""


class ResumeParseResponse(BaseModel):
    success: bool
    message: str
    profile: UserProfile
    extracted_skills_count: int
