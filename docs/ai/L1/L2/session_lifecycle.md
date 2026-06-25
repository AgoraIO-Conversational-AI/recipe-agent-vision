# Deep Dive — Session Lifecycle

**When to Read This:** You are touching client-side join, camera track acquisition, token renewal, RTC/RTM wiring, transcript handling, or mid-call control. For the contracts these calls hit, see [06_interfaces](../06_interfaces.md).

The browser owns the full RTC/RTM client lifecycle and the camera track; the backend owns tokens and the agent session. The two meet only at `/api/*`.

## End-to-end flow

1. **Config** — `LandingPage.tsx` calls `getConfig()` (`web/src/services/api.ts`) → `GET /api/get_config`. Backend mints a Token007 (RTC+RTM, 3600s) for a concrete non-zero UID and returns `{ app_id, token, uid, channel_name, agent_uid }`.
2. **Join** — `ConversationComponent.tsx` joins the RTC channel with the returned token/UID via `useJoin`, then logs in to RTM.
3. **Camera + mic acquire** — `useLocalMicrophoneTrack` and `useLocalCameraTrack` obtain both tracks. Both are published together via `usePublish([localMicrophoneTrack, localCameraTrack])`. A local preview renders the camera stream inline.
4. **Start agent** — `startAgent(channelName, rtcUid, userUid)` → `POST /api/startAgent`. Backend builds the vendor cascade, starts the async session, and returns `agent_id`.
5. **Converse** — user audio flows through Deepgram STT; camera frames are captured and forwarded to `gpt-4o-mini`; MiniMax TTS synthesises the reply. RTM delivers transcript + metrics.
6. **Stop** — `stopAgent(agentId)` → `POST /api/stopAgent`. The client also unpublishes and closes both the mic and camera tracks on end-call.

## Camera track lifecycle

```
useLocalCameraTrack(isReady)
  → localCameraTrack acquired
  → usePublish([..., localCameraTrack])   // camera active in channel
  → Agora captures frames → forwards to LLM

handleEndConversation():
  client.unpublish(localCameraTrack)
  localCameraTrack.stop()
  localCameraTrack.close()               // camera light off

useEffect cleanup (unmount):
  localCameraTrack?.stop()
  localCameraTrack?.close()              // safety cleanup on navigation/reload
```

The cleanup `useEffect` is the safety net for unexpected unmounts (navigation, reload, error boundary). Do not remove it.

## Backend session bookkeeping

`Agent` (`server/src/agent.py`) keeps an in-memory map `self._sessions[agent_id] = session`.

- `stop(agent_id)` pops the session and calls `session.stop()`.
- If the session is missing (e.g. process restarted), it falls back to `self.client.stop_agent(agent_id)` — the stateless cloud path. This is why stop is robust across restarts but `_sessions` itself is **not** a durable store.

## Transcript handling (`web/src/lib/conversation.ts`)

- `normalizeTranscript(transcript, localUid)` — maps `uid === '0'` to the local UID and runs `normalizeTranscriptSpacing` on text.
- `normalizeTimestampMs(ts)` — promotes second-precision timestamps to ms.
- `getMessageList` / `getCurrentInProgressMessage` — split finalized vs in-progress turns (by `TurnStatus.IN_PROGRESS`).
- `mapAgentVisualizerState(agentState, isConnected, connectionState)` — maps SDK state → UIKit visualizer state (`joining`, `listening`, `analyzing`, `talking`, `ambient`, `disconnected`).

## Token renewal

Tokens expire at 3600s. The client handles `token-privilege-will-expire` in `ConversationComponent.tsx` by calling `onTokenWillExpire` (provided by `LandingPage.tsx`), which re-fetches config and renews both RTC and RTM tokens. Keep renewal client-side — the backend stays stateless about who is connected.

## What stays where

- **Client owns:** RTC join, mic + camera publish, local preview, RTM login, transcript/metrics/state listeners, token renewal, explicit end-call media release, camera cleanup on unmount.
- **Backend owns:** token minting, vendor cascade build, session start/stop.
- Do not move token logic into the web app or add Route Handlers for it (see [07_gotchas](../07_gotchas.md)).

## Related L1

- [02_architecture](../02_architecture.md) · [03_code_map](../03_code_map.md) · [06_interfaces](../06_interfaces.md)
