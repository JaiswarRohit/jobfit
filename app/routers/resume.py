from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from app.schemas.profile import UserProfile, ProfileInputRequest, ResumeParseResponse
from app.services.resume_service import ResumeService
from app.services.db_service import DBService

router = APIRouter(prefix="/api/resume", tags=["Resume & Profile"])


@router.post("/upload", response_model=ResumeParseResponse)
async def upload_resume(
    file: UploadFile = File(...),
    candidate_name: Optional[str] = Form("Candidate")
):
    """
    Upload a resume in PDF, DOCX, or TXT format.
    Automatically parses text, detects technical skills, estimates years of experience,
    and constructs candidate profile.
    """
    filename = file.filename.lower()
    content = await file.read()

    try:
        if filename.endswith(".pdf"):
            text = ResumeService.extract_text_from_pdf(content)
        elif filename.endswith(".docx"):
            text = ResumeService.extract_text_from_docx(content)
        elif filename.endswith(".txt"):
            text = content.decode("utf-8", errors="ignore")
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format. Please upload .pdf, .docx, or .txt"
            )

        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract readable text from the uploaded file."
            )

        profile = ResumeService.parse_profile(text, name=candidate_name)

        # Persist extracted profile and resume to SQLite Database
        DBService.save_user_profile({
            "candidate_name": profile.name,
            "primary_title": profile.title,
            "experience_years": profile.experience_years,
            "skills": profile.skills,
            "suggested_titles": profile.suggested_titles,
            "resume_filename": file.filename,
            "resume_text": text
        }, user_id=1)

        return ResumeParseResponse(
            success=True,
            message=f"Resume parsed successfully! Extracted {len(profile.skills)} skills.",
            profile=profile,
            extracted_skills_count=len(profile.skills)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process resume: {str(e)}")


@router.post("/parse-text", response_model=ResumeParseResponse)
async def parse_profile_text(request: ProfileInputRequest):
    """
    Parse a profile from raw text or structured skills input.
    """
    raw = request.resume_text or ""
    if not raw.strip() and request.skills:
        raw = f"{request.title}. Skills: {', '.join(request.skills)}. {request.summary}"

    if not raw.strip():
        raise HTTPException(status_code=400, detail="Please provide either resume_text or a list of skills.")

    profile = ResumeService.parse_profile(raw, name=request.name or "Candidate")
    
    # Merge any manually provided skills
    if request.skills:
        combined = set(profile.skills).union(set(request.skills))
        profile.skills = sorted(list(combined))

    if request.title:
        profile.title = request.title
    if request.experience_years:
        profile.experience_years = request.experience_years

    # Persist to SQLite Database
    DBService.save_user_profile({
        "candidate_name": profile.name,
        "primary_title": profile.title,
        "experience_years": profile.experience_years,
        "skills": profile.skills,
        "suggested_titles": profile.suggested_titles,
        "resume_text": profile.raw_text
    }, user_id=1)

    return ResumeParseResponse(
        success=True,
        message=f"Profile generated successfully with {len(profile.skills)} skills.",
        profile=profile,
        extracted_skills_count=len(profile.skills)
    )
