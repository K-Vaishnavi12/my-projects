"""Symposium - Streamlit Home page."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Make ``app`` importable when Streamlit runs this file directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.components import hero, inject_css, persona_card, section_title
from app.bootstrap import ensure_bootstrapped
from symposium.config import PERSONAS

st.set_page_config(
    page_title="Symposium",
    page_icon=":performing_arts:",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()
ensure_bootstrapped()

# =============== Hero ===============
hero(
    title="Symposium",
    subtitle="A multi-agent RAG where five AI personas debate your question, live.",
    badges=[
        "Multi-Agent",
        "RAG",
        "MongoDB Vector Search",
        "Star-Schema DWH",
        "Groq + Llama-3.3",
        "6 ML Models",
    ],
)

# =============== Intro ===============
c1, c2 = st.columns([2, 1])
with c1:
    st.markdown(
        """
        Ask any question. Five AI personas retrieve evidence from **their own worldview**
        of a shared Wikipedia corpus, then argue about it. A moderator scores the debate
        turn-by-turn using ML models trained on the fly, and every piece of the conversation
        is warehoused in a star-schema DWH.
        """
    )
    st.markdown(
        """
        Unlike a single-agent chatbot that mirrors what you already believe, Symposium
        forces you to hear **five grounded perspectives** on the same question, each
        anchored in retrieved evidence. The moderator's consensus score tells you how
        much the personas agreed and where the real debate lies.
        """
    )
with c2:
    st.markdown(
        """
        <div class="glass" style="padding: 1.5rem;">
            <div style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em;
                        color:rgba(45,27,78,0.55); margin-bottom:0.75rem;">Get started</div>
            <div style="display:flex; flex-direction:column; gap:0.5rem;">
                <div style="font-family:'Space Grotesk',sans-serif;
                            font-weight:500; padding:0.4rem 0; border-bottom:1px solid rgba(168,85,247,0.10);">
                    <span style="opacity:0.5; font-size:0.85rem;">01</span>
                    &nbsp;&nbsp;Live Debate
                </div>
                <div style="font-family:'Space Grotesk',sans-serif;
                            font-weight:500; padding:0.4rem 0; border-bottom:1px solid rgba(168,85,247,0.10);">
                    <span style="opacity:0.5; font-size:0.85rem;">02</span>
                    &nbsp;&nbsp;Analytics
                </div>
                <div style="font-family:'Space Grotesk',sans-serif;
                            font-weight:500; padding:0.4rem 0; border-bottom:1px solid rgba(168,85,247,0.10);">
                    <span style="opacity:0.5; font-size:0.85rem;">03</span>
                    &nbsp;&nbsp;Corpus
                </div>
                <div style="font-family:'Space Grotesk',sans-serif;
                            font-weight:500; padding:0.4rem 0; border-bottom:1px solid rgba(168,85,247,0.10);">
                    <span style="opacity:0.5; font-size:0.85rem;">04</span>
                    &nbsp;&nbsp;ML Playground
                </div>
                <div style="font-family:'Space Grotesk',sans-serif;
                            font-weight:500; padding:0.4rem 0;">
                    <span style="opacity:0.5; font-size:0.85rem;">05</span>
                    &nbsp;&nbsp;Prompt Lab
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =============== The Problem / Solution ===============
section_title("The Problem With Modern AI")

