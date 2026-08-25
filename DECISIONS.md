# Decisions and environmental constraints

## Git metadata is read-only in this execution environment (2026-08-25)

Stage commits and pushes were attempted after Stage 1. Git could not create
`.git/index.lock` because `.git` is mounted read-only. Source changes remain in the
working tree and are verified locally, but cannot be committed or pushed from this
environment. This does not affect implementation or runtime verification.

## Faster-whisper live model smoke test deferred in this environment (2026-08-25)

The transcriber wrapper is independently unit-tested with a short mocked Whisper
segment. A live smoke test requires downloading a Whisper model and an audio fixture;
the environment does not provide either. `scripts/test_ingest.py audio sample.wav`
is included for the required local run after `faster-whisper` has downloaded its model.

## Ollama server unavailable to sandbox (2026-08-25)

`ollama` is installed, but the sandbox prevents a connection to `localhost:11434`.
The generation repair path is tested through an Ollama-shaped provider fake, including
invalid-JSON retry. A real local server run must be performed on a host where the
daemon is reachable; no API keys are required by the implementation.

## Frontend dependency installation unavailable in sandbox (2026-08-25)

The frontend uses Vite/React/TypeScript, but `npm run build` cannot locate `tsc` and `npm install` did not populate `node_modules` in this restricted environment. The source is included and the README gives the reproducible host-side build command.

## Docker daemon unavailable to sandbox (2026-08-25)

`docker compose config` validates successfully using `.env.example`, and the host was able to build the API/worker images. Startup then failed while Docker attempted to create a bridge-network veth pair (`operation not supported`), including for `hello-world`. Compose therefore uses Linux host networking so it does not require veth creation; services use loopback for Redis and Ollama. On bridge-capable hosts, `network_mode: host` can be removed and the original published ports/DNS settings restored.

The same host-network setting is now applied to Compose image builds (`build.network: host`), because the original failure occurred during the Dockerfile's networked `apt-get` build step.
