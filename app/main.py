from __future__ import annotations

import io
import os
from typing import List, Optional

from fastapi import FastAPI, File, Form, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from PIL import Image

try:
    import pytesseract
except Exception:  # pragma: no cover
    pytesseract = None  # type: ignore

from .generator import generate_test_cases
from .schemas import GenerateResponse

app = FastAPI(title="Test Case Generator", version="0.1.0")

# CORS for simplicity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/generate-testcases", response_model=GenerateResponse)
async def generate(
    request: Request,
    prompt: Optional[str] = Form(None),
    num_cases: int = Form(8),
    mode: str = Form("auto"),
):
    prompt_text = prompt or ""

    # Read uploaded files robustly (single or multiple)
    form = await request.form()
    uploaded_files = form.getlist("image_files") if form else []

    ocr_texts: List[str] = []

    if uploaded_files:
        for f in uploaded_files:
            try:
                if isinstance(f, UploadFile):
                    content = await f.read()
                else:
                    # Some clients might supply bytes-like
                    content = await f.read() if hasattr(f, "read") else bytes(f)
                image = Image.open(io.BytesIO(content))
                image = image.convert("RGB")
                if pytesseract is not None:
                    extracted = pytesseract.image_to_string(image)
                    if extracted and extracted.strip():
                        ocr_texts.append(extracted.strip())
            except Exception:
                # Ignore OCR errors for robustness
                continue

    source = "\n\n".join([t for t in [prompt_text] + ocr_texts if t])

    result = generate_test_cases(source_text=source, num_cases=num_cases, mode=mode)
    return JSONResponse(content=result.model_dump())

# Serve static web UI if present (after routes so it doesn't intercept them)
static_dir = os.path.join(os.path.dirname(__file__), "..", "web")
static_dir = os.path.abspath(static_dir)
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")