"""Shared UI components + soft-light glassmorphism CSS.

Design system:
- Light aurora background: soft lavender / pink / peach blobs on off-white
- Frosted-glass surfaces: rgba white + backdrop-filter blur
- Radiant pastel accents: lavender #A855F7, pink #F472B6, peach #FDB4A6, mint #A7F3D0
- Rounded 20-24px, generous padding, gentle shadows
"""

from __future__ import annotations

import streamlit as st


CUSTOM_CSS = """
<style>
    /* ============================== */
    /* Fonts                          */
    /* ============================== */
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"], .stMarkdown, .stText {
        font-family: 'Inter', -apple-system, sans-serif !important;
    }
    h1, h2, h3, h4, h5 {
        font-family: 'Space Grotesk', sans-serif !important;
        letter-spacing: -0.02em;
        color: #2D1B4E !important;
    }
    p, span, div, label { color: #2D1B4E; }
    code, pre, .stCodeBlock, code * {
        font-family: 'JetBrains Mono', monospace !important;
        color: #6D28D9 !important;
    }

    /* ============================== */
    /* Light AURORA background        */
    /* ============================== */
    .stApp {
        background:
            radial-gradient(1000px 600px at 10% -10%, rgba(216, 180, 254, 0.55) 0%, transparent 60%),
            radial-gradient(900px 550px at 90% 10%, rgba(251, 207, 232, 0.55) 0%, transparent 60%),
            radial-gradient(700px 500px at 50% 90%, rgba(191, 219, 254, 0.45) 0%, transparent 60%),
            radial-gradient(600px 400px at 80% 60%, rgba(253, 230, 138, 0.30) 0%, transparent 60%),
            #FDFBFF;
        background-attachment: fixed;
    }

    /* Hide streamlit chrome */
    #MainMenu, footer, header {visibility: hidden;}

    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
        max-width: 1400px;
    }

    /* ============================== */
    /* Glass surface primitive        */
    /* ============================== */
    .glass {
        background: rgba(255, 255, 255, 0.55);
        backdrop-filter: blur(24px) saturate(180%);
        -webkit-backdrop-filter: blur(24px) saturate(180%);
        border: 1px solid rgba(168, 85, 247, 0.10);
        border-radius: 24px;
        box-shadow:
            inset 0 1px 0 rgba(255, 255, 255, 0.9),
            0 8px 32px rgba(168, 85, 247, 0.08);
    }

    /* ============================== */
    /* HERO                           */
    /* ============================== */
    .hero {
        background:
            linear-gradient(135deg, rgba(216, 180, 254, 0.45) 0%, rgba(251, 207, 232, 0.35) 100%),
            rgba(255, 255, 255, 0.5);
        backdrop-filter: blur(28px) saturate(180%);
        -webkit-backdrop-filter: blur(28px) saturate(180%);
        border: 1px solid rgba(168, 85, 247, 0.15);
        padding: 2.75rem 2.5rem;
        border-radius: 28px;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
        box-shadow:
            inset 0 1px 0 rgba(255, 255, 255, 0.9),
            0 20px 60px rgba(168, 85, 247, 0.10);
    }
    .hero::before {
        content: "";
        position: absolute;
        top: -60%;
        right: -20%;
        width: 500px;
        height: 500px;
        background: radial-gradient(circle, rgba(251, 207, 232, 0.60) 0%, transparent 65%);
        pointer-events: none;
        filter: blur(20px);
    }
    .hero::after {
        content: "";
        position: absolute;
        bottom: -50%;
        left: -10%;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(191, 219, 254, 0.55) 0%, transparent 65%);
        pointer-events: none;
        filter: blur(20px);
    }
    .hero-inner { position: relative; z-index: 1; }
    .hero-title {
        font-size: 3.25rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.03em;
        line-height: 1.05;
        background: linear-gradient(135deg, #7C3AED 0%, #EC4899 60%, #F472B6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .hero-subtitle {
        font-size: 1.15rem;
        color: rgba(45, 27, 78, 0.75);
        margin-top: 0.75rem;
        font-weight: 400;
        max-width: 700px;
    }
    .hero-badges {
        display: flex;
        gap: 0.5rem;
        margin-top: 1.5rem;
        flex-wrap: wrap;
    }
    .hero-badge {
        background: rgba(255, 255, 255, 0.65);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(168, 85, 247, 0.20);
        color: #6D28D9;
        padding: 5px 14px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 500;
        letter-spacing: 0.02em;
    }

    /* ============================== */
    /* SECTION TITLE                  */
    /* ============================== */
    .section-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.5rem;
        font-weight: 600;
        margin: 2.5rem 0 1.25rem 0;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        color: #2D1B4E !important;
    }
    .section-title-accent {
        width: 4px;
        height: 26px;
        background: linear-gradient(180deg, #A855F7 0%, #F472B6 100%);
        border-radius: 4px;
        box-shadow: 0 0 12px rgba(168, 85, 247, 0.35);
    }

    /* ============================== */
    /* PERSONA CARDS                  */
    /* ============================== */
    .persona-card {
        background: rgba(255, 255, 255, 0.65);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid rgba(168, 85, 247, 0.10);
        border-radius: 20px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: transform 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
        height: 100%;
        position: relative;
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(168, 85, 247, 0.06);
    }
    .persona-card::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: var(--persona-color, #A855F7);
        opacity: 0.85;
    }
    .persona-card:hover {
        transform: translateY(-6px);
        border-color: rgba(168, 85, 247, 0.25);
        box-shadow:
            0 20px 40px rgba(168, 85, 247, 0.15),
            0 0 50px var(--persona-color-glow, rgba(168, 85, 247, 0.15));
    }
    .persona-avatar {
        width: 52px;
        height: 52px;
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.5rem;
        font-weight: 700;
        color: white;
        margin-bottom: 1rem;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.4), 0 6px 16px rgba(0,0,0,0.12);
    }
    .persona-name {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.15rem;
        font-weight: 600;
        margin: 0;
        color: #2D1B4E !important;
    }
    .persona-tagline {
        font-size: 0.85rem;
        font-style: italic;
        color: rgba(45, 27, 78, 0.55) !important;
        margin-top: 0.35rem;
        line-height: 1.4;
    }
    .persona-details {
        font-size: 0.82rem;
        color: rgba(45, 27, 78, 0.7) !important;
        margin-top: 1rem;
        line-height: 1.5;
        max-height: 4.5em;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
    }

    /* ============================== */
    /* TURN CARDS                     */
    /* ============================== */
    .turn-card {
        background: rgba(255, 255, 255, 0.65);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(168, 85, 247, 0.10);
        border-radius: 18px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 0.9rem;
        position: relative;
        animation: fadeSlide 0.5s cubic-bezier(0.22, 1, 0.36, 1);
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(168, 85, 247, 0.06);
    }
    .turn-card::before {
        content: "";
        position: absolute;
        top: 0; left: 0; bottom: 0;
        width: 4px;
        background: var(--persona-color, #A855F7);
        box-shadow: 0 0 12px var(--persona-color, #A855F7);
    }
    @keyframes fadeSlide {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .turn-header {
        display: flex; align-items: center; gap: 0.5rem;
        font-size: 0.78rem;
        color: rgba(45, 27, 78, 0.55) !important;
        margin-bottom: 0.6rem;
    }
    .stance-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .stance-agree    { background: rgba(167, 243, 208, 0.5);  color: #047857; border: 1px solid rgba(52,211,153,0.4); }
    .stance-disagree { background: rgba(254, 202, 202, 0.5); color: #B91C1C; border: 1px solid rgba(248,113,113,0.4); }
    .stance-neutral  { background: rgba(226, 232, 240, 0.6); color: #475569; border: 1px solid rgba(148,163,184,0.4); }

    /* ============================== */
    /* KPI METRICS                    */
    /* ============================== */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.65);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid rgba(168, 85, 247, 0.12);
        padding: 1.5rem 1.25rem;
        border-radius: 20px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.9), 0 4px 16px rgba(168, 85, 247, 0.06);
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        box-shadow:
            inset 0 1px 0 rgba(255,255,255,0.9),
            0 20px 40px rgba(168, 85, 247, 0.18);
    }
    [data-testid="stMetric"] label {
        color: rgba(45, 27, 78, 0.55) !important;
        font-size: 0.78rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-family: 'Space Grotesk', sans-serif !important;
        background: linear-gradient(135deg, #7C3AED 0%, #EC4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.25rem !important;
        font-weight: 700 !important;
    }

    /* ============================== */
    /* SIDEBAR                        */
    /* ============================== */
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.55);
        backdrop-filter: blur(24px) saturate(180%);
        -webkit-backdrop-filter: blur(24px) saturate(180%);
        border-right: 1px solid rgba(168, 85, 247, 0.10);
    }
    [data-testid="stSidebar"] * {
        color: #2D1B4E !important;
    }
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2 {
        background: linear-gradient(90deg, #7C3AED 0%, #EC4899 60%, #F472B6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    [data-testid="stSidebarNav"] a {
        border-radius: 10px;
        transition: background 0.2s ease;
    }
    [data-testid="stSidebarNav"] a:hover {
        background: rgba(168, 85, 247, 0.08);
    }

    /* ============================== */
    /* BUTTONS                        */
    /* ============================== */
    .stButton > button, .stFormSubmitButton > button,
    button[kind="secondary"], button[kind="primary"] {
        background: linear-gradient(135deg, #A855F7 0%, #EC4899 100%) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.4) !important;
        padding: 0.65rem 1.75rem !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        border-radius: 14px !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
        box-shadow: 0 8px 24px rgba(168, 85, 247, 0.35), inset 0 1px 0 rgba(255,255,255,0.35) !important;
    }
    .stButton > button:hover, .stFormSubmitButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 32px rgba(236, 72, 153, 0.45), inset 0 1px 0 rgba(255,255,255,0.4) !important;
    }
    .stButton > button:active { transform: translateY(0) !important; }

    /* ============================== */
    /* INPUTS                         */
    /* ============================== */
    .stTextInput input, .stTextArea textarea,
    .stSelectbox > div > div, .stNumberInput input {
        background: rgba(255, 255, 255, 0.75) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(168, 85, 247, 0.15) !important;
        border-radius: 14px !important;
        color: #2D1B4E !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus {
        border-color: rgba(168, 85, 247, 0.5) !important;
        box-shadow: 0 0 0 4px rgba(168, 85, 247, 0.12) !important;
    }
    .stSlider [data-baseweb="slider"] div[role="slider"] {
        background: #A855F7 !important;
        border: 3px solid white !important;
        box-shadow: 0 2px 8px rgba(168, 85, 247, 0.35) !important;
    }

    /* ============================== */
    /* TABS                           */
    /* ============================== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: transparent;
        border-bottom: 1px solid rgba(168, 85, 247, 0.10);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px 12px 0 0;
        padding: 0.7rem 1.4rem;
        background: rgba(255, 255, 255, 0.5);
        border: 1px solid rgba(168, 85, 247, 0.10);
        border-bottom: none;
        font-weight: 500;
        color: #6D28D9 !important;
        transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.75);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(168, 85, 247, 0.20) 0%, rgba(236, 72, 153, 0.15) 100%) !important;
        border-color: rgba(168, 85, 247, 0.35) !important;
        color: #6D28D9 !important;
    }

    /* ============================== */
    /* DATAFRAME                      */
    /* ============================== */
    .stDataFrame, [data-testid="stDataFrame"] {
        border-radius: 16px !important;
        overflow: hidden !important;
        border: 1px solid rgba(168, 85, 247, 0.10) !important;
    }

    /* ============================== */
    /* PROGRESS                       */
    /* ============================== */
    .stProgress > div > div {
        background: linear-gradient(90deg, #A855F7 0%, #EC4899 60%, #F472B6 100%);
        box-shadow: 0 0 12px rgba(168, 85, 247, 0.4);
    }
    .stProgress > div {
        background: rgba(168, 85, 247, 0.10);
        border-radius: 999px;
    }

    /* ============================== */
    /* EXPANDER                       */
    /* ============================== */
    .streamlit-expanderHeader, [data-testid="stExpander"] summary {
        background: rgba(255, 255, 255, 0.6) !important;
        border-radius: 14px !important;
        border: 1px solid rgba(168, 85, 247, 0.10) !important;
        color: #2D1B4E !important;
        transition: background 0.2s ease !important;
    }
    .streamlit-expanderHeader:hover, [data-testid="stExpander"] summary:hover {
        background: rgba(255, 255, 255, 0.85) !important;
    }
    [data-testid="stExpander"] {
        border: none !important;
        background: transparent !important;
    }

    /* ============================== */
    /* ALERTS                         */
    /* ============================== */
    .stAlert {
        border-radius: 16px !important;
        border: 1px solid rgba(168, 85, 247, 0.15) !important;
        backdrop-filter: blur(10px) !important;
        background: rgba(255, 255, 255, 0.65) !important;
        color: #2D1B4E !important;
    }
    .stAlert * { color: #2D1B4E !important; }

    /* ============================== */
    /* VERDICT CARD                   */
    /* ============================== */
    .verdict-card {
        background: linear-gradient(135deg, rgba(216, 180, 254, 0.35) 0%, rgba(251, 207, 232, 0.25) 100%);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid rgba(168, 85, 247, 0.25);
        border-radius: 20px;
        padding: 1.75rem;
        margin-top: 1rem;
        box-shadow: 0 20px 40px rgba(168, 85, 247, 0.10), inset 0 1px 0 rgba(255,255,255,0.9);
    }
    .verdict-card h2, .verdict-card h3 {
        color: #6D28D9 !important;
        margin-top: 1rem;
    }
    .verdict-card p, .verdict-card li { color: #2D1B4E !important; }

    /* Selectbox popover */
    ul[data-baseweb="menu"] {
        background: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(168, 85, 247, 0.15) !important;
        border-radius: 12px !important;
    }
    ul[data-baseweb="menu"] li { color: #2D1B4E !important; }

    /* ============================== */
    /* SPINNER                        */
    /* ============================== */
    [data-testid="stSpinner"] > div {
        border-top-color: #A855F7 !important;
    }
</style>
"""


