from __future__ import annotations

import os
import io

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from app.main import app


def test_generate_prompt_only_local():
    os.environ.pop("OPENAI_API_KEY", None)
    client = TestClient(app)

    resp = client.post(
        "/generate-testcases",
        data={
            "prompt": "Login feature: user enters valid credentials to access dashboard.",
            "num_cases": 6,
            "mode": "local",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "test_cases" in data
    assert isinstance(data["test_cases"], list)
    assert len(data["test_cases"]) == 6
    first = data["test_cases"][0]
    assert set(["id", "title", "steps", "expected_result"]).issubset(first.keys())


def test_generate_image_only_local():
    os.environ.pop("OPENAI_API_KEY", None)
    client = TestClient(app)

    # Create a simple image with text "Login"
    img = Image.new("RGB", (200, 80), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((10, 30), "Login", fill=(0, 0, 0))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    files = [("image_files", ("login.png", buf, "image/png"))]

    resp = client.post(
        "/generate-testcases",
        data={"prompt": "", "num_cases": 3, "mode": "local"},
        files=files,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "test_cases" in data and len(data["test_cases"]) == 3