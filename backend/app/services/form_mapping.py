"""Conservative, deterministic canonical mapping. Unknown facts remain questions."""

import re
from functools import lru_cache

from pydantic import EmailStr, TypeAdapter, ValidationError

from app.core.errors import AppError
from app.ml.scoring import digest

ALIASES = {
    "full_name": {"full name", "name", "legal name"},
    "email": {"email", "email address"},
    "phone": {"phone", "phone number", "telephone"},
    "location": {"location", "current location", "city", "current city"},
    "linkedin_url": {"linkedin", "linkedin url", "linkedin profile"},
    "github_url": {"github", "github url"},
    "portfolio_url": {"portfolio", "portfolio url", "website", "personal website"},
    "resume": {"resume", "cv", "resume cv", "upload resume", "resume upload", "upload resume cv", "resume cv upload", "curriculum vitae", "upload your resume", "resume pdf"},
    "work_authorization_status": {"work authorization", "work authorization status"},
    "sponsorship_required": {"sponsorship required", "require sponsorship", "do you require visa sponsorship"},
}


def normalize_label(label: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", label.casefold().replace("résumé", "resume")).split())


@lru_cache(maxsize=2048)
def intent(label: str, input_type: str) -> str:
    key = normalize_label(label)
    for name, aliases in ALIASES.items():
        if key in aliases:
            return name
    return "custom"  # Never infer sensitive intent from a keyword in a longer question.


def question_key(field) -> str:
    return digest([normalize_label(field.label), field.input_type, field.options])


def profile_value(field, profile, email, resume_id):
    canonical = field.normalized_intent
    if canonical == "email":
        value = email
    elif canonical == "resume":
        value = str(resume_id) if resume_id else None
    elif canonical != "custom":
        value = getattr(profile, canonical, None)
    else:
        value = None
    if value is not None and field.input_type == "select":
        target = ("yes" if value else "no") if isinstance(value, bool) else str(value).casefold()
        value = next((str(o["value"]) for o in field.options if str(o["value"]).casefold() == target or o["label"].casefold() == target), None)
    return value


def has_value(value) -> bool:
    return value is not None and (not isinstance(value, str) or bool(value.strip()))


def validate_answer(field, value, resume_id):
    if not has_value(value):
        return None
    if isinstance(value, str) and len(value) > 10000:
        raise AppError("MISSING_REQUIRED_FIELD", "Application answers must be at most 10,000 characters.", 422)
    if field.input_type == "checkbox":
        if not isinstance(value, bool):
            raise AppError("MISSING_REQUIRED_FIELD", "Choose yes or no for the checkbox.", 422)
    elif not isinstance(value, str):
        raise AppError("MISSING_REQUIRED_FIELD", "This field requires a text value.", 422)
    if field.input_type == "select" and value not in [str(o["value"]) for o in field.options]:
        raise AppError("MISSING_REQUIRED_FIELD", "Choose an available option.", 422)
    if field.normalized_intent == "resume" and value != str(resume_id):
        raise AppError("FORBIDDEN", "Only the selected, user-owned resume can be uploaded.", 403)
    if field.input_type == "email":
        try:
            TypeAdapter(EmailStr).validate_python(value)
        except ValidationError as exc:
            raise AppError("MISSING_REQUIRED_FIELD", "Enter a valid email address.", 422) from exc
    return value


def complete(field, answer) -> bool:
    if not answer or not answer.user_confirmed or not has_value(answer.value):
        return False
    # Required checkbox is consent, not merely a known boolean.
    return not (field.input_type == "checkbox" and field.required and answer.value is not True)
