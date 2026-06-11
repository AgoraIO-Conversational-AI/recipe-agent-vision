# Agora Conversational AI — Vision Recipe (Python)

A voice agent that **sees your camera**. The user publishes their camera via
the web UI and the agent answers the question "what do you see?" by describing
the most recent frame — no extra configuration beyond standard Agora credentials.

## How it works

Agora's Conversational AI Engine captures the user's published camera track and
forwards frames as image content to the LLM. The agent is powered by
**managed `gpt-4o`** (zero-key: Agora manages the OpenAI key) with
`input_modalities=["text","image"]`. STT (Deepgram) and TTS (MiniMax) are also
Agora-managed.

This is a **zero-key** recipe: `OPENAI_API_KEY` is optional. Only your Agora
App ID and App Certificate are required.

## Prerequisites

- [Python 3.8+](https://www.python.org/)
- [Bun](https://bun.sh/)
- Agora App ID + App Certificate (the [Agora CLI](https://github.com/AgoraIO/cli) makes this easy)
- A browser with camera access (allow when prompted)

## Run it

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

## Project structure

```
recipe-agent-vision/
├── server/   # Agent backend (:8000) — tokens + agent lifecycle, vision config
│   ├── src/{server.py, agent.py, vision_config.py}
│   └── tests/test_vision_config.py
├── web/      # Next.js frontend (:3000) — publishes mic + camera
│   └── src/components/ConversationComponent.tsx  (useLocalCameraTrack)
└── package.json
```

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

## Troubleshooting

| Problem | Fix |
| --- | --- |
| No camera preview appears | Allow camera access in the browser when prompted |
| Agent does not describe the camera | Confirm the model is vision-capable (`gpt-4o` default) and camera track published |
| `AGORA_APP_ID` or `AGORA_APP_CERTIFICATE` missing | Run `agora project env write server/.env.local` or fill `server/.env.local` manually |

## License

MIT
