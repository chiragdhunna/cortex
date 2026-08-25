# ARCHITECTURE.md — Cortex

> Solution-architect level design. Read alongside REQUIREMENTS.md. The single most important architectural decision in this system is **separation of the three pipeline stages — Ingestion, Generation, Formatting — via a canonical intermediate representation.** Every other decision supports that.

---

## 1. Guiding Principle: The Canonical Notes Object

Category and output format are **orthogonal axes**. If they are not decoupled, you end up writing `categories × formats` prompts (3×4 = 12 and growing). Instead:

```
[Raw Source] → [Transcript/Text] → [Category-aware LLM generation] → [Canonical Notes JSON] → [Formatter] → [Output file]
```

The **Canonical Notes JSON** is the contract between generation and formatting. Generation only needs to know about category. Formatting only needs to know about the canonical schema — it never talks to the LLM and never knows about category. This single decision drives most of the module boundaries below.

---

## 2. System Context Diagram (textual)

```
                     ┌────────────────────┐
                     │      Browser        │
                     │  (Web Frontend)      │
                     └─────────┬───────────┘
                               │ REST (upload, submit link, poll status, download)
                     ┌─────────▼───────────┐
                     │   FastAPI Backend    │
                     │  (API + Orchestrator)│
                     └────┬───────────┬────┘
                          │           │
              enqueue job │           │ read/write
                          ▼           ▼
                 ┌────────────┐  ┌──────────────┐
                 │ Job Queue   │  │  Datastore    │
                 │ (Celery/RQ) │  │ (SQLite/Postgres
                 └─────┬───────┘  │ + local file    │
                       │          │ storage)         │
        ┌──────────────┼─────────┴──────────────┐
        ▼              ▼                         ▼
 ┌─────────────┐ ┌──────────────┐        ┌───────────────┐
 │ Ingestion    │ │ Generation    │        │ Formatting     │
 │ Worker       │ │ Worker        │        │ Worker         │
 │ (extract +   │ │ (category     │        │ (canonical JSON│
 │ faster-      │ │ prompt → LLM  │        │ → md/pdf/anki/ │
 │ whisper)     │ │ → canonical   │        │ json)          │
 │              │ │ JSON)         │        │                │
 └─────────────┘ └──────────────┘        └───────────────┘
```

All three workers are stages of the **same job**, chained via the queue (job moves through states: `queued → transcribing → generating_notes → formatting → done`).

---

## 3. Component Breakdown

### 3.1 API Layer (FastAPI)
- `POST /jobs` — accepts multipart file OR `{type: "link", url, category, formats[]}`. Returns `job_id`.
- `GET /jobs/{id}` — returns job status + progress stage.
- `GET /jobs/{id}/result` — returns canonical notes JSON once done.
- `GET /jobs/{id}/download?format=pdf` — streams a rendered output.
- `POST /jobs/{id}/regenerate` — re-run generation stage only, with a new category, reusing the stored transcript (this is the endpoint that proves the architecture — no re-ingestion).
- `POST /jobs/{id}/format` — render an additional format from the existing canonical JSON, no LLM call needed.

### 3.2 Ingestion Layer
- `pdf_extractor.py` — PyMuPDF; preserves headings/structure where possible.
- `link_resolver.py` — `yt-dlp`-based; detects YouTube vs generic; pulls existing captions if available (skips Whisper), else downloads audio stream only (not full video) to minimize bandwidth/storage.
- `transcriber.py` — `faster-whisper` wrapper; runs on chunked audio; returns text + timestamps.
- Output of this layer is always normalized to:
```json
{
  "source_type": "pdf | audio | video | video_link | audio_link",
  "source_meta": { "title": "...", "duration_sec": 0, "page_count": 0 },
  "raw_text": "...",
  "segments": [ { "start": 0.0, "end": 12.4, "text": "..." } ]
}
```

### 3.3 Chunking
- `chunker.py` — semantic chunking (paragraph/section boundaries for PDF; sentence-cluster boundaries for transcripts), target ~1500–2500 tokens per chunk with slight overlap, to keep each chunk coherent for the LLM and cheap enough to process in parallel.

