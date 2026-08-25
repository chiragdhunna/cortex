# Cortex

Cortex converts PDFs, audio, video, YouTube/direct media links into structured study notes. Choose an independent note category (`interview`, `exam`, or `understanding`) and any combination of Markdown, PDF, Anki CSV, and JSON exports.

## Run locally

1. Copy `.env.example` to `.env`. The default is `LLM_PROVIDER=ollama`; install and pull the selected local model (for example `ollama pull llama3.1:8b`). No API key is required. Set `GEMINI_API_KEY` and `LLM_PROVIDER=gemini` only for Gemini.
2. On Linux hosts where Docker bridge networking is available, run `docker-compose up --build`. This repository's Compose file uses host networking because some EndeavourOS/kernel configurations reject Docker's veth bridge creation; services bind directly to ports 8000, 5173, and 6379.
3. Open `http://localhost:5173`; Compose starts the web UI. For frontend-only development, run `cd frontend && npm install && npm run dev`.

The API is on port 8000 (`GET /health` is a liveness check). Use `POST /jobs/upload` for files or `POST /jobs` for a link. The frontend polls jobs every 2.5 seconds and renders notes plus downloads.

## Architecture

`ingestion → transcript → category-aware generation → canonical Notes JSON → formatter`.
The canonical JSON is the hard boundary: formatters never call an LLM and do not import generation code, so categories and formats remain independently extensible.

## Development

Run tests with `pytest -q`. Test adapters manually with `python scripts/test_ingest.py pdf path/to/file.pdf`. Screenshot placeholder: add UI screenshots here after launching the frontend.
