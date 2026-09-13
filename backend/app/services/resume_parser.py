"""Deterministic resume parsing (DATA_PIPELINE.md section 1, ADR-008).

Rules only: no model is involved, so a field the rules cannot establish stays
`None` rather than being guessed. Several heuristics here deliberately give up
and return `None` when the input is ambiguous - an empty field is recoverable,
a confidently wrong one is not (CLAUDE.md section 9).

Sensitive attributes (work authorization, sponsorship) are never derived from a
resume at all; they are collected explicitly in a later phase.
"""

import re
from dataclasses import dataclass, field
from datetime import date

from app.services.skills import normalize_skill as _normalize_skill

SECTION_ALIASES: dict[str, set[str]] = {
    "summary": {"summary", "profile", "objective", "about", "about me"},
    "experience": {
        "experience",
        "work experience",
        "professional experience",
        "employment",
        "employment history",
        "work history",
    },
    "education": {"education", "academics", "academic background", "qualifications"},
    "skills": {
        "skills",
        "technical skills",
        "core competencies",
        "technologies",
        "technical proficiencies",
    },
    "projects": {"projects", "personal projects", "selected projects", "side projects"},
}

_ALIAS_TO_SECTION = {
    alias: section for section, aliases in SECTION_ALIASES.items() for alias in aliases
}

# A heading is a short line whose text is exactly one of the known aliases.
_MAX_HEADING_LENGTH = 40

_BULLET_PREFIX = re.compile(r"^\s*(?:[-•▪◦*·‣]|\d+[.)])\s*")
_SKILL_SEPARATORS = re.compile(r"\s*[,;|•·/]\s*|\s{2,}")

_TITLE_KEYWORDS = frozenset(
    {
        "engineer", "developer", "manager", "analyst", "intern", "internship",
        "consultant", "designer", "architect", "scientist", "lead", "director",
        "specialist", "associate", "administrator", "coordinator", "officer",
        "technician", "researcher", "founder", "president", "trainee",
    }
)
_DEGREE_KEYWORDS = frozenset(
    {
        "b.tech", "btech", "b.e", "be", "b.sc", "bsc", "bachelor", "bachelors",
        "m.tech", "mtech", "m.sc", "msc", "master", "masters", "mba", "phd",
        "doctorate", "diploma", "associate degree", "high school",
    }
)
_INSTITUTION_KEYWORDS = frozenset(
    {"university", "college", "institute", "institution", "school", "academy", "polytechnic"}
)

_MONTH_NUMBERS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10,
    "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}
_MONTH_YEAR = re.compile(
    r"\b(" + "|".join(_MONTH_NUMBERS) + r")[a-z]*\.?,?\s+(\d{4})\b", re.IGNORECASE
)
_NUMERIC_MONTH_YEAR = re.compile(r"\b(\d{1,2})/(\d{4})\b")
_YEAR_ONLY = re.compile(r"\b((?:19|20)\d{2})\b")
_PRESENT = re.compile(r"\b(present|current|now|ongoing)\b", re.IGNORECASE)

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")
_URL = re.compile(r"https?://[^\s,;)]+|(?:www\.)[^\s,;)]+", re.IGNORECASE)

# Words that look like a name line but are not one.
_NAME_STOPWORDS = frozenset({"resume", "curriculum vitae", "cv", "bio", "profile"})
_MAX_NAME_WORDS = 5


@dataclass(frozen=True)
class ParsedExperience:
    company: str | None = None
    title: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = None


@dataclass(frozen=True)
class ParsedEducation:
    institution: str | None = None
    degree: str | None = None
    field: str | None = None
    start_date: date | None = None
    end_date: date | None = None


@dataclass(frozen=True)
class ParsedProject:
    name: str | None = None
    description: str | None = None
    technologies: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ParsedResume:
    full_name: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    skills: list[str] = field(default_factory=list)
    experiences: list[ParsedExperience] = field(default_factory=list)
    educations: list[ParsedEducation] = field(default_factory=list)
    projects: list[ParsedProject] = field(default_factory=list)


def _normalize_heading(line: str) -> str:
    return line.strip().rstrip(":").strip().lower()


def _section_for(line: str) -> str | None:
    stripped = line.strip()
    if not stripped or len(stripped) > _MAX_HEADING_LENGTH:
        return None
    heading = _normalize_heading(stripped)
    if heading in _ALIAS_TO_SECTION:
        return _ALIAS_TO_SECTION[heading]
    # "TECHNICAL SKILLS" and "Technical Skills" are headings; a sentence that
    # merely contains the word is not.
    if stripped.isupper() and heading in _ALIAS_TO_SECTION:
        return _ALIAS_TO_SECTION[heading]
    return None


