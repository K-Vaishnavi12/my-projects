"""Live Debate page: run a symposium interactively."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.components import hero, inject_css, section_title, turn_card
from app.bootstrap import ensure_bootstrapped
from symposium.agents.orchestrator import Symposium, DebateTurn
from symposium.config import PERSONAS

st.set_page_config(page_title="Live Debate | Symposium", layout="wide")
inject_css()
ensure_bootstrapped()

hero(
    title="Live Debate",
    subtitle="Ask anything. Five personas argue with retrieved evidence. A moderator scores it.",
    badges=["Retrieval-Augmented", "Multi-Agent", "Streaming", "SVM-Scored", "Fully Warehoused"],
)

# ================ Explainer ================
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(
        """
        <div class="glass" style="padding: 1.25rem; min-height: 155px;">
            <div style="font-family:'Space Grotesk',sans-serif; font-weight:700;
                        color:#7C3AED; font-size:1.05rem;">1. Retrieve</div>
            <div style="margin-top:0.5rem; color:rgba(45,27,78,0.7);
                        font-size:0.9rem; line-height:1.55;">
                Each persona queries its OWN Mongo collection for the top-K most
                relevant chunks. Same question, different evidence.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        """
        <div class="glass" style="padding: 1.25rem; min-height: 155px;">
            <div style="font-family:'Space Grotesk',sans-serif; font-weight:700;
                        color:#EC4899; font-size:1.05rem;">2. Argue</div>
            <div style="margin-top:0.5rem; color:rgba(45,27,78,0.7);
                        font-size:0.9rem; line-height:1.55;">
                Each persona speaks in turn using a prompt with system voice,
                prior turns, retrieved evidence, and anti-hallucination guardrails.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        """
        <div class="glass" style="padding: 1.25rem; min-height: 155px;">
            <div style="font-family:'Space Grotesk',sans-serif; font-weight:700;
                        color:#F472B6; font-size:1.05rem;">3. Score</div>
            <div style="margin-top:0.5rem; color:rgba(45,27,78,0.7);
                        font-size:0.9rem; line-height:1.55;">
                SVM + regressor score each turn. Moderator synthesizes a verdict
                and computes a consensus number in [0,1].
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ------------------- Controls -------------------

section_title("Ask a Question")

