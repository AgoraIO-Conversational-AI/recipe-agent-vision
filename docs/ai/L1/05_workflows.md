# 05 · Workflows

> Step-by-step guides for the common changes in this recipe. Each ends with the narrowest verify command to run.

## Add or change a browser-facing route

1. Add the FastAPI handler in `server/src/server.py` (return the `{ code, msg, data }` envelope).
2. Add the `/api/<name>` → `/<name>` mapping in `web/next.config.ts` `rewrites()`.
3. Add a client helper in `web/src/services/api.ts`.
4. Extend `web/scripts/verify-api-contracts.ts` with the new path + envelope assertions.
5. Verify: `bun run verify:web` (and `bun run verify:local:fastapi` if it should go through the real backend).

## Change the agent prompt / greeting / model

1. Greeting: set `AGENT_GREETING` (env) or edit the default in `server/src/agent.py`.
2. Model: set `OPENAI_MODEL` (default `gpt-4o-mini`; must be vision-capable and Agora-managed).
3. System messages: edit `build_vision_system_messages()` in `server/src/vision_config.py`.
4. Verify: `bun run verify:backend` (compile) + `cd server && pytest tests -v`.

## Change vision modalities or system messages

1. Edit `INPUT_MODALITIES` in `server/src/vision_config.py` (currently `["text","image"]`).
2. Edit `build_vision_system_messages()` in the same file for prompt changes.
3. Update `test_vision_config.py` if the values or message content change.
4. Verify: `cd server && pytest tests -v`.

For full vendor build details see [vision_input_modalities](L2/vision_input_modalities.md).

## Adjust session parameters (codec, VAD)

1. Edit the `parameters` dict in `Agent.start()` (`audio_scenario`, `data_channel`, `enable_metrics`, etc.). `output_audio_codec` is also accepted per-request via `parameters` on `POST /startAgent`.
2. To change VAD, edit `turn_detection` in `AgoraAgent(...)` construction in `agent.py`.
3. Verify: `bun run verify:local:fastapi`.

## Run / debug locally

```bash
bun run dev              # both processes
bun run doctor:local     # check creds + .env.local before a live call
```

## Verify before finishing

| Change touches…              | Run                                                                  |
| ---------------------------- | -------------------------------------------------------------------- |
| Web only                     | `bun run verify:web`                                                 |
| Backend logic / vendor config| `bun run verify:backend` + `cd server && pytest tests -v`            |
| Route/proxy boundary         | `bun run verify:web:proxy` and/or `bun run verify:local:fastapi`     |
| Anything end-to-end (local)  | `bun run verify:local`                                               |

## Deploy

1. Deploy `web/` as a Next.js app.
2. Deploy `server/` (or any reachable FastAPI host); the published backend-only image is `ghcr.io/AgoraIO-Conversational-AI/recipe-agent-vision` on `v*` tags.
3. Set `AGENT_BACKEND_URL` in the web deployment so rewrites reach the backend.

## Related Deep Dives

- [vision_input_modalities](L2/vision_input_modalities.md) — vendor build and modalities config.
- [session_lifecycle](L2/session_lifecycle.md) — client-side join/camera/renewal/teardown.
