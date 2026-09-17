"""Run database fixtures in isolated schemas of the dedicated test database."""
import os
import sys
from sqlalchemy.engine import make_url

if __name__ == "__main__":
    import pytest
    target = os.environ.get("TURIO_TEST_DATABASE_URL")
    if not target:
        raise SystemExit("Set TURIO_TEST_DATABASE_URL to a dedicated turio_test_ database.")
    url = make_url(target)
    if url.get_backend_name() != "postgresql" or not (url.database or "").startswith("turio_test_"):
        raise SystemExit("Refusing tests outside a dedicated PostgreSQL turio_test_ database.")
    raise SystemExit(pytest.main(["-q", "--tb=short", "-p", "no:cacheprovider", *sys.argv[1:]]))
