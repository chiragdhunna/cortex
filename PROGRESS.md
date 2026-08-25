# Cortex Build Progress

## Definition of Done

- [ ] All source types produce canonical notes JSON.
- [ ] Each category produces its distinct shape.
- [ ] All formats render without a new LLM call.
- [ ] Regenerate and format skip earlier stages (integration-tested).
- [ ] Frontend supports submit, progress, view, and download.
- [ ] Docker Compose works from a clean checkout.
- [ ] Ollama works with no API keys; Gemini works with a supplied key.
- [ ] Requirements are satisfied or explicitly deferred.

## Stage log

- [x] Stage 1 — Project scaffold (database initialization and compilation verified)
- [x] Stage 2 — Ingestion (PDF and transcription adapter contracts unit-tested)
- [x] Stage 3 — Chunking (long-text boundary/overlap test verified)
- [x] Stage 4 — Generation (provider-neutral schema retry tests verified; live providers constrained)
- [x] Stage 5 — Formatting (all four renderers tested against canonical fixture)
- [x] Stage 6 — Job orchestration (state transitions and skip-stage integration test verified)
- [x] Stage 7 — Frontend (React submission, polling, rendering, downloads, history implemented; production build verified)
- [x] Stage 8 — Polish (caching, limits, retention, README, and critical-path tests implemented)

## Final verification status

Implementation through Stages 1–8 is complete and the local Python test suite passes.
The remaining live-environment checks are recorded in `DECISIONS.md`: a reachable
Ollama daemon/model (with no API key), an optional Gemini key, frontend dependencies,
and a Docker daemon are required to check the remaining Definition of Done items.

The host now has Docker Compose running and `llama3.1:8b` pulled. The live API and
Ollama pipeline smoke test is the final verification step; the API image must be
rebuilt after the `/health` endpoint addition.
