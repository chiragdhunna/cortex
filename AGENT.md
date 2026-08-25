# AGENT.md — Build Instructions for AI IDE

You are building **Cortex**: a multi-modal notes-generation agent. Read `REQUIREMENTS.md` and `ARCHITECTURE.md` in this same directory fully before writing any code — they are the source of truth for scope and design. Do not deviate from the architecture's core principle (canonical Notes JSON decoupling category from format) without flagging why.

## Project Name
**Cortex**. Repo/package name: `cortex`. Python package: `cortex_backend`. Frontend package: `cortex-frontend`.

---

## 0. Operating Rules

1. Work stage by stage, in the order given in §2 below. Do not skip ahead to frontend before the backend pipeline works end-to-end on at least one path (PDF → markdown).
2. After finishing each stage, run/lint/test what you built before moving to the next stage. Do not accumulate untested code across stages.
3. Keep ingestion, generation, and formatting as genuinely separate modules with no circular imports between them (formatting must never import from generation; generation must never import from ingestion — they only share the canonical schema types).
4. Every new category is a new file in `core/categories/`. Every new output format is a new file in `formatters/`. Do not hardcode category or format branching logic (`if category == "exam"`) outside of a registry lookup.
5. Prefer explicit Pydantic models over dicts for anything crossing a module boundary (ingestion output, canonical notes, job state).
6. Write docstrings and type hints on every public function. This is a portfolio project — code quality matters as much as functionality.
7. Commit after each completed stage with a clear message (e.g., `feat: PDF ingestion + markdown formatter, stage 1 complete`).
8. If a design decision in ARCHITECTURE.md turns out to be impractical during implementation, note the deviation and reasoning in a `DECISIONS.md` file you create — do not silently diverge.

---

## 1. Tech Stack (do not substitute without strong reason — see ARCHITECTURE.md §6)

- Backend: FastAPI, SQLAlchemy + SQLite, Celery + Redis, Pydantic v2
- Ingestion: PyMuPDF, faster-whisper, yt-dlp
- LLM: Gemini API + Ollama (local), both implementing a shared `core/llm/provider.py` interface. Ollama must work with zero paid API keys configured — it is the default/no-cost path, not a fallback.
- Formatting: WeasyPrint for PDF, plain Python for markdown/CSV/JSON
- Frontend: React + Vite, TypeScript, minimal styling (Tailwind acceptable)
- Containerization: docker-compose (api, worker, redis)

---

## 2. Build Order (follow sequentially)

### Stage 1 — Project Scaffold
- Initialize repo structure exactly as in ARCHITECTURE.md §3 (`api/`, `ingestion/`, `core/`, `formatters/`, `jobs/`, `frontend/`).
- Set up `pyproject.toml`/`requirements.txt`, `.env.example`, `docker-compose.yml` skeleton (services can be stubs for now).
- Set up SQLAlchemy models: `Job`, `Transcript`, `NotesResult`, `Artifact` (fields per ARCHITECTURE.md §3.6/3.7).
- Set up Alembic (or simple `create_all`) migrations.

### Stage 2 — Ingestion (PDF first, simplest path)
- Implement `pdf_extractor.py` → normalized ingestion output (schema in ARCHITECTURE.md §3.2).
- Implement `transcriber.py` (faster-whisper wrapper) — build and unit-test independently with a short sample audio file before wiring into the pipeline.
- Implement `link_resolver.py` (yt-dlp) — including the "use existing captions if available" optimization (FR-7).
- Write a small CLI test harness (`scripts/test_ingest.py`) to run each ingestion path standalone and print the normalized output — do not wait for the API layer to test this.

### Stage 3 — Chunking
- Implement `chunker.py` per ARCHITECTURE.md §3.3. Unit test with a long sample text to confirm chunk boundaries are sane (no mid-sentence splits where avoidable).

### Stage 4 — Generation
- Define Pydantic schemas for the canonical envelope + all three category `content` shapes (ARCHITECTURE.md §5).
- Implement `core/llm/provider.py` interface plus `GeminiProvider` and `OllamaProvider` (ARCHITECTURE.md §3.4.1). Build and smoke-test `OllamaProvider` first — it has no external key dependency, so it's the fastest path to a working end-to-end test, and it's the path that must work with zero configuration beyond having Ollama installed.
- Implement `category_prompts.py` with one prompt template per category, each instructing the LLM to emit only JSON matching its schema (schema included inline in the prompt, not relying solely on provider-native JSON mode).
- Implement `notes_generator.py`: per-chunk generation → synthesis/merge pass → validated canonical JSON. Include the schema-validation + corrective-retry loop (max 2 retries) described in ARCHITECTURE.md §3.4.1 before failing the job with `generation_schema_invalid`.
- Test this stage standalone against Stage 2/3 output, **against both providers** (Ollama with a locally pulled small model such as `llama3.1:8b`, and Gemini if a key is available) before wiring into the job queue.

### Stage 5 — Formatting
- Implement the format registry and `markdown.py`, `json_export.py` first (simplest, no external deps).
- Implement `anki.py` (CSV export).
- Implement `pdf.py` (WeasyPrint, HTML template → PDF) last (most complex).
- Test each formatter against a hand-written sample canonical JSON fixture, independent of the LLM.

### Stage 6 — Job Orchestration
- Wire Celery + Redis. Define the task chain: ingest → generate → format(s).
- Implement job status transitions and error capture on the `Job` row per stage.
- Implement `/jobs` (POST), `/jobs/{id}` (GET), `/jobs/{id}/result`, `/jobs/{id}/download`, `/jobs/{id}/regenerate`, `/jobs/{id}/format` per ARCHITECTURE.md §3.1.
- **Explicitly verify** `/regenerate` does not re-trigger ingestion and `/format` does not re-trigger generation — this is the architectural point of the whole project. Write an integration test proving it.

### Stage 7 — Frontend
- Upload/link submission form (category select, multi-select formats).
- Job status polling view.
- Notes viewer rendering canonical JSON per category shape (don't just dump raw JSON — render Q&A pairs, definitions, concept maps reasonably).
- Download buttons per generated artifact.
- Job history list.

### Stage 8 — Polish
- Add content-hash caching on ingestion (skip reprocessing duplicate sources).
- Add file size/duration validation (FR-6) with clear error messages.
- Add retention/cleanup job for old artifacts (NFR-6).
- Write `README.md` for the repo (setup, run instructions, architecture summary, screenshots placeholder).
- Write basic tests for every stage if not already covered; aim for the critical paths (ingestion normalization, schema validation, format registry, job state machine) to have test coverage.

---

## 3. Definition of Done

The project is complete when all of the following are true:
1. A user can submit a PDF, an audio file, a video file, a YouTube link, and a generic audio link, and each produces a valid canonical notes JSON.
2. All three categories produce distinctly-shaped, sensible output for the same source.
3. All four formats render correctly from a canonical JSON without needing a fresh LLM call.
4. `/regenerate` and `/format` endpoints work without re-running earlier pipeline stages (verified by a test, not just manual check).
5. The frontend supports the full flow: submit → watch progress → view notes → download in chosen formats.
6. `docker-compose up` brings up a working system from a clean checkout with only `.env` filled in.
7. The system runs the full pipeline successfully with `LLM_PROVIDER=ollama` and **no API keys configured at all** — this is checked explicitly, not assumed. Gemini is also verified to work when a key is supplied.
8. `REQUIREMENTS.md` FR/NFR list is fully satisfied or explicitly deferred with reasoning in `DECISIONS.md`.

Do not declare the project finished until every item above is checked.
