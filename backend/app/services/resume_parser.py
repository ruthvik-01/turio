"""Deterministic resume parsing (DATA_PIPELINE.md section 1, ADR-008).

Rules only: no model is involved, so a field the rules cannot establish stays
`None` rather than being guessed. Several heuristics here deliberately give up
and return `None` when the input is ambiguous - an empty field is recoverable,
a confidently wrong one is not.

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
        "internship", "internships", "internship experience",
    },
    "education": {"education", "academics", "academic background", "qualifications"},
    "skills": {
        "skills",
        "technical skills",
        "core competencies",
        "technologies",
        "technical proficiencies",
    },
    "projects": {"projects", "personal projects", "selected projects", "side projects",
                 "academic projects", "technical projects", "key projects"},
    "certifications": {"certifications", "certification", "certificates", "credentials", "licenses", "licenses and certifications"},
    "achievements": {"achievements", "achievement", "awards", "honors", "honours", "awards and achievements"},
    "other": {"interests", "languages", "references", "publications"},
}

_ALIAS_TO_SECTION = {
    alias: section for section, aliases in SECTION_ALIASES.items() for alias in aliases
}
_COMPACT_ALIAS_TO_SECTION = {"".join(alias.split()): section for alias, section in _ALIAS_TO_SECTION.items()}

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
_URL = re.compile(r"https?://[^\s,;)]+|(?:www\.)[^\s,;)]+|(?<![\w@./-])(?:linkedin\.com/in|github\.com)/[^\s,;)]+", re.IGNORECASE)
_BARE_URL = re.compile(r"(?<![\w@./-])(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+(?:com|me|dev|io|net|org|app|co|ai|in)\b(?:/[^\s,;)]+)?", re.I)

# Words that look like a name line but are not one.
_NAME_STOPWORDS = frozenset({"resume", "curriculum vitae", "cv", "bio", "profile"})
_MAX_NAME_WORDS = 5
_DECORATION = re.compile(r"^(?:last\s+updated\b.*|(?:.*?[-–—|]\s*)?page\s+\d+\s*(?:of|/)\s*\d+|\d+\s*/\s*\d+)\s*$", re.I)

_DESCRIPTION_START = re.compile(r"^(?:built|designed|developed|implemented|engineered|architected|automated|optimized|created|deployed|integrated|managed|led|worked|contributed|collaborated)\b", re.I)


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
    contact_email: str | None = None
    summary: str | None = None
    certifications: list[str] = field(default_factory=list)
    achievements: list[str] = field(default_factory=list)
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
    heading = _normalize_heading(stripped)
    compact = "".join(heading.split())
    if not compact or len(compact) > _MAX_HEADING_LENGTH:
        return None
    # Character-spaced typography may introduce spaces inside words. Only
    # exact known aliases collapse; never rewrite source prose or offsets.
    return _ALIAS_TO_SECTION.get(heading) or _COMPACT_ALIAS_TO_SECTION.get(compact)


def split_sections(text: str, heading_sections: dict[int, str] | None = None) -> dict[str, list[str]]:
    """Group the document's lines under the heading that precedes them."""
    sections: dict[str, list[str]] = {}
    current = "header"
    for index, line in enumerate(text.split("\n")):
        if _DECORATION.match(line.strip()) or re.fullmatch(r"\s*(?:\(cid:\d+\)|[\uf000-\uf8ff])+\s*", line):
            continue
        section = _section_for(line) or (heading_sections or {}).get(index)
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
    grouped, categorized = [], False
    category = re.compile(r"^[\w &/+-]{1,50}:\s*", re.I)
    for raw in lines:
        line = _strip_bullet(raw)
        match = category.match(line)
        if match:
            grouped.append(line[match.end():]); categorized = True
        elif line and categorized and not _BULLET_PREFIX.match(raw):
            grouped[-1] += " " + line
        else:
            grouped.append(line); categorized = False
    for line in grouped:
        protected = re.sub(r"\bci/cd\b", lambda m: m.group().replace("/", "\x01"), line, flags=re.I)
        protected = re.sub(r"\([^)]*\)", lambda m: m.group().replace(",", "\x02").replace(";", "\x03").replace("/", "\x01"), protected)
        for token in _SKILL_SEPARATORS.split(protected):
            token = token.replace("\x01", "/").replace("\x02", ",").replace("\x03", ";")
            name = token.strip(" .;:-")
            normalized = _normalize_skill(name)
            # A "skill" of one character or a whole sentence is a parsing
            # artefact, not a skill.
            if (len(normalized) < 2 and normalized not in {"c", "r"}) or len(normalized) > 60 or normalized in seen:
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

    parts = [part.strip(" .-–—|\ufffd") for part in re.split(r"\s*[|–—\ufffd]\s*|\s+at\s+|\s+-\s+", without_dates)]
    parts = [part for part in parts if part]
    if len(parts) < 2:
        parts = [part.strip(" .-–—|\ufffd") for part in re.split(r"\s*,\s*", without_dates) if part.strip(" .-–—|\ufffd")]
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
    def header(line):
        cleaned = _strip_bullet(line)
        title, company = _split_header_line(cleaned)
        return bool(title and company and len(cleaned) <= 180 and not _DESCRIPTION_START.match(cleaned))
    entries, current = [], []
    if any(header(line) for line in lines):
        seen_header = False
        for index, line in enumerate(lines):
            following = [v.strip() for v in lines[index + 1:index + 4] if v.strip()]
            multiline_header = (index > 0 and not lines[index - 1].strip()
                and bool(_TITLE_KEYWORDS & set(line.lower().split()))
                and not _DESCRIPTION_START.match(line.strip()) and len(line.split()) <= 8
                and len(following) >= 2 and (len(_dates_in(following[1])) >= 2
                    or (bool(_dates_in(following[1])) and bool(re.search(r"\b(?:present|current|ongoing)\b", following[1], re.I)))))
            if header(line) or multiline_header:
                if current:
                    entries.extend([current] if seen_header else _blocks(current))
                current = [line]
                seen_header = True
            elif line.strip() or not seen_header:
                current.append(line)
        if current: entries.append(current)
    else:
        entries = _blocks(lines)
    for block in entries:
        text = "\n".join(block)
        dates = _dates_in(text)
        title, company = _split_header_line(_strip_bullet(block[0]))
        if not title and not company and len(block) > 1 and all(
            len(line.strip()) <= 180 and not _DESCRIPTION_START.match(_strip_bullet(line)) for line in block[:2]):
            # An explicitly separate company and role line has the same
            # evidence as an inline header; preserve descriptions unchanged.
            title, company = _split_header_line(" | ".join(_strip_bullet(line) for line in block[:2]))
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
    degree_header = re.compile(r"^(?:b\.?\s*(?:tech|sc|e)\b|m\.?\s*(?:tech|sc)\b|mba\b|ph\.?d\b|bachelor\w*\b|master\w*\b|doctorate\b|diploma\b|(?:senior\s+)?secondary\b|high school\b)", re.I)
    entries, current = [], []
    if any(degree_header.match(_strip_bullet(line)) for line in lines):
        has_degree = False
        for index, line in enumerate(lines):
            cleaned = _strip_bullet(line)
            is_degree = bool(degree_header.match(cleaned))
            following = next((v for v in lines[index + 1:] if v.strip()), "")
            institution_first = (has_degree and index > 0 and not lines[index - 1].strip()
                                 and bool(_INSTITUTION_KEYWORDS & set(re.findall(r"[a-z]+", cleaned.lower())))
                                 and not is_degree and bool(degree_header.match(_strip_bullet(following))))
            if current and ((is_degree and has_degree) or institution_first):
                entries.append(current); current = []
                has_degree = False
            if line.strip(): current.append(line)
            has_degree |= is_degree
        if current: entries.append(current)
    else:
        entries = _blocks(lines)
    for block in entries:
        text = " ".join(_strip_bullet(line) for line in block)
        lowered = text.lower()
        dates = _dates_in(text)
        degree_line = next((_strip_bullet(line) for line in block if degree_header.match(_strip_bullet(line))), _strip_bullet(block[0]))

        degree_line = _MONTH_YEAR.sub("", degree_line)
        degree_line = _NUMERIC_MONTH_YEAR.sub("", degree_line)
        degree_line = _YEAR_ONLY.sub("", degree_line).strip(" .-–—|")
        degree = next(
            (part.strip() for part in re.split(r"\s*[|,–—]\s*", degree_line)
             if _DEGREE_KEYWORDS & set(re.findall(r"[a-z.]+", part.lower()))),
            None,
        )
        if degree:
            # "B.Tech in Computer Science" -> the field is reported separately,
            # so the degree should not repeat it.
            degree = re.split(r"\s+in\s+", degree, maxsplit=1, flags=re.IGNORECASE)[0].strip()
        school = re.match(r"(?i)^((?:Senior\s+)?Secondary\s*\([^)]*\)|High School)", degree_line)
        if school: degree = school.group(1)
        institution = next((part.strip() for line in block for part in re.split(r"\s*[|,–—]\s*", line)
            if _INSTITUTION_KEYWORDS & set(re.findall(r"[a-z]+", part.lower())) and not degree_header.match(part.strip())), None)
        if institution:
            institution = _MONTH_YEAR.sub("", institution)
            institution = _NUMERIC_MONTH_YEAR.sub("", institution)
            institution = _YEAR_ONLY.sub("", institution).strip(" .-–—|")
        field_match = re.search(r"\bin\s+([^|,]{2,100})", degree_line, re.I)
        field_name = field_match.group(1).strip().rstrip(".") if field_match else None
        if not field_name and degree:
            header_parts = re.split(r"\s*[,|]\s*", degree_line)
            if len(header_parts) > 1 and not school and not _INSTITUTION_KEYWORDS & set(re.findall(r"[a-z]+", header_parts[1].lower())):
                field_name = header_parts[1].strip() or None

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
    # Description bullets belong to their project, not to separate projects.
    # PDF normalization discards indentation, so use blank separators and
    # unbulleted/numbered headings rather than the generic entry splitter.
    blocks: list[list[str]] = []
    current: list[str] = []
    separated = False
    for index, line in enumerate(lines):
        if not line.strip():
            separated = True
            continue
        cleaned = _strip_bullet(line)
        if re.fullmatch(r"\d+", cleaned):
            continue  # Detached PDF hyperlink footnote marker, not a project.
        following = next((v for v in lines[index + 1:] if v.strip() and not re.fullmatch(r"\d+", v.strip())), "")
        numbered = bool(re.match(r"^\s*\d+[.)]\s+", line))
        bullet = bool(_BULLET_PREFIX.match(line))
        heading = (len(cleaned.split()) <= 10 and len(cleaned) <= 120 and not cleaned.endswith((".", "!", "?", ":", "-"))
                   and not _DESCRIPTION_START.match(cleaned)
                   and not re.match(r"(?i)^(technologies|tech stack|tools|stack)\s*:", cleaned))
        if current and heading and (
            numbered or (not bullet and (separated or _BULLET_PREFIX.match(following)
                or (_DESCRIPTION_START.match(following.strip()) and current[-1].rstrip().endswith((".", "!", "?")))))
        ):
            blocks.append(current)
            current = []
        current.append(line)
        separated = False
    if current:
        blocks.append(current)
    projects: list[ParsedProject] = []
    for block in blocks:
        name = re.split(r"\s+(?:https?://|www\.|github/|github\.com/)", _strip_bullet(block[0]), maxsplit=1)[0].strip()
        body = "\n".join(_strip_bullet(line) for line in block[1:])
        # Multiword skills and punctuation (Node.js, C++) must match intact.
        # Only source-stated skills or explicitly labelled technology lists
        # are extracted; nothing is inferred from a project's subject.
        source = "\n".join(block)
        technologies = [
            skill for skill in skills
            if re.search(r"(?<![\w+#])" + re.escape(skill) + r"(?![\w+#])", source, re.I)
        ]
        for line in block:
            explicit = re.match(r"(?i)^(?:technologies|tech stack|tools|stack)\s*:\s*(.+)$", _strip_bullet(line))
            if explicit:
                technologies.extend(_parse_skills([explicit.group(1)]))
        technologies = list({_normalize_skill(skill): skill for skill in technologies}.values())
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
    header = "\n".join(header_lines)
    urls = [url if re.match(r"https?://", url, re.I) else "https://" + url for url in dict.fromkeys(_URL.findall(header) + _BARE_URL.findall(header))]
    linkedin = next((url for url in urls if re.match(r"https?://(?:www\.)?linkedin\.com/in/[^/\s]+", url, re.I)), None)
    if linkedin is None:
        short = next((re.fullmatch(r"https?://(?:www\.)?linkedin\.com/([\w-]+)/?", url, re.I) for url in urls
            if re.fullmatch(r"https?://(?:www\.)?linkedin\.com/([\w-]+)/?", url, re.I)), None)
        handle = re.search(r"^\s*LinkedIn\s*:\s*@?([\w-]+)\s*$", header, re.I | re.M)
        username = short.group(1) if short else handle.group(1) if handle else None
        if username and username.casefold() not in {"in", "company", "jobs", "feed", "school", "learning"}:
            linkedin = "https://www.linkedin.com/in/" + username
    contact_source = re.sub(r"\(cid:\d+\)", "", _EMAIL.sub("", _URL.sub("", _BARE_URL.sub("", header))))
    phone_match = next((match for match in _PHONE.finditer(contact_source)
        if 8 <= len(re.sub(r"\D", "", match.group())) <= 15), None)
    email_match = _EMAIL.search(header)

    # Contact details are usually packed onto one line, so the location is
    # looked for in the pieces rather than in the whole line.
    segments = [
        part.strip()
        for line in header_lines
        for part in re.split(r"\s*[|•·#]\s*|\(cid:\d+\)", line)
    ]
    location = next((segment for segment in segments if _looks_like_location(segment)), None)
    if location is None:
        # Explicit marker supplied by some icon-font resumes, not a bare name.
        location = next((segment[1:].strip() for segment in segments if segment.startswith("+ ")
            and not re.search(r"\d|@|https?://", segment) and 1 < len(segment.split()) <= 6), None)

    return {
        "contact_email": email_match.group(0).strip() if email_match else None,
        "phone": phone_match.group(0).strip() if phone_match else None,
        "location": location,
        "linkedin_url": linkedin,
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
            and all(re.sub(r"[.,'’\-]", "", part).isalpha() for part in words)
        ):
            return candidate
    return None


def _parse_supplemental(lines: list[str]) -> list[str]:
    entries, separated = [], True
    for line in lines:
        if not line.strip():
            separated = True
            continue
        value = _strip_bullet(line)
        if entries and not separated and not _BULLET_PREFIX.match(line) and (
            value[:1].islower() or entries[-1].endswith("-")):
            entries[-1] += " " + value
        else:
            entries.append(value)
        separated = False
    return list(dict.fromkeys(entries))


def parse_resume(text: str, heading_sections: dict[int, str] | None = None) -> ParsedResume:
    sections = split_sections(text, heading_sections)
    header_lines = sections.get("header", [])
    contact = _extract_contact(header_lines, text)
    skills = _parse_skills(sections.get("skills", []))

    return ParsedResume(
        full_name=_extract_name(header_lines),
        contact_email=contact["contact_email"],
        summary="\n".join(line.strip() for line in sections.get("summary", []) if line.strip()) or None,
        certifications=_parse_supplemental(sections.get("certifications", [])),
        achievements=_parse_supplemental(sections.get("achievements", [])),
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
