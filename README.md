# Test Case Generator

A small FastAPI service and simple web UI to generate structured test cases from:
- prompt only
- image/screenshot only (OCR)
- prompt + screenshots

It uses OpenAI when configured, with a robust local fallback that creates high-coverage test suites (functional, negative, boundary, non-functional).

## Setup

Requirements: Python 3.10+

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional: install Tesseract OCR binary for better screenshot extraction.
- On Ubuntu/Debian: `sudo apt-get update && sudo apt-get install -y tesseract-ocr`

To enable OpenAI mode, set your API key:

```bash
export OPENAI_API_KEY=sk-...  # or use a secrets manager
# Optional: choose a model (defaults to gpt-4o-mini)
export OPENAI_MODEL=gpt-4o-mini
```

## Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open the web UI at `http://localhost:8000/`.

## API

POST `/generate-testcases` (multipart/form-data)
- `prompt`: string (optional)
- `num_cases`: int (default 8)
- `mode`: `auto|openai|local` (default `auto`)
- `image_files`: one or more image files (optional)

Response:
```json
{
  "summary": "...",
  "source_summary": "...",
  "test_cases": [
    {
      "id": "TC-...",
      "title": "...",
      "objective": "...",
      "preconditions": ["..."],
      "steps": ["..."],
      "expected_result": "...",
      "priority": "High|Medium|Low",
      "type": "Functional|Negative|Boundary|Performance|Security|Accessibility|Other",
      "tags": ["..."]
    }
  ]
}
```

## Tests

```bash
pytest -q
```

## Notes
- If Tesseract is not installed, OCR will be skipped gracefully.
- In `auto` mode, the service uses OpenAI when `OPENAI_API_KEY` is present; otherwise it falls back to the local generator.
