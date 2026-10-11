"""Corpus Explorer page.

Shows which chunks each persona "claims" as its evidence pool.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.components import hero, inject_css, section_title
from app.bootstrap import ensure_bootstrapped
from symposium.config import PERSONAS
from symposium.dwh import Warehouse

st.set_page_config(page_title="Corpus | Symposium", layout="wide")
inject_css()
ensure_bootstrapped()

hero(
    title="Corpus Explorer",
    subtitle="See exactly which chunks each persona has claimed as its private evidence pool.",
    badges=["Per-Persona Retrieval", "MongoDB", "Rule-Based Scorer"],
)

# ================ Intro cards ================
c1, c2, c3 = st.columns(3)
for col, title, desc, color in [
    (c1, "The core innovation",
     "Every chunk is scored against every persona at ETL time. A chunk about the French Revolution scores high for Historian, low for Poet. That's why they see different evidence.",
     "#7C3AED"),
    (c2, "Six MongoDB collections",
     "One per persona (chunks_historian, chunks_scientist, ...) plus a global 'chunks_all' fallback. Each has its own vector-search index.",
     "#EC4899"),
    (c3, "Lexicon-driven",
     "Instead of an LLM (slow, expensive), a small hand-tuned lexicon of evidence-words and narrative-words scores chunks in milliseconds during ETL.",
     "#F472B6"),
]:
    with col:
        st.markdown(
            f"""
            <div class="glass" style="padding:1.25rem; min-height:180px;">
                <div style="font-family:'Space Grotesk',sans-serif; font-weight:700;
                            color:{color}; font-size:1.05rem;">{title}</div>
                <div style="margin-top:0.5rem; color:rgba(45,27,78,0.7);
                            font-size:0.9rem; line-height:1.55;">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

wh = Warehouse()

# Sidebar
persona_key = st.sidebar.selectbox(
    "Persona",
    options=list(PERSONAS.keys()),
    format_func=lambda k: PERSONAS[k].name,
)
top_n = st.sidebar.slider("How many chunks", 5, 100, 30)

persona = PERSONAS[persona_key]

# Persona header
st.markdown(
    f"""
    <div style="background: linear-gradient(135deg, {persona.color}22 0%, transparent 100%);
                border: 1px solid {persona.color}44;
                padding: 1.5rem; border-radius: 16px; margin-bottom: 1.5rem;">
        <div style="display:flex; align-items:center; gap:1rem;">
            <div style="width:56px; height:56px; border-radius:14px;
                        background: linear-gradient(135deg, {persona.color} 0%, {persona.color}88 100%);
                        display:flex; align-items:center; justify-content:center;
                        color:white; font-size:1.5rem; font-weight:700;
                        box-shadow: 0 8px 24px {persona.color}44;">
                {persona.name[4]}
            </div>
            <div>
                <div style="font-size: 1.4rem; font-weight: 700; color: {persona.color};">
                    {persona.name}
                </div>
                <div style="font-style: italic; opacity: 0.75; margin-top: 0.25rem;">
                    "{persona.tagline}"
                </div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Top chunks
section_title(f"Top {top_n} Chunks (by affinity)")
df = wh.sp_chunk_persona_top(persona_key=persona_key, n=top_n)
if df.empty:
    st.info("No chunks yet - run the ETL first.")
else:
    st.dataframe(df, use_container_width=True, hide_index=True)

# Cross-topic leaderboard (uses SQL window function)
section_title("Cross-Topic Leaderboard (SQL Window Function)")
lb = wh.query(
    "SELECT * FROM v_chunk_persona_leaderboard WHERE persona_key = ? "
    "AND topic_rank <= 5 ORDER BY topic_key, topic_rank",
    (persona_key,),
)
st.dataframe(lb, use_container_width=True, hide_index=True)

wh.close()
