import pytest

from app.adapters.ashby import AshbyAdapter
from app.core.config import get_settings
from app.core.errors import AppError


@pytest.mark.parametrize("url", [
    "http://jobs.ashbyhq.com/linear/one", "https://localhost/linear/one",
    "https://jobs.ashbyhq.com.evil.invalid/linear/one", "https://jobs.ashbyhq.com:bad/linear/one",
    "https://user:pass@jobs.ashbyhq.com/linear/one", "https://jobs.ashbyhq.com/unknown",
])
def test_browser_url_gate_rejects_unapproved_destinations(url, monkeypatch):
    monkeypatch.setattr(get_settings(), "browser_automation_enabled", True)
    with pytest.raises(AppError):
        AshbyAdapter(None).check_url(url)


async def test_validation_envelope_does_not_echo_credentials(client):
    response = await client.post("/api/v1/auth/register", json={"email": "not-an-email", "password": "secret"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REQUEST"
    assert response.json()["data"] is None
    assert "not-an-email" not in response.text and "secret" not in response.text
