# REQUIREMENTS.md — Cortex

> Working name: **Cortex** (alternatives considered: NoteForge, Synapse, Distillery — see AGENT.md for naming rationale)
> Cortex ingests any learning material — PDF, audio, video, or a link to either — and produces structured, purpose-driven notes based on a category the user selects (Interview Prep, Exam Prep, Understanding). Output format is independently selectable (Markdown, PDF, Anki flashcards, JSON).

---

## 1. Problem Statement

Learners consume source material (lecture PDFs, podcast episodes, YouTube tutorials, recorded meetings) but manually converting that into *purpose-fit* study material is slow and repetitive. The same source material needs to be summarized differently depending on **why** you're studying it — cramming for an interview needs different structure than cramming for an exam, which is different again from building deep understanding.

Cortex automates ingestion + transcription + category-aware synthesis + multi-format export in one pipeline.

---

## 2. Personas

| Persona | Goal |
|---|---|
| **Interview Candidate** | Convert a long tech talk / course video into rapid-recall Q&A and "gotcha" points before an interview. |
| **Student (Exam Prep)** | Convert lecture PDFs/recordings into definitions, structured summaries, and likely exam questions. |
| **Curious Learner** | Convert dense material into a plain-language explanation with analogies and a concept map, for genuine understanding rather than recall. |

---

## 3. Functional Requirements

### 3.1 Input / Ingestion
- FR-1: User can upload a **PDF** file.
- FR-2: User can upload an **audio file** (mp3, wav, m4a).
- FR-3: User can upload a **video file** (mp4, mov) — audio track is extracted for transcription; video itself is not analyzed visually in v1.
- FR-4: User can submit a **video link** (YouTube primary; generic direct-media URLs as fallback).
- FR-5: User can submit an **audio link** (podcast RSS episode URL, direct audio URL).
- FR-6: System validates file size/duration limits before accepting a job (configurable, default: 500MB / 3 hours).
- FR-7: If a YouTube video already has captions/transcript available, system uses that directly and skips Whisper transcription (cost/time optimization).

### 3.2 Category Selection
- FR-8: User selects exactly one category per job: `interview`, `exam`, `understanding`.
- FR-9: Each category maps to a distinct **note schema** (see ARCHITECTURE.md §5) — not just a different prompt wording, but a different structured output shape.
- FR-10: Category is extensible — adding a new category should not require touching ingestion or formatter code (open/closed principle — see AGENT.md).

### 3.3 Output Format Selection
- FR-11: Output format is selected **independently** of category: `markdown`, `pdf`, `anki_csv`, `json`.
- FR-12: User can request **multiple formats** for the same job without re-running generation (formats are rendered from one canonical structured JSON result).
- FR-13: All formats are downloadable; markdown/JSON also viewable inline in the web UI.

### 3.4 Processing / Jobs
- FR-14: All ingestion + transcription + generation happens as an **async background job** with a job ID.
- FR-15: User can poll job status (`queued`, `transcribing`, `generating_notes`, `formatting`, `done`, `failed`) and see progress.
- FR-16: Failed jobs surface a human-readable error (e.g., "video too long", "unsupported link", "transcription failed").
- FR-17: Job history is persisted per user session — user can revisit past notes without regenerating.

### 3.5 Notes Content (per category)
- FR-18 (Interview): Output includes Q&A pairs, key talking points, likely follow-up/gotcha questions, and a difficulty tag per question.
- FR-19 (Exam): Output includes key definitions/terms, structured topic summaries, and a set of self-test questions with answers.
- FR-20 (Understanding): Output includes a plain-language explanation, analogies, a prerequisite-concept list, and a simple concept map (nodes/edges, renderable as a diagram).

### 3.6 Editing & Iteration
- FR-21: User can regenerate notes for an existing transcript with a different category or format without re-uploading/re-transcribing.
- FR-22: User can edit generated notes (basic text edit) before export.

---

## 4. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-1 | Transcription runs **locally** via `faster-whisper` — no third-party transcription API cost. |
| NFR-2 | LLM calls are provider-agnostic behind an interface. v1 ships with two providers: **Gemini API** (hosted, key-based) and **Ollama** (local, no API key, no external cost). No paid/hosted key is required to run the system — Ollama alone must be sufficient end-to-end. |
| NFR-2a | Provider is a per-job or global config choice, not hardcoded. Adding a third provider later (e.g. Anthropic, OpenAI) must only require one new file implementing the provider interface. |
| NFR-2b | Because local models (via Ollama) are less reliable at strict JSON/structured output than hosted APIs, the generation stage must include schema validation + repair/retry logic regardless of provider, and this must be tested specifically against an Ollama-backed run, not just the hosted-API path. |
| NFR-3 | Long-running jobs (transcription, generation) must never block the API request thread — async job queue required. |
| NFR-4 | System should degrade gracefully: partial transcript failures should not lose already-processed chunks. |
| NFR-5 | Single-user / small-team scale for v1 (no need to design for thousands of concurrent jobs) — but architecture should not preclude scaling later. |
| NFR-6 | All uploaded source files and generated notes are stored with a retention policy (default: 30 days, configurable). |
| NFR-7 | Whisper transcription should use the smallest model that meets accuracy needs by default (`base`/`small`), with a config option to upgrade to `medium`/`large-v3` for accuracy-critical jobs. |
| NFR-8 | Frontend must show real-time-ish job progress (polling every 2–3s is acceptable; WebSocket is a stretch goal, not v1-required). |

---

## 5. Out of Scope (v1)

- Visual analysis of video frames (slides, diagrams in the video) — audio/transcript only in v1.
- Multi-user auth/teams/roles — single-user local tool for v1.
- Real-time streaming transcription (only file/link based, not live mic).
- Mobile app — web app only.

---

## 6. Success Criteria

- A user can go from "raw YouTube lecture link" to "downloadable exam-prep markdown notes" in one flow with no manual steps.
- Switching category or output format on an already-processed source takes **no re-transcription** (proves architecture correctly separates ingestion from generation from formatting).
- Adding a 4th category (e.g., "Quick Skim") requires only a new prompt template + schema file — no changes to ingestion, job queue, or formatters.
