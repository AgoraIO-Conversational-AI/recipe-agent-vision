# Agora Agent Backend — Vision Recipe

FastAPI service that owns Agora token generation and agent session lifecycle for
the vision recipe. It is the service the web client reaches through the
Next.js `/api/*` rewrite proxy (port 8000).

## What makes this the vision recipe

The agent uses the SDK's `OpenAI` vendor with `input_modalities=["text","image"]`
and `model="gpt-4o-mini"`. Agora captures the user's published camera track and
forwards frames as image content to the LLM. No custom endpoint or tunnel is
required — OpenAI is Agora-managed (zero-key by default).

System messages and the `INPUT_MODALITIES` constant live in `vision_config.py`
so they can be unit-tested without importing `agora_agent`.

## Run

Use the repo-root `README.md` for the full local flow (`bun run dev`). To work
on this module directly:

```bash
cd server
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python src/server.py
```

## Tests

```bash
cd server
source venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest tests/ -q
```

## Environment

`server/.env.example` is the template.

| Variable | Required | Default | Notes |
| --- | :---: | :---: | --- |
| `AGORA_APP_ID` | yes | — | Agora Console → Project → App ID |
| `AGORA_APP_CERTIFICATE` | yes | — | Agora Console → Project → App Certificate |
| `OPENAI_MODEL` | | `gpt-4o-mini` | Must be vision-capable and Agora-managed (keyless) |
| `OPENAI_API_KEY` | | — | Optional — Agora manages the OpenAI key (keyless) |
| `AGENT_GREETING` | | built-in | Optional opening line override |
| `PORT` | | `8000` | Agent backend port |

## API

- `GET /get_config` — token + channel/UID config
- `POST /startAgent` — start a vision agent session
- `POST /stopAgent` — stop an agent session

The repo-root `bun run verify:local:fastapi` exercises these routes through the
Next proxy using a fake agent (`scripts/run_fake_server.py`), so no live Agora
session is required.