c1, c2 = st.columns(2)
with c1:
    st.markdown(
        """
        <div class="glass" style="padding: 1.75rem; min-height: 220px;">
            <div style="font-size:1.75rem;">Problem</div>
            <div style="font-family:'Space Grotesk',sans-serif; font-weight:700;
                        font-size:1.35rem; margin-top:0.5rem;
                        color: #7C3AED;">One AI, one perspective.</div>
            <div style="margin-top:1rem; line-height:1.65; color: rgba(45,27,78,0.75);">
                Traditional RAG systems return a single, homogenized answer. The AI acts
                as a mirror \u2014 reflecting whatever your prompt implies. There's no
                friction, no dissent, no <em>debate</em>. Complex questions like
                <em>"is progress good?"</em> get flattened into a bland summary that
                nobody actually learns from.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        """
        <div class="glass" style="padding: 1.75rem; min-height: 220px;">
            <div style="font-size:1.75rem;">Solution</div>
            <div style="font-family:'Space Grotesk',sans-serif; font-weight:700;
                        font-size:1.35rem; margin-top:0.5rem;
                        color: #EC4899;">Five AIs, five worldviews.</div>
            <div style="margin-top:1rem; line-height:1.65; color: rgba(45,27,78,0.75);">
                Symposium spawns five persona agents, each with its OWN slice of the
                corpus and its OWN voice. They argue in front of you. A moderator
                measures agreement using our own ML models. The result: a
                <em>living transcript</em> instead of a dead answer, with numbers
                you can actually trust.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =============== Meet the personas ===============
section_title("Meet the Five Personas")

st.markdown(
    """
    Each persona has its own retrieval bias, its own voice, and its own private
    slice of the Wikipedia corpus. When you ask a question, they don't see the
    same evidence \u2014 that's the whole point.
    """
)

cols = st.columns(len(PERSONAS))
for col, persona in zip(cols, PERSONAS.values()):
    with col:
        st.markdown(persona_card(persona), unsafe_allow_html=True)

# =============== Live warehouse stats ===============
section_title("Live Warehouse Stats")

try:
    from symposium.dwh import Warehouse
    wh = Warehouse()
    counts = wh.counts()
    wh.close()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Documents", f"{counts['dim_document']:,}")
    c2.metric("Chunks",    f"{counts['fact_chunk']:,}")
    c3.metric("Debates",   f"{counts['fact_query']:,}")
    c4.metric("Turns",     f"{counts['fact_turn']:,}")

    st.markdown(
        f"""
        <div style="color: rgba(45,27,78,0.6); font-size:0.9rem; margin-top:0.75rem;">
            The corpus currently spans <strong>{counts['dim_document']}</strong> source
            documents chunked into <strong>{counts['fact_chunk']:,}</strong> passages,
            each embedded with sentence-transformers/all-MiniLM-L6-v2 and indexed
            across six MongoDB collections \u2014 one per persona plus a global one.
        </div>
        """,
        unsafe_allow_html=True,
    )
except Exception as exc:  # noqa: BLE001
    st.warning(
        "Data warehouse isn't populated yet. Run "
        "`.\\tasks.ps1 etl` in your terminal to load the Wikipedia corpus."
    )
    st.caption(f"(diagnostic: {exc})")

# =============== How it works ===============
section_title("How It Works")

steps = [
    ("1", "Ingest", "Wikipedia articles across 5 topic buckets are fetched, cleaned, and chunked into overlapping sentence windows."),
    ("2", "Score", "Every chunk is scored against each persona's retrieval bias \u2014 date density, evidence density, narrative density, etc."),
    ("3", "Store", "Chunks land in per-persona MongoDB collections plus a SQLite star-schema DWH. Vectors go through Atlas Vector Search."),
    ("4", "Debate", "Five persona agents each retrieve their OWN top-K chunks from Mongo and speak in order, injecting prior turns as context."),
    ("5", "Score", "SVM + Ridge regressor score every turn for stance and agreement. Moderator LLM synthesizes a verdict."),
    ("6", "Slice", "Every debate turn is warehoused as a fact row \u2014 fully queryable in SQL, Power BI, or via the built-in analytics page."),
]

cols = st.columns(3)
for i, (n, title, desc) in enumerate(steps):
    with cols[i % 3]:
        st.markdown(
            f"""
            <div class="glass" style="padding: 1.5rem; margin-bottom: 1rem; min-height: 200px;">
                <div style="display:flex; align-items:center; gap:0.85rem;">
                    <div style="width:40px; height:40px; border-radius:12px;
                                background: linear-gradient(135deg,#A855F7,#EC4899);
                                display:flex; align-items:center; justify-content:center;
                                color:white; font-weight:700; font-size:1.05rem;
                                box-shadow: 0 8px 20px rgba(168,85,247,0.35),
                                            inset 0 1px 0 rgba(255,255,255,0.4);">
                        {n}
                    </div>
                    <div style="font-family:'Space Grotesk',sans-serif;
                                font-weight:600; font-size:1.1rem;">{title}</div>
                </div>
                <div style="color: rgba(45,27,78,0.7); margin-top:1rem;
                            font-size:0.92rem; line-height:1.55;">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# =============== Tech stack ===============
section_title("Under the Hood")

tech = [
    ("LLM",           "Groq (Llama-3.3-70B)",             "Blazing-fast inference. Free tier. Powers persona voices and moderator synthesis."),
    ("Embeddings",    "MiniLM-L6-v2",                     "384-dim sentence-transformers model. Runs locally, no API calls. Powers vector search."),
    ("Vector DB",     "MongoDB Atlas",                    "Native $vectorSearch operator on per-persona collections. Cosine similarity."),
    ("SQL DWH",       "SQLite (star schema)",             "3 dims + 4 facts + 4 views + 3 triggers. Window functions for rolling averages."),
    ("Classical ML",  "scikit-learn",                     "SVM, Naive Bayes, KNN, Ridge, Logistic, K-Means, PCA. All trained + persisted."),
    ("Deep Learning", "TensorFlow / Keras",               "Small MLP for debate-outcome tier prediction. Trained on synthetic outcomes."),
    ("Web UI",        "Streamlit (multi-page)",           "6 pages. Real-time streaming. Custom glassmorphism theme."),
    ("Deploy",        "Docker + AWS EC2",                 "One-shot deploy script. LocalStack + Atlas for zero-cost dev."),
]

cols = st.columns(4)
for i, (label, value, desc) in enumerate(tech):
    with cols[i % 4]:
        st.markdown(
            f"""
            <div class="glass" style="padding: 1.25rem; margin-bottom: 1rem; min-height: 160px;">
                <div style="font-size:0.72rem; text-transform:uppercase; letter-spacing:0.08em;
                            color:rgba(45,27,78,0.55);">{label}</div>
                <div style="font-family:'Space Grotesk',sans-serif;
                            font-weight:700; font-size:1rem; margin-top:0.4rem;
                            background: linear-gradient(135deg,#A855F7,#EC4899);
                            -webkit-background-clip: text;
                            -webkit-text-fill-color: transparent;
                            background-clip: text;">{value}</div>
                <div style="color: rgba(45,27,78,0.65); font-size:0.82rem;
                            margin-top:0.6rem; line-height:1.5;">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# =============== Corpus topics ===============
section_title("What's in the Corpus")

topics = [
    ("history",         "French Revolution, WW1/2, Cold War, Ancient Rome, Silk Road, Mongol Empire, Renaissance..."),
    ("science",         "General Relativity, Quantum Mechanics, Evolution, DNA, Climate Change, CRISPR, Fusion..."),
    ("philosophy",      "Socrates, Kant, Existentialism, Stoicism, Utilitarianism, Nietzsche, Free Will..."),
    ("literature",      "Shakespeare, Iliad, Don Quixote, Dostoevsky, Austen, Joyce, Kafka, Toni Morrison..."),
    ("current_events",  "Artificial Intelligence, LLMs, Renewable Energy, Cryptocurrency, Cybersecurity..."),
]
for topic, articles in topics:
    st.markdown(
        f"""
        <div class="glass" style="padding: 1rem 1.25rem; margin-bottom: 0.75rem;
                    display:flex; align-items:center; gap:1rem;">
            <div style="min-width:130px; font-family:'Space Grotesk',sans-serif;
                        font-weight:600; text-transform:uppercase; letter-spacing:0.05em;
                        font-size:0.85rem;
                        background: linear-gradient(135deg,#A855F7,#EC4899);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        background-clip: text;">
                {topic.replace("_", " ")}
            </div>
            <div style="color: rgba(45,27,78,0.7); font-size:0.9rem; line-height:1.5;">
                {articles}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =============== Sample questions ===============
section_title("Sample Questions to Try")

questions = [
    ("Is progress in artificial intelligence ultimately good for humanity?",     "current_events"),
    ("Was the Industrial Revolution a net gain for civilization?",                "history"),
    ("Does quantum mechanics rule out free will?",                                "science"),
    ("Is Nietzsche's 'God is dead' a warning or a celebration?",                  "philosophy"),
    ("Why does Kafka's writing feel so bureaucratically hopeless?",               "literature"),
    ("Should governments regulate large language models?",                        "current_events"),
    ("Was Napoleon a liberator or a tyrant?",                                     "history"),
    ("Can consciousness be reduced to physical processes?",                       "philosophy"),
]

cols = st.columns(2)
for i, (q, topic) in enumerate(questions):
    with cols[i % 2]:
        st.markdown(
            f"""
            <div class="glass" style="padding: 1rem 1.25rem; margin-bottom: 0.75rem;">
                <div style="font-size:0.7rem; text-transform:uppercase;
                            letter-spacing:0.08em;
                            color: #A855F7; font-weight:600;">
                    {topic.replace("_", " ")}
                </div>
                <div style="margin-top:0.4rem; line-height:1.5;
                            color: rgba(45,27,78,0.85);">
                    "{q}"
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# =============== Feature Highlights ===============
section_title("What You Can Do")

features = [
    ("Live Debate",       "Ask a question, watch five personas retrieve different evidence and argue in real time. Each turn is scored by SVM + regressor as it streams."),
    ("Analytics",         "Slice past debates by persona, topic, or time. See which persona wins most, rolling consensus averages, disagreement heatmaps."),
    ("Corpus Explorer",   "Browse which chunks each persona has claimed. See exactly why the Skeptic and Poet retrieve different evidence for the same query."),
    ("ML Playground",     "Test all 6 trained models: SVM stance classifier, Naive Bayes topic router, Ridge regressor, KNN retriever, K-Means clustering, neural net."),
    ("Prompt Lab",        "Compare zero-shot, few-shot, and chain-of-thought prompting on the same question. See how output changes as you engineer the prompt."),
    ("Evidence Trail",    "Every debate produces a full audit log \u2014 which chunks were retrieved for each turn, similarity scores, source URLs. Nothing is hidden."),
]

cols = st.columns(3)
for i, (title, desc) in enumerate(features):
    with cols[i % 3]:
        st.markdown(
            f"""
            <div class="glass" style="padding: 1.5rem; margin-bottom: 1rem; min-height: 180px;">
                <div style="font-family:'Space Grotesk',sans-serif;
                            font-weight:700; font-size:1.15rem;
                            color: #7C3AED;">
                    {title}
                </div>
                <div style="color: rgba(45,27,78,0.7); margin-top:0.75rem;
                            font-size:0.9rem; line-height:1.55;">
                    {desc}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# =============== Design principles ===============
section_title("Design Principles")

principles = [
    ("Grounded",       "Every persona is forced to cite retrieved evidence with [E1]-style tags. Guardrails baked into the system prompt block hallucinations."),
    ("Transparent",    "SVM stance, regression score, retrieval sources, and moderator reasoning are all visible in the UI. No black boxes."),
    ("Warehoused",     "Every question, turn, and retrieval is a row in SQLite. Debates aren't ephemeral. You can slice a year of debates in Power BI."),
    ("Polyglot",       "SQL for aggregation, joins, and analytics. NoSQL for flexible schemas and vector search. Each database does what it's good at."),
]

for title, desc in principles:
    st.markdown(
        f"""
        <div class="glass" style="padding: 1.25rem 1.5rem; margin-bottom: 0.85rem;
                    display:flex; gap:1.5rem; align-items:flex-start;">
            <div style="min-width:120px; font-family:'Space Grotesk',sans-serif;
                        font-weight:700; font-size:1.05rem;
                        background: linear-gradient(135deg,#A855F7,#EC4899);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        background-clip: text;">
                {title}
            </div>
            <div style="color: rgba(45,27,78,0.75); line-height:1.6; font-size:0.92rem;">
                {desc}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