def split_sections(text: str) -> dict[str, list[str]]:
    """Group the document's lines under the heading that precedes them."""
    sections: dict[str, list[str]] = {}
    current = "header"
    for line in text.split("\n"):
        section = _section_for(line)
        if section is not None:
            current = section
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return sections


def _strip_bullet(line: str) -> str:
    return _BULLET_PREFIX.sub("", line).strip()


def _to_date(year: str, month: str | None) -> date | None:
    try:
        return date(int(year), int(month) if month else 1, 1)
    except ValueError:
        return None


def _dates_in(text: str) -> list[date]:
    """Every date the text states, in the order it states them."""
    found: list[tuple[int, date]] = []
    for match in _MONTH_YEAR.finditer(text):
        parsed = _to_date(match.group(2), str(_MONTH_NUMBERS[match.group(1).lower()]))
        if parsed:
            found.append((match.start(), parsed))
    for match in _NUMERIC_MONTH_YEAR.finditer(text):
        parsed = _to_date(match.group(2), match.group(1))
        if parsed:
            found.append((match.start(), parsed))
    if not found:
        for match in _YEAR_ONLY.finditer(text):
            parsed = _to_date(match.group(1), None)
            if parsed:
                found.append((match.start(), parsed))
    return [value for _, value in sorted(found, key=lambda item: item[0])]


def _blocks(lines: list[str]) -> list[list[str]]:
    """Split a section into entries at blank lines or top-level bullets."""
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if not line.strip():
            if current:
                blocks.append(current)
                current = []
            continue
        starts_entry = bool(_BULLET_PREFIX.match(line)) and current
        if starts_entry:
            blocks.append(current)
            current = [line]
            continue
        current.append(line)
    if current:
        blocks.append(current)
    return blocks


def _parse_skills(lines: list[str]) -> list[str]:
    skills: list[str] = []
    seen: set[str] = set()
    for line in lines:
        for token in _SKILL_SEPARATORS.split(_strip_bullet(line)):
            name = token.strip(" .;:-")
            normalized = _normalize_skill(name)
            # A "skill" of one character or a whole sentence is a parsing
            # artefact, not a skill.
            if len(normalized) < 2 or len(normalized) > 60 or normalized in seen:
                continue
            if not re.search(r"[a-z]", normalized):
                continue
            seen.add(normalized)
            skills.append(name.strip())
    return skills


def _split_header_line(line: str) -> tuple[str | None, str | None]:
    """Return (title, company) when the line can be read unambiguously."""
    # Dates are removed but the separators between fields are kept: they are
    # what the split below depends on.
    without_dates = re.sub(
        r"\b(?:" + "|".join(_MONTH_NUMBERS) + r")[a-z]*\.?\s*(?:19|20)\d{2}\b",
        " ",
        line,
        flags=re.IGNORECASE,
    )
    without_dates = _PRESENT.sub(" ", without_dates)
    without_dates = re.sub(r"\b(?:19|20)\d{2}\b", " ", without_dates)

    parts = [part.strip(" .-–—|") for part in re.split(r"\s*[|–—]\s*|\s+at\s+|\s*,\s*", without_dates)]
    parts = [part for part in parts if part]
    if len(parts) != 2:
        return None, None

    looks_like_title = [bool(_TITLE_KEYWORDS & set(part.lower().split())) for part in parts]
    if looks_like_title[0] and not looks_like_title[1]:
        return parts[0], parts[1]
    if looks_like_title[1] and not looks_like_title[0]:
        return parts[1], parts[0]
    # Ambiguous ordering - report neither rather than guess which is which.
    return None, None


def _parse_experiences(lines: list[str]) -> list[ParsedExperience]:
    experiences: list[ParsedExperience] = []
    for block in _blocks(lines):
        text = "\n".join(block)
        dates = _dates_in(text)
        title, company = _split_header_line(_strip_bullet(block[0]))
        description_lines = [_strip_bullet(line) for line in block[1:] if line.strip()]
        experiences.append(
            ParsedExperience(
                company=company,
                title=title,
                start_date=dates[0] if dates else None,
                end_date=dates[1] if len(dates) > 1 else None,
                description="\n".join(description_lines) or None,
            )
        )
    return experiences


