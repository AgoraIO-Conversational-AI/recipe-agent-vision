# Architecture — Vision Recipe

Two processes: the agent backend and the Next.js frontend. The browser
publishes both mic and camera; the web tier proxies API calls to the backend.
No separate LLM service is required — Agora manages the OpenAI connection.

## Request flow

```
Browser
  │  GET /api/get_config            → token + channel/UIDs
  │  POST /api/startAgent           → start agent session
  │  publishes mic + camera via RTC
  ▼
Next.js  (rewrites /api/* → AGENT_BACKEND_URL)
  ▼
Agent backend (server/, :8000)
  │  builds session with OpenAI(model="gpt-4o-mini", input_modalities=["text","image"])
  ▼
Agora ConvoAI Cloud
  │  user speech → Deepgram STT (managed)
  │  camera frames captured from user's published video track
  │  frames forwarded as image content to gpt-4o-mini
  │  response text → MiniMax TTS (managed)
  ▼
Agent audio + RTM transcript/metrics → browser
```

`POST /api/stopAgent { agentId }` ends the session.

## Camera forwarding (confirmed)

Agora's Conversational AI Engine captures frames from the user's **published
video track** (the `localCameraTrack` published via `usePublish` in
`ConversationComponent.tsx`). These frames are forwarded to the LLM as image
content. The `input_modalities=["text","image"]` parameter on the `OpenAI`
vendor enables this path.

## API (agent backend, port 8000)

| Endpoint | Method | Description |
| --- | --- | --- |
| `/get_config` | GET | Token + channel/UID config |
| `/startAgent` | POST | Start the agent session |
| `/stopAgent` | POST | Stop the agent by `agent_id` |

The browser calls these as `/api/*`; Next rewrites them to `AGENT_BACKEND_URL`.

## Auth

- Browser → agent backend: none (local dev).
- Agent backend → Agora cloud: Token007, generated from `AGORA_APP_ID` +
  `AGORA_APP_CERTIFICATE`.
- Agent backend → OpenAI (via Agora cloud): Agora-managed; `OPENAI_API_KEY`
  is optional (zero-key setup).

## Key source files

| File | Purpose |
| --- | --- |
| `server/src/agent.py` | Builds the `OpenAI` vendor with `input_modalities=["text","image"]` |
| `server/src/vision_config.py` | Pure config: `INPUT_MODALITIES` and system messages |
| `web/src/components/ConversationComponent.tsx` | Adds `useLocalCameraTrack` + `usePublish([mic, camera])` |