with st.container():
    st.markdown('<div class="glass" style="padding: 1.5rem; margin-bottom: 1.5rem;">',
                unsafe_allow_html=True)

    with st.form("debate_form"):
        q = st.text_area(
            "Your question",
            value="Is progress in artificial intelligence ultimately good for humanity?",
            height=100,
        )
        c1, c2 = st.columns(2)
        topic = c1.selectbox(
            "Topic bucket (auto-routed if left blank)",
            options=["", "history", "science", "philosophy", "literature", "current_events"],
            index=0,
            help="If blank, our Naive Bayes topic classifier picks the bucket for you.",
        )
        rounds = c2.slider(
            "Rounds per persona",
            min_value=1, max_value=3, value=1,
            help="More rounds = deeper debate, longer wait, more Groq calls.",
        )
        submitted = st.form_submit_button("Start Debate", type="primary", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ================ Sample questions ================
if not submitted:
    st.markdown(
        """
        <div class="glass" style="padding: 1.25rem; margin-bottom: 1rem;">
            <div style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em;
                        color: rgba(45,27,78,0.55);">Not sure what to ask?</div>
            <div style="margin-top:0.75rem; color: rgba(45,27,78,0.75); line-height:1.6;">
                Try:
                <em>"Was the Industrial Revolution a net gain?"</em>,
                <em>"Does quantum mechanics rule out free will?"</em>,
                <em>"Is Nietzsche's 'God is dead' a warning or a celebration?"</em>,
                <em>"Should governments regulate LLMs?"</em>,
                or <em>"Can consciousness be reduced to physical processes?"</em>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info(
        "Type a question above and hit **Start Debate**. Each persona will stream "
        "their turn as they retrieve evidence from their OWN MongoDB collection."
    )
    st.stop()

# ------------------- Setup persona lanes -------------------

section_title("Debate Floor")

placeholders: dict[str, st.delta_generator.DeltaGenerator] = {}
turn_area = st.container()
with turn_area:
    cols = st.columns(len(PERSONAS))
    for col, persona in zip(cols, PERSONAS.values()):
        with col:
            st.markdown(
                f"""
                <div style="text-align:center; padding:0.5rem 0;">
                    <div style="width:44px; height:44px; border-radius:12px;
                                background: linear-gradient(135deg, {persona.color} 0%, {persona.color}88 100%);
                                margin: 0 auto 0.5rem; display:flex; align-items:center;
                                justify-content:center; color:white; font-weight:700;
                                box-shadow: inset 0 1px 0 rgba(255,255,255,0.35),
                                            0 8px 20px rgba(0,0,0,0.15);">
                        {persona.name[4]}
                    </div>
                    <div style="font-family:'Space Grotesk',sans-serif;
                                font-weight:600; font-size:0.95rem; color:{persona.color};">
                        {persona.name}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            placeholders[persona.key] = st.empty()
            placeholders[persona.key].markdown(
                '<div class="glass" style="padding: 0.75rem; text-align: center; '
                'color: rgba(45,27,78,0.5); font-size: 0.85rem;">'
                'Waiting to speak...</div>',
                unsafe_allow_html=True,
            )

st.markdown("<br>", unsafe_allow_html=True)

# ------------------- Run -------------------

sym = Symposium(rounds=rounds)

progress = st.progress(0, text="Debate starting...")
total_expected = len(sym.persona_keys) * rounds
done = 0

def on_turn(turn: DebateTurn) -> None:
    global done
    done += 1
    persona = PERSONAS[turn.persona_key]
    with placeholders[turn.persona_key].container():
        st.markdown(
            turn_card(
                persona_name=persona.name,
                persona_color=persona.color,
                content=turn.content,
                stance_label=turn.stance_label,
                stance_score=turn.stance_score,
                agreement_score=turn.agreement_score,
                latency_ms=turn.latency_ms,
                n_evidence=len(turn.retrievals),
            ),
            unsafe_allow_html=True,
        )
    progress.progress(
        min(1.0, done / total_expected),
        text=f"Turn {done}/{total_expected} - {persona.name} spoke",
    )

result = sym.run(question=q, topic=topic or None, on_turn=on_turn)
progress.progress(1.0, text="Debate complete")

# ------------------- Verdict -------------------

st.markdown("<br>", unsafe_allow_html=True)
section_title("Moderator's Verdict")

v = result.verdict
if v is None:
    st.warning("Moderator failed to produce a verdict.")
    st.stop()

c1, c2, c3 = st.columns([1, 1, 2])
c1.metric("Consensus", f"{v.consensus_score:.0%}")
c2.metric("Winner", v.winner_persona.title() if v.winner_persona else "—")
c3.metric("Routed topic", result.topic.replace("_", " ").title())

st.markdown(
    f'<div class="verdict-card">{v.summary_markdown}</div>',
    unsafe_allow_html=True,
)

# ================ ML signals ================
section_title("ML Signals This Debate Produced")

signals = result.ml_signals
c1, c2 = st.columns(2)
with c1:
    st.markdown('<div class="glass" style="padding:1.25rem; min-height:200px;">'
                '<div style="font-family:\'Space Grotesk\',sans-serif; font-weight:700; '
                'font-size:1rem; color:#7C3AED;">Stance distribution</div>',
                unsafe_allow_html=True)
    stance_dist = signals.get("stance_distribution", {})
    if stance_dist:
        for label, count in stance_dist.items():
            color = {"agree": "#22C55E", "disagree": "#EF4444", "neutral": "#94A3B8"}.get(label, "#A855F7")
            st.markdown(
                f'<div style="display:flex; align-items:center; gap:0.75rem; margin-top:0.6rem;">'
                f'<div style="min-width:80px; color:{color}; font-weight:600;">{label}</div>'
                f'<div style="flex:1; background:rgba(168,85,247,0.10); border-radius:999px; height:8px; overflow:hidden;">'
                f'<div style="background:{color}; height:100%; width:{count / max(sum(stance_dist.values()), 1) * 100}%;"></div>'
                f'</div>'
                f'<div style="min-width:30px; color:rgba(45,27,78,0.75); font-weight:600;">{count}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("No stance signals produced (SVM model missing?)")
    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.markdown('<div class="glass" style="padding:1.25rem; min-height:200px;">'
                '<div style="font-family:\'Space Grotesk\',sans-serif; font-weight:700; '
                'font-size:1rem; color:#EC4899;">Agreement per persona</div>',
                unsafe_allow_html=True)
    per_persona = signals.get("avg_agreement_per_persona", {})
    if per_persona:
        for persona_key, score in per_persona.items():
            if score is None:
                continue
            persona = PERSONAS[persona_key]
            st.markdown(
                f'<div style="display:flex; align-items:center; gap:0.75rem; margin-top:0.6rem;">'
                f'<div style="min-width:100px; color:{persona.color}; font-weight:600;">{persona.name.replace("The ", "")}</div>'
                f'<div style="flex:1; background:rgba(168,85,247,0.10); border-radius:999px; height:8px; overflow:hidden;">'
                f'<div style="background:{persona.color}; height:100%; width:{score * 100}%;"></div>'
                f'</div>'
                f'<div style="min-width:40px; color:rgba(45,27,78,0.75); font-weight:600;">{score:.2f}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("No agreement signals produced (Ridge model missing?)")
    st.markdown('</div>', unsafe_allow_html=True)

# ================ Evidence trail ================
section_title("Evidence Trail")

st.caption("Every persona's retrieved chunks are logged to `fact_retrieval` and joined "
           "with `dim_document` in the `v_debate_evidence_trail` SQL view. "
           "Below is the full evidence chain for this debate.")

from symposium.dwh import Warehouse
wh = Warehouse()
trail = wh.sp_evidence_for_query(result.query_id)
wh.close()
st.dataframe(trail, use_container_width=True, hide_index=True)

with st.expander("Debate metadata (JSON)"):
    st.json({
        "query_id": result.query_id,
        "question": result.question,
        "topic": result.topic,
        "ml_signals": result.ml_signals,
        "verdict_raw": v.raw_text,
    })

sym.close()
