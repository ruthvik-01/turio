"""Validate provider configuration; --probe sends only a synthetic JSON check.

Never opens an employer site, reads candidate data, or submits an application.
No network request is made unless --probe is explicitly supplied.
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.adapters.agent_models import build_agent_models, validate_provider_settings
from app.core.config import Settings
from app.core.errors import AppError


class ProbeResponse(BaseModel):
    ready: bool


async def check(settings: Settings, probe: bool) -> int:
    order = validate_provider_settings(settings)
    print(json.dumps({"configured_order": order, "live_probe": probe}))
    if not probe:
        return 0
    models = build_agent_models(settings)
    from browser_use.llm.messages import UserMessage

    failed = False
    try:
        for model in (models.primary, models.fallback):
            if model is None:
                continue
            try:
                result = await model.ainvoke(
                    [UserMessage(content="Synthetic connection check. Return ready=true. No candidate data is included.")],
                    output_format=ProbeResponse,
                )
                passed = result.completion.ready is True
                print(json.dumps({"provider": model.provider, "structured_output_verified": passed}))
                failed |= not passed
            except Exception as exc:
                # Do not print provider response bodies or a traceback with secrets.
                print(json.dumps({"provider": model.provider, "structured_output_verified": False,
                                  "status": getattr(exc, "status_code", None)}))
                failed = True
    finally:
        await models.aclose()
    return int(failed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--probe", action="store_true", help="Make one billable synthetic structured-output request per configured provider.")
    args = parser.parse_args()
    try:
        settings = Settings(_env_file=args.env_file)
        return asyncio.run(check(settings, args.probe))
    except AppError as exc:
        print(json.dumps({"error": exc.code, "message": exc.message}))
        return 2
    except Exception:
        print(json.dumps({"error": "CONFIGURATION_ERROR", "message": "Check the backend environment and pinned runtime dependencies."}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
