"""Source-only optional metadata and deterministic description presentation."""

import json
import re
from datetime import datetime, time, timezone
from html.parser import HTMLParser
from urllib.parse import urlparse


def source_metadata(row):
    raw = row.get("raw")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (ValueError, TypeError):
            raw = {}
    return {**(raw if isinstance(raw, dict) else {}), **row}


def deadline(value):
    """Accept ISO dates/offset timestamps only; unknown/ambiguous stays null.

    Date-only deadlines remain eligible through that UTC calendar day.
    Offset-free times are ambiguous and are not assigned a timezone.
    """
    if not isinstance(value, str):
        return None
    try:
        value = value.strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return datetime.combine(datetime.fromisoformat(value).date(), time.max, timezone.utc)
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return result.astimezone(timezone.utc) if result.tzinfo else None
    except ValueError:
        return None


def logo_url(value):
    if not isinstance(value, str):
        return None
    value = value.strip()
    try:
        parsed = urlparse(value)
        if parsed.scheme == "https" and parsed.hostname and not parsed.username and not parsed.password:
            return value
    except ValueError:
        pass
    return None


class DescriptionText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1
        if not self.hidden and tag in {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "tr"}:
            self.parts.append("\n")
        if not self.hidden and tag == "li":
            self.parts.append("• ")

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.hidden = max(0, self.hidden - 1)
        if not self.hidden and tag in {"p", "div", "li", "h1", "h2", "h3", "h4", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def readable_description(value):
    if not value:
        return None
    parser = DescriptionText()
    parser.feed(value)
    text = "".join(parser.parts).replace("\x00", " ")
    # Remove formatting, not the source's words, numbers, links or technical symbols.
    text = re.sub(r"(\*{2,}|_{2,}|`{1,3})(.+?)\1", r"\2", text)
    text = re.sub(r"(?<!\w)\*([^*\n]+)\*(?!\w)", r"\1", text)
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s+", "", text)
    text = re.sub(r"(?m)^\s*[-*]\s+", "• ", text)
    text = re.sub(r"(?m)^[\s*_=~#•-]+$", "", text)
    text = re.sub(r"\*{2,}", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip() or None
