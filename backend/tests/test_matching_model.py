"""Opt-in real-model API smoke. Synthetic inputs do not measure model quality."""

import os

import pytest

from test_matching import seed


@pytest.mark.skipif(os.environ.get("TURIO_ML_SMOKE") != "1", reason="Opt-in local model smoke; install/download the pinned model first.")
async def test_real_pinned_model_through_api_and_cache(client, session, tmp_path):
    headers, _ = await seed(client, session, tmp_path)
    response = await client.post("/api/v1/matches", headers=headers, json={"method": "sbert"})
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["matches"][0]["job"]["title"] == "Python Engineer"
    assert data["matches"][0]["model_name"] == "sentence-transformers/all-MiniLM-L6-v2"
    assert all(0 <= row["final_score"] <= 1 for row in data["matches"])
    repeated = await client.post("/api/v1/matches", headers=headers, json={"method": "sbert"})
    assert repeated.json()["data"] == data
