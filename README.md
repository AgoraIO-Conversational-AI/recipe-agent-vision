# Agora Conversational AI — Vision Recipe (Python)

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![python>=3.10](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://www.python.org/)
[![bun](https://img.shields.io/badge/bun-%E2%89%A51.0-black)](https://bun.sh/)

A voice agent that **sees your camera**. The user publishes their camera via
the web UI and the agent answers the question "what do you see?" by describing
the most recent frame — no extra configuration beyond standard Agora credentials.

## Prerequisites

- [Python 3.10+](https://www.python.org/)
- [Bun](https://bun.sh/)
- Agora App ID + App Certificate (the [Agora CLI](https://github.com/AgoraIO/cli) makes this easy)
- A browser that grants camera access (allow when prompted)

## Run It

```bash
# 1. Install web deps + create the Python venv
bun run setup

# 2. Add Agora credentials (CLI), or edit server/.env.local by hand
agora login
agora project use <your-project>
agora project env write server/.env.local

# 3. Start backend + frontend
bun run dev
```

Open [http://localhost:3000](http://localhost:3000) → **Start Conversation** →
allow camera access → ask "what do you see?"

### Working from a clone

| Service | URL |
| --- | --- |
| Web frontend | http://localhost:3000 |
| Agent backend | http://localhost:8000 |
| Backend API docs | http://localhost:8000/docs |

## Deploy

Deploy `web` (Next.js) and `server` (FastAPI). Set `AGENT_BACKEND_URL` in the
web deployment to point at the backend.

Docker image (published on `v*` tags): `ghcr.io/AgoraIO-Conversational-AI/recipe-agent-vision`

The Docker image is **BACKEND-ONLY** (:8000). Deploy `web` separately (e.g. Vercel).

## Environment variables

Backend env file: [`server/.env.example`](server/.env.example).

| Variable | Required | Default | Notes |
| --- | :---: | :---: | --- |
| `AGORA_APP_ID` | yes | — | Agora Console → Project → App ID |
| `AGORA_APP_CERTIFICATE` | yes | — | Agora Console → Project → App Certificate |
| `OPENAI_MODEL` | | `gpt-4o` | Must be a vision-capable model |
| `OPENAI_API_KEY` | | — | Optional — Agora manages the OpenAI key (keyless) |
| `AGENT_GREETING` | | built-in | Optional opening line override |
| `PORT` | | `8000` | Agent backend port |
| `AGENT_BACKEND_URL` (web deploy) | yes (deploy) | — | Required when deploying `web` to point at the backend |

## Commands

```bash
bun run setup            # install web deps + create server/ venv
bun run dev              # start backend (:8000) + web (:3000)

bun run doctor           # prerequisite check (no creds needed)
bun run doctor:local     # + .env.local + credentials checks

bun run verify           # web-only gate (no Agora creds needed)
bun run verify:local     # full local gate: backend compile + smoke tests + web build
bun run clean            # remove venv and build artifacts
```

Tests run standalone (no Agora cloud needed): `pytest` in `server/`, plus
`bun run verify` in `web/`. CI runs them on Linux/macOS/Windows × Python 3.10 & 3.13.

## Architecture

```
Browser (localhost:3000)
  │  publishes mic + camera via agora-rtc-react
  │  fetch /api/*
  ▼
Next.js  ──rewrite──▶  Agent backend  (server/, localhost:8000)
                          │  starts agent session (OpenAI vendor, gpt-4o)
                          ▼
                       Agora ConvoAI Cloud
                          │  user speech → Deepgram STT (managed)
                          │  camera frames → gpt-4o input_modalities=["text","image"]
                          │  response text → MiniMax TTS (managed)
                          ▼
                       Agent speaks back over RTC
```

The browser calls Next `/api/*`, which rewrites to the agent backend. The agent
backend owns Agora tokens and session lifecycle. No separate LLM service is
needed — Agora manages the OpenAI connection. See [ARCHITECTURE.md](./ARCHITECTURE.md).

## What You Get

- **Web client** that publishes both mic and camera using `agora-rtc-react`
- **Agent backend** (FastAPI :8000) handling Agora tokens and session lifecycle
- **API contract** at `/get_config`, `/startAgent`, `/stopAgent`
- **Managed keyless `gpt-4o`** with `input_modalities:["text","image"]` — Agora
  forwards the user's published camera frames to the LLM; no OpenAI key required
- **Zero-key** — only Agora App ID and App Certificate are required

## How It Works

1. The browser publishes both mic audio and the camera track into an Agora RTC channel.
2. The web UI calls `/api/get_config` (rewritten to the agent backend) to obtain channel credentials.
3. The backend calls Agora's Conversational AI API to start an agent session using the managed `OpenAI` vendor with `input_modalities=["text","image"]`.
4. Agora's cloud engine receives the user's audio stream and transcribes it with managed Deepgram STT.
5. Agora also captures the user's **published camera track** and forwards frames as `image_url` content to `gpt-4o`.
6. `gpt-4o` reasons over both voice intent and the camera image, and Agora synthesises the reply with managed MiniMax TTS.
7. The spoken reply is delivered back over RTC.

On the web side, `useLocalCameraTrack` obtains the camera stream and `usePublish([mic, camera])` sends both tracks into the channel. A small local preview shows the user what the agent sees.

## Repo Map

```
recipe-agent-vision/
├── web/      # Next.js frontend (:3000) — publishes mic + camera
├── server/   # Agent backend (:8000) — tokens, session lifecycle, vision config
├── ARCHITECTURE.md
└── AGENTS.md
```

## Troubleshooting

| Problem | Fix |
| --- | --- |
| No camera preview appears | Allow camera access in the browser when prompted |
| Agent does not describe the camera | Confirm the model is vision-capable (`gpt-4o` default) and camera track published |
| `AGORA_APP_ID` or `AGORA_APP_CERTIFICATE` missing | Run `agora project env write server/.env.local` or fill `server/.env.local` manually |

## More Docs

- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [AGENTS.md](./AGENTS.md)

## License

Released under the [MIT License](./LICENSE).
