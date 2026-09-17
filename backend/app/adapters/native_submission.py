"""Single-use native POST permit bound to reviewed text and original file bytes."""

import hashlib
import re
from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from urllib.parse import parse_qsl


def canonical_text(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n")


@dataclass(frozen=True)
class FileProof:
    filename: str
    size: int
    checksum: str
    mime: str = "application/pdf"

    @classmethod
    def from_bytes(cls, filename: str, data: bytes, mime="application/pdf"):
        return cls(filename, len(data), hashlib.sha256(data).hexdigest(), mime)


def parse_native_body(content_type: str, body: bytes) -> tuple[dict, dict]:
    """Reject ambiguous/unknown encodings rather than guess what a server receives."""
    if len(body) > 8 * 1024 * 1024 or "\r" in content_type or "\n" in content_type:
        raise ValueError("Unsupported body.")
    kind = content_type.split(";", 1)[0].strip().lower()
    fields, files = {}, {}
    if kind == "application/x-www-form-urlencoded":
        header = BytesParser(policy=policy.default).parsebytes(f"Content-Type: {content_type}\r\n\r\n".encode())
        if header.get_content_charset() not in {None, "utf-8"}:
            raise ValueError("Only UTF-8 form encoding is supported.")
        text = body.decode("utf-8")
        if re.search(r"%(?![0-9a-fA-F]{2})", text):
            raise ValueError("Malformed percent encoding.")
        for name, value in parse_qsl(text, keep_blank_values=True,
                                    strict_parsing=True, errors="strict", max_num_fields=100):
            if name in fields:
                raise ValueError("Duplicate field.")
            fields[name] = canonical_text(value)
    elif kind == "multipart/form-data":
        message = BytesParser(policy=policy.default).parsebytes(
            f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode() + body)
        if not message.is_multipart() or message.defects or (message.preamble or "").strip() or (message.epilogue or "").strip():
            raise ValueError("Malformed multipart body.")
        for part in message.iter_parts():
            name = part.get_param("name", header="content-disposition")
            if not name or name in fields or name in files or part.is_multipart() or part.defects or part.get_content_disposition() != "form-data":
                raise ValueError("Ambiguous form field.")
            header_names = [name.lower() for name in part.keys()]
            if (len(header_names) != len(set(header_names)) or
                set(header_names) - {"content-disposition", "content-type"} or
                part.get_content_charset() not in {None, "utf-8"} or
                any(getattr(value, "defects", ()) for value in part.values())):
                raise ValueError("Ambiguous multipart headers.")
            data = part.get_payload(decode=True) or b""
            filename = part.get_filename()
            if filename is None:
                fields[name] = canonical_text(data.decode("utf-8"))
            else:
                files[name] = FileProof.from_bytes(filename, data, part.get_content_type())
            if len(fields) + len(files) > 100:
                raise ValueError("Too many fields.")
    else:
        raise ValueError("Transport requires a separately audited serializer.")
    return fields, files


@dataclass
class SubmissionPermit:
    action: str
    fields: dict[str, str]
    files: dict[str, FileProof]
    consumed: bool = False
    rejected: bool = False
    request: object | None = None

    def allow(self, request) -> bool:
        if self.consumed or self.rejected:
            self.rejected = True
            return False
        try:
            if request.method != "POST" or request.url != self.action:
                raise ValueError("Unexpected destination.")
            fields, files = parse_native_body(request.headers.get("content-type", ""), request.post_data_buffer or b"")
            if fields != {name: canonical_text(value) for name, value in self.fields.items()} or files != self.files:
                raise ValueError("Payload differs from review.")
        except (ValueError, TypeError, UnicodeError):
            self.rejected = True
            return False
        self.consumed, self.request = True, request
        return True