### 3.4 Generation Layer (the "brains")
- `category_prompts.py` — one prompt template per category, each instructed to return **only** JSON matching that category's schema (see §5).
- `notes_generator.py` — orchestrates: chunk → per-chunk extraction → merge/de-duplicate across chunks → final canonical JSON. For long sources, a **map-reduce** pattern: generate per-chunk notes, then a final "synthesis" LLM call merges/de-dupes/orders them into one coherent canonical object.
- This is the only layer that calls the LLM. It is category-aware but format-agnostic.

#### 3.4.1 LLM Provider Abstraction (Gemini / Ollama)

`core/llm/provider.py` defines a minimal interface both providers implement:

```python
class LLMProvider(Protocol):
    def generate_json(self, prompt: str, schema: type[BaseModel]) -> BaseModel: ...
```

- **`GeminiProvider`** — calls the Gemini API (`google-generativeai` SDK), uses Gemini's native structured-output/JSON mode where available, reads `GEMINI_API_KEY` from `.env`.
- **`OllamaProvider`** — calls a local Ollama server (`http://localhost:11434` by default) via its REST API, using a model the user has pulled locally (e.g. `llama3.1`, `mistral`, `qwen2.5`). No API key, no external network call, no per-token cost.
- Provider choice is a config value (`LLM_PROVIDER=gemini|ollama` in `.env`, overridable per job request). **Ollama must be a fully functional default** — the system should run start-to-finish with zero paid API keys configured.
- **Reliability difference to design for**: local open-weight models via Ollama are meaningfully less consistent at emitting valid structured JSON than Gemini's hosted structured-output mode. To handle this uniformly regardless of provider:
  1. Prompt always includes the target schema (as JSON schema or a clear example) inline, not just relying on provider-native "JSON mode."
  2. `notes_generator.py` validates every LLM response against the Pydantic schema immediately.
  3. On validation failure: retry with a corrective follow-up prompt ("your last response was invalid JSON because X, return only valid JSON matching the schema") — max 2 retries, provider-agnostic.
  4. If still invalid after retries, the job fails cleanly with a specific error (`generation_schema_invalid`), not a silent partial result.
- Both providers are exercised in integration tests — the pipeline is not considered done if it only works against Gemini (see AGENT.md Definition of Done).

### 3.5 Formatting Layer
- Pure functions, no LLM calls: `canonical_json → output_bytes`.
- `markdown.py`, `pdf.py` (e.g. via `weasyprint` or `reportlab` from templated HTML), `anki.py` (CSV in Anki-importable format: front/back/tags), `json_export.py` (pass-through/pretty-print).
- Formatters are registered in a small registry (`{format_name: formatter_fn}`) — adding a new format is a one-file addition, per FR-11/12.

### 3.6 Job Orchestration
- Job queue: Celery + Redis (preferred) or RQ if the team wants a lighter dependency footprint. `BackgroundTasks` in FastAPI is explicitly **not** used for the transcription stage (too long-running/blocking for a single-process background task at scale) but may be acceptable for the lightweight `format`-only regeneration path.
- Each job is a row in the datastore with `status`, `stage`, `error`, timestamps, and foreign keys to its transcript record and canonical-notes record — this is what makes `/regenerate` and `/format` cheap (they read existing rows instead of redoing work).

### 3.7 Persistence
- v1: SQLite (zero-ops, fine for single-user) with a clean repository-pattern data access layer so swapping to Postgres later is a config change, not a rewrite.
- File storage: local disk under a content-addressed path (hash of source) so re-uploading the same source doesn't redundantly reprocess it — cache hit on ingestion.

### 3.8 Frontend
- Simple React (or plain HTML+HTMX if the user wants to minimize frontend complexity) app:
  - Upload/link submission form with category + format multi-select.
  - Job status view (polls `/jobs/{id}` every 2–3s).
  - Notes viewer (renders canonical JSON nicely) + download buttons per format.
  - Job history list.

---

## 4. Data Flow (End-to-End Example)

