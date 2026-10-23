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
    "linkedin_url": {"linkedin", "linkedin url", "linkedin profile", "linkedin profile url", "linkedin profile link", "linkedin page"},
    "github_url": {"github", "github url", "github profile", "github profile url", "github profile link"},
    "portfolio_url": {"portfolio", "portfolio url", "website", "personal website"},
    "summary": {"summary", "professional summary", "profile summary"},
    "certifications": {"certifications", "certificates", "licenses and certifications"},
    "achievements": {"achievements", "awards", "awards and achievements"},
    "resume": {"resume", "cv", "resume cv", "upload resume", "resume upload", "upload resume cv", "resume cv upload", "curriculum vitae", "upload your resume", "resume pdf"},
    "work_authorization_status": {"work authorization", "work authorization status"},
    "sponsorship_required": {"sponsorship required", "require sponsorship", "do you require visa sponsorship"},
}

CONTACT_FACTS = {"full_name", "email", "phone", "location", "linkedin_url", "github_url", "portfolio_url"}


def normalize_label(label: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", label.casefold().replace("résumé", "resume")).split())


@lru_cache(maxsize=2048)
def intent(label: str, input_type: str) -> str:
    key = normalize_label(label)
    factual_key = re.sub(r"^(?:please )?(?:share|provide|enter|what is) (?:your )?", "", key)
    factual_key = re.sub(r" (?:optional|required)$", "", factual_key)
    factual_key = re.sub(r"^(?:link|url) to (?:your )?", "", factual_key)
    for name, aliases in ALIASES.items():
        if key in aliases or (name in CONTACT_FACTS and factual_key in aliases):
            return name
    return "custom"  # Never infer sensitive intent from a keyword in a longer question.


def legacy_question_key(field) -> str:
    return digest([normalize_label(field.label), field.input_type, field.options])


def question_key(field) -> str:
    canonical = intent(field.label, field.input_type)
    if canonical in CONTACT_FACTS and field.input_type in {"text", "email", "tel", "url"}:
        return digest(["contact_fact", canonical])
    return legacy_question_key(field)


def profile_value(field, profile, email, resume_id):
    canonical = field.normalized_intent
    if canonical == "email":
        value = getattr(profile, "contact_email", None) or email
    elif canonical == "resume":
        value = str(resume_id) if resume_id else None
    elif canonical != "custom":
        value = getattr(profile, canonical, None)
    else:
        value = None
    if canonical in {"certifications", "achievements"}:
        value = "\n".join(value) if isinstance(value, list) else value
    if value is not None and field.input_type == "select":
        target = ("yes" if value else "no") if isinstance(value, bool) else str(value).casefold()
        value = next((str(o["value"]) for o in field.options if str(o["value"]).casefold() == target or o["label"].casefold() == target), None)
    return value


def has_value(value) -> bool:
    return value is not None and (bool(value) if isinstance(value, list) else not isinstance(value, str) or bool(value.strip()))


def reusable(field) -> bool:
    return not (field.input_type == "checkbox" and field.required)


def salary_help(label: str, input_type: str, employer_hint: str | None = None) -> str | None:
    context = " ".join([label, employer_hint or ""])
    if not re.search(r"\b(?:salary|compensation|pay expectation|expected pay)\b", context, re.I):
        return employer_hint
    currencies = {"USD": "US dollars", "INR": "Indian rupees", "EUR": "euros", "GBP": "British pounds",
                  "CAD": "Canadian dollars", "AUD": "Australian dollars", "SGD": "Singapore dollars",
                  "AED": "UAE dirhams", "NZD": "New Zealand dollars"}
    found = [code for code, name in currencies.items() if re.search(r"\b" + code + r"\b|\b" + name + r"\b", context, re.I)]
    if not found:
        found = [code for symbol, code in [("US$", "USD"), ("₹", "INR"), ("€", "EUR")] if symbol in context]
    currency = ", ".join(f"{code} ({currencies[code]})" for code in found) if found else "not specified by employer"
    period = next((name for name, pattern in [("annual", r"per annum|annual|yearly|per year|/year"),
        ("monthly", r"monthly|per month|/month"), ("hourly", r"hourly|per hour|/hour")] if re.search(pattern, context, re.I)), "not specified by employer")
    numeric = input_type == "number" or bool(re.search(r"(?:numbers|digits) only", context, re.I))
    suffix = {"annual": "/year", "monthly": "/month", "hourly": "/hour"}.get(period, "/year")
    example = f"{found[0]} 120000{suffix}" if found else f"USD 120000{suffix} or INR 1200000{suffix}"
    format_help = "Enter numbers only, e.g. 120000; check the posting for currency and pay period." if numeric else f"Include currency and pay period, e.g. {example}."
    guidance = f"Currency: {currency}. Pay period: {period}. {format_help}"
    return f"{employer_hint} {guidance}" if employer_hint else guidance


def validate_answer(field, value, resume_id):
    if not has_value(value):
        return None
    if isinstance(value, str) and len(value) > 10000:
        raise AppError("MISSING_REQUIRED_FIELD", "Application answers must be at most 10,000 characters.", 422)
    if field.input_type == "multiselect":
        if (not isinstance(value, list) or len(value) > 100 or any(not isinstance(v, str) for v in value)
            or len(set(value)) != len(value) or not set(value) <= {str(o["value"]) for o in field.options}):
            raise AppError("MISSING_REQUIRED_FIELD", "Choose available options without duplicates.", 422)
        return value
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
