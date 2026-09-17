"""Browser mode wiring without opening a window or contacting any site."""
import sys
from types import ModuleType

import pytest

from app.adapters.ashby import AshbyAdapter
from app.core.config import get_settings
from app.core.errors import AppError


@pytest.mark.parametrize("headless", [True, False])
async def test_browser_mode_is_forwarded_and_cleanup_retained(monkeypatch, headless):
    settings = get_settings()
    monkeypatch.setattr(settings, "browser_automation_enabled", True)
    monkeypatch.setattr(settings, "browser_headless", headless)
    calls, cleanup = [], []

    class StubBrowser:
        def __init__(self, **kwargs):
            calls.append(kwargs)

        async def start(self):
            raise RuntimeError("Stop before opening any browser.")

        async def kill(self):
            cleanup.append(True)

    runtime = ModuleType("browser_use")
    runtime.Browser = StubBrowser
    playwright = ModuleType("playwright.async_api")
    playwright.async_playwright = lambda: pytest.fail("No browser should be opened")
    playwright_package = ModuleType("playwright")
    playwright_package.__path__ = []
    playwright_package.async_api = playwright
    monkeypatch.setitem(sys.modules, "browser_use", runtime)
    monkeypatch.setitem(sys.modules, "playwright", playwright_package)
    monkeypatch.setitem(sys.modules, "playwright.async_api", playwright)
    adapter = AshbyAdapter(None)
    with pytest.raises(AppError, match="Browser assistance stopped"):
        async with adapter.page("https://jobs.ashbyhq.com/1password/configuration-fixture"):
            pytest.fail("Startup must stop before page creation")
    assert calls[0]["headless"] is headless
    assert calls[0]["keep_alive"] is False
    assert calls[0]["allowed_domains"] == ["jobs.ashbyhq.com"]
    assert cleanup == [True]
