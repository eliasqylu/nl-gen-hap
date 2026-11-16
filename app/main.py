"""NL Gen Hap — first preview prototype.

Run:
    .venv/bin/python -m streamlit run app/main.py --server.address 127.0.0.1
DEBUG mode: waveform preview only; no real haptic hardware output.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage

from app.ir_model import sample_splash, sample_impact, HapticBlock
from app.signal_preview import render_track
from app.llm_interface import generate_track

st.set_page_config(page_title="NL Gen Hap", layout="wide")
st.title("💬 NL Gen Hap")
st.caption("DEBUG 波形预览原型 · 不输出真实振动 · 设备无关 IR 第一版")

KEY_OK = bool(os.getenv("OPENAI_API_KEY", "").strip())


# --- Sidebar: model status + sample loading ---
with st.sidebar:
    st.subheader("模型设置")
    st.write("模型：", os.getenv("CH_OPENAI_MODEL", "deepseek-chat"))
    st.write("服务地址：", os.getenv("OPENAI_BASE_URL", "(OpenAI 官方)"))
    st.write("密钥：", "已配置" if KEY_OK else "未配置（聊天不可用）")
    st.divider()
    st.subheader("内置样例")
    if st.button("落水（连续涌动 + 气泡）"):
        st.session_state.track = sample_splash()
    if st.button("重击（短促强脉冲）"):
        st.session_state.track = sample_impact()


if "track" not in st.session_state:
    st.session_state.track = sample_splash()
if "messages" not in st.session_state:
    st.session_state.messages = []

track: HapticTrack = st.session_state.track
data, t, dur = render_track(track)

# --- Waveform preview ---
if len(data):
    st.line_chart({"amplitude": data}, height=220)
    st.caption(f"时长 {dur:.2f}s · {len(track.blocks)} 个事件块 · 通道 {track.channel.value}")
else:
    st.info("当前轨道没有可预览的块。")

# --- IR structure + sensation profile ---
col1, col2 = st.columns([3, 2])
with col1:
    st.subheader("结构层（IR 事件序列）")
    rows = [
        {
            "类型": b.type.value,
            "时长(s)": b.duration,
            "波形": b.waveform.value,
            "强度": round(b.intensity, 2),
            "频率(Hz)": round(b.frequency, 1),
            "强度包络": b.envelope.intensity_curve.value,
        }
        for b in track.blocks
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)

with col2:
    st.subheader("感受层评分")
    st.json(track.sensation.model_dump(mode="json"), expanded=True)

# --- Chat input ---
prompt = st.chat_input("描述想要的振动反馈，例如：一次沉闷的落地，带一点余震。", disabled=not KEY_OK)
if prompt:
    st.session_state.messages.append(HumanMessage(content=prompt))
    with st.spinner("生成中…"):
        try:
            new_track = generate_track(st.session_state.messages)
            st.session_state.track = new_track
            st.session_state.messages.append(
                AIMessage(content=f"已生成：{new_track.title or '未命名轨道'}")
            )
            st.rerun()
        except Exception as e:  # surface LLM / schema errors in the UI
            st.error(f"生成失败：{type(e).__name__}: {e}")
