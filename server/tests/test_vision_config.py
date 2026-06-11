import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import vision_config as cfg  # noqa: E402

def test_input_modalities():
    assert cfg.INPUT_MODALITIES == ["text", "image"]

def test_build_vision_system_messages():
    msgs = cfg.build_vision_system_messages()
    assert msgs[0]["role"] == "system"
    assert "camera" in msgs[0]["content"].lower()
