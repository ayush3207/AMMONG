import json
import re
from typing import Any, Dict, List, Optional, Set
from openai import AsyncOpenAI

from app.core.config import settings
from app.core.logging import logger

# Curated high-frequency technical and professional skills for deterministic extraction
SKILL_TAXONOMY = {
    # Programming Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "c", "go", "golang", "ruby", "php", "rust", "swift", "kotlin", "scala", "r", "dart",
    # Frameworks & Libraries
    "react", "react.js", "next.js", "nextjs", "vue", "angular", "node.js", "nodejs", "express", "express.js", "fastapi", "flask", "django", "spring", "spring boot", "asp.net", ".net", "tailwind", "tailwindcss", "bootstrap", "graphql", "rest apis", "rest api", "html", "css",
    # Databases & Storage
    "sql", "mysql", "postgresql", "postgres", "sqlite", "mongodb", "redis", "cassandra", "elasticsearch", "oracle", "dynamodb", "firebase",
    # Cloud & DevOps
    "aws", "amazon web services", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s", "git", "github", "gitlab", "ci/cd", "cicd", "terraform", "ansible", "jenkins", "linux", "unix", "bash", "nginx",
    # Data Science & AI/ML
    "machine learning", "deep learning", "nlp", "computer vision", "tensorflow", "pytorch", "pandas", "numpy", "scikit-learn", "data analysis", "data visualization", "power bi", "tableau",
    # Architecture & Concepts
    "system design", "microservices", "object oriented programming", "oop", "data structures", "algorithms", "agile", "scrum", "unit testing", "tdd",
}