PERSONA_INITIALS = {
    "historian": "H",
    "scientist": "S",
    "poet": "P",
    "skeptic": "K",
    "child": "C",
}


def inject_css() -> None:
    """Inject the custom CSS. Call once at the top of every page."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def hero(title: str, subtitle: str, badges: list[str] | None = None) -> None:
    """Aurora glass hero header (light theme)."""
    badges_html = ""
    if badges:
        chips = "".join(f'<span class="hero-badge">{b}</span>' for b in badges)
        badges_html = f'<div class="hero-badges">{chips}</div>'
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-inner">
                <h1 class="hero-title">{title}</h1>
                <p class="hero-subtitle">{subtitle}</p>
                {badges_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(text: str) -> None:
    st.markdown(
        f'<div class="section-title"><span class="section-title-accent"></span>{text}</div>',
        unsafe_allow_html=True,
    )


def persona_card(persona) -> str:
    """Return glass persona card HTML."""
    initial = PERSONA_INITIALS.get(persona.key, persona.key[0].upper())
    return f"""
    <div class="persona-card" style="--persona-color: {persona.color}; --persona-color-glow: {persona.color}55;">
        <div class="persona-avatar" style="background: linear-gradient(135deg, {persona.color} 0%, {persona.color}88 100%);">
            {initial}
        </div>
        <p class="persona-name">{persona.name}</p>
        <p class="persona-tagline">"{persona.tagline}"</p>
        <p class="persona-details">{persona.system[:180]}...</p>
    </div>
    """


def turn_card(
    *,
    persona_name: str,
    persona_color: str,
    content: str,
    stance_label: str | None = None,
    stance_score: float | None = None,
    agreement_score: float | None = None,
    latency_ms: int | None = None,
    n_evidence: int | None = None,
) -> str:
    """Return glass turn card HTML."""
    badges = []
    if stance_label:
        badges.append(
            f'<span class="stance-badge stance-{stance_label}">'
            f'{stance_label}'
            + (f' &middot; {stance_score:.2f}' if stance_score is not None else '')
            + '</span>'
        )
    if agreement_score is not None:
        badges.append(f'<span style="opacity:0.7;">agree {agreement_score:.2f}</span>')
    if n_evidence is not None:
        badges.append(f'<span style="opacity:0.6;">{n_evidence} sources</span>')
    if latency_ms is not None:
        badges.append(f'<span style="opacity:0.6;">{latency_ms} ms</span>')

    badges_html = " &middot; ".join(badges)

    return f"""
    <div class="turn-card" style="--persona-color: {persona_color};">
        <div class="turn-header">
            <strong style="color: {persona_color};">{persona_name}</strong>
            &middot; {badges_html}
        </div>
        <div style="line-height: 1.65; color: #2D1B4E;">{content}</div>
    </div>
    """


def glass_card(inner_html: str, min_height: str | None = None) -> str:
    """Generic glass wrapper."""
    style = f'min-height: {min_height};' if min_height else ""
    return f'<div class="glass" style="padding: 1.5rem; {style}">{inner_html}</div>'
