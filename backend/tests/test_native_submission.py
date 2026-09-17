"""Pure transport-permit tests run without installing a browser runtime."""

from types import SimpleNamespace

import pytest

from app.adapters.native_submission import FileProof, SubmissionPermit, parse_native_body

ACTION = "https://jobs.ashbyhq.com/1password/fixture-submit"


def request(body, content_type="application/x-www-form-urlencoded", url=ACTION):
    return SimpleNamespace(method="POST", url=url, headers={"content-type": content_type}, post_data_buffer=body)


def test_single_use_permit_matches_text_and_rejects_duplicates():
    permit = SubmissionPermit(ACTION, {"name": "Synthetic Candidate", "empty": ""}, {})
    assert permit.allow(request(b"name=Synthetic+Candidate&empty="))
    assert permit.consumed
    assert not permit.allow(request(b"name=Synthetic+Candidate&empty="))
    assert permit.rejected


@pytest.mark.parametrize("body,content_type", [
    (b"name=changed", "application/x-www-form-urlencoded"),
    (b"name=approved&name=changed", "application/x-www-form-urlencoded"),
    (b'{"name":"approved"}', "application/json"),
    (b"not-multipart", "multipart/form-data; boundary=missing"),
    (b"name=approved&hidden=extra", "application/x-www-form-urlencoded"),
])
def test_unknown_or_changed_payload_is_rejected(body, content_type):
    permit = SubmissionPermit(ACTION, {"name": "approved"}, {})
    assert not permit.allow(request(body, content_type))
    assert permit.rejected and not permit.consumed
    assert not permit.allow(request(b"name=approved"))  # An invalid attempt closes the permit.


def test_destination_is_bound_to_approval():
    permit = SubmissionPermit(ACTION, {"name": "approved"}, {})
    assert not permit.allow(request(b"name=approved", url=ACTION + "-other"))


def test_multipart_compares_original_file_bytes_name_and_type():
    prefix = b'--fixture\r\nContent-Disposition: form-data; name="resume"; filename="original.pdf"\r\nContent-Type: application/pdf\r\n\r\n'
    body = prefix + b"original-bytes" + b"\r\n--fixture--\r\n"
    content_type = "multipart/form-data; boundary=fixture"
    expected = {"resume": FileProof.from_bytes("original.pdf", b"original-bytes")}
    assert SubmissionPermit(ACTION, {}, expected).allow(request(body, content_type))
    for replacement in (body.replace(b"original-bytes", b"modified-bytes"), body.replace(b"original.pdf", b"other.pdf"),
                        body.replace(b"application/pdf", b"text/plain")):
        assert not SubmissionPermit(ACTION, {}, expected).allow(request(replacement, content_type))


def test_newline_normalization_preserves_text_without_weakening_other_values():
    fields, files = parse_native_body("application/x-www-form-urlencoded", b"notes=line1%0D%0Aline2")
    assert fields == {"notes": "line1\nline2"} and files == {}
    assert SubmissionPermit(ACTION, fields, {}).allow(request(b"notes=line1%0Aline2"))


@pytest.mark.parametrize("body,content_type", [
    (b"name=approved", "application/x-www-form-urlencoded; charset=iso-8859-1"),
    (b"name=%ZZ", "application/x-www-form-urlencoded"),
])
def test_non_native_encoding_is_rejected(body, content_type):
    with pytest.raises(ValueError):
        parse_native_body(content_type, body)


@pytest.mark.parametrize("extra_header", [
    "Content-Transfer-Encoding: base64\r\n",
    'Content-Disposition: form-data; name="different"\r\n',
    "Content-Type: text/plain; charset=iso-8859-1\r\n",
])
def test_ambiguous_mime_headers_are_not_decoded_into_approved_values(extra_header):
    body = (b'--fixture\r\nContent-Disposition: form-data; name="name"\r\n' +
            extra_header.encode() + b"\r\napproved\r\n--fixture--\r\n")
    assert not SubmissionPermit(ACTION, {"name": "approved"}, {}).allow(request(body, "multipart/form-data; boundary=fixture"))
