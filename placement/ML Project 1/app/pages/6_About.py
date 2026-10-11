"""About page."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.components import hero, inject_css, section_title
from app.bootstrap import ensure_bootstrapped

st.set_page_config(page_title="About | Symposium", layout="wide")
inject_css()
ensure_bootstrapped()

hero(
    title="About Symposium",
    subtitle="Rationale, tech stack, and full syllabus-coverage matrix.",
    badges=["1-Credit Project", "AI / ML / DS"],
)

# ------------- Rationale -------------
section_title("Why This Project")

c1, c2 = st.columns(2)
with c1:
    st.markdown(
        """
        <div class="glass" style="padding:1.5rem; min-height:230px;">
            <div style="font-family:'Space Grotesk',sans-serif; font-weight:700;
                        color:#7C3AED; font-size:1.15rem;">The frustration</div>
            <div style="margin-top:0.75rem; color:rgba(45,27,78,0.75);
                        font-size:0.95rem; line-height:1.65;">
                Most student RAG projects are variants of "chat with your PDF" \u2014
                a single AI reads a document and answers questions. The AI acts as
                a mirror, giving you one perspective. This misses the real strength
                of modern LLMs: they can play many voices at once.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        """
        <div class="glass" style="padding:1.5rem; min-height:230px;">
            <div style="font-family:'Space Grotesk',sans-serif; font-weight:700;
                        color:#EC4899; font-size:1.15rem;">The idea</div>
            <div style="margin-top:0.75rem; color:rgba(45,27,78,0.75);
                        font-size:0.95rem; line-height:1.65;">
                What if five different personalities each read the same knowledge base
                but retrieved DIFFERENT parts of it based on their worldview? What if
                they then debated your question live, with a moderator scoring the
                debate using ML models? That's Symposium.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ------------- Design decisions -------------
section_title("Key Design Decisions")

decisions = [
    ("Why five personas, not two?",
     "Two personas reduce to pro/con \u2014 the classic binary that dominates online debate and misses everything in between. Five forces multi-dimensional discourse: evidence (Scientist), narrative (Poet), stress-testing (Skeptic), context (Historian), and grounding (Child)."),
    ("Why per-persona MongoDB collections?",
     "Filtering a global collection at query time by persona is possible but slow and mixes evidence pools. Per-persona collections mean each persona's vector index is naturally scoped \u2014 no WHERE clause needed \u2014 and we can enforce 'the Skeptic literally cannot see chunks the Poet claimed' as a database invariant."),
    ("Why SQLite for the DWH?",
     "Portability. A single file, no server, works everywhere. All queries are ANSI SQL so swapping to Postgres/RDS is a URL change. For a demo with ~10k rows, SQLite is faster than any managed service."),
    ("Why Groq over OpenAI or Gemini?",
     "Groq's Llama-3.3-70B is faster (~500 tokens/sec), free at the quota we need, and quality is competitive for the 'debate persona' task. Gemini/OpenAI would work identically \u2014 the LLM adapter is one file (`symposium/agents/llm.py`)."),
    ("Why train our own SVM/Ridge/Naive Bayes when the LLM could just self-report?",
     "Because 'trust the LLM to score itself' is exactly the black-box the project exists to avoid. Our own models give us numbers we can defend, cross-check, and version. If the SVM disagrees with the LLM's self-report, that's diagnostic \u2014 we can inspect why."),
    ("Why a star schema and not a document store for debates?",
     "Debates need to be sliced across many dimensions (persona X topic X time X consensus). That's textbook OLAP. Star schemas are optimal for BI tools like Power BI, and window functions (RANK, LAG, rolling AVG) are trivial in SQL and painful in Mongo aggregations."),
]

for q, a in decisions:
    st.markdown(
        f"""
        <div class="glass" style="padding:1.35rem 1.5rem; margin-bottom:0.85rem;">
            <div style="font-family:'Space Grotesk',sans-serif; font-weight:700;
                        color:#7C3AED; font-size:1.05rem;">{q}</div>
            <div style="margin-top:0.6rem; color:rgba(45,27,78,0.75);
                        font-size:0.93rem; line-height:1.65;">{a}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ------------- Tech stack -------------
section_title("Tech Stack")

stack = [
    ("LLM",          "Groq (Llama-3.3-70B)",             "#A855F7"),
    ("Embeddings",   "sentence-transformers MiniLM",     "#EC4899"),
    ("Vector DB",    "MongoDB Atlas Vector Search",      "#F472B6"),
    ("SQL DWH",      "SQLite (Kimball star schema)",     "#8B5CF6"),
    ("ML",           "scikit-learn + TensorFlow/Keras",  "#7C3AED"),
    ("Web UI",       "Streamlit multi-page app",         "#F59E0B"),
    ("BI",           "Power BI + DAX",                   "#22D3EE"),
    ("Deploy",       "Docker + AWS EC2",                 "#EC4899"),
]

