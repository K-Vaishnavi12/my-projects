"""Analytics page: slice past debates from the SQL DWH."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.components import hero, inject_css, section_title
from app.bootstrap import ensure_bootstrapped
from symposium.dwh import Warehouse

st.set_page_config(page_title="Analytics | Symposium", layout="wide")
inject_css()
ensure_bootstrapped()

hero(
    title="Debate Analytics",
    subtitle="Every debate is a row. Slice, dice, and roll up debates from the SQL DWH.",
    badges=["Star Schema", "Window Functions", "Views + Triggers", "Power BI Ready"],
)

# ------------- Plotly light theme -------------
PLOTLY_TEMPLATE = "plotly_white"
COLORS = ["#A855F7", "#EC4899", "#F472B6", "#8B5CF6", "#F59E0B", "#22D3EE"]

wh = Warehouse()

# ================ Intro cards ================
c1, c2, c3 = st.columns(3)
for col, title, desc, color in [
    (c1, "OLAP-shaped", "SQLite backs a Kimball star schema with 3 dimensions, 4 fact tables, 4 views, and 3 triggers.", "#7C3AED"),
    (c2, "Grain: one turn = one row", "The finest fact grain is fact_turn. Everything above rolls up: turns per query, queries per topic, chunks per persona.", "#EC4899"),
    (c3, "Power BI export", "One command dumps every table + view to CSV so Power BI Desktop can render the same schema.", "#F472B6"),
]:
    with col:
        st.markdown(
            f"""
            <div class="glass" style="padding:1.25rem; min-height:145px;">
                <div style="font-family:'Space Grotesk',sans-serif; font-weight:700;
                            color:{color}; font-size:1.05rem;">{title}</div>
                <div style="margin-top:0.5rem; color:rgba(45,27,78,0.7);
                            font-size:0.9rem; line-height:1.55;">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

# ------------- KPIs -------------
section_title("Warehouse KPIs")
counts = wh.counts()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Documents",  f"{counts['dim_document']:,}")
c2.metric("Chunks",     f"{counts['fact_chunk']:,}")
c3.metric("Debates",    f"{counts['fact_query']:,}")
c4.metric("Turns",      f"{counts['fact_turn']:,}")

st.markdown(
    f"""
    <div style="color: rgba(45,27,78,0.6); font-size:0.9rem; margin-top:0.75rem;">
        Star-schema breakdown &middot;
        <strong>{counts.get('dim_topic', 0)}</strong> topics &middot;
        <strong>{counts.get('dim_persona', 0)}</strong> personas &middot;
        <strong>{counts.get('fact_retrieval', 0):,}</strong> retrieval events tracked
    </div>
    """,
    unsafe_allow_html=True,
)

# ------------- Persona leaderboard -------------
section_title("Persona Airtime & Agreement")
lead = wh.sp_persona_leaderboard()

if lead.empty:
    st.info("No debates recorded yet - run one in the **Live Debate** page.")
else:
    st.caption("Query: `SELECT * FROM v_persona_activity ORDER BY total_turns DESC` — "
               "a view aggregating fact_turn by persona_key.")

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(
            lead, x="persona_name", y="total_turns",
            color="persona_name", color_discrete_sequence=COLORS,
            template=PLOTLY_TEMPLATE,
        )
        fig.update_layout(
            title="Turns per persona",
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#2D1B4E"),
        )
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(
            lead, x="persona_name", y="avg_agreement_score",
            color="persona_name", color_discrete_sequence=COLORS,
            template=PLOTLY_TEMPLATE,
        )
        fig.update_layout(
            title="Average agreement score per persona",
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#2D1B4E"),
        )
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(lead, use_container_width=True, hide_index=True)