def _parse_educations(lines: list[str]) -> list[ParsedEducation]:
    educations: list[ParsedEducation] = []
    for block in _blocks(lines):
        text = " ".join(_strip_bullet(line) for line in block)
        lowered = text.lower()
        dates = _dates_in(text)

        degree = next(
            (part.strip() for part in re.split(r"\s*[|,–—]\s*", text)
             if _DEGREE_KEYWORDS & set(re.findall(r"[a-z.]+", part.lower()))),
            None,
        )
        if degree:
            # "B.Tech in Computer Science" -> the field is reported separately,
            # so the degree should not repeat it.
            degree = re.split(r"\s+in\s+", degree, maxsplit=1, flags=re.IGNORECASE)[0].strip()
        institution = next(
            (part.strip() for part in re.split(r"\s*[|,–—]\s*", text)
             if _INSTITUTION_KEYWORDS & set(re.findall(r"[a-z]+", part.lower()))),
            None,
        )
        field_match = re.search(r"\bin\s+([A-Z][\w\s&]{2,60}?)(?:[.,|]|$)", text)
        field_name = field_match.group(1).strip() if field_match else None

        # A single date on an education entry is conventionally the graduation
        # year, so it becomes end_date here rather than start_date. The value
        # comes from the document; only its role is rule-assigned.
        if len(dates) > 1:
            start_date, end_date = dates[0], dates[1]
        elif dates:
            start_date, end_date = None, dates[0]
        else:
            start_date = end_date = None

        if not any((degree, institution, field_name, start_date, end_date)):
            continue
        educations.append(
            ParsedEducation(
                institution=institution,
                degree=degree,
                field=field_name,
                start_date=start_date,
                end_date=end_date,
            )
        )
    return educations


def _parse_projects(lines: list[str], skills: list[str]) -> list[ParsedProject]:
    known = {_normalize_skill(skill) for skill in skills}
    projects: list[ParsedProject] = []
    for block in _blocks(lines):
        name = _strip_bullet(block[0])
        body = " ".join(_strip_bullet(line) for line in block[1:])
        tokens = re.findall(r"[A-Za-z][\w.+#-]*", body)
        technologies = sorted({token for token in tokens if _normalize_skill(token) in known})
        projects.append(
            ParsedProject(
                name=name or None,
                description=body or None,
                technologies=technologies,
            )
        )
    return projects


def _looks_like_location(segment: str) -> bool:
    """`San Francisco, CA` yes; a job title or an email line no.

    Requiring a comma keeps this from claiming a bare word that could be
    anything. A location written without one is left null rather than guessed.
    """
    if not segment or len(segment) > 60 or "," not in segment:
        return False
    if _EMAIL.search(segment) or _URL.search(segment) or "@" in segment:
        return False
    if re.search(r"\d", segment):
        return False
    return 1 < len(segment.split()) <= 5


def _extract_contact(header_lines: list[str], text: str) -> dict[str, str | None]:
    urls = _URL.findall(text)
    phone_match = _PHONE.search(text)

    # Contact details are usually packed onto one line, so the location is
    # looked for in the pieces rather than in the whole line.
    segments = [
        part.strip()
        for line in header_lines
        for part in re.split(r"\s*[|•·]\s*", line)
    ]
    location = next((segment for segment in segments if _looks_like_location(segment)), None)

    return {
        "phone": phone_match.group(0).strip() if phone_match else None,
        "location": location,
        "linkedin_url": next((url for url in urls if "linkedin.com" in url.lower()), None),
        "github_url": next((url for url in urls if "github.com" in url.lower()), None),
        "portfolio_url": next(
            (
                url
                for url in urls
                if "linkedin.com" not in url.lower() and "github.com" not in url.lower()
            ),
            None,
        ),
    }


def _extract_name(header_lines: list[str]) -> str | None:
    for line in header_lines:
        candidate = _strip_bullet(line)
        if not candidate or _EMAIL.search(candidate) or _URL.search(candidate):
            continue
        lowered = candidate.lower()
        if lowered in _NAME_STOPWORDS or _section_for(candidate) is not None:
            continue
        words = candidate.split()
        # A name line is short, has no digits, and is not a sentence.
        if (
            1 < len(words) <= _MAX_NAME_WORDS
            and not any(char.isdigit() for char in candidate)
            and all(part.strip(".,'-").isalpha() for part in words)
        ):
            return candidate
        return None
    return None


def parse_resume(text: str) -> ParsedResume:
    sections = split_sections(text)
    header_lines = sections.get("header", [])
    contact = _extract_contact(header_lines, text)
    skills = _parse_skills(sections.get("skills", []))

    return ParsedResume(
        full_name=_extract_name(header_lines),
        phone=contact["phone"],
        location=contact["location"],
        linkedin_url=contact["linkedin_url"],
        github_url=contact["github_url"],
        portfolio_url=contact["portfolio_url"],
        skills=skills,
        experiences=_parse_experiences(sections.get("experience", [])),
        educations=_parse_educations(sections.get("education", [])),
        projects=_parse_projects(sections.get("projects", []), skills),
    )
