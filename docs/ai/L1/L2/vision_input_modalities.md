# Deep Dive — Vision Input Modalities

**When to Read This:** You are changing the LLM model, modifying `input_modalities`, editing system messages, swapping a vendor (STT/LLM/TTS), or trying to understand how camera frames reach the LLM. For the high-level picture, start at [02_architecture](../02_architecture.md).

This recipe uses a cascading `DeepgramSTT → OpenAI → MiniMaxTTS` pipeline built via `AgoraAgent.with_stt().with_llm().with_tts()`. The `input_modalities=["text","image"]` parameter on the `OpenAI` vendor is what instructs Agora to capture the user's published camera frames and forward them as image content to the LLM.

## The vision config module (`vision_config.py`)

`vision_config.py` is intentionally import-free of `agora_agent` — it only defines pure Python constants:

```python
INPUT_MODALITIES = ["text", "image"]

def build_vision_system_messages() -> List[Dict[str, str]]:
    return [{"role": "system", "content": (
        "You are a helpful visual assistant in a voice call. The user shares their "
        "camera with you. When they ask what you see, describe the most recent image "
        "from their camera concisely. Keep replies to one or two sentences.")}]
```

Both are unit-tested in `tests/test_vision_config.py` without importing the SDK.

## Vendor cascade (`agent.py`)

`Agent.start()` constructs the full pipeline:

```python
llm = OpenAI(
    api_key=self.openai_api_key,        # None → Agora-managed (keyless)
    model=self.openai_model,            # OPENAI_MODEL, default "gpt-4o-mini"
    input_modalities=INPUT_MODALITIES,  # ["text", "image"] — enables camera frames
    system_messages=build_vision_system_messages(),
    greeting_message=self.greeting,
)
stt = DeepgramSTT(model="nova-3", language="en")
tts = MiniMaxTTS(model="speech_2_6_turbo", voice_id="English_captivating_female1")

agora_agent = AgoraAgent(
    client=self.client,
    greeting=self.greeting,
    failure_message="Please wait a moment.",
    max_history=50,
    turn_detection={
        "config": {
            "speech_threshold": 0.5,
            "start_of_speech": {"mode": "vad", "vad_config": {"interrupt_duration_ms": 160, "prefix_padding_ms": 300}},
            "end_of_speech": {"mode": "vad", "vad_config": {"silence_duration_ms": 480}},
        },
    },
    advanced_features={"enable_rtm": True},
    parameters=parameters,
).with_stt(stt).with_llm(llm).with_tts(tts)
```

Unlike the realtime recipe, `turn_detection` is set on `AgoraAgent(...)` directly, not on the vendor.

## How camera forwarding works

1. The browser calls `usePublish([localMicrophoneTrack, localCameraTrack])` in `ConversationComponent.tsx`.
2. Both the audio and video streams are published into the Agora RTC channel.
3. Agora's Conversational AI Engine detects the published video track and, because `input_modalities` includes `"image"`, captures frames and forwards them as image content alongside the transcribed user speech to the LLM.
4. No extra backend configuration is needed — the `input_modalities` parameter on the `OpenAI` vendor is the sole enabler.

## Session parameters

Set in `Agent.start()` and passed to `AgoraAgent`:

| Key                    | Value     | Why                                              |
| ---------------------- | --------- | ------------------------------------------------ |
| `audio_scenario`       | `chorus`  | Ultra-low-latency profile for web clients.       |
| `data_channel`         | `rtm`     | Transcript + metrics delivered over RTM.         |
| `enable_error_message` | `true`    | Surface agent-side errors to the client.         |
| `enable_metrics`       | `true`    | Emit pipeline metrics to the UI.                 |
| `output_audio_codec`   | optional  | Forwarded from `POST /startAgent` `parameters`.  |

## Zero-key model selection

`OPENAI_API_KEY` passed as `None` to `OpenAI(api_key=None, ...)` signals Agora-managed mode. The model must be on Agora's managed keyless list. `gpt-4o-mini` is the default and is both vision-capable and Agora-managed. Changing to a model not on that list requires setting `OPENAI_API_KEY`.

## Changing the system prompt or modalities

- Edit `build_vision_system_messages()` in `vision_config.py` for prompt changes.
- Edit `INPUT_MODALITIES` in `vision_config.py` for modality changes (e.g. drop `"image"` to go voice-only).
- Update `tests/test_vision_config.py` to match any new assertions.
- Run `cd server && pytest tests -v` to verify.

## Related L1

- [02_architecture](../02_architecture.md) · [06_interfaces](../06_interfaces.md) · [07_gotchas](../07_gotchas.md)