# ------------- Topic stats -------------
section_title("Topic-Level Consensus")
topic_stats = wh.query("SELECT * FROM v_topic_debate_stats")
if not topic_stats.empty:
    st.caption("Query: `SELECT * FROM v_topic_debate_stats` — joins fact_query with fact_turn "
               "and groups by topic to expose min/max/avg consensus per topic.")
    c1, c2 = st.columns([2, 1])
    with c1:
        fig = px.bar(
            topic_stats, x="topic_key", y="avg_consensus",
            color="topic_key", color_discrete_sequence=COLORS,
            template=PLOTLY_TEMPLATE,
        )
        fig.update_layout(
            title="Average consensus by topic",
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#2D1B4E"),
        )
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown(
            """
            <div class="glass" style="padding:1.25rem; min-height:340px;">
                <div style="font-family:'Space Grotesk',sans-serif; font-weight:700;
                            color:#7C3AED; font-size:1.05rem;">How to read this</div>
                <div style="margin-top:0.75rem; color:rgba(45,27,78,0.75);
                            font-size:0.88rem; line-height:1.6;">
                    Consensus is the fraction of persona turns whose stance
                    matches the majority. A tall bar means personas agree
                    on that topic. A short bar means genuine disagreement,
                    which is often more interesting to explore.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.dataframe(topic_stats, use_container_width=True, hide_index=True)

# ------------- Chunk feature distributions -------------
section_title("Chunk Feature Distributions")

st.caption("Density features computed during ETL from `fact_chunk`.")

chunk_df = wh.query(
    "SELECT c.*, d.topic_key FROM fact_chunk c JOIN dim_document d USING(doc_id)"
)
if not chunk_df.empty:
    c1, c2 = st.columns(2)
    with c1:
        fig = px.box(
            chunk_df, x="topic_key", y="evidence_density",
            color="topic_key", color_discrete_sequence=COLORS,
            template=PLOTLY_TEMPLATE,
        )
        fig.update_layout(
            title="Evidence density by topic",
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#2D1B4E"),
        )
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.box(
            chunk_df, x="topic_key", y="narrative_density",
            color="topic_key", color_discrete_sequence=COLORS,
            template=PLOTLY_TEMPLATE,
        )
        fig.update_layout(
            title="Narrative density by topic",
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#2D1B4E"),
        )
        st.plotly_chart(fig, use_container_width=True)

    fig = px.scatter(
        chunk_df, x="evidence_density", y="narrative_density",
        color="topic_key", color_discrete_sequence=COLORS,
        template=PLOTLY_TEMPLATE,
        opacity=0.6,
    )
    fig.update_layout(
        title="Evidence vs Narrative density (each dot = one chunk)",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#2D1B4E"),
    )
    st.plotly_chart(fig, use_container_width=True)

# ------------- Persona affinity heatmap -------------
if not chunk_df.empty:
    section_title("Persona Affinity Correlations")

    st.caption("Are the personas' affinity scores correlated? A high red cell means "
               "chunks that appeal to persona A also appeal to persona B.")

    score_cols = [c for c in chunk_df.columns if c.startswith("score_")]
    corr = chunk_df[score_cols].corr()
    fig = px.imshow(
        corr, text_auto=".2f",
        color_continuous_scale="RdPu",
        template=PLOTLY_TEMPLATE,
    )
    fig.update_layout(
        title="Correlation between persona affinity scores",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#2D1B4E"),
    )
    st.plotly_chart(fig, use_container_width=True)

# ------------- Recent debates -------------
section_title("Recent Debates")
recent = wh.sp_recent_debates(limit=25)
if not recent.empty:
    st.dataframe(recent, use_container_width=True, hide_index=True)
else:
    st.info("Nothing here yet.")

# ------------- Rolling consensus (window function) -------------
if not topic_stats.empty:
    section_title("Rolling Consensus (SQL Window Function)")

    st.caption("Uses `AVG(consensus_score) OVER (PARTITION BY topic_key ORDER BY started_at "
               "ROWS BETWEEN 4 PRECEDING AND CURRENT ROW)` \u2014 a textbook window function.")

    selected_topic = st.selectbox(
        "Topic",
        options=topic_stats["topic_key"].tolist(),
    )
    if selected_topic:
        rc = wh.sp_rolling_consensus(selected_topic)
        if not rc.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=rc["started_at"], y=rc["consensus_score"],
                mode="lines+markers", name="Consensus",
                line=dict(color="#A855F7", width=2),
            ))
            fig.add_trace(go.Scatter(
                x=rc["started_at"], y=rc["rolling5"],
                mode="lines", name="5-debate rolling avg",
                line=dict(color="#EC4899", width=3, dash="dot"),
            ))
            fig.update_layout(
                title=f"Consensus vs 5-debate rolling avg ({selected_topic})",
                template=PLOTLY_TEMPLATE,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color="#2D1B4E"),
                hovermode="x unified",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough data for a rolling avg yet. Run a few debates first.")

# ------------- SQL reference -------------
section_title("SQL Reference Library")

st.caption("The exact analytical queries this dashboard is built on.")

with st.expander("v_persona_activity (view)"):
    st.code(
        """
CREATE VIEW v_persona_activity AS
SELECT  p.persona_key,
        p.name AS persona_name,
        COUNT(t.turn_id)                    AS total_turns,
        COALESCE(AVG(t.stance_score), 0)    AS avg_stance_score,
        COALESCE(AVG(t.agreement_score), 0) AS avg_agreement_score,
        COALESCE(AVG(t.latency_ms), 0)      AS avg_latency_ms
FROM    dim_persona p
LEFT    JOIN fact_turn t ON t.persona_key = p.persona_key
GROUP   BY p.persona_key, p.name;
        """,
        language="sql",
    )

with st.expander("Rolling consensus (window function)"):
    st.code(
        """
SELECT  query_id, started_at, consensus_score,
        AVG(consensus_score) OVER (
            PARTITION BY topic_key
            ORDER BY started_at
            ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
        ) AS rolling5
FROM    fact_query
WHERE   topic_key = :topic
        AND consensus_score IS NOT NULL
ORDER   BY started_at;
        """,
        language="sql",
    )

with st.expander("Winners per query (CTE + rank window)"):
    st.code(
        """
WITH per_query AS (
    SELECT query_id, persona_key, AVG(agreement_score) AS avg_agree
    FROM   fact_turn
    WHERE  agreement_score IS NOT NULL
    GROUP  BY query_id, persona_key
),
ranked AS (
    SELECT query_id, persona_key, avg_agree,
           RANK() OVER (PARTITION BY query_id ORDER BY avg_agree DESC) AS rk
    FROM   per_query
)
SELECT persona_key, COUNT(*) AS wins
FROM   ranked
WHERE  rk = 1
GROUP  BY persona_key
ORDER  BY wins DESC;
        """,
        language="sql",
    )

wh.close()
