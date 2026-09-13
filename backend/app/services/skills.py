"""Shared skill vocabulary.

Used by both resume parsing and job parsing. It lives in one module not for
DRY but for correctness: Phase 4 compares candidate skills against job skills,
and two sides that normalise differently would compare unequal strings for the
same skill.

Matching is exact whole-word against the lexicon. Nothing is inferred, so a
skill that is absent stays absent (CLAUDE.md section 9).
"""

import re

# Canonical spellings. Deliberately conservative: an entry here will be
# reported as a job requirement whenever it appears, so ambiguous words that
# are also ordinary English are left out.
SKILL_LEXICON: frozenset[str] = frozenset(
    {
        # languages
        "python", "javascript", "typescript", "java", "kotlin", "swift", "go",
        # Bare "c" and "r" are deliberately absent: they appear constantly as
        # ordinary prose ("R&D", "option C") and a false positive here becomes a
        # false requirement in matching. "c++", "c#" and "objective-c" stay.
        "rust", "ruby", "php", "scala", "perl", "matlab", "sql", "bash",
        "shell", "powershell", "c++", "c#", "objective-c", "dart", "elixir",
        "haskell", "lua", "groovy", "vba", "cobol", "fortran", "julia",
        # frontend
        "react", "angular", "vue", "svelte", "next.js", "nuxt", "remix",
        "redux", "jquery", "html", "css", "sass", "less", "tailwind",
        "bootstrap", "webpack", "vite", "babel", "storybook", "web components",
        # backend / frameworks
        "node.js", "express", "nestjs", "django", "flask", "fastapi", "spring",
        "spring boot", "rails", "laravel", "asp.net", ".net", "graphql", "grpc",
        "rest", "soap", "websockets", "celery", "gunicorn", "uvicorn",
        # data
        "postgresql", "mysql", "mariadb", "sqlite", "oracle", "sql server",
        "mongodb", "redis", "elasticsearch", "opensearch", "cassandra",
        "dynamodb", "neo4j", "snowflake", "bigquery", "redshift", "databricks",
        "clickhouse", "sqlalchemy", "prisma", "hibernate", "kafka", "rabbitmq",
        "sqs", "airflow", "dbt", "spark", "hadoop", "hive", "flink", "etl",
        "data warehouse", "data modeling", "pandas", "numpy", "scipy",
        # cloud / infra
        "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "helm",
        "terraform", "ansible", "pulumi", "cloudformation", "jenkins",
        "github actions", "gitlab ci", "circleci", "argo cd", "ci/cd",
        "linux", "unix", "nginx", "apache", "serverless", "lambda", "ec2",
        "s3", "eks", "openshift", "prometheus", "grafana", "datadog",
        "splunk", "opentelemetry", "istio", "vagrant",
        # ml / ai
        "machine learning", "deep learning", "nlp", "computer vision",
        "pytorch", "tensorflow", "keras", "scikit-learn", "xgboost",
        "hugging face", "transformers", "llm", "rag", "langchain", "opencv",
        "mlops", "feature engineering", "a/b testing", "statistics",
        # practices / tooling
        "git", "github", "gitlab", "bitbucket", "jira", "confluence", "agile",
        "scrum", "kanban", "tdd", "unit testing", "integration testing",
        "pytest", "jest", "cypress", "playwright", "selenium", "junit",
        "code review", "pair programming", "microservices", "oauth", "jwt",
        "saml", "sso", "rest api", "api design", "accessibility", "seo",
        "figma", "sketch", "adobe xd", "wireframing", "prototyping",
        "product management", "stakeholder management", "salesforce",
        "sap", "workday", "tableau", "power bi", "looker", "excel",
    }
)

# Spellings that mean the same skill. Normalising both sides through this is
# what lets "Postgres" on a resume meet "postgresql" in a job description.
SKILL_ALIASES: dict[str, str] = {
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "node": "node.js",
    "nodejs": "node.js",
    "node js": "node.js",
    "reactjs": "react",
    "react.js": "react",
    "nextjs": "next.js",
    "vuejs": "vue",
    "vue.js": "vue",
    "angularjs": "angular",
    "postgres": "postgresql",
    "psql": "postgresql",
    "k8s": "kubernetes",
    "golang": "go",
    "ml": "machine learning",
    "dl": "deep learning",
    "nlp": "nlp",
    "gcp": "gcp",
    "amazon web services": "aws",
    "google cloud platform": "google cloud",
    "ms sql": "sql server",
    "mssql": "sql server",
    "mongo": "mongodb",
    "tf": "tensorflow",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "ci cd": "ci/cd",
    "cicd": "ci/cd",
    "restful": "rest",
    "restful api": "rest api",
    "dotnet": ".net",
    "c sharp": "c#",
    "csharp": "c#",
    "cpp": "c++",
    "github actions": "github actions",
}

# Longest first, so "github actions" is preferred over "github" and "c++" over
# a bare "c".
#
# The trailing guard excludes word characters, "+" and "#" but deliberately not
# ".": a skill at the end of a sentence ("...and Docker.") must still match,
# while "java" inside "javascript" and "c" inside "c++" must not.
_LEXICON_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?<![\w.+#-])" + re.escape(term) + r"(?![\w+#-])", re.IGNORECASE), term)
    for term in sorted(SKILL_LEXICON, key=len, reverse=True)
]


def normalize_skill(name: str) -> str:
    """Canonical form of a skill name, for comparison across both sides."""
    cleaned = name.strip().strip(".").lower()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return SKILL_ALIASES.get(cleaned, cleaned)


def extract_skills(text: str) -> list[str]:
    """Canonical skills named verbatim in `text`.

    Exact lexicon matches only — a skill the text does not name is not
    returned, so a job with an unremarkable description reports few or no
    skills rather than a guess.
    """
    if not text:
        return []

    found: list[str] = []
    seen: set[str] = set()
    for pattern, term in _LEXICON_PATTERNS:
        canonical = normalize_skill(term)
        if canonical in seen:
            continue
        if pattern.search(text):
            seen.add(canonical)
            found.append(canonical)
    return sorted(found)
