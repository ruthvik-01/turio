"""Non-sensitive form intents only; values never leave the local profile."""
import json
import re

from app.adapters.jev import assistance, supported
from app.ml.scoring import digest

INTENTS = {"full_name", "email", "phone", "location", "linkedin_url", "github_url", "portfolio_url", "resume"}
DESCRIPTIONS = {
    "full_name": "Applicant's name: how to address or call the person by name, not their postal address.",
    "email": "Applicant's email address for recruiter messages or updates. An email control asking where to send updates requests this address even without the word email in its label.",
    "phone": "Applicant's telephone/mobile number to reach them.",
    "location": "Applicant's physical city/country/current residence, not their name or salutation.",
    "linkedin_url": "Applicant's LinkedIn or professional-network profile URL.",
    "github_url": "Applicant's GitHub or source-code profile URL.",
    "portfolio_url": "Applicant's personal website or work-showcase/portfolio URL.",
    "resume": "Upload the applicant's stored resume/CV document.",
}
SENSITIVE = re.compile(r"\b(?:authori[sz]\w*|sponsor\w*|visa|citizen\w*|national(?:ity)?|gender|sex|race|racial|ethnic\w*|veteran\w*|disabil\w*|consent|agree\w*|certif\w*|attest\w*|salary|pay|compensation|criminal|religion|birth|age|legal\w*|pronouns?|marital)\b|work\s+(?:permit|permission|eligib\w*)|(?:right|allowed)\s+to\s+work|employment\s+eligib\w*", re.I)


def choices(input_type):
    return {"email": {"email"}, "tel": {"phone"}, "url": {"linkedin_url", "github_url", "portfolio_url"},
            "file": {"resume"}}.get(input_type, INTENTS - {"resume"})


def fingerprint(field):
    return digest([field.field_key, field.label, field.input_type, field.required, field.options, field.source_locator])


def eligible(field):
    # Unknown controls and every checkbox remain user decisions, even if a
    # hostile label embeds a benign contact-word alongside a declaration.
    return field.normalized_intent == "custom" and field.input_type in {"text", "email", "tel", "url", "select", "file"} and not SENSITIVE.search(field.label + " " + json.dumps(field.options))


async def map_fields(session, user_id, fields, skip):
    candidates = [f for f in fields if f.field_key not in skip and eligible(f)]
    items = [{"id": f.field_key, "text": f"Employer field: {f.label}\nControl type: {f.input_type}\nOptions: {json.dumps(f.options, ensure_ascii=False)}",
        "instruction": "Select the stored contact/resume intent requested by this employer control. Interpret the label together with the control type: email receives written updates, tel receives calls, file uploads a document. Unfamiliar wording can still request a standard contact field. Never infer a legal, sensitive or consent declaration. Use custom when neither label nor control type identifies a supported intent.",
        "criteria": {**{i: DESCRIPTIONS[i] for i in sorted(choices(f.input_type))}, "custom": "Unknown, sensitive, unsupported or ambiguous"}}
        for f in candidates]
    async with assistance(session, user_id) as op:
        decisions = await op.evaluate(items)
    accepted = {f.field_key: {**decisions[f.field_key], "field_hash": fingerprint(f)} for f in candidates
        if f.field_key in decisions and decisions[f.field_key]["choice"] in choices(f.input_type)
        and supported(decisions[f.field_key])
        and ((decisions[f.field_key]["choice"] == "resume") == (f.input_type == "file"))}
    return accepted, {"model": op.model, "provider": op.provider, "status": op.status, "overflow": op.overflow}
