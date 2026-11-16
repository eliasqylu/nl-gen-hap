"""Render an IR track into a preview waveform (numpy only).

This is a visualization aid, NOT a hardware playback path. The first version
renders a single mixed channel; left/right separation is reserved in the IR
(Channel) and will be handled by device backends later.
"""

import numpy as np

from .ir_model import HapticTrack, HapticBlock, BlockType, Waveform, Curve

SAMPLE_RATE = 10000  # Hz, preview only
DEFAULT_PULSE_SECONDS = 0.06


def _curve(curve: Curve, n: int) -> np.ndarray:
    if n <= 0:
        return np.array([])
    x = np.linspace(0.0, 1.0, n)
    if curve == Curve.RAMP_UP:
        return x
    if curve == Curve.RAMP_DOWN:
        return 1.0 - x
    if curve == Curve.UP_DOWN:
        half = n // 2
        return np.concatenate((x[:half], 1.0 - x[: n - half]))
    return np.ones(n)


def _carrier(wave: Waveform, t: np.ndarray, freq: float) -> np.ndarray:
    if wave == Waveform.SINE:
        return np.sin(2.0 * np.pi * freq * t)
    if wave == Waveform.SAW:
        return 2.0 * np.mod(t * freq, 1.0) - 1.0
    return np.zeros_like(t)


def _render_block(block: HapticBlock, sr: int) -> tuple[np.ndarray, np.ndarray, float]:
    if block.type == BlockType.PAUSE:
        dur = block.duration or 0.0
        n = max(1, int(dur * sr))
        return np.zeros(n), np.linspace(0.0, dur, n, endpoint=False), dur

    dur = block.duration if block.type == BlockType.VIBRATION else (
        block.duration or DEFAULT_PULSE_SECONDS
    )
    n = max(1, int(dur * sr))
    t = np.linspace(0.0, dur, n, endpoint=False)
    carrier = _carrier(block.waveform, t, block.frequency)
    env = _curve(block.envelope.intensity_curve, n)
    sig = block.intensity * env * carrier

    if block.type == BlockType.PULSE:
        # Short decay so a pulse reads as a discrete tap.
        decay = np.linspace(1.0, 0.0, n)
        sig = sig * decay
    return sig, t, dur


def render_track(track: HapticTrack, sr: int = SAMPLE_RATE):
    """Return (data: 1D ndarray, t: 1D ndarray, duration: seconds)."""
    pieces: list[np.ndarray] = []
    total = 0.0
    for block in track.blocks:
        sig, _, dur = _render_block(block, sr)
        pieces.append(sig)
        total += dur

    if not pieces:
        return np.array([]), np.array([]), 0.0

    signal = np.concatenate(pieces)
    if track.repeats > 1:
        signal = np.tile(signal, track.repeats)
        total *= track.repeats

    n = len(signal)
    t = np.linspace(0.0, total, n, endpoint=False)
    # Normalize for preview only; clipping guard.
    peak = np.max(np.abs(signal)) if n else 0.0
    if peak > 1.0:
        signal = signal / peak
    return signal, t, total
