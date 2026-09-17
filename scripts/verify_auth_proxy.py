"""Check the deployed frontend's origin guard without changing any accounts."""

import argparse
import json
from pathlib import Path

import httpx


def verify(base_url: str) -> dict:
    base_url = base_url.rstrip("/")
    cases = [
        ("public-origin", {"Origin": base_url}, 404),
        ("cross-origin", {"Origin": "https://untrusted.invalid"}, 403),
        ("missing-origin-evidence", {}, 403),
        ("same-origin-referer", {
            "Referer": base_url + "/login", "Sec-Fetch-Site": "same-origin",
        }, 404),
        ("cross-origin-referer", {
            "Referer": "https://untrusted.invalid/login", "Sec-Fetch-Site": "same-origin",
        }, 403),
        ("same-site-not-same-origin", {
            "Referer": base_url + "/login", "Sec-Fetch-Site": "same-site",
        }, 403),
        ("origin-takes-precedence", {
            "Origin": "https://untrusted.invalid", "Referer": base_url + "/login",
            "Sec-Fetch-Site": "same-origin",
        }, 403),
    ]
    results = []
    with httpx.Client(timeout=15) as client:
        for name, headers, expected in cases:
            # Refresh is server-managed: accepted origin checks return 404 before
            # any backend call; rejected origins return 403.
            response = client.post(base_url + "/api/auth/refresh", headers=headers, json={})
            assert response.status_code == expected, f"{name}: {response.status_code}, expected {expected}"
            if expected == 404:
                assert response.json()["error"]["message"] == "Sessions are refreshed by the server."
            results.append({"check": name, "status": response.status_code})
    return {"base_url": base_url, "passed": len(results), "checks": results}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:13000")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = verify(args.url)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
