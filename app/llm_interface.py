"""LLM interface (OpenAI-compatible, tested against DeepSeek).

First version wires the generation chain (NL -> HapticTrack). The modification
chain is reserved: direction 1's compensation logic (change target sensation,
preserve others) will be built on top of `modify_track`.
"""

import os
from typing import Optional, Sequence

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from .ir_model import HapticTrack, EditIntent

load_dotenv()

GEN_SYSTEM = SystemMessage(
    content=(
        "You design game haptic feedback as a device-independent track. "
        "Translate the user's request into a sequence of blocks "
        "(vibration / pulse / pause) with intensity 0..1, carrier frequency "
        "50..500 Hz, duration in seconds, and a waveform (sine/saw). "
        "Also fill a sensation profile: roughness, valence, arousal, energy "
        "(1..5) and tempo (slow/medium/fast), plus metaphor and scenario tags. "
        "Keep parameters physically plausible; do not emit hardware-specific signals."
    )
)


def configured_model() -> ChatOpenAI:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise ValueError("请先在 .env 填写 OPENAI_API_KEY。")
    return ChatOpenAI(
        api_key=key,
        base_url=os.getenv("OPENAI_BASE_URL") or None,
        model=os.getenv("CH_OPENAI_MODEL", "deepseek-chat"),
        temperature=0,
        request_timeout=60,
        max_retries=1,
    )


def _as_track(result) -> HapticTrack:
    # langchain/openai may return a plain dict instead of a validated model
    # instance depending on version and provider; validate explicitly.
    if isinstance(result, dict):
        return HapticTrack.model_validate(result)
    return result


def generate_track(conversation: Sequence[BaseMessage], model: Optional[ChatOpenAI] = None) -> HapticTrack:
    model = model or configured_model()
    chain = model.with_structured_output(HapticTrack)
    messages = [GEN_SYSTEM, *conversation]
    return _as_track(chain.invoke(messages))


def modify_track(
    current: HapticTrack,
    intent: EditIntent,
    conversation: Sequence[BaseMessage],
    model: Optional[ChatOpenAI] = None,
) -> HapticTrack:
    """Reserved for direction 1.

    Planned behavior: identify target vs preserved sensations, apply
    compensation adjustments so preserved sensations stay stable, and return
    the edited track. Not implemented in the first preview version.
    """
    raise NotImplementedError("修改/补偿编辑将在方向一阶段实现。")