class LLMService:
    """
    LLM extraction and placement intelligence service.
    Uses LLM when configured, with a robust deterministic NLP fallback.
    """
    def __init__(self):
        self.client: Optional[AsyncOpenAI] = None
        if settings.LLM_API_KEY:
            client_kwargs = {"api_key": settings.LLM_API_KEY}
            if settings.LLM_BASE_URL:
                client_kwargs["base_url"] = settings.LLM_BASE_URL
            self.client = AsyncOpenAI(**client_kwargs)

    async def extract_student_profile(self, resume_text: str, target_role: str) -> Dict[str, Any]:
        """
        Extract student's technical skills and project evidence from resume text.
        """
        if self.client and settings.LLM_API_KEY:
            try:
                return await self._extract_with_llm(resume_text, target_role)
            except Exception as e:
                logger.warning(f"LLM extraction failed: {e}. Falling back to rule-based NLP extraction.")

        return self._extract_with_rules(resume_text)

    async def _extract_with_llm(self, resume_text: str, target_role: str) -> Dict[str, Any]:
        prompt = f"""You are AMMONG, an AI Student Placement Intelligence System.
Analyze this student resume for the target role: "{target_role}".

Extract:
1. All technical and relevant professional skills explicitly or implicitly demonstrated.
2. Distinct projects and work evidence mentioned (title and 1-line summary).

Respond ONLY with valid JSON in this exact structure:
{{
  "skills": ["Skill1", "Skill2", ...],
  "projects": ["Project Name: brief description with technologies", ...],
  "weaknesses": [
    {{"title": "Weakness Title", "problem": "Observed issue in resume", "suggestion": "Actionable fix"}}
  ]
}}

RESUME TEXT:
{resume_text[:4000]}
"""
        response = await self.client.chat.completions.create(
            model=settings.LLM_MODEL or "gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        return {
            "skills": data.get("skills", []),
            "projects": data.get("projects", []),
            "weaknesses": data.get("weaknesses", []),
        }

    def _extract_with_rules(self, resume_text: str) -> Dict[str, Any]:
        """
        Deterministic NLP extractor scanning for skills, projects, and evidence.
        """
        text_lower = resume_text.lower()
        extracted_skills: Set[str] = set()

        # Match against taxonomy
        for skill in SKILL_TAXONOMY:
            # Word boundary regex search
            pattern = r"(?:\b|_)" + re.escape(skill) + r"(?:\b|_)"
            if re.search(pattern, text_lower):
                # Standardize title casing
                if skill in ["sql", "aws", "gcp", "ci/cd", "cicd", "html", "css", "nlp", "ai", "ml", "oop", "tdd"]:
                    extracted_skills.add(skill.upper())
                elif skill in ["react.js", "next.js", "node.js", "express.js"]:
                    extracted_skills.add(skill.capitalize())
                elif skill == "fastapi":
                    extracted_skills.add("FastAPI")
                elif skill == "mongodb":
                    extracted_skills.add("MongoDB")
                elif skill == "postgresql":
                    extracted_skills.add("PostgreSQL")
                elif skill == "docker":
                    extracted_skills.add("Docker")
                elif skill == "kubernetes":
                    extracted_skills.add("Kubernetes")
                elif skill == "spring boot":
                    extracted_skills.add("Spring Boot")
                else:
                    extracted_skills.add(skill.title())

        # Extract projects / evidence lines
        projects: List[str] = []
        lines = [l.strip() for l in resume_text.split("\n") if l.strip()]
        in_project_section = False
        project_headers = ["projects", "personal projects", "academic projects", "key projects", "work experience", "experience"]

        for i, line in enumerate(lines):
            line_low = line.lower()
            if any(h in line_low for h in project_headers) and len(line) < 30:
                in_project_section = True
                continue
            if in_project_section:
                # If hit another major section, exit
                if any(h in line_low for h in ["education", "skills", "certifications", "hobbies", "awards"]) and len(line) < 25:
                    in_project_section = False
                    continue
                # Collect bullet points or project headers
                if len(line) > 20 and (line.startswith("•") or line.startswith("-") or line.startswith("*") or ":" in line):
                    cleaned_line = re.sub(r"^[•\-\*]\s*", "", line)
                    projects.append(cleaned_line)
                    if len(projects) >= 6:
                        break

        # Check for resume weaknesses heuristically
        weaknesses: List[Dict[str, str]] = []
        has_metrics = bool(re.search(r"\b\d+%\b|\b\d+x\b|\bincreased\b|\breduced\b|\bimproved by\b", text_lower))
        if not has_metrics:
            weaknesses.append({
                "title": "Achievements & Metrics",
                "problem": "Your project descriptions list responsibilities but lack measurable results or metrics.",
                "suggestion": "Convert duty statements into achievement statements with measurable outcomes (e.g. 'improved latency by 25%')."
            })

        has_deploy = any(w in text_lower for w in ["deployed", "production", "hosted", "aws", "docker", "ci/cd", "kubernetes"])
        if not has_deploy:
            weaknesses.append({
                "title": "Deployment & Production Evidence",
                "problem": "Limited evidence of deployment, containers, or production environment usage.",
                "suggestion": "Highlight deployed links or mention containerization tools like Docker for your applications."
            })

        weaknesses.append({
            "title": "Technical Evidence",
            "problem": "Some listed technical skills do not clearly link to specific project outcomes.",
            "suggestion": "Explicitly link each core skill to the project where it was actively applied."
        })

        weaknesses.append({
            "title": "Role Alignment",
            "problem": "Resume layout could prioritize key technical competencies higher on the page.",
            "suggestion": "Lead with relevant tools and frameworks at the top of your technical skills section."
        })

        return {
            "skills": sorted(list(extracted_skills)),
            "projects": projects[:5],
            "weaknesses": weaknesses,
        }

    # ── Skill Roadmap Generation ──────────────────────────────────────────

    async def generate_skill_roadmap(
        self,
        skill_gaps: List[str],
        partial_skills: List[str],
        target_role: str,
    ) -> List[Dict[str, Any]]:
        """
        Generate a practical learning roadmap for missing and partial skills.
        Uses LLM when available, deterministic templates otherwise.
        """
        if not skill_gaps and not partial_skills:
            return []

        if self.client and settings.LLM_API_KEY:
            try:
                return await self._roadmap_with_llm(skill_gaps, partial_skills, target_role)
            except Exception as e:
                logger.warning(f"LLM roadmap generation failed: {e}. Falling back to rule-based.")

        return self._roadmap_with_rules(skill_gaps, partial_skills, target_role)

    async def _roadmap_with_llm(
        self,
        skill_gaps: List[str],
        partial_skills: List[str],
        target_role: str,
    ) -> List[Dict[str, Any]]:
        """Ask the LLM to generate structured roadmaps for each weak skill."""
        all_skills = []
        for s in skill_gaps:
            all_skills.append({"skill": s, "status": "Missing"})
        for s in partial_skills:
            all_skills.append({"skill": s, "status": "Needs Improvement"})

        # Cap at 10 to stay within token limits
        all_skills = all_skills[:10]

        prompt = f"""You are AMMONG, an AI Student Placement Intelligence System.
A student is targeting the role: "{target_role}".

The following skills are either missing or need improvement in their resume:
{json.dumps(all_skills, indent=2)}

For EACH skill, generate a practical learning roadmap:
- "skill": exact skill name (string)
- "status": "Missing" or "Needs Improvement" (string)
- "priority": "High" (core role requirement), "Medium" (useful supporting skill), or "Low" (optional)
- "why_required": 1 concise sentence explaining why this skill is required for {target_role} (string)
- "learning_steps": 4-5 concrete step-by-step learning progression from beginner to job-ready (array of strings)
- "topics": 3-5 key topics to study (array of strings)
- "practice_project": One practical, hands-on mini project to solidify the skill (string)
- "estimated_duration": realistic duration like "5-7 days" or "1-2 weeks" (string)

RULES:
- Do NOT invent student experience. This is for skills they LACK.
- Keep learning_steps actionable and beginner-friendly.
- Prioritize core skills for {target_role}.

Respond ONLY with valid JSON: {{ "roadmap": [ ... ] }}
"""
        response = await self.client.chat.completions.create(
            model=settings.LLM_MODEL or "gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        items = data.get("roadmap", [])
        for item in items:
            if "learning_steps" in item and "steps" not in item:
                item["steps"] = item["learning_steps"]
            elif "steps" in item and "learning_steps" not in item:
                item["learning_steps"] = item["steps"]
        return items

    def _roadmap_with_rules(
        self,
        skill_gaps: List[str],
        partial_skills: List[str],
        target_role: str,
    ) -> List[Dict[str, Any]]:
        """Deterministic roadmap generator using curated templates."""
        roadmap = []
        role_lower = target_role.lower()

        def _priority(skill: str) -> str:
            s = skill.lower()
            if any(kw in role_lower for kw in ["data", "ml", "machine learning", "ai", "scientist"]):
                if s in {"python", "machine learning", "deep learning", "pytorch", "tensorflow", "scikit-learn", "numpy", "pandas"}:
                    return "High"
                if s in {"sql", "statistics", "data preprocessing", "model evaluation", "feature engineering", "git", "mlops", "spark"}:
                    return "Medium"
                return "Low"
            if any(kw in role_lower for kw in ["backend", "server", "api"]):
                if s in {"docker", "sql", "python", "java", "node.js", "rest api", "spring boot", "fastapi", "postgresql", "mysql"}:
                    return "High"
                if s in {"redis", "microservices", "linux", "git", "ci/cd", "mongodb"}:
                    return "Medium"
                return "Low"
            if any(kw in role_lower for kw in ["frontend", "ui", "web"]):
                if s in {"react", "javascript", "typescript", "html/css", "html", "css", "next.js"}:
                    return "High"
                if s in {"tailwind css", "tailwind", "git", "redux", "web performance", "responsive design"}:
                    return "Medium"
                return "Low"
            if any(kw in role_lower for kw in ["devops", "cloud", "sre"]):
                if s in {"docker", "kubernetes", "aws", "ci/cd", "linux", "terraform"}:
                    return "High"
                if s in {"git", "bash", "ansible", "monitoring", "python"}:
                    return "Medium"
                return "Low"
            if any(kw in role_lower for kw in ["full stack", "fullstack", "software"]):
                if s in {"python", "java", "javascript", "typescript", "react", "node.js", "sql", "git", "docker"}:
                    return "High"
                if s in {"rest apis", "data structures & algorithms", "linux", "ci/cd", "unit testing", "system design"}:
                    return "Medium"
                return "Low"
            return "Medium"

        def _why_required(skill: str) -> str:
            s = skill.lower()
            whys = {
                "pytorch": "Used for building, training, and deploying deep learning neural network architectures.",
                "tensorflow": "Industry-standard framework for building and deploying production deep learning models.",
                "scikit-learn": "Core Python library for classical machine learning algorithms, preprocessing, and evaluation.",
                "machine learning": "Fundamental discipline for developing predictive models and intelligent algorithms.",
                "deep learning": "Powers modern computer vision, NLP, and generative AI systems in machine learning.",
                "numpy": "Foundational numerical computation library for vectorized array operations in Python.",
                "pandas": "Standard library for data cleaning, transformation, and exploratory data analysis.",
                "mlops": "Automates machine learning lifecycles from continuous integration to production deployment and monitoring.",
                "data preprocessing": "Ensures training data is correctly scaled, cleaned, and encoded for optimal model performance.",
                "feature engineering": "Extracts predictive domain attributes to substantially improve model accuracy.",
                "model evaluation": "Measures validation metrics and prevents overfitting prior to production release.",
                "statistics": "Provides the mathematical foundation for hypothesis testing, distributions, and predictive modeling.",
                "docker": f"Docker is commonly used to package and deploy applications for {target_role} positions.",
                "kubernetes": f"Kubernetes orchestrates containerized applications, a key skill for {target_role} roles.",
                "aws": f"AWS is the leading cloud platform, widely required in {target_role} job postings.",
                "python": f"Python is the primary language for {target_role} positions.",
                "java": f"Java is widely used in enterprise {target_role} systems.",
                "javascript": f"JavaScript is essential for web and full-stack {target_role} roles.",
                "typescript": f"TypeScript adds type safety, preferred in professional {target_role} teams.",
                "react": f"React is the leading frontend library for building modern {target_role} user interfaces.",
                "node.js": f"Node.js powers server-side runtime environments in {target_role} tech stacks.",
                "sql": f"SQL is fundamental for relational database querying in {target_role} positions.",
                "git": f"Git version control is essential for collaborative engineering in {target_role} teams.",
                "linux": f"Linux server administration is commonly required for {target_role} positions.",
                "ci/cd": f"CI/CD pipelines automate testing and deployment in modern {target_role} teams.",
                "fastapi": f"FastAPI is a high-performance Python framework for building production APIs.",
                "spring boot": f"Spring Boot is a leading enterprise Java framework for {target_role} services.",
                "spark": "Apache Spark enables large-scale distributed data processing and machine learning.",
            }
            return whys.get(s, f"{skill} is a relevant skill for {target_role} positions based on industry requirements.")

        def _steps(skill: str) -> List[str]:
            s = skill.lower()
            templates = {
                "pytorch": [
                    "Learn PyTorch tensors, operations, and autograd",
                    "Understand neural network fundamentals with torch.nn",
                    "Build data loading pipelines using Dataset and DataLoader",
                    "Implement training loops, loss functions, and optimizers",
                    "Build and evaluate an image classification or NLP model",
                ],
                "tensorflow": [
                    "Learn TensorFlow 2.x and Keras Sequential & Functional APIs",
                    "Build, compile, and train neural network models",
                    "Implement convolutional and recurrent layers",
                    "Use tf.data for high-performance data loading",
                    "Export and serve a trained model with TensorFlow Serving",
                ],
                "scikit-learn": [
                    "Master dataset train/test splitting and cross-validation",
                    "Train and evaluate linear models, decision trees, and random forests",
                    "Perform hyperparameter tuning with GridSearchCV",
                    "Build reproducible preprocessing and modeling Pipelines",
                    "Evaluate models using ROC-AUC, precision-recall, and confusion matrices",
                ],
                "machine learning": [
                    "Understand supervised vs unsupervised learning paradigms",
                    "Implement core algorithms: regression, classification, clustering",
                    "Master regularization techniques (L1/L2) and bias-variance tradeoff",
                    "Learn cross-validation, feature scaling, and metric selection",
                    "Train and deploy a complete predictive ML model",
                ],
                "deep learning": [
                    "Understand artificial neural networks, activation functions, and backpropagation",
                    "Build convolutional neural networks (CNNs) for image tasks",
                    "Learn sequence modeling with RNNs, LSTMs, and Transformers",
                    "Apply transfer learning with pre-trained models",
                    "Fine-tune a model on a custom task and evaluate performance",
                ],
                "numpy": [
                    "Master N-dimensional array creation, indexing, and slicing",
                    "Learn broadcasting rules and vectorized mathematical operations",
                    "Perform matrix multiplications and linear algebra with np.linalg",
                    "Use boolean indexing and fancy masking",
                    "Implement a simple algorithm from scratch using pure NumPy",
                ],
                "pandas": [
                    "Master Series and DataFrame indexing, filtering, and selection",
                    "Handle missing data, type casting, and string manipulation",
                    "Use groupby, aggregations, and pivot tables",
                    "Merge, join, and concatenate multiple datasets",
                    "Perform time-series resampling and window operations",
                ],
                "mlops": [
                    "Learn experiment tracking and model registry with MLflow",
                    "Version datasets and models using DVC",
                    "Package ML models into Docker containers for inference",
                    "Set up automated CI/CD testing pipelines for model code",
                    "Implement model monitoring for data and concept drift",
                ],
                "data preprocessing": [
                    "Detect and impute missing data using mean/median and KNN",
                    "Encode categorical features with One-Hot and Target encoding",
                    "Scale numerical features using StandardScaler and RobustScaler",
                    "Identify and handle outliers with IQR and Z-scores",
                    "Assemble preprocessing steps into a reusable Scikit-learn Pipeline",
                ],
                "feature engineering": [
                    "Create interaction features and mathematical ratios",
                    "Extract datetime components and cyclical sinusoidal encodings",
                    "Extract text features using TF-IDF and word embeddings",
                    "Apply dimensionality reduction using PCA",
                    "Select top predictive features using mutual information and SHAP values",
                ],
                "model evaluation": [
                    "Understand precision, recall, F1, ROC-AUC, and PR curves",
                    "Analyze confusion matrices and residual plots",
                    "Implement Stratified K-Fold cross-validation for imbalanced data",
                    "Detect overfitting and underfitting using learning curves",
                    "Calibrate predicted probabilities for deployment",
                ],
                "statistics": [
                    "Master descriptive statistics: mean, median, variance, and standard deviation",
                    "Understand probability distributions: Normal, Binomial, Poisson",
                    "Perform hypothesis tests: t-tests, ANOVA, Chi-Square",
                    "Interpret p-values, confidence intervals, and effect sizes",
                    "Design and analyze an A/B test with sample size calculations",
                ],
                "docker": [
                    "Learn Docker basics: images, containers, and command-line tools",
                    "Write a multi-stage Dockerfile for a backend or ML app",
                    "Use Docker Compose to run an application alongside a database",
                    "Manage persistent storage with Docker volumes",
                    "Optimize image size and security for production",
                ],
                "sql": [
                    "Master SELECT, WHERE, GROUP BY, and HAVING queries",
                    "Perform INNER, LEFT, RIGHT, and FULL OUTER JOINs",
                    "Write subqueries, Common Table Expressions (CTEs), and Window Functions",
                    "Understand indexes, execution plans, and query optimization",
                    "Design a normalized relational schema with constraints",
                ],
                "git": [
                    "Learn Git basics: init, add, commit, push, pull, log",
                    "Practice branching, merging, and rebasing workflows",
                    "Create pull requests and conduct code reviews on GitHub",
                    "Resolve merge conflicts cleanly",
                    "Use Git tags, stashing, and interactive rebase",
                ],
                "python": [
                    "Master Python syntax, data structures, and comprehensions",
                    "Write object-oriented code with classes, methods, and inheritance",
                    "Learn file handling, context managers, and exception handling",
                    "Use virtual environments and dependency managers (pip, poetry)",
                    "Build a modular project with unit tests using pytest",
                ],
            }
            if s in templates:
                return templates[s]
            return [
                f"Learn core concepts and syntax of {skill}",
                f"Complete hands-on tutorials and exercises for {skill}",
                f"Build a small practical component demonstrating {skill}",
                f"Study industry best practices and architecture patterns for {skill}",
                f"Integrate {skill} into an end-to-end portfolio project for {target_role}",
            ]

        def _topics(skill: str) -> List[str]:
            s = skill.lower()
            topic_map = {
                "pytorch": ["Tensors & Autograd", "torch.nn Modules", "DataLoaders", "Loss & Optimizers", "Model Checkpointing"],
                "tensorflow": ["Keras API", "Sequential vs Functional", "tf.data Pipelines", "Callbacks", "SavedModel Export"],
                "scikit-learn": ["Pipelines", "Cross-Validation", "Ensemble Methods", "Hyperparameter Tuning", "Classification Metrics"],
                "machine learning": ["Supervised Learning", "Unsupervised Learning", "Regularization", "Bias-Variance Tradeoff", "Cross-Validation"],
                "deep learning": ["Neural Networks", "Backpropagation", "CNNs", "Transformers", "Transfer Learning"],
                "numpy": ["Arrays & Broadcasting", "Vectorization", "Linear Algebra", "Array Manipulation", "Random Sampling"],
                "pandas": ["DataFrames", "Data Cleaning", "GroupBy & Aggregation", "Merging & Joins", "Time Series"],
                "mlops": ["Experiment Tracking", "Model Registry", "Containerization", "CI/CD for ML", "Model Monitoring"],
                "data preprocessing": ["Imputation", "Encoding", "Feature Scaling", "Outlier Treatment", "ColumnTransformer"],
                "feature engineering": ["Feature Extraction", "Polynomial Features", "PCA", "Feature Selection", "SHAP Values"],
                "model evaluation": ["ROC-AUC", "F1 Score", "Confusion Matrix", "Learning Curves", "Cross-Validation"],
                "statistics": ["Probability Distributions", "Hypothesis Testing", "p-values", "A/B Testing", "Confidence Intervals"],
                "docker": ["Images & Containers", "Dockerfile", "Docker Compose", "Volumes & Networks", "Multi-stage Builds"],
                "sql": ["SELECT & JOINs", "Window Functions", "CTEs", "Indexes & Optimization", "Schema Design"],
                "git": ["Branching & Merging", "Pull Requests", "Conflict Resolution", "Git Rebase", "Git Workflows"],
                "python": ["OOP & Design Patterns", "Data Structures", "Generators & Decorators", "Virtual Environments", "Unit Testing"],
            }
            if s in topic_map:
                return topic_map[s]
            return [f"{skill} fundamentals", f"{skill} best practices", f"{skill} practical patterns", f"Testing with {skill}"]

        def _practice(skill: str) -> str:
            s = skill.lower()
            projects = {
                "pytorch": "Build an image classification model using PyTorch.",
                "tensorflow": "Build a sentiment analysis classifier using TensorFlow/Keras.",
                "scikit-learn": "Build an end-to-end customer churn prediction pipeline with Scikit-learn.",
                "machine learning": "Train and tune a housing price prediction system with feature engineering.",
                "deep learning": "Fine-tune a pre-trained Vision Transformer or BERT model on a custom dataset.",
                "numpy": "Implement a 2-layer neural network from scratch using only NumPy arrays.",
                "pandas": "Clean, transform, and analyze a messy 50,000-row e-commerce dataset.",
                "mlops": "Build an automated ML training and tracking pipeline using MLflow and Docker.",
                "data preprocessing": "Create a reusable tabular data preprocessing pipeline with ColumnTransformer.",
                "feature engineering": "Engineer 10+ new features that improve baseline model performance on Kaggle data.",
                "model evaluation": "Perform in-depth evaluation and threshold calibration on an imbalanced fraud dataset.",
                "statistics": "Design, simulate, and statistically analyze an A/B test with hypothesis testing.",
                "docker": "Dockerize a Python backend application with a PostgreSQL database.",
                "sql": "Design an e-commerce database schema and write 10 complex analytical queries with window functions.",
                "git": "Create a GitHub repository with branches, pull requests, and automated GitHub Actions tests.",
                "python": "Build a CLI application with argparse, modular classes, and pytest coverage.",
            }
            return projects.get(s, f"Build a practical hands-on project that demonstrates {skill} usage for {target_role}.")

        def _duration(skill: str) -> str:
            s = skill.lower()
            durations = {
                "pytorch": "5-7 days", "tensorflow": "1-2 weeks", "scikit-learn": "1-2 weeks",
                "machine learning": "2-3 weeks", "deep learning": "3-4 weeks", "numpy": "3-5 days",
                "pandas": "5-7 days", "mlops": "2-3 weeks", "data preprocessing": "3-5 days",
                "feature engineering": "1-2 weeks", "model evaluation": "3-5 days", "statistics": "1-2 weeks",
                "docker": "5-7 days", "sql": "1-2 weeks", "git": "3-5 days", "python": "2-3 weeks",
                "kubernetes": "2-3 weeks", "aws": "2-3 weeks", "react": "2-3 weeks", "node.js": "1-2 weeks",
            }
            return durations.get(s, "1-2 weeks")

        # Build roadmap for gaps (Missing)
        for skill in skill_gaps:
            steps = _steps(skill)
            roadmap.append({
                "skill": skill,
                "status": "Missing",
                "priority": _priority(skill),
                "why_required": _why_required(skill),
                "learning_steps": steps,
                "steps": steps,
                "topics": _topics(skill),
                "practice_project": _practice(skill),
                "estimated_duration": _duration(skill),
            })

        # Build roadmap for partial skills (Needs Improvement)
        for skill in partial_skills:
            steps = _steps(skill)
            roadmap.append({
                "skill": skill,
                "status": "Needs Improvement",
                "priority": _priority(skill),
                "why_required": _why_required(skill),
                "learning_steps": steps,
                "steps": steps,
                "topics": _topics(skill),
                "practice_project": _practice(skill),
                "estimated_duration": _duration(skill),
            })

        # Sort by priority: High > Medium > Low
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        roadmap.sort(key=lambda x: priority_order.get(x["priority"], 1))

        return roadmap


llm_service = LLMService()