1. User submits a YouTube link, category=`exam`, formats=`[markdown, anki_csv]`.
2. API creates a `Job` row (`status=queued`), enqueues ingestion task, returns `job_id`.
3. Ingestion worker: `link_resolver` detects YouTube → checks for captions → (found) skips Whisper → normalizes to raw text/segments → stores `Transcript` row → job stage = `generating_notes`.
4. Generation worker: chunks transcript → runs `exam` prompt per chunk → synthesis pass merges into canonical JSON → stores `NotesResult` row → job stage = `formatting`.
5. Formatting worker: renders `markdown` and `anki_csv` from the canonical JSON → stores both as `Artifact` rows → job stage = `done`.
6. Frontend polls, sees `done`, shows download links.
7. Later, user hits `/jobs/{id}/regenerate` with category=`interview` → generation worker re-runs on the **already-stored transcript** (step 3 is skipped entirely) → new `NotesResult`.

---

## 5. Canonical Notes Schema (per category)

All categories share an envelope:
```json
{
  "category": "interview | exam | understanding",
  "source_title": "string",
  "generated_at": "iso8601",
  "topics": [ { "title": "string", "content": { /* category-specific, see below */ } } ]
}
```

- **interview** `content`: `{ "qa_pairs": [{q, a, difficulty}], "talking_points": [string], "gotchas": [string] }`
- **exam** `content`: `{ "definitions": [{term, definition}], "summary": "string", "self_test": [{q, a}] }`
- **understanding** `content`: `{ "explanation": "string", "analogies": [string], "prerequisites": [string], "concept_map": {"nodes": [string], "edges": [[from, to]]} }`

Schemas are enforced with Pydantic models; the LLM is prompted to emit exactly this shape (structured output / JSON mode), and a validation step rejects/retries malformed responses before they reach the formatter.

---

## 6. Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Backend framework | FastAPI | Async-first, matches user's existing FastAPI/jobctl experience |
| Job queue | Celery + Redis | Mature, production-proven for chained multi-stage jobs |
| Transcription | `faster-whisper` | Local, no per-minute API cost, good accuracy/speed tradeoff |
| PDF extraction | PyMuPDF (`fitz`) | Fast, preserves structure |
| Link download | `yt-dlp` | Best-in-class extractor coverage |
| LLM | Gemini API + Ollama (local), behind a provider interface | Gemini for quality/free-tier hosted use; Ollama for zero-cost fully local runs. No hard dependency on a paid key. |
| DB (v1) | SQLite via SQLAlchemy | Zero-ops; repository pattern for future Postgres swap |
| PDF output | WeasyPrint (HTML→PDF) | Easiest to template/style |
| Frontend | React + Vite (or HTMX if minimal) | User's stated preference for "web app" |

---

## 7. Cross-Cutting Concerns

- **Idempotency/caching**: content-hash the source file/link; skip re-ingestion on duplicate submissions.
- **Error isolation**: each pipeline stage catches and records its own errors on the `Job` row; a failure in formatting should not discard a successfully generated canonical JSON.
- **Cost/perf control**: chunk-level parallelism for generation (bounded concurrency), Whisper model size configurable per job or globally.
- **Extensibility**: new category = new prompt template + Pydantic schema, registered in a category registry. New format = new formatter function, registered in a format registry. Neither requires touching ingestion, the job orchestrator, or each other.
- **Security**: validate/sanitize uploaded file types and link domains; size/duration caps enforced before job acceptance (FR-6).

---

## 8. Deployment (v1, single-user)

- `docker-compose` with services: `api`, `worker` (Celery), `redis`, optionally `frontend` (or served statically by `api`).
- Local disk volume for `uploads/` and `artifacts/`.
- `.env` for `LLM_PROVIDER` (`gemini` or `ollama`), `GEMINI_API_KEY` (only required if provider=gemini), `OLLAMA_BASE_URL` + `OLLAMA_MODEL` (only relevant if provider=ollama), Whisper model size, retention days.
- If `LLM_PROVIDER=ollama`, `docker-compose` should either point `OLLAMA_BASE_URL` at an Ollama instance already running on the host, or optionally include an `ollama` service in `docker-compose.yml` (commented out by default, since most users running Ollama locally already have it outside Docker).
