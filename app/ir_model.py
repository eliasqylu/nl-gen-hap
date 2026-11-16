"""Device-independent haptic intermediate representation (IR).

Layers (see docs/IR_CONTRACT.md):
  - SensationProfile : perception-level, device-independent subjective attributes.
  - HapticTrack      : structure-level, event sequence described in device-
                       independent blocks and parameters.
  - Device signal     : translated per backend (preview waveform now; DS/ERM
                       backends later). This module does NOT emit hardware signals.

Design intent for the main research thread (direction 1): local editing that
changes a target sensation while preserving others. `EditIntent` explicitly
separates target sensations from preserved sensations; the compensation step
lives in the editing logic, not in the IR itself.
"""

from enum import Enum
from typing import Optional, Literal
from pydantic import BaseModel, Field


# --- Sensation dimensions (shared by LLM prompts, UI labels and experiments) ---
SENSATION_DIMENSIONS = ["roughness", "valence", "arousal", "energy", "tempo"]


class Channel(str, Enum):
    A = "a"
    B = "b"
    AB = "ab"


class BlockType(str, Enum):
    VIBRATION = "vibration"  # sustained vibration block
    PULSE = "pulse"          # short discrete pulse
    PAUSE = "pause"          # silence / gap


class Waveform(str, Enum):
    SINE = "sine"
    SAW = "saw"
    NONE = "none"


class Curve(str, Enum):
    FLAT = "flat"
    RAMP_UP = "ramp_up"
    RAMP_DOWN = "ramp_down"
    UP_DOWN = "up_down"


class Tempo(str, Enum):
    SLOW = "slow"
    MEDIUM = "medium"
    FAST = "fast"


class Envelope(BaseModel):
    """Per-block amplitude / frequency envelope. First version keeps simple
    named curves; attack/release seconds are reserved for later refinement."""

    intensity_curve: Curve = Curve.FLAT
    freq_curve: Curve = Curve.FLAT
    attack: float = Field(0.0, ge=0.0, description="Ramp-in seconds (reserved).")
    release: float = Field(0.0, ge=0.0, description="Ramp-out seconds (reserved).")


class HapticBlock(BaseModel):
    block_id: str
    type: BlockType
    duration: Optional[float] = Field(
        None, ge=0.0, description="Seconds; omitted for a standalone pulse."
    )
    waveform: Waveform = Waveform.NONE
    intensity: float = Field(0.5, ge=0.0, le=1.0)
    frequency: float = Field(200.0, ge=0.0, le=500.0, description="Carrier Hz.")
    envelope: Envelope = Field(default_factory=Envelope)


class SensationProfile(BaseModel):
    """Subjective ratings 1 (low) .. 5 (high), plus free-text tags."""

    roughness: int = Field(3, ge=1, le=5, description="1 very smooth .. 5 very rough")
    valence: int = Field(3, ge=1, le=5, description="1 unpleasant .. 5 pleasant")
    arousal: int = Field(3, ge=1, le=5, description="1 calm .. 5 exciting")
    energy: int = Field(3, ge=1, le=5, description="1 low .. 5 high")
    tempo: Tempo = Tempo.MEDIUM
    metaphor_tags: list[str] = Field(default_factory=list)
    scenario_tags: list[str] = Field(default_factory=list)


class HapticTrack(BaseModel):
    track_id: str
    title: str = ""
    repeats: int = Field(1, ge=1)
    channel: Channel = Channel.AB
    blocks: list[HapticBlock] = Field(default_factory=list)
    sensation: SensationProfile = Field(default_factory=SensationProfile)


class EditIntent(BaseModel):
    """What the user wants to change versus what must be preserved.

    target_sensations / preserve_sensations use entries from SENSATION_DIMENSIONS.
    """

    target_sensations: list[str] = Field(default_factory=list)
    preserve_sensations: list[str] = Field(default_factory=list)
    direction: str = Field("", description="Natural-language direction, e.g. stronger / rougher / slower.")
    rationale: str = ""


# --- Built-in preview samples (for offline testing before LLM is wired) ---

def sample_splash() -> HapticTrack:
    """Water splash: low, soft, continuous swell fading out + a few small bubbles."""
    return HapticTrack(
        track_id="sample-splash",
        title="Water splash (preview)",
        channel=Channel.AB,
        blocks=[
            HapticBlock(
                block_id="b1", type=BlockType.VIBRATION, duration=1.5,
                waveform=Waveform.SINE, intensity=0.35, frequency=120,
                envelope=Envelope(intensity_curve=Curve.RAMP_DOWN),
            ),
            HapticBlock(block_id="b2", type=BlockType.PAUSE, duration=0.1),
            HapticBlock(
                block_id="b3", type=BlockType.PULSE, waveform=Waveform.SINE,
                intensity=0.25, frequency=220,
            ),
            HapticBlock(block_id="b4", type=BlockType.PAUSE, duration=0.08),
            HapticBlock(
                block_id="b5", type=BlockType.PULSE, waveform=Waveform.SINE,
                intensity=0.2, frequency=240,
            ),
        ],
        sensation=SensationProfile(
            roughness=2, valence=4, arousal=2, energy=2, tempo=Tempo.SLOW,
            metaphor_tags=["water", "bubble", "splash"],
            scenario_tags=["environment", "liquid contact"],
        ),
    )


def sample_impact() -> HapticTrack:
    """Sharp hit: one strong short pulse."""
    return HapticTrack(
        track_id="sample-impact",
        title="Heavy impact (preview)",
        channel=Channel.AB,
        blocks=[
            HapticBlock(
                block_id="b1", type=BlockType.VIBRATION, duration=0.18,
                waveform=Waveform.SAW, intensity=0.9, frequency=180,
                envelope=Envelope(intensity_curve=Curve.RAMP_DOWN),
            ),
        ],
        sensation=SensationProfile(
            roughness=4, valence=2, arousal=5, energy=5, tempo=Tempo.FAST,
            metaphor_tags=["impact", "hit", "thud"],
            scenario_tags=["collision", "attack"],
        ),
    )
