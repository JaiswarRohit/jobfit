import re
import io
from typing import List, Set, Tuple
from pypdf import PdfReader
import docx
from app.schemas.profile import UserProfile

# Comprehensive dictionary of technical, engineering, and data skills
KNOWN_SKILLS = {
    # Programming Languages
    "python", "javascript", "typescript", "java", "c++", "c#", "go", "golang", "rust",
    "ruby", "php", "swift", "kotlin", "scala", "r", "sql", "bash", "shell", "html", "css",
    
    # Frameworks & Libraries
    "fastapi", "django", "flask", "express", "nodejs", "node.js", "react", "react.js",
    "next.js", "vue", "vue.js", "angular", "spring", "spring boot", "laravel", "rails",
    "ruby on rails", "asp.net", ".net", "dotnet", "tailwind", "bootstrap",
    
    # Databases & Caching
    "postgresql", "postgres", "mysql", "mongodb", "sqlite", "redis", "elasticsearch",
    "dynamodb", "cassandra", "neo4j", "supabase", "firebase", "mariadb", "oracle",
    
    # Cloud & DevOps
    "aws", "amazon web services", "azure", "gcp", "google cloud", "docker", "kubernetes",
    "k8s", "terraform", "ansible", "ci/cd", "github actions", "gitlab ci", "jenkins",
    "helm", "nginx", "linux", "git", "github", "bitbucket",
    
    # Architecture & APIs
    "rest", "restful api", "rest api", "graphql", "grpc", "microservices", "websockets",
    "kafka", "rabbitmq", "celery", "message queues", "system design", "distributed systems",
    "jwt", "oauth", "oauth2", "openapi", "swagger",
    
    # AI / ML / Data Science
    "machine learning", "deep learning", "nlp", "llm", "genai", "generative ai",
    "pytorch", "tensorflow", "scikit-learn", "sklearn", "pandas", "numpy",
    "langchain", "llamaindex", "huggingface", "opencv", "computer vision",
    
    # Methodologies & Tools
    "agile", "scrum", "jira", "unit testing", "pytest", "tdd", "postman", "playwright", "selenium"
}


