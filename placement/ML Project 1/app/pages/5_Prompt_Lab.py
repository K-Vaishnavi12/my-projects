"""Prompt Lab page."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.components import hero, inject_css, section_title
from app.bootstrap import ensure_bootstrapped
from symposium.agents.llm import get_llm
from symposium.prompts import SAFETY_GUARDRAILS

st.set_page_config(page_title="Prompt Lab | Symposium", layout="wide")
inject_css()
ensure_bootstrapped()

hero(
    title="Prompt Lab",
    subtitle="Same question. Three prompting styles. See what changes.",
    badges=["Zero-Shot", "Few-Shot", "Chain-of-Thought", "Guardrails"],
)

# ================ Intro cards ================
c1, c2, c3 = st.columns(3)
for col, title, desc, color in [
    (c1, "Zero-shot",
     "Just the task, no examples. Fast, but the LLM guesses the answer's shape from training data alone.",
     "#A855F7"),
    (c2, "Few-shot",
     "Prepend 2\u20135 hand-crafted Q/A examples. The LLM imitates the pattern without any fine-tuning.",
     "#EC4899"),
    (c3, "Chain-of-thought",
     "Force the LLM to reason step-by-step BEFORE committing to an answer. Reduces silly mistakes on multi-step problems.",
     "#F472B6"),
]:
    with col:
        st.markdown(
            f"""
            <div class="glass" style="padding:1.25rem; min-height:170px;">
                <div style="font-family:'Space Grotesk',sans-serif; font-weight:700;
                            color:{color}; font-size:1.05rem;">{title}</div>
                <div style="margin-top:0.5rem; color:rgba(45,27,78,0.7);
                            font-size:0.9rem; line-height:1.55;">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown(
    """
    <div class="glass" style="padding: 1rem 1.25rem; margin: 1.5rem 0;">
        <span style="opacity: 0.85; font-size: 0.9rem;">
            This page runs the exact same question through three different prompt
            templates and shows the LLM's response side-by-side. It's the
            <strong>Prompt Engineering Mindset</strong> from the syllabus made tangible.
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)

question = st.text_input(
    "Question",
    value="Was the Industrial Revolution ultimately good for humanity?",
)


ZERO_SHOT = """You are an expert. Answer the question in 3-5 sentences.

Question: {q}
"""

FEW_SHOT = """You are an expert. Answer the question in 3-5 sentences.
Follow the style shown below.

Example 1:
Q: Was the French Revolution progress or chaos?
A: Both. It ended feudal privilege and codified rights, but also unleashed
   terror. Historians measure it against the alternatives that existed at
   the time.

Example 2:
Q: Was the printing press a net good?
A: Yes: it democratised knowledge and accelerated science - but at the
   cost of destabilising older institutions and enabling propaganda.

Now:
Q: {q}
A:
"""

COT = """You are an expert. Answer the question in 3-5 sentences.

Before answering, THINK STEP BY STEP inside <thinking>...</thinking> tags.
Then give a concise final answer inside <answer>...</answer> tags.

Question: {q}
"""


llm = get_llm()

if st.button("Run All Three Styles", type="primary", use_container_width=True):
    col1, col2, col3 = st.columns(3)

    for col, style_name, template, color in [
        (col1, "Zero-Shot", ZERO_SHOT, "#FF6B9D"),
        (col2, "Few-Shot",  FEW_SHOT,  "#6366F1"),
        (col3, "Chain-of-Thought", COT, "#34D399"),
    ]:
        with col:
            st.markdown(
                f"""
                <div style="background: linear-gradient(135deg, {color}22 0%, transparent 100%);
                            border: 1px solid {color}66; border-radius: 14px;
                            padding: 0.75rem 1rem; margin-bottom: 1rem;">
                    <div style="font-size:0.75rem; text-transform:uppercase;
                                letter-spacing:0.06em; opacity:0.7;">Style</div>
                    <div style="font-size:1.1rem; font-weight:700; color: {color};">
                        {style_name}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.expander("Prompt template"):
                st.code(template.format(q=question), language="text")
            with st.spinner("Generating..."):
                response = llm.generate(template.format(q=question))
            st.markdown(
                f"""
                <div style="background: rgba(255,255,255,0.03);
                            border: 1px solid rgba(255,255,255,0.06);
                            border-radius: 12px; padding: 1rem;
                            line-height: 1.6; min-height: 200px;">
                    {response}
                </div>
                """,
                unsafe_allow_html=True,
            )

section_title("Safety Guardrails")

st.markdown(
    """
    These hard rules are baked into <strong>every</strong> persona prompt so
    the LLM can't hallucinate confidently. It's how we turn a generative model
    into a grounded one.
    """,
    unsafe_allow_html=True,
)

st.code(SAFETY_GUARDRAILS, language="markdown")
