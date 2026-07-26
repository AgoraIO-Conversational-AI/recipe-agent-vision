# 02 · Architecture

> Two co-located processes. The browser publishes mic and camera into an Agora RTC channel and calls Next.js `/api/*`, which rewrites to the FastAPI backend. The backend owns tokens and the agent session using a cascading STT→LLM→TTS pipeline where the LLM receives camera frames as image input.

## Topology

```
Browser (localhost:3000)
  │  publishes mic + camera via agora-rtc-react
  │  fetch /api/*
  ▼
Next.js (web/)  ──rewrite──▶  Agent backend (server/, :8000)
                                 │  DeepgramSTT → OpenAI gpt-4o-mini (input_modalities=["text","image"]) → MiniMaxTTS
                                 ▼
                              Agora ConvoAI Cloud
                                 │  user speech → Deepgram STT (managed)
                                 │  camera frames from published video track → gpt-4o-mini
                                 │  response text → MiniMax TTS (managed)
                                 ▼
                              Agent audio + RTM transcript/metrics → browser
```

- **`web/`** — Next.js 16 / React 19 / TypeScript. Owns UI plus the RTC/RTM client lifecycle. Calls only `/api/*`. Publishes both mic and camera tracks via `useLocalCameraTrack` + `usePublish([mic, camera])`.
- **`server/`** — Python FastAPI (:8000). Owns Agora token generation and agent session lifecycle. SDK: `agora-agents>=2.3.0` (`import agora_agent`).
- No `llm/` service — Agora manages the OpenAI connection (zero-key by default).

## Camera forwarding

Agora's Conversational AI Engine captures frames from the user's **published video track** (the `localCameraTrack` published via `usePublish` in `ConversationComponent.tsx`). Frames are forwarded as image content to the LLM. The `input_modalities=["text","image"]` parameter on the `OpenAI` vendor enables this path. No extra configuration or tunnel is required beyond standard Agora credentials.

## Request lifecycle

1. Browser `GET /api/get_config` → Next rewrites to backend `/get_config`; backend mints a Token007 from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE` and returns channel + UIDs.
2. Browser joins the RTC channel, publishes mic + camera, then `POST /api/startAgent`; backend builds the vendor cascade and starts an async agent session.
3. Agora captures user audio (Deepgram STT) and camera frames (forwarded as images) and routes both to `gpt-4o-mini`; the model's text response is synthesised via MiniMax TTS and streamed back into the channel.
4. RTM delivers transcript + metrics to the web UI.
5. `POST /api/stopAgent { agentId }` ends the session.

## Key abstractions

- **`Agent`** (`server/src/agent.py`) — async wrapper around `AgoraAgent`; builds the cascading `DeepgramSTT` → `OpenAI` (with `input_modalities`) → `MiniMaxTTS` vendors; owns `_sessions` keyed by `agent_id`.
- **`vision_config.py`** (`server/src/vision_config.py`) — pure config (no `agora_agent` import): `INPUT_MODALITIES = ["text","image"]` and `build_vision_system_messages()`. Unit-tested independently.
- **Rewrite proxy** (`web/next.config.ts`) — the only browser→backend boundary; no Next Route Handlers for agent/token logic.

## Tech decisions

- **Cascading vendors, not MLLM** — this recipe uses `DeepgramSTT` + `OpenAI` + `MiniMaxTTS` via `AgoraAgent.with_stt().with_llm().with_tts()`, not a single MLLM `.with_mllm()`.
- **Vision config isolated** — `INPUT_MODALITIES` and system messages live in `vision_config.py` with no SDK imports so they can be unit-tested cleanly.
- **Zero-key default** — Agora manages the OpenAI API key; `OPENAI_API_KEY` is optional.
- **Agent-level VAD** — `turn_detection` is set on `AgoraAgent(...)` directly (not vendor-owned as in the realtime recipe).

## Related Deep Dives

- [vision_input_modalities](L2/vision_input_modalities.md) — full vendor build, `INPUT_MODALITIES`, system messages, and how camera forwarding is activated.
- [session_lifecycle](L2/session_lifecycle.md) — browser orchestration of config + start/stop, RTC/RTM, camera track lifecycle.
