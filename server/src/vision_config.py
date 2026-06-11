"""Pure config for the vision recipe — no agora_agent import."""
from typing import Dict, List

INPUT_MODALITIES = ["text", "image"]


def build_vision_system_messages() -> List[Dict[str, str]]:
    return [{"role": "system", "content": (
        "You are a helpful visual assistant in a voice call. The user shares their "
        "camera with you. When they ask what you see, describe the most recent image "
        "from their camera concisely. Keep replies to one or two sentences.")}]
