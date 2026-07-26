# Agent Development Guide

For coding agents working in `recipe-agent-vision`. This repository is the
**vision** recipe in the Agora Conversational AI recipes family. A voice agent
that sees the user's camera via managed `gpt-4o-mini` with
`input_modalities=["text","image"]`.

## How to Load

This repository uses progressive disclosure documentation. Docs live under
`docs/ai/` in three levels.

1. Read [docs/ai/L0_repo_card.md](docs/ai/L0_repo_card.md) to identify the repo.
2. This repo declares `Recipe Role: base`; read [docs/ai/RECIPE.md](docs/ai/RECIPE.md) before changing reusable recipe contracts.
3. Load ALL 8 files in [docs/ai/L1/](docs/ai/L1/). They are small — load all upfront.
4. Follow L2 deep-dive links only when L1 isn't detailed enough. The index is at [docs/ai/L1/L2/_index.md](docs/ai/L1/L2/_index.md).

The sections below remain the canonical contributor handbook for hands-on work;
the `docs/ai/` tree is the structured summary used by AI agents.

## System shape

- **`server/`** — Python FastAPI agent backend (:8000). Owns Agora token
  generation and agent session lifecycle. Uses the `OpenAI` vendor with
  `input_modalities=["text","image"]` and `vision_config.py` for system
  messages. SDK: `agora-agents>=2.3.0` (`import agora_agent`).
- **`web/`** — Next.js 16 / React 19 / TypeScript frontend (:3000). Publishes
  both mic and camera via `agora-rtc-react` (`useLocalCameraTrack`,
  `usePublish([mic, camera])`). Shows a small local camera preview.
- Auth: Token007 from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE`.
- No `llm/` directory — this recipe uses Agora-managed OpenAI (zero-key).

## Pipeline

Cascading STT→LLM→TTS: `DeepgramSTT` → `OpenAI` (`gpt-4o-mini`, `input_modalities=["text","image"]`) → `MiniMaxTTS`.
Turn detection is agent-level VAD (set on `AgoraAgent(...)` directly). Zero-key by default.

## Routing / ownership

- UI and RTC/RTM lifecycle live in `web/`.
- Browser-facing `/api/*` paths are Next rewrites (`web/next.config.ts`) to the
  agent backend; do not add `web/app/api/**/route.ts` for agent/token logic.
- Token generation and agent lifecycle live in `server/src/`.
- Vision config (modalities + system messages) lives in `server/src/vision_config.py`.

## Supported modes

- **Local:** `bun run dev` starts `server` (:8000) and `web` (:3000). The web
  app calls `/api/*`; Next rewrites to `AGENT_BACKEND_URL=http://localhost:8000`.
  No tunnel required — Agora manages the OpenAI connection.
- **Deploy:** deploy `web` (Next) + `server` (reachable FastAPI). Set
  `AGENT_BACKEND_URL` in the web deployment. A backend-only image is published to
  `ghcr.io/AgoraIO-Conversational-AI/recipe-agent-vision` on `v*` tags.

## Env vars

| Variable | Default | Notes |
|---|---|---|
| `AGORA_APP_ID` | — | required |
| `AGORA_APP_CERTIFICATE` | — | required |
| `OPENAI_MODEL` | `gpt-4o-mini` | Must be vision-capable and Agora-managed (keyless) |
| `OPENAI_API_KEY` | — | Optional — Agora manages the OpenAI key by default |
| `AGENT_GREETING` | built-in | Optional opening line override |

## Key vision details

- `INPUT_MODALITIES = ["text", "image"]` is defined in `vision_config.py` and
  passed to `OpenAI(input_modalities=...)` in `agent.py`.
- Agora captures the user's **published camera track** and forwards frames as
  image content to the LLM. This is confirmed behavior.
- The model must be vision-capable and Agora-managed (keyless). Default is `gpt-4o-mini` (env: `OPENAI_MODEL`).
- `OPENAI_API_KEY` is optional — Agora manages the OpenAI key (zero-key).

## Patterns

- Keep the web client calling `/api/*`; hide backend placement behind Next rewrites.
- Keep token generation and the App Certificate in `server/`.
- Keep `vision_config.py` import-free of `agora_agent` (pure config, unit-tested).
- Do not add an `llm/` directory to this recipe.

## Anti-patterns

- Do not reintroduce Next Route Handlers for agent/token logic.
- Do not add a `CustomLLM` vendor — this recipe uses managed `OpenAI`.
- Do not put `PORT` in `server/.env.example` (it would clobber the random port
  that `verify:local:fastapi` injects via `load_dotenv(override=True)`).
- Do not reference competing RTC platforms in this repo.

## Commands

```bash
bun run setup
bun run dev
bun run doctor
bun run doctor:local
bun run verify         # web-only, no creds
bun run verify:local   # full local gate
```

Narrower checks: `bun run verify:backend`, `bun run verify:local:fastapi`,
`bun run verify:web:proxy`. Backend tests: `cd server && pytest tests -v`.

## Done criteria

1. Run the narrowest relevant verification command.
2. Web-affecting changes: `bun run verify:web` passes (includes next build).
3. Backend-affecting changes: `bun run verify:backend` passes.
4. If you change required env vars or setup steps, update the root README, the
   relevant module README, and `server/.env.example` together.
5. If the change touches workflows, interfaces, gotchas, or security details,
   update the matching file under [docs/ai/L1/](docs/ai/L1/) and bump
   `Last Reviewed` in [docs/ai/L0_repo_card.md](docs/ai/L0_repo_card.md).

## Git Conventions

### Commit messages — conventional commits

- **Format:** `type: description` or `type(scope): description`
- **Types:** `feat:` (new feature), `fix:` (bug fix), `chore:` (maintenance, version bumps), `test:` (test additions/changes), `docs:` (documentation)
- **Scoped variant:** `feat(scope):`, `fix(scope):` — e.g. `fix(server): validate agora credentials`
- **Lowercase after prefix** — `feat: add feature`, not `feat: Add feature`
- **Present tense** — "add feature", not "added feature"

### Branch names

- **Format:** `type/short-description` — lowercase, hyphen-separated
- **Types match commit types:** `feat/`, `fix/`, `chore/`, `test/`, `docs/`
- **Examples:** `feat/vision-modalities`, `fix/camera-cleanup`, `docs/progressive-disclosure`

### General rules

- **Repo-local `AGENTS.md` is the authoritative source for repo conventions.**
- **No AI tool names** — never mention claude, cursor, copilot, cody, aider, gemini, codex, chatgpt, or gpt-3/4 in commit messages or PR descriptions.
- **No Co-Authored-By trailers** — omit AI attribution lines.
- **No `--no-verify`** — let git hooks run normally.
- **No git config changes** — do not modify `user.name` or `user.email`.

## Doc Commands

| Command       | When to use                                                                  |
| ------------- | ---------------------------------------------------------------------------- |
| generate docs | No `docs/ai/` directory exists yet                                           |
| update docs   | Code changed since the `Last Reviewed` date in L0                            |
| test docs     | Verify docs give agents the right context (writes `docs/ai/test-results.md`) |
| fix docs      | Close findings from a docs review or test run                                |

See the [progressive disclosure standard](https://github.com/AgoraIO-Community/ai-devkit/blob/main/docs/standard/progressive-disclosure-standard.md) and [workflows](https://github.com/AgoraIO-Community/ai-devkit/blob/main/docs/workflows/progressive-disclosure-docs.md) for the full specification.
