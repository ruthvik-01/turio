"""Prepare an isolated Compose project without printing credentials."""
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parents[1]
project = "turio-verify-" + datetime.now(timezone.utc).strftime("%Y%m%d") + "-" + secrets.token_hex(3)
folder = root / ".verification" / project
folder.mkdir(parents=True)
password = secrets.token_urlsafe(24)
env = {
    "POSTGRES_USER": "turio", "POSTGRES_DB": "turio", "POSTGRES_PASSWORD": password,
    "DATABASE_URL": f"postgresql+psycopg://turio:{password}@postgres:5432/turio",
    "SECRET_KEY": secrets.token_urlsafe(48),
    "OBJECT_STORAGE_ACCESS_KEY": "turio_verify",
    "OBJECT_STORAGE_SECRET_KEY": secrets.token_urlsafe(32),
    "APP_ENV": "development", "CORS_ORIGINS": "http://localhost:13000",
    "NEXT_PUBLIC_API_BASE_URL": "http://localhost:18080/api/v1",
    "INTERNAL_API_BASE_URL": "http://backend:8000/api/v1",
    "INSTALL_ML": "false", "INSTALL_BROWSER": "false", "BROWSER_AUTOMATION_ENABLED": "false",
}
(folder / ".env").write_text("\n".join(f"{key}={value}" for key, value in env.items()) + "\n")
state = {"project": project, "folder": str(folder), "env_file": str(folder / ".env")}
(root / "data" / "stack-verification.json").write_text(json.dumps(state, indent=2))
print(json.dumps({"project": project, "configuration": str(folder / ".env")}))
