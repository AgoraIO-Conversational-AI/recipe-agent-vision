# Agent Development Guide

For coding agents working in `recipe-agent-vision`. This repository is the
**vision** recipe (`Recipe Role: vision`) in the Agora Conversational AI
recipes family. A voice agent that sees the user's camera via managed `gpt-4o`
with `input_modalities=["text","image"]`.

## System shape

- **`server/`** — Python FastAPI agent backend (:8000). Owns Agora token
  generation and agent session lifecycle. Uses the `OpenAI` vendor with
  `input_modalities=["text","image"]` and `vision_config.py` for system
  messages. SDK: `agora-agents>=2.0.0` (`import agora_agent`).
- **`web/`** — Next.js 16 / React 19 / TypeScript frontend (:3000). Publishes
  both mic and camera via `agora-rtc-react` (`useLocalCameraTrack`,
  `usePublish([mic, camera])`). Shows a small local camera preview.
- Auth: Token007 from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE`.
- No `llm/` directory — this recipe uses Agora-managed OpenAI (zero-key).

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
  `AGENT_BACKEND_URL` in the web deployment.

## Key vision details

- `INPUT_MODALITIES = ["text", "image"]` is defined in `vision_config.py` and
  passed to `OpenAI(input_modalities=...)` in `agent.py`.
- Agora captures the user's **published camera track** and forwards frames as
  image content to the LLM. This is confirmed behavior.
- The model must be vision-capable. Default is `gpt-4o` (env: `OPENAI_MODEL`).
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
`bun run verify:web:proxy`.

## Done criteria

1. Run the narrowest relevant verification command.
2. Web-affecting changes: `bun run verify:web` passes (includes next build).
3. Backend-affecting changes: `bun run verify:backend` passes.
4. If you change required env vars or setup steps, update the root README, the
   relevant module README, and `server/.env.example` together.

## Git conventions

- Conventional Commits: `type: description` or `type(scope): description`
  (`feat`, `fix`, `chore`, `test`, `docs`). Lowercase after the prefix, present
  tense.
- No AI tool names in commit messages or PR descriptions. No `Co-Authored-By`
  trailers. No `--no-verify`. No git config changes.
- Branch names: `type/short-description` (e.g. `feat/vision-config`).