class ResumeService:
    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        """Extract text from PDF bytes."""
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            return "\n".join(text_parts).strip()
        except Exception as e:
            raise ValueError(f"Failed to parse PDF: {str(e)}")

    @staticmethod
    def extract_text_from_docx(file_bytes: bytes) -> str:
        """Extract text from DOCX bytes."""
        try:
            doc = docx.Document(io.BytesIO(file_bytes))
            text_parts = [p.text for p in doc.paragraphs if p.text.strip()]
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            text_parts.append(cell.text.strip())
            return "\n".join(text_parts).strip()
        except Exception as e:
            raise ValueError(f"Failed to parse DOCX: {str(e)}")

    @classmethod
    def extract_skills(cls, text: str) -> List[str]:
        """Extract matched technical skills from text using boundary-safe matching."""
        normalized_text = text.lower()
        extracted: Set[str] = set()

        for skill in KNOWN_SKILLS:
            # Escape regex special chars like c++, .net, c#
            escaped_skill = re.escape(skill)
            # Match with word boundaries, taking care of symbols
            pattern = rf"(?:\b|(?<=[\s,./(])){escaped_skill}(?:\b|(?=[\s,./)]))"
            if re.search(pattern, normalized_text):
                # Standardize capitalization for presentation
                clean_name = cls.format_skill_name(skill)
                extracted.add(clean_name)

        return sorted(list(extracted))

    @staticmethod
    def format_skill_name(skill: str) -> str:
        """Present skills with standard industry casing."""
        casing_map = {
            "fastapi": "FastAPI",
            "aws": "AWS",
            "gcp": "GCP",
            "ci/cd": "CI/CD",
            "rest api": "REST API",
            "restful api": "RESTful API",
            "api": "API",
            "graphql": "GraphQL",
            "grpc": "gRPC",
            "k8s": "Kubernetes",
            "nodejs": "Node.js",
            "node.js": "Node.js",
            "postgresql": "PostgreSQL",
            "postgres": "PostgreSQL",
            "mongodb": "MongoDB",
            "mysql": "MySQL",
            "sqlite": "SQLite",
            "redis": "Redis",
            "docker": "Docker",
            "kubernetes": "Kubernetes",
            "scikit-learn": "Scikit-Learn",
            "sklearn": "Scikit-Learn",
            "pytorch": "PyTorch",
            "tensorflow": "TensorFlow",
            "llm": "LLM",
            "nlp": "NLP",
            "genai": "Generative AI",
            "jwt": "JWT",
            "oauth": "OAuth2",
            "oauth2": "OAuth2",
            "html": "HTML5",
            "css": "CSS3",
            "javascript": "JavaScript",
            "typescript": "TypeScript",
            "c++": "C++",
            "c#": "C#",
            "github actions": "GitHub Actions",
            "vue": "Vue.js",
            "vue.js": "Vue.js",
            "react": "React",
            "react.js": "React",
            "next.js": "Next.js"
        }
        return casing_map.get(skill.lower(), skill.title())

    @classmethod
    def estimate_experience_years(cls, text: str) -> float:
        """Estimate years of experience from resume text."""
        patterns = [
            r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+experience",
            r"experience:\s*(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)",
            r"total\s+experience:\s*(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)"
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    pass
        return 2.0  # sensible default if unspecified

    @classmethod
    def extract_target_title(cls, text: str) -> str:
        """Extract or infer primary role/title."""
        common_titles = [
            "Senior Python Developer", "Python Developer", "Full Stack Developer",
            "Backend Developer", "Software Engineer", "Senior Software Engineer",
            "FastAPI Developer", "DevOps Engineer", "Machine Learning Engineer",
            "Data Engineer", "Frontend Developer"
        ]
        for title in common_titles:
            if re.search(rf"\b{re.escape(title)}\b", text, re.IGNORECASE):
                return title
        return "Software Engineer"

    @classmethod
    def generate_suggested_titles(
        cls,
        text: str,
        skills: List[str],
        primary_title: str,
        exp_years: float = 2.0
    ) -> List[str]:
        """Suggest 3 to 4 tailored target job titles based on resume skills and experience."""
        skills_lower = set(s.lower() for s in skills)
        is_senior = exp_years >= 4.0 or "senior" in text.lower() or "lead" in text.lower() or "senior" in primary_title.lower()
        prefix = "Senior " if is_senior else ""

        candidates: List[str] = []

        # 1. Primary Title if specific
        if primary_title and primary_title != "Software Engineer":
            candidates.append(primary_title)

        # 2. FastAPI / Python backend focus
        if "fastapi" in skills_lower:
            candidates.append(f"{prefix}FastAPI Developer")
            candidates.append(f"{prefix}Python Backend Engineer")

        if "python" in skills_lower:
            candidates.append(f"{prefix}Python Developer")
            candidates.append(f"{prefix}Backend Software Engineer")
            if any(s in skills_lower for s in ["docker", "aws", "postgresql", "gcp"]):
                candidates.append(f"{prefix}Python Cloud Engineer")

        # 3. Full Stack check
        if any(s in skills_lower for s in ["react", "vue", "javascript", "typescript", "html", "css"]):
            if "python" in skills_lower:
                candidates.append(f"{prefix}Full Stack Python Developer")
            else:
                candidates.append(f"{prefix}Full Stack Engineer")

        # 4. AI / Data / ML check
        if any(s in skills_lower for s in ["machine learning", "llm", "genai", "pytorch", "tensorflow", "pandas"]):
            candidates.append(f"{prefix}Machine Learning Engineer")
            candidates.append(f"{prefix}AI Backend Developer")

        # 5. Cloud / DevOps check
        if any(s in skills_lower for s in ["kubernetes", "docker", "terraform", "ci/cd"]):
            candidates.append(f"{prefix}DevOps / Cloud Platform Engineer")

        # Fallback defaults if few skills detected
        default_pool = [
            f"{prefix}Software Engineer",
            f"{prefix}Backend Developer",
            f"{prefix}Python API Engineer",
            f"{prefix}Application Developer"
        ]
        for def_title in default_pool:
            if def_title not in candidates:
                candidates.append(def_title)

        # Deduplicate while preserving order and pick exactly 3 to 4 titles
        seen = set()
        results = []
        for c in candidates:
            clean = c.strip()
            if clean.lower() not in seen:
                seen.add(clean.lower())
                results.append(clean)
            if len(results) == 4:
                break

        return results

    @classmethod
    def parse_profile(cls, text: str, name: str = "Candidate") -> UserProfile:
        """Parse raw resume text into a structured UserProfile."""
        skills = cls.extract_skills(text)
        exp_years = cls.estimate_experience_years(text)
        title = cls.extract_target_title(text)
        suggested_titles = cls.generate_suggested_titles(
            text=text,
            skills=skills,
            primary_title=title,
            exp_years=exp_years
        )

        # Build a concise summary from the first 400 characters
        summary = text[:400].replace("\n", " ").strip()
        if len(text) > 400:
            summary += "..."

        return UserProfile(
            name=name,
            title=title,
            skills=skills,
            experience_years=exp_years,
            suggested_titles=suggested_titles,
            summary=summary,
            raw_text=text
        )
