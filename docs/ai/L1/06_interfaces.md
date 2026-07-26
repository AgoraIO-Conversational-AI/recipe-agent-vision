# 06 · Interfaces

> Boundary contracts: backend routes, the `/api/*` rewrite map, env vars, the response envelope, and the vision vendor config.

## Backend routes (port 8000)

The browser calls these as `/api/<name>`; Next rewrites to the backend `/<name>`.

### `GET /get_config`

- Query (optional): `channel?: string`, `uid?: int` (≤ 0 or missing → backend generates one).
- Returns `data`: `{ app_id, token, uid (string), channel_name, agent_uid (string) }`.
- Token is a Token007 RTC+RTM token, expiry 3600s, for a concrete non-zero UID.

### `POST /startAgent`

- Body: `{ channelName: string, rtcUid: int, userUid: int, parameters?: object }`.
  - `parameters.output_audio_codec?: string` is the only honored parameter field.
- Returns `data`: `{ agent_id, channel_name, status: "started" }`.
- 400 if `channelName`/`rtcUid`/`userUid` invalid. 500 if `AGORA_APP_ID`/`AGORA_APP_CERTIFICATE` missing.

### `POST /stopAgent`

- Body: `{ agentId: string }`.
- Returns `{ code: 0, msg: "success" }` (no `data`).

## Response envelope

```json
{ "code": 0, "msg": "success", "data": { } }
```

`data` omitted when the route has no payload. Non-zero `code` or missing `data` = error on the client side.

## Rewrite map (`web/next.config.ts`)

| Browser path        | Backend destination |
| ------------------- | ------------------- |
| `/api/get_config`   | `/get_config`       |
| `/api/startAgent`   | `/startAgent`       |
| `/api/stopAgent`    | `/stopAgent`        |

`rewrites()` returns `[]` when `AGENT_BACKEND_URL` is unset. The contract is asserted by `verify-api-contracts.ts` and exercised by `verify-local-proxy.ts`.

## Browser API client (`web/src/services/api.ts`)

- `getConfig({ channel?, uid? }) → GetConfigResponse`
- `startAgent(channelName, rtcUid, userUid) → agent_id`
- `stopAgent(agentId) → void`

## Environment variables

| Variable                | Scope              | Required | Default       |
| ----------------------- | ------------------ | :------: | ------------- |
| `AGORA_APP_ID`          | backend            |    ✅    | —             |
| `AGORA_APP_CERTIFICATE` | backend            |    ✅    | —             |
| `OPENAI_MODEL`          | backend            |          | `gpt-4o-mini` |
| `OPENAI_API_KEY`        | backend            |          | — (optional)  |
| `AGENT_GREETING`        | backend            |          | built-in line |
| `AGENT_BACKEND_URL`     | web (deploy)       |    ✅\*  | `http://localhost:8000` (dev) |
| `PORT`                  | backend (env only) |          | `8000` — do **not** put in `.env.example` |

\* Required wherever the web app is deployed; rewrites are empty without it.

## Vision vendor config (`agent.py` + `vision_config.py`)

`Agent.start()` constructs the cascade inline:

```python
llm = OpenAI(
    api_key=self.openai_api_key,        # None → Agora-managed (keyless)
    model=self.openai_model,            # OPENAI_MODEL, default "gpt-4o-mini"
    input_modalities=INPUT_MODALITIES,  # ["text", "image"] from vision_config.py
    system_messages=build_vision_system_messages(),
    greeting_message=self.greeting,
)
stt = DeepgramSTT(model="nova-3", language="en")
tts = MiniMaxTTS(model="speech_2_6_turbo", voice_id="English_captivating_female1")
```

`INPUT_MODALITIES = ["text", "image"]` is the key parameter that enables camera-frame forwarding. See [vision_input_modalities](L2/vision_input_modalities.md).

## Related Deep Dives

- [vision_input_modalities](L2/vision_input_modalities.md) — every vendor field, system messages, and how `input_modalities` activates camera forwarding.
