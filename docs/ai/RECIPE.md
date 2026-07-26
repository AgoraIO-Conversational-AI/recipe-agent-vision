---
recipe_version: 1.0.0
recipe_status: experimental
extension_points:
  - id: api.routes
    name: Browser-facing API routes
  - id: agent.vendor-config
    name: OpenAI vendor model, modalities, system messages, and STT/TTS vendor selection
  - id: web.conversation-ui
    name: Conversation UI panels, camera preview, and controls
  - id: verification.contracts
    name: Contract, proxy, and local FastAPI smoke verification
invariants:
  - id: api.rewrite-boundary
    summary: Browser calls stay on /api/* and Next rewrites to FastAPI; no Route Handlers for agent/token logic.
  - id: secrets.server-only
    summary: Agora App Certificate stays in the Python backend. OPENAI_API_KEY is optional and, when set, also stays in the backend.
  - id: vendor.cascading
    summary: The agent uses DeepgramSTT + OpenAI + MiniMaxTTS via .with_stt().with_llm().with_tts(); no single MLLM .with_mllm().
  - id: vision.input-modalities
    summary: input_modalities=["text","image"] on the OpenAI vendor enables camera-frame forwarding from the user's published video track.
  - id: vision.config-isolated
    summary: INPUT_MODALITIES and system messages live in vision_config.py with no agora_agent import; unit-tested independently.
  - id: token.uid-concrete
    summary: Backend resolves missing, zero, or negative UIDs before issuing an RTC+RTM token.
stable_contracts:
  - id: env.required
    summary: AGORA_APP_ID and AGORA_APP_CERTIFICATE are required; AGENT_BACKEND_URL is required by deployed web rewrites.
  - id: env.zero-key
    summary: OPENAI_API_KEY is optional; Agora manages the OpenAI key by default. OPENAI_MODEL must be vision-capable and Agora-managed.
  - id: api.core-routes
    summary: GET /api/get_config, POST /api/startAgent, and POST /api/stopAgent remain the browser-facing contract.
  - id: response.envelope
    summary: Successful backend responses use { code, msg, data }.
---

# Recipe Contract

This base recipe defines the reusable surface for a Python-backed Agora Conversational AI **vision** quickstart: a cascading STT→LLM→TTS pipeline where the LLM receives the user's camera frames via `input_modalities=["text","image"]`, behind a Next.js web client.

## Recipe Role

- Role: `base` recipe (self-contained, clone-and-run; no `Extends` pin).
- Target audience: developers building a voice + vision agent where the LLM can see the user's camera, with a Python FastAPI backend and Next.js web client.
- Reuse model: clone, bind project, run, then customize vendor config, system messages, or browser UI.

## Recipe Scope

- Python FastAPI token generation and managed agent lifecycle.
- A cascading `DeepgramSTT` → `OpenAI` (with `input_modalities=["text","image"]`) → `MiniMaxTTS` pipeline.
- Zero-key by default — Agora manages the OpenAI connection; `OPENAI_API_KEY` is optional.
- Vision config isolated in `vision_config.py` (no SDK import) for clean unit testing.
- Next.js browser UI with RTC audio + camera, RTM transcript/metrics, local camera preview.
- Rewrite-only `/api/*` browser facade hiding backend placement.
- Contract, proxy, and local FastAPI smoke verification that need no live Agora calls.

## Baseline Implementation Guidance

Use this repo's source and progressive disclosure docs as the starting point, then customize. Do not recreate the Agora ConvoAI integration from memory — vendor schemas, SDK builder fields, token behavior, and RTM details drift. Copy verified patterns from this repo.

## Extension Points

| ID | Surface | How to extend | Required follow-up |
| -- | ------- | ------------- | ------------------ |
| `api.routes` | `server/src/server.py`, `web/next.config.ts`, `web/src/services/api.ts` | Add FastAPI route, add rewrite, add browser fetch helper. | Extend `web/scripts/verify-api-contracts.ts`; add proxy/fastapi coverage if it belongs in local verification. |
| `agent.vendor-config` | `server/src/vision_config.py`, `server/src/agent.py` | Change `OPENAI_MODEL`, `INPUT_MODALITIES`, `build_vision_system_messages()`, or swap STT/TTS vendors. | Run `verify:backend` + `pytest tests`; update `test_vision_config.py` if constants change; document new env in `server/.env.example` (never add `PORT`). |
| `web.conversation-ui` | `web/src/components/*`, `web/src/lib/conversation.ts` | Customize pre-call, transcript, metrics, camera preview, connection status, or mic UI. | Preserve RTC/RTM lifecycle ownership, camera track cleanup, and transcript UID normalization. |
| `verification.contracts` | `web/scripts/*.ts`, root `package.json` | Add checks for new browser/backend boundaries. | Keep checks runnable without live Agora credentials. |

## Invariants

- Browser code calls only `/api/get_config`, `/api/startAgent`, and `/api/stopAgent` for the default flow.
- Next.js owns `/api/*` through rewrites only; no `web/app/api/**/route.ts` for agent/token logic.
- FastAPI owns token generation, `AGORA_APP_CERTIFICATE`, and agent lifecycle.
- The cascading `DeepgramSTT + OpenAI + MiniMaxTTS` pipeline is built via `.with_stt().with_llm().with_tts()`.
- `input_modalities=["text","image"]` is the sole parameter that activates camera-frame forwarding from the user's published video track.
- `vision_config.py` has no `agora_agent` import; it is pure config.
- The backend issues one RTC+RTM-capable token for a concrete non-zero UID.

## Stable Contracts

| Contract | Stable shape |
| -------- | ------------ |
| Required backend env | `AGORA_APP_ID`, `AGORA_APP_CERTIFICATE` |
| Optional backend env | `OPENAI_MODEL`, `OPENAI_API_KEY`, `AGENT_GREETING`, `PORT` (env only) |
| Required web deploy env | `AGENT_BACKEND_URL` |
| `GET /api/get_config` | Query `channel?`, `uid?`; returns `data.app_id`, `data.token`, `data.uid`, `data.channel_name`, `data.agent_uid`. |
| `POST /api/startAgent` | Body `{ channelName, rtcUid, userUid, parameters? }`; returns `data.agent_id`, `data.channel_name`, `data.status`. |
| `POST /api/stopAgent` | Body `{ agentId }`; returns `{ code: 0, msg: "success" }`. |
| Success envelope | `{ "code": 0, "msg": "success", "data": ... }` where the route has data. |
| Verification entry points | `bun run verify:web`, `bun run verify:backend`, `bun run verify:web:proxy`, `bun run verify:local:fastapi`, `bun run verify:local`. |

## Internal / Subject to Change

- Visual layout, component composition, Tailwind classes, and assets under `web/src/components/`.
- Exact model name, STT/TTS vendor choice, VAD timing, voice ID, and greeting text, as long as they stay documented extension points.
- In-memory `Agent._sessions` details; the stable behavior is start by channel/user and stop by returned `agent_id`.
- Verification internals under `web/scripts/`; the stable surface is the root script names and what they assert.
- `agora-agents` SDK minor-version behavior; this recipe lower-bounds `>=2.3.0` but does not freeze every field.

## Related Progressive Disclosure Docs

- `L1/01_setup.md` — setup, env, and commands.
- `L1/02_architecture.md` — request flow, camera forwarding, and topology.
- `L1/05_workflows.md` — common modification workflows.
- `L1/06_interfaces.md` — route, rewrite, env, and vision vendor contracts.
- `L1/L2/vision_input_modalities.md` — full vendor build and modalities detail.
- `L1/L2/session_lifecycle.md` — camera track and RTC/RTM/session orchestration.
