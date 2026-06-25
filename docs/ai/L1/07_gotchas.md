# 07 · Gotchas

> Non-obvious pitfalls specific to the vision recipe. Read before changing the agent, camera handling, env, or verify scripts.

## Zero-key vs BYO-key

`OPENAI_API_KEY` is **optional** in this recipe. Agora manages the OpenAI connection by default (keyless). The server boots and agents start without an OpenAI key. Only set `OPENAI_API_KEY` if your Agora account requires you to supply your own key. This is the opposite of the realtime recipe where the key is required.

## Camera frames only reach the LLM if the track is published

The browser **must** publish the camera track (`usePublish([mic, camera])`) into the RTC channel. If the track is not published, Agora has no video stream to capture frames from and the LLM will see no images — the agent cannot answer "what do you see?". Confirm the browser granted camera permission and the track is active.

## Camera track must be cleaned up on unmount

`localCameraTrack.stop()` + `localCameraTrack.close()` must be called when the conversation component unmounts (turns off the camera light). A cleanup `useEffect` in `ConversationComponent.tsx` handles this. Do not remove it — leaving the track open keeps the camera light on after the user leaves the page.

## VAD is agent-level, not vendor-level

`turn_detection` is set on `AgoraAgent(...)` directly (not on the `OpenAI` vendor). This is different from the realtime recipe where `server_vad` is vendor-owned. Do not attempt to move `turn_detection` onto the `OpenAI` vendor — that is only valid for MLLM (`.with_mllm()`) configs.

## `OPENAI_MODEL` must be vision-capable and Agora-managed

Not all OpenAI models support image input, and not all vision-capable models are on the Agora-managed keyless list. The default `gpt-4o-mini` is both vision-capable and keyless. Changing `OPENAI_MODEL` to a model not on the Agora-managed list will fail unless `OPENAI_API_KEY` is also set.

## Do not put `PORT` in `server/.env.example`

`verify:local:fastapi` injects a random `PORT` and loads env with `load_dotenv(override=True)`. A `PORT` line in `.env.example` (copied to `.env.local`) would clobber the injected port and break the smoke test.

## Keep `/api/*` ownership in rewrites

Adding `web/app/api/**/route.ts` for agent/token logic breaks the boundary — `verify-api-contracts.ts` explicitly fails if a `route.ts` exists under `app/api`. Token logic belongs in `server/`.

## camelCase request fields

`StartAgentRequest` uses `channelName`, `rtcUid`, `userUid` (camelCase) to match the browser client. Renaming one side without the other breaks the contract tests.

## UID normalization in transcripts

`normalizeTranscript` maps `uid === '0'` to the local UID. Token issuance also rejects zero/negative UIDs and generates a concrete one. Preserve both — speaker mapping and tokens depend on concrete UIDs.

## Local calls under a global proxy

Global proxies (Clash, etc.) can break `localhost`/RFC-1918 traffic. Configure the proxy to send `127.0.0.1`, `localhost`, and private ranges DIRECT, or `socksio` (in `requirements.txt`) plus `all_proxy` to route the backend through SOCKS.

## Related Deep Dives

- [vision_input_modalities](L2/vision_input_modalities.md) — correct vendor and modalities wiring.
