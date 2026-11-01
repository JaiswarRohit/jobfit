import math
from typing import List, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.schemas.profile import UserProfile
from app.schemas.job import JobPost, JobMatchResult
from app.services.resume_service import ResumeService


class MatchingService:
    @classmethod
    def calculate_match(
        cls,
        profile: UserProfile,
        job: JobPost
    ) -> JobMatchResult:
        """
        Calculate deep percentage match, selection probability, skill overlap,
        and recommendations between a user's profile and a job post.
        100% Free - uses TF-IDF, N-gram cosine similarity, and skill extraction.
        """
        job_full_text = f"{job.title} {job.company} {job.description}"
        profile_skills = set(s.lower() for s in profile.skills)
        job_skills = set(s.lower() for s in ResumeService.extract_skills(job_full_text))

        # 1. Skill Overlap Calculation
        matching_skills_raw = profile_skills.intersection(job_skills)
        missing_skills_raw = job_skills - profile_skills

        matching_skills = [ResumeService.format_skill_name(s) for s in sorted(list(matching_skills_raw))]
        missing_skills = [ResumeService.format_skill_name(s) for s in sorted(list(missing_skills_raw))]

        if len(job_skills) > 0:
            skill_score = len(matching_skills_raw) / len(job_skills)
        else:
            # If job didn't explicitly list specific keywords, base it on candidate skills count
            skill_score = 0.5 if len(profile.skills) > 0 else 0.2

        # 2. Semantic TF-IDF Similarity
        corpus = [profile.raw_text or " ".join(profile.skills), job_full_text]
        try:
            vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
            tfidf_matrix = vectorizer.fit_transform(corpus)
            semantic_score = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
        except Exception:
            semantic_score = 0.3

        # 3. Title & Role Seniority Alignment
        title_score = 0.0
        job_title_lower = job.title.lower()
        user_title_lower = (profile.title or "").lower()

        user_title_words = [w for w in user_title_lower.split() if len(w) > 3]
        if user_title_words:
            matched_words = [w for w in user_title_words if w in job_title_lower]
            title_score = len(matched_words) / len(user_title_words)
        else:
            title_score = 0.5

        # 4. Composite Match Percentage
        # Weights: 50% Skills Overlap, 35% Semantic/Contextual match, 15% Title alignment
        raw_percentage = (skill_score * 50.0) + (semantic_score * 35.0) + (title_score * 15.0)

        # Scale bonus if key skills match
        if len(matching_skills) >= 4:
            raw_percentage += 10.0
        elif len(matching_skills) >= 2:
            raw_percentage += 5.0

        # Experience Alignment Check
        exp_years = profile.experience_years or 2.0
        job_exp = (job.experience_level or "").lower()
        if exp_years < 2.0 and any(w in job_exp for w in ["senior", "lead", "director"]):
            # Significant seniority gap: penalize match to avoid showing mismatched senior roles to freshers
            raw_percentage -= 15.0
        elif exp_years >= 4.0 and any(w in job_exp for w in ["intern", "entry"]):
            # Overqualified
            raw_percentage -= 10.0
        elif (exp_years >= 4.0 and "senior" in job_exp) or (exp_years <= 3.0 and "associate" in job_exp):
            raw_percentage += 5.0

        # Bound to 5% - 98%
        match_percentage = round(min(max(raw_percentage, 5.0), 98.0), 1)

        # 5. Selection Likelihood & Rationale
        if match_percentage >= 78.0:
            selection_probability = "Very High"
            summary = (
                f"Exceptional alignment! Resume covers {len(matching_skills)} primary requirements "
                f"including {', '.join(matching_skills[:3])}. Experience level matches {job.experience_level or 'role'}. High ATS selection probability."
            )
        elif match_percentage >= 65.0:
            selection_probability = "High"
            summary = (
                f"Strong candidate match. Primary stack ({', '.join(matching_skills[:3]) if matching_skills else 'core stack'}) "
                f"and experience level ({job.experience_level or 'Mid-Senior'}) align well. Very likely to be shortlisted."
            )
        elif match_percentage >= 50.0:
            selection_probability = "Moderate"
            summary = (
                f"Good foundational qualifications with {len(matching_skills)} matching skills. "
                f"Highlighting {', '.join(missing_skills[:2]) if missing_skills else 'project depth'} will increase selection rate."
            )
        else:
            selection_probability = "Low"
            summary = "Partial match. Notable skill or experience gap for this specific role."

        # 6. Actionable Selection Tips
        selection_tips = []
        if matching_skills:
            selection_tips.append(f"Emphasize your hands-on experience in {', '.join(matching_skills[:2])} prominently in your summary.")
        if missing_skills:
            selection_tips.append(f"Address {missing_skills[0]} in your application or demonstrate fast-learning capability.")
        if job.posted_date:
            selection_tips.append(f"Posted {job.posted_date} — apply immediately while this posting is fresh!")
        else:
            selection_tips.append("Apply within 24-48 hours of posting for maximum visibility.")

        return JobMatchResult(
            job=job,
            match_percentage=match_percentage,
            selection_probability=selection_probability,
            matching_skills=matching_skills,
            missing_skills=missing_skills,
            match_summary=summary,
            selection_tips=selection_tips
        )

    @classmethod
    def rank_jobs_by_match(
        cls,
        profile: UserProfile,
        jobs: List[JobPost],
        min_match_percentage: float = 50.0,
        sort_by: str = "recent",
        experience_level: Optional[str] = "all"
    ) -> List[JobMatchResult]:
        """
        Rank and filter jobs by criteria.
        Default sequence: Newest / Most Recent first as top priority!
        Ties are broken by match percentage.
        """
        results: List[JobMatchResult] = []
        exp_key = (experience_level or "all").lower().strip()

        for job in jobs:
            # Check hard experience clash if user specified an experience level
            if exp_key and exp_key != "all":
                j_exp = (job.experience_level or "").lower()
                if exp_key == "entry" and any(k in j_exp for k in ["director", "lead", "principal"]):
                    continue
                if exp_key == "director" and any(k in j_exp for k in ["intern", "entry"]):
                    continue

            match_res = cls.calculate_match(profile, job)
            if match_res.match_percentage >= min_match_percentage:
                results.append(match_res)

        # Sequence Sorting:
        # If sort_by is 'recent' (default), newest jobs (lowest posted_age_hours) are top priority!
        # Secondary sort key is highest match percentage.
        if sort_by == "recent":
            results.sort(key=lambda x: (
                x.job.posted_age_hours if x.job.posted_age_hours is not None else 999.0,
                -x.match_percentage
            ))
        else:
            # Sort by highest match percentage
            results.sort(key=lambda x: (
                -x.match_percentage,
                x.job.posted_age_hours if x.job.posted_age_hours is not None else 999.0
            ))

        return results