cols = st.columns(4)
for i, (label, value, color) in enumerate(stack):
    with cols[i % 4]:
        st.markdown(
            f"""
            <div class="glass" style="padding:1.25rem; margin-bottom:1rem; min-height:120px;">
                <div style="font-size:0.72rem; text-transform:uppercase; opacity:0.6;
                            letter-spacing:0.08em;">{label}</div>
                <div style="font-family:'Space Grotesk',sans-serif;
                            font-weight:700; font-size:1rem; margin-top:0.5rem;
                            color: {color};">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ------------- Project stats -------------
section_title("Project Stats")

stats = [
    ("Python files",     "60"),
    ("Lines of code",    "~5,000"),
    ("SQL scripts",      "4"),
    ("Unit tests",       "20/20 passing"),
    ("ML models",        "6 trained"),
    ("Corpus chunks",    "6,380"),
    ("MongoDB collections", "6"),
    ("Streamlit pages",  "6"),
    ("Documentation files", "10"),
    ("Docker",           "Compose + Dockerfile"),
    ("AWS deploy",       "One-shot script"),
    ("Star-schema tables", "8"),
]

cols = st.columns(4)
for i, (k, v) in enumerate(stats):
    with cols[i % 4]:
        st.markdown(
            f"""
            <div class="glass" style="padding:1.1rem; margin-bottom:0.85rem;
                                       text-align:center;">
                <div style="font-family:'Space Grotesk',sans-serif;
                            font-weight:700; font-size:1.5rem;
                            background: linear-gradient(135deg,#A855F7,#EC4899);
                            -webkit-background-clip: text;
                            -webkit-text-fill-color: transparent;
                            background-clip: text;">{v}</div>
                <div style="color: rgba(45,27,78,0.6); font-size:0.8rem;
                            text-transform:uppercase; letter-spacing:0.05em;
                            margin-top:0.3rem;">{k}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ------------- Syllabus matrix -------------
section_title("Syllabus Coverage Matrix")

st.caption("Every syllabus topic mapped to the exact file that satisfies it.")

rows = [
    ("DWH concepts (OLTP/OLAP, ETL, Data Marts, Metadata)", "symposium/dwh/"),
    ("Data Lakehouse", "data/raw + data/staging + DWH"),
    ("ETL (extract, transform, load; joins, DQ rules)", "symposium/etl/"),
    ("SQL DQL/DDL/DML + joins + window functions", "symposium/dwh/sql/*.sql"),
    ("SQL Advanced (views, triggers, stored procs)", "03_views_triggers.sql + warehouse.py"),
    ("NoSQL + comparison with SQL", "symposium/vectorstore/ + docs/NOSQL_VS_SQL.md"),
    ("Power BI", "powerbi/ + scripts/export_csv.py"),
    ("Python Beginner + Advanced", "symposium/utils/python_showcase.py"),
    ("Cloud (AWS)", "Dockerfile + deployment/aws/"),
    ("NumPy / Pandas / Matplotlib / Scikit-Learn", "symposium/ml/ + notebooks/"),
    ("Linear + Logistic Regression", "agreement_regressor.py"),
    ("SVM, Naive Bayes, KNN", "stance_svm.py, topic_naive_bayes.py, similar_turn_knn.py"),
    ("K-Means + PCA", "clustering.py"),
    ("Neural Networks / TensorFlow", "neural_debate_scorer.py"),
    ("Prompt Engineering (zero/few-shot, CoT, hallucinations)", "symposium/prompts/ + Prompt Lab page"),
    ("Generative AI / LLMs", "symposium/agents/llm.py (Groq/Gemini)"),
    ("AI-Assisted Development", "docs/COPILOT_WORKFLOW.md"),
]

df = pd.DataFrame(rows, columns=["Syllabus topic", "Where it lives"])
st.dataframe(df, use_container_width=True, hide_index=True)

# ------------- Roadmap -------------
section_title("Roadmap")

roadmap = [
    ("Shipped",  "Multi-agent RAG with per-persona retrieval", "#22C55E"),
    ("Shipped",  "Star-schema DWH with views + triggers",       "#22C55E"),
    ("Shipped",  "6 ML models trained + persisted",             "#22C55E"),
    ("Shipped",  "Streamlit UI + Power BI export",              "#22C55E"),
    ("Shipped",  "Docker + AWS deploy scripts",                 "#22C55E"),
    ("Next",     "Add a 6th persona (the Comedian?) as a plugin", "#F59E0B"),
    ("Next",     "Live WebSocket streaming instead of blocking",   "#F59E0B"),
    ("Next",     "Fine-tuned neural moderator on real debates",   "#F59E0B"),
    ("Later",    "LangGraph rewrite for cyclical debate flow",    "#94A3B8"),
    ("Later",    "Voice input + audio output per persona",        "#94A3B8"),
    ("Later",    "Multi-tenant auth via Cognito",                 "#94A3B8"),
]

for status, item, color in roadmap:
    st.markdown(
        f"""
        <div class="glass" style="padding:0.9rem 1.25rem; margin-bottom:0.6rem;
                    display:flex; gap:1rem; align-items:center;">
            <div style="min-width:80px; text-align:center; padding:4px 10px;
                        border-radius:999px; background:{color}22;
                        color:{color}; font-weight:600; font-size:0.75rem;
                        text-transform:uppercase; letter-spacing:0.05em;
                        border:1px solid {color}55;">
                {status}
            </div>
            <div style="color:rgba(45,27,78,0.8); font-size:0.92rem;">{item}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ------------- Credits -------------
section_title("Credits")

st.markdown(
    """
    <div class="glass" style="padding:1.5rem;">
        <div style="color:rgba(45,27,78,0.8); line-height:1.7; font-size:0.95rem;">
            <strong>Data</strong> \u2014 Wikipedia (CC-BY-SA). Fetched via the official
            <code>wikipedia-api</code> client. Article titles hand-curated across five
            topic buckets.
            <br><br>
            <strong>LLM</strong> \u2014 Groq (Llama-3.3-70B-Versatile). Free tier is
            generous enough to run debates continuously during development.
            <br><br>
            <strong>Embeddings</strong> \u2014
            <code>sentence-transformers/all-MiniLM-L6-v2</code>, a distilled BERT model
            producing 384-dim vectors. Runs locally on CPU in seconds.
            <br><br>
            <strong>Inspiration</strong> \u2014 Plato's <em>Symposium</em> (~385 BCE),
            in which several speakers took turns describing love from different
            perspectives. That's the template we ported to LLMs.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
