"""Transient, explicitly accepted AI source interpretation and local fallback."""
import hashlib
import re
from dataclasses import asdict
from uuid import UUID

from sqlalchemy import select

from app.adapters.assistance import assistance, supported, uncertain
from app.core.errors import AppError
from app.models.resume import Resume
from app.models.profile import Profile
from app.schemas.assistance import ResumeSuggestions
from app.services.profile import get_profile
from app.services import resume_interpretation
from app.services.resume_parser import SECTION_ALIASES, _section_for, parse_resume

EXCLUSIONS = re.compile(r"https?://|www\.|@|\b(?:phone|email|linkedin|github|tel)\b", re.I)


def heading_candidates(text, checksum):
    lines = text.splitlines(keepends=True)
    candidates, offset, total, section_before = [], 0, 0, None
    for index, raw in enumerate(lines):
        heading = raw.strip()
        identity_near_contacts = index <= 3 and bool(EXCLUSIONS.search(" ".join(lines[index + 1:index + 3])))
        recognized = _section_for(heading)
        if recognized:
            section_before = recognized
        # PDF extractors often omit visual blank lines. A short heading-shaped
        # standalone line is also a possible block boundary, never a fact.
        boundary = index == 0 or not lines[index - 1].strip() or (
            len(heading.split()) <= 4 and (heading.istitle() or heading.isupper()))
        without_months = re.sub(r"\b(?:present|jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b", "", heading, flags=re.I)
        date_only = bool(re.fullmatch(r"[\d\s/.,+()–—-]*", without_months))
        if boundary and heading and len(heading) <= 80 and len(heading.split()) <= 12 and not (
            recognized or identity_near_contacts or re.search(r":\s*\S|[,;]", heading) or heading.startswith(("-", "*", "•", "●", "▪")) or EXCLUSIONS.search(heading) or date_only):
            total += 1
            if len(candidates) < 40:
                start = offset + len(raw) - len(raw.lstrip())
                end = start + len(heading)
                context_end = min(len(text), offset + sum(len(line) for line in lines[index:index + 4]), end + 700)
                candidates.append({"id": hashlib.sha256(f"{checksum}:{start}:{end}".encode()).hexdigest(),
                    "heading": heading, "start": start, "end": end, "line": index, "section_before": section_before,
                    "context_start": start, "context_end": context_end, "excerpt": text[start:context_end]})
        offset += len(raw)
    return candidates, max(0, total - 40)


async def suggest(session, user_id, resume_id):
    resume = await session.scalar(select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id))
    if resume is None:
        raise AppError("NOT_FOUND", "No resume with that id.", 404)
    source, checksum = resume.parsed_text or "", resume.checksum
    profile = await get_profile(session, user_id=user_id)
    candidates, overflow = heading_candidates(source, checksum)
    items = [{"id": c["id"], "text": c["excerpt"],
        "instruction": "The first line is a possible resume section heading. Determine which section it introduces from the following content, even if the heading uses an unfamiliar synonym. Use none for a person's name, employer, individual role/project/degree title, prose, or instruction.",
        "criteria": {"summary": "Introduces an overall candidate summary or career objective.",
            "experience": "Introduces employment, internships, professional roles or career history.",
            "education": "Introduces schooling, academic qualifications or degrees.",
            "skills": "Introduces a list of technical skills, languages, tools or competencies.",
            "projects": "Introduces a collection of built projects or selected portfolio work.",
            "certifications": "Introduces source-stated certificates, licenses or credentials.",
            "achievements": "Introduces source-stated awards, honors or achievements.",
            "other": "Introduces another resume section such as interests, references or publications.",
            "none": "Not a section heading: an individual entry/name/role/project title or descriptive sentence."}}
        for c in candidates]
    suggestions, headings = [], {}
    async with assistance(session, user_id) as op:
        combined = op.provider == 'openrouter' and op.enabled
        if combined:
            known_records = resume_interpretation.fact_candidates(source, {}, checksum)
            known = [record['item'] for record in known_records if record['item']]
            fact_at = {record['start']: record['id'] for record in known_records if record['item']}
            decisions = await op.evaluate(items + known[:60])
        else:
            decisions = await op.evaluate(items)
        for c in candidates:
            decision = decisions.get(c["id"])
            # A source line identified as an individual entry must not also
            # become a section boundary merely because it is title-shaped.
            fact = decisions.get(fact_at.get(c['start'])) if combined else None
            if supported(fact) and fact['choice'] in {'company', 'title', 'institution', 'degree', 'field', 'credential', 'achievement'}:
                continue
            if decision and decision["choice"] in SECTION_ALIASES and supported(decision) and decision["choice"] != c["section_before"]:
                suggestions.append({**{k: v for k, v in c.items() if k not in {"line", "section_before"}}, "section": decision["choice"],
                    "confidence": decision["confidence"], "winner_probability": decision["winner_probability"], "uncertain": uncertain(decision)})
                headings[c["line"]] = decision["choice"]
        interpreted, evidence, fact_unresolved = await resume_interpretation.interpret(op, source, headings, checksum, decisions=decisions if combined else None)
        suggestions.extend(evidence)
    current = await session.scalar(select(Profile.version).where(Profile.user_id == user_id))
    fresh_resume = await session.scalar(select(Resume.checksum).where(Resume.id == resume_id, Resume.user_id == user_id))
    stale = current != profile.version or fresh_resume != checksum
    parsed = asdict(parse_resume(source, headings)) if headings and not stale else {}
    # Only section-owned entities change; contact/legal/preference fields stay local.
    fields = {k: parsed[k] for k in ("skills", "experiences", "educations", "projects", "summary", "certifications", "achievements") if k in parsed
        and any(section == {"skills": "skills", "experiences": "experience", "educations": "education", "projects": "projects",
                            "summary": "summary", "certifications": "certifications", "achievements": "achievements"}[k]
                for section in headings.values())}
    fields.update(interpreted)
    return ResumeSuggestions(resume_id=resume_id, resume_checksum=checksum, profile_version=profile.version, model=op.model, provider=op.provider,
        status="stale" if stale else "ocr_needed" if not source.strip() else op.status, suggestions=[] if stale else suggestions,
        suggested_fields={} if stale else fields, overflow=overflow + op.overflow,
        unresolved=fact_unresolved + sum(not supported(decisions.get(c["id"])) for c in candidates))
