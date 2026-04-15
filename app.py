import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from database import (
    init_db, add_topic, get_all_topics, add_review,
    init_streak_table, mark_today_studied,
    get_streak, get_total_study_days,
    init_xp_table, add_xp, get_total_xp,
    get_today_xp, get_xp_by_subject,
    get_league, get_xp_history, LEAGUE_THRESHOLDS,
    sign_up, sign_in, sign_out, get_supabase
)
from model import (
    get_retention_curve, current_retention,
    classify_topic, get_review_priority,
    predict_future_retention, cluster_topics
)

st.set_page_config(
    page_title="Smriti",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── INJECT STYLES ────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@300;400;500;600&display=swap');

/* ── GLOBAL ── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
#MainMenu, footer, header   { visibility: hidden; }
section[data-testid="stSidebar"]  { display: none !important; }
[data-testid="collapsedControl"]  { display: none !important; }

/* ── APP BACKGROUND ── */
.stApp { background-color: #F1F4F8 !important; }

/* ── NAV BAR ── */
.nav-wrapper {
    background: linear-gradient(135deg, #0F1B2D 0%, #1E3A5F 100%);
    padding: 0 32px;
    margin: -1rem -1rem 0 -1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 60px;
    box-shadow: 0 2px 16px rgba(15,27,45,0.18);
    position: sticky;
    top: 0;
    z-index: 999;
}
.nav-brand {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 1.35rem;
    font-weight: 700;
    color: #FFFFFF;
    display: flex;
    align-items: center;
    gap: 8px;
}
.nav-brand span { color: #C9A84C; }
.nav-tagline {
    font-size: 10px;
    color: rgba(255,255,255,0.4);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-left: 4px;
}

/* ── PAGE HEADER ── */
.page-header {
    background: linear-gradient(135deg, #0F1B2D 0%, #1E3A5F 100%);
    margin: 0 -1rem 2rem -1rem;
    padding: 32px 40px 28px;
    border-bottom: 3px solid #C9A84C;
}
.page-title {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 2rem;
    font-weight: 700;
    color: #FFFFFF;
    margin: 0 0 4px 0;
}
.page-subtitle {
    font-size: 0.875rem;
    color: rgba(255,255,255,0.5);
    margin: 0;
}

/* ── METRIC CARDS ── */
[data-testid="metric-container"] {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;
    padding: 18px 20px !important;
    box-shadow: 0 1px 6px rgba(15,27,45,0.06) !important;
    border-left: 4px solid #1E3A5F !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Playfair Display', serif !important;
    color: #0F1B2D !important;
    font-size: 2rem !important;
}
[data-testid="stMetricLabel"] {
    color: #64748B !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    font-weight: 500 !important;
}

/* ── BUTTONS ── */
.stButton > button {
    background: #1E3A5F !important;
    color: #FFFFFF !important;
    border: 1px solid #2D5A8E !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    padding: 10px 20px !important;
    transition: background 0.2s, transform 0.1s !important;
    letter-spacing: 0.02em !important;
}
.stButton > button:hover {
    background: #2D5A8E !important;
    transform: translateY(-1px) !important;
}
.stButton > button p, .stButton > button span { color: #FFFFFF !important; }

[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #0F1B2D, #1E3A5F) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 12px 24px !important;
}

/* ── INPUTS ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 8px !important;
    color: #0F1B2D !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextInput > div > div > input:focus {
    border-color: #1E3A5F !important;
    box-shadow: 0 0 0 3px rgba(30,58,95,0.1) !important;
}
div[data-baseweb="select"] > div {
    background: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 8px !important;
    color: #0F1B2D !important;
}
div[data-baseweb="select"] span,
div[data-baseweb="select"] div { color: #0F1B2D !important; }
li[role="option"] { color: #0F1B2D !important; background: #FFFFFF !important; }
li[role="option"]:hover { background: #F1F4F8 !important; }

/* ── EXPANDER ── */
details {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 10px !important;
    margin-bottom: 8px !important;
    box-shadow: 0 1px 4px rgba(15,27,45,0.05) !important;
}
details summary {
    color: #0F1B2D !important;
    font-weight: 500 !important;
    padding: 14px 18px !important;
}

/* ── PROGRESS BAR ── */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #0F1B2D, #1E3A5F) !important;
    border-radius: 999px !important;
}
.stProgress > div > div {
    background: #E2E8F0 !important;
    border-radius: 999px !important;
}

/* ── TEXT ── */
.stMarkdown p       { color: #0F1B2D !important; }
.stMarkdown strong  { color: #0F1B2D !important; font-weight: 700 !important; }
[data-testid="stRadio"] label p { color: #0F1B2D !important; }
.stRadio label      { color: #0F1B2D !important; }
p                   { color: #0F1B2D !important; }
label               { color: #374151 !important; font-weight: 500 !important; }
h1, h2, h3          { font-family: 'Playfair Display', serif !important; color: #0F1B2D !important; }
[data-testid="stMarkdownContainer"] p { color: #0F1B2D !important; }

/* ── MISC ── */
hr { border-color: #E2E8F0 !important; }
.stAlert { border-radius: 10px !important; border-left-width: 4px !important; }

/* ── GOLD LINE ── */
.gold-line {
    height: 3px;
    background: linear-gradient(90deg, #C9A84C, #E8C96D, #C9A84C);
    border-radius: 2px;
    margin: 16px 0 24px 0;
}

/* ── STREAK CARD ── */
.streak-card {
    background: linear-gradient(135deg, #0F1B2D, #1E3A5F);
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 20px;
    border: 1px solid rgba(201,168,76,0.3);
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 16px;
}
.streak-stat {
    text-align: center;
    padding: 0 16px;
    border-left: 1px solid rgba(255,255,255,0.1);
}

/* ── BLOOM NODES ── */
.bloom-path {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0;
    margin: 16px 0;
    flex-wrap: nowrap;
    overflow-x: auto;
    padding: 8px 0;
}
.bloom-node { display: flex; flex-direction: column; align-items: center; position: relative; min-width: 80px; }
.bloom-node-circle {
    width: 52px; height: 52px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.4rem; font-weight: 700; border: 3px solid;
    position: relative; z-index: 2;
}
.bloom-node-label {
    font-size: 9px; font-weight: 600; margin-top: 6px;
    text-align: center; text-transform: uppercase; letter-spacing: 0.06em;
}
.bloom-connector { width: 40px; height: 3px; margin-top: -26px; position: relative; z-index: 1; }

/* ── MEMORY SCORE ── */
.memory-score-card {
    background: #FFFFFF; border-radius: 14px; padding: 20px 24px;
    border: 1px solid #E2E8F0; box-shadow: 0 2px 8px rgba(15,27,45,0.06);
    text-align: center;
}

/* ── ONBOARDING ── */
.ob-option-btn {
    background: #FFFFFF;
    border: 1.5px solid #E2E8F0;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 10px;
    cursor: pointer;
    transition: all 0.2s;
    text-align: left;
    width: 100%;
}
.ob-option-btn:hover { border-color: #1E3A5F; background: #F8FAFC; }

/* ── AI INSIGHT CARD ── */
.ai-card {
    background: linear-gradient(135deg, #0F1B2D, #1E3A5F);
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 16px;
    border-left: 4px solid #C9A84C;
}
.ai-card-title { color: #C9A84C; font-size: 10px; text-transform: uppercase; letter-spacing: 0.12em; font-weight: 600; margin-bottom: 6px; }
.ai-card-text  { color: #FFFFFF; font-size: 0.95rem; line-height: 1.6; }

/* ── NEXT ACTION BANNER ── */
.next-action {
    background: #EEF2FF;
    border: 1px solid #C7D2FE;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 12px;
}
.next-action-emoji { font-size: 1.5rem; }
.next-action-title { font-weight: 600; color: #3730A3; font-size: 0.95rem; }
.next-action-desc  { color: #6366F1; font-size: 0.82rem; margin-top: 2px; }

@keyframes pulse {
    0%   { box-shadow: 0 0 0 0 rgba(99,102,241,0.4); }
    70%  { box-shadow: 0 0 0 8px rgba(99,102,241,0); }
    100% { box-shadow: 0 0 0 0 rgba(99,102,241,0); }
}
</style>
""", unsafe_allow_html=True)

# ── INIT DB ───────────────────────────────────────────────
init_db()
init_streak_table()
init_xp_table()

# ── SESSION STATE ─────────────────────────────────────────
if "user"      not in st.session_state: st.session_state.user      = None
if "auth_mode" not in st.session_state: st.session_state.auth_mode = "landing"

# ════════════════════════════════════════════════════════
# LANDING PAGE
# ════════════════════════════════════════════════════════
def create_landing_page():
    st.markdown("""
    <style>
    /* Landing page styles */
    .landing-hero {
        background: linear-gradient(135deg, #0F1B2D 0%, #1E3A5F 60%, #0F1B2D 100%);
        padding: 80px 40px 60px;
        margin: -1rem -1rem 0 -1rem;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    .landing-hero::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(201,168,76,0.06) 0%, transparent 60%);
        animation: pulse-bg 4s ease-in-out infinite;
    }
    @keyframes pulse-bg {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }
    .hero-badge {
        display: inline-block;
        background: rgba(201,168,76,0.15);
        border: 1px solid rgba(201,168,76,0.4);
        color: #C9A84C;
        padding: 6px 18px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 24px;
    }
    .hero-title {
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 4.5rem;
        font-weight: 700;
        color: #FFFFFF;
        line-height: 1.1;
        margin-bottom: 16px;
    }
    .hero-title span { color: #C9A84C; }
    .hero-tagline {
        font-size: 1.25rem;
        color: rgba(255,255,255,0.6);
        max-width: 560px;
        margin: 0 auto 40px;
        line-height: 1.6;
    }
    .hero-stats {
        display: flex;
        justify-content: center;
        gap: 48px;
        margin-top: 48px;
        padding-top: 40px;
        border-top: 1px solid rgba(255,255,255,0.08);
        flex-wrap: wrap;
    }
    .hero-stat-num {
        font-family: Georgia, serif;
        font-size: 2rem;
        font-weight: 700;
        color: #C9A84C;
    }
    .hero-stat-label {
        font-size: 11px;
        color: rgba(255,255,255,0.4);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 4px;
    }
    .feature-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 28px 24px;
        height: 100%;
        box-shadow: 0 2px 12px rgba(15,27,45,0.06);
        transition: transform 0.2s, box-shadow 0.2s;
        border-top: 3px solid;
    }
    .feature-icon { font-size: 2.2rem; margin-bottom: 14px; }
    .feature-title {
        font-family: Georgia, serif;
        font-size: 1.1rem;
        font-weight: 700;
        color: #0F1B2D;
        margin-bottom: 10px;
    }
    .feature-desc {
        font-size: 0.88rem;
        color: #64748B;
        line-height: 1.6;
    }
    .how-step {
        display: flex;
        align-items: flex-start;
        gap: 20px;
        margin-bottom: 28px;
    }
    .how-step-num {
        min-width: 44px;
        height: 44px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 1rem;
        font-family: Georgia, serif;
        flex-shrink: 0;
    }
    .cta-section {
        background: linear-gradient(135deg, #0F1B2D, #1E3A5F);
        border-radius: 20px;
        padding: 56px 40px;
        text-align: center;
        margin: 40px 0;
    }
    .footer {
        text-align: center;
        padding: 32px;
        color: #94A3B8;
        font-size: 13px;
        border-top: 1px solid #E2E8F0;
        margin-top: 40px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── HERO ─────────────────────────────────────────────
    st.markdown("""
    <div class='landing-hero'>
        <div class='hero-badge'>🧠 AI-Powered Memory Science</div>
        <div class='hero-title'>Never Forget<br>What You <span>Learn</span></div>
        <div class='hero-tagline'>
            Smriti uses Machine Learning to predict exactly when you'll forget —
            and reminds you to review before it happens.
        </div>
        <div class='hero-stats'>
            <div>
                <div class='hero-stat-num'>95.4%</div>
                <div class='hero-stat-label'>Model Accuracy</div>
            </div>
            <div>
                <div class='hero-stat-num'>13M+</div>
                <div class='hero-stat-label'>Training Records</div>
            </div>
            <div>
                <div class='hero-stat-num'>6</div>
                <div class='hero-stat-label'>Bloom's Levels</div>
            </div>
            <div>
                <div class='hero-stat-num'>100%</div>
                <div class='hero-stat-label'>Free to Use</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── CTA BUTTONS ──────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([2, 1, 2])
    with c2:
        if st.button("🚀 Get Started — Free", use_container_width=True, key="hero_cta"):
            st.session_state.auth_mode = "signup"
            st.rerun()

    c1, c2, c3 = st.columns([2.5, 1, 2.5])
    with c2:
        if st.button("🔑 Login", use_container_width=True, key="hero_login"):
            st.session_state.auth_mode = "login"
            st.rerun()

    # ── FEATURES ─────────────────────────────────────────
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align:center;margin-bottom:32px;'>
        <div style='font-size:12px;color:#C9A84C;text-transform:uppercase;
                    letter-spacing:0.12em;font-weight:600;margin-bottom:8px;'>
            Why Smriti?
        </div>
        <div style='font-family:Georgia,serif;font-size:2rem;
                    font-weight:700;color:#0F1B2D;'>
            Built on Real Science
        </div>
        <div style='color:#64748B;font-size:0.95rem;margin-top:8px;'>
            Inspired by Duolingo's Half-Life Regression — adapted for academic learning
        </div>
    </div>
    """, unsafe_allow_html=True)

    features = [
        {
            "icon": "📉",
            "title": "Personal Forgetting Curve",
            "desc": "ML model trained on 13M+ Duolingo records predicts YOUR retention — not a generic curve. R² = 0.9539.",
            "color": "#6366F1",
        },
        {
            "icon": "🔴",
            "title": "Weak Topic Detection",
            "desc": "Decision Tree classifier automatically flags topics as Strong, At-Risk, or Weak — before you forget.",
            "color": "#DC2626",
        },
        {
            "icon": "🧪",
            "title": "Bloom's Taxonomy Quiz",
            "desc": "AI-generated questions across 6 cognitive levels — from basic recall to creative problem solving.",
            "color": "#059669",
        },
        {
            "icon": "🏆",
            "title": "XP & Leaderboard",
            "desc": "Earn XP for every study activity. Climb from Bronze to Legend league — stay motivated every day.",
            "color": "#D97706",
        },
    ]

    cols = st.columns(4)
    for i, f in enumerate(features):
        with cols[i]:
            st.markdown(f"""
            <div class='feature-card' style='border-top-color:{f["color"]};'>
                <div class='feature-icon'>{f["icon"]}</div>
                <div class='feature-title'>{f["title"]}</div>
                <div class='feature-desc'>{f["desc"]}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── HOW IT WORKS ─────────────────────────────────────
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align:center;margin-bottom:32px;'>
        <div style='font-size:12px;color:#C9A84C;text-transform:uppercase;
                    letter-spacing:0.12em;font-weight:600;margin-bottom:8px;'>
            How It Works
        </div>
        <div style='font-family:Georgia,serif;font-size:2rem;
                    font-weight:700;color:#0F1B2D;'>
            4 Simple Steps
        </div>
    </div>
    """, unsafe_allow_html=True)

    steps = [
        ("#6366F1", "1", "📖 Add Topic",       "Enter topic name, subject & understanding score (1–10). Pick date you studied it."),
        ("#059669", "2", "🧠 ML Calculates",   "Our model computes your personal forgetting curve — powered by Duolingo's dataset."),
        ("#D97706", "3", "📊 See Your Curve",  "Dashboard shows retention % over 30 days. Red zone = review urgently!"),
        ("#DC2626", "4", "✅ Quiz & Update",    "Take Bloom's Taxonomy quiz → score updates your curve → memory gets stronger!"),
    ]

    col_l, col_r = st.columns(2)
    for i, (color, num, title, desc) in enumerate(steps):
        col = col_l if i % 2 == 0 else col_r
        with col:
            st.markdown(f"""
            <div class='how-step'>
                <div class='how-step-num'
                     style='background:{color}18;color:{color};border:2px solid {color};'>
                    {num}
                </div>
                <div>
                    <div style='font-weight:700;color:#0F1B2D;font-size:0.95rem;
                                margin-bottom:4px;'>{title}</div>
                    <div style='color:#64748B;font-size:0.85rem;line-height:1.5;'>
                        {desc}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── CTA SECTION ──────────────────────────────────────
    st.markdown("""
    <div class='cta-section'>
        <div style='font-size:12px;color:#C9A84C;text-transform:uppercase;
                    letter-spacing:0.12em;font-weight:600;margin-bottom:12px;'>
            Start Today — It's Free
        </div>
        <div style='font-family:Georgia,serif;font-size:2rem;font-weight:700;
                    color:#FFFFFF;margin-bottom:12px;'>
            Take Control of Your Memory
        </div>
        <div style='color:rgba(255,255,255,0.5);font-size:0.95rem;margin-bottom:32px;'>
            Join students who study smarter — not harder.
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([2, 1, 2])
    with c2:
        if st.button("🚀 Start for Free", use_container_width=True, key="cta_bottom"):
            st.session_state.auth_mode = "signup"
            st.rerun()

    # ── FOOTER ───────────────────────────────────────────
    st.markdown("""
    <div class='footer'>
        🧠 <strong>Smriti</strong> — AI-Powered Forgetting Curve Predictor<br>
        Made with ❤️ in Kanpur, Uttar Pradesh 🇮🇳<br>
        <span style='color:#CBD5E1;'>
            Inspired by Ebbinghaus (1885) · Duolingo Half-Life Regression · Bloom's Taxonomy
        </span>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════
# AUTH PAGE — LOGIN / SIGNUP
# ════════════════════════════════════════════════════════
def create_auth_page():
    # Back button
    if st.button("← Back to Home", key="back_home"):
        st.session_state.auth_mode = "landing"
        st.rerun()

    st.markdown("""
    <div style='text-align:center;margin:32px 0 24px;'>
        <div style='font-size:2.8rem;'>🧠</div>
        <div style='font-family:Georgia,serif;font-size:1.8rem;
                    font-weight:700;color:#0F1B2D;'>Smriti</div>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        mode_c1, mode_c2 = st.columns(2)
        with mode_c1:
            if st.button("🔑 Login",    use_container_width=True, key="tab_login"):
                st.session_state.auth_mode = "login"
        with mode_c2:
            if st.button("📝 Sign Up",  use_container_width=True, key="tab_signup"):
                st.session_state.auth_mode = "signup"

        st.markdown("---")

        if st.session_state.auth_mode == "login":
            st.markdown("#### 👋 Welcome back!")
            email    = st.text_input("Email", placeholder="you@example.com", key="login_email")
            password = st.text_input("Password", type="password", key="login_pass")

            if st.button("Login →", use_container_width=True, key="do_login"):
                if not email or not password:
                    st.error("Please enter email and password!")
                else:
                    with st.spinner("Logging in..."):
                        user, error = sign_in(email, password)
                    if user:
                        st.session_state.user      = user
                        st.session_state.auth_mode = "landing"
                        st.rerun()
                    else:
                        st.error(f"❌ {error}")

            st.markdown("<br>", unsafe_allow_html=True)
            st.caption("No account? Click **Sign Up** above!")

        else:
            st.markdown("#### 🚀 Create Account")
            email    = st.text_input("Email", placeholder="you@example.com", key="signup_email")
            password = st.text_input("Password (min 6 chars)", type="password", key="signup_pass")
            confirm  = st.text_input("Confirm Password", type="password", key="signup_confirm")

            if st.button("Create Account →", use_container_width=True, key="do_signup"):
                if not email or not password:
                    st.error("Please fill all fields!")
                elif password != confirm:
                    st.error("Passwords do not match!")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters!")
                else:
                    with st.spinner("Creating account..."):
                        user, error = sign_up(email, password)
                    if user:
                        st.session_state.user      = user
                        st.session_state.auth_mode = "landing"
                        st.rerun()
                    else:
                        st.error(f"❌ {error}")

            st.markdown("<br>", unsafe_allow_html=True)
            st.caption("Already have an account? Click **Login** above!")


# ════════════════════════════════════════════════════════
# SMART ONBOARDING — Branching + One-time + DB Save
# ════════════════════════════════════════════════════════

# ── Branching question tree ───────────────────────────

# ════════════════════════════════════════════════════════
# ONBOARDING MODULE (inline)
# ════════════════════════════════════════════════════════
# ── BRANCHING QUESTION TREE ───────────────────────────────
ONBOARDING_TREE = {
    "start": {
        "step":     0,
        "emoji":    "👋",
        "title":    "Welcome to Smriti!",
        "subtitle": "Let's personalize your experience — takes 30 seconds",
        "color":    "#6366F1",
        "question": "Who are you?",
        "options": [
            ("🏫", "School Student",           "school",       "Smart choice! Let's set up your study plan."),
            ("🎓", "College Student",           "college",      "Great! College learning needs smart revision."),
            ("📚", "Competitive Exam Aspirant", "competitive",  "Excellent! Let's sharpen your exam prep!"),
        ],
        "key":      "user_type",
        "feedback": True,
    },
    "school": {
        "step":     1,
        "emoji":    "🏫",
        "title":    "Which class are you in?",
        "subtitle": "We'll match content to your syllabus",
        "color":    "#059669",
        "options": [
            ("6️⃣",  "Class 6",  "school_6",  "Class 6 — great foundation year!"),
            ("7️⃣",  "Class 7",  "school_7",  "Class 7 — building strong concepts!"),
            ("8️⃣",  "Class 8",  "school_8",  "Class 8 — exciting new topics ahead!"),
            ("9️⃣",  "Class 9",  "school_9",  "Class 9 — boards are coming, let's prepare!"),
            ("🔟",  "Class 10", "school_10", "Class 10 — boards year, Smriti will help!"),
            ("1️⃣1️⃣","Class 11","school_11", "Class 11 — new chapter, new challenges!"),
            ("1️⃣2️⃣","Class 12","school_12", "Class 12 — final push, let's ace it!"),
        ],
        "key":      "user_detail",
        "feedback": True,
    },
    "college": {
        "step":     1,
        "emoji":    "🎓",
        "title":    "Which degree are you pursuing?",
        "subtitle": "We'll recommend the right subjects",
        "color":    "#D97706",
        "options": [
            ("💻", "B.Tech / B.E.", "college_btech", "Engineering — tough but rewarding!"),
            ("🔬", "B.Sc",          "college_bsc",   "Science — curiosity is your superpower!"),
            ("📊", "B.Com",         "college_bcom",  "Commerce — numbers are your friends!"),
            ("📜", "BA",            "college_ba",    "Arts — critical thinking at its best!"),
            ("⚕️", "MBBS / BDS",   "college_mbbs",  "Medicine — a noble and challenging path!"),
            ("📐", "Other",         "college_other", "Every degree is a unique journey!"),
        ],
        "key":      "user_detail",
        "feedback": True,
    },
    "competitive": {
        "step":     1,
        "emoji":    "📚",
        "title":    "Which exam are you preparing for?",
        "subtitle": "We'll focus on the right topics for you",
        "color":    "#DC2626",
        "options": [
            ("🏛️", "UPSC / IAS", "comp_upsc", "UPSC — the ultimate challenge!"),
            ("⚗️", "JEE",        "comp_jee",  "JEE — physics, math, and grit!"),
            ("🩺", "NEET",       "comp_neet", "NEET — healing begins with learning!"),
            ("⚙️", "GATE",       "comp_gate", "GATE — engineering mastery!"),
            ("📋", "SSC / CGL",  "comp_ssc",  "SSC — consistent effort wins!"),
            ("📝", "Other",      "comp_other","Every exam rewards smart preparation!"),
        ],
        "key":      "user_detail",
        "feedback": True,
    },
}

# ── SUMMARY LABELS ────────────────────────────────────────
SUMMARY_MAP = {
    "school_6":     ("Class 6 Student",          "🏫", "#059669"),
    "school_7":     ("Class 7 Student",          "🏫", "#059669"),
    "school_8":     ("Class 8 Student",          "🏫", "#059669"),
    "school_9":     ("Class 9 Student",          "🏫", "#059669"),
    "school_10":    ("Class 10 Student",         "🏫", "#059669"),
    "school_11":    ("Class 11 Student",         "🏫", "#059669"),
    "school_12":    ("Class 12 Student",         "🏫", "#059669"),
    "college_btech":("B.Tech / B.E. Student",   "🎓", "#D97706"),
    "college_bsc":  ("B.Sc Student",             "🎓", "#D97706"),
    "college_bcom": ("B.Com Student",            "🎓", "#D97706"),
    "college_ba":   ("BA Student",               "🎓", "#D97706"),
    "college_mbbs": ("MBBS / BDS Student",       "🎓", "#D97706"),
    "college_other":("College Student",           "🎓", "#D97706"),
    "comp_upsc":    ("UPSC / IAS Aspirant",      "📚", "#DC2626"),
    "comp_jee":     ("JEE Aspirant",             "📚", "#DC2626"),
    "comp_neet":    ("NEET Aspirant",            "📚", "#DC2626"),
    "comp_gate":    ("GATE Aspirant",            "📚", "#DC2626"),
    "comp_ssc":     ("SSC / CGL Aspirant",       "📚", "#DC2626"),
    "comp_other":   ("Competitive Exam Aspirant","📚", "#DC2626"),
}

# ── AI SUGGESTIONS based on profile ──────────────────────
def get_ai_suggestion(user_detail):
    suggestions = {
        "school_10":    "Class 10 boards need strong concept revision. Start with Science and Math weak topics daily.",
        "school_12":    "Class 12 is crucial! Revise each chapter within 3 days of studying using Smriti's curve.",
        "comp_jee":     "JEE needs deep problem-solving. Use Bloom's L3-L4 Apply & Analyze quizzes for Physics and Math.",
        "comp_neet":    "NEET is memory-heavy. Biology topics need daily revision — Smriti's forgetting curve is perfect!",
        "comp_upsc":    "UPSC needs vast coverage. Add 5-8 topics daily from Current Affairs, History, and Polity.",
        "college_btech":"Engineering needs application skills. Use L3 Apply quizzes for your core subjects.",
    }
    # Default suggestion
    return suggestions.get(user_detail,
        "Add your study topics daily and take quizzes to strengthen your memory retention.")

# ── DATABASE FUNCTIONS ────────────────────────────────────
def save_onboarding(user_id, user_type, user_detail):
    try:
        sb    = get_supabase()
        today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sb.table("onboarding").upsert({
            "user_id":      user_id,
            "user_type":    user_type,
            "user_detail":  user_detail,
            "completed_at": today,
        }).execute()
        return True
    except Exception as e:
        print(f"Onboarding save error: {e}")
        return False

def get_onboarding(user_id):
    try:
        sb  = get_supabase()
        res = sb.table("onboarding").select("*").eq("user_id", user_id).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None

# ── MAIN ONBOARDING UI ────────────────────────────────────
def create_onboarding(user_id):
    # Init state
    if "ob_node"     not in st.session_state: st.session_state.ob_node     = "start"
    if "ob_answers"  not in st.session_state: st.session_state.ob_answers  = {}
    if "ob_done"     not in st.session_state: st.session_state.ob_done     = False
    if "ob_feedback" not in st.session_state: st.session_state.ob_feedback = None

    # ── RESULT PAGE ───────────────────────────────────────
    if st.session_state.ob_done:
        detail           = st.session_state.ob_answers.get("user_detail", "")
        summary, emoji, color = SUMMARY_MAP.get(detail, ("Student", "👤", "#6366F1"))
        ai_tip           = get_ai_suggestion(detail)

        st.markdown(f"""
        <div style='text-align:center;padding:56px 24px 32px;'>
            <div style='font-size:4rem;margin-bottom:16px;'>🎉</div>
            <div style='font-size:12px;color:{color};text-transform:uppercase;
                        letter-spacing:0.12em;font-weight:600;margin-bottom:10px;'>
                Profile Ready!
            </div>
            <div style='font-family:Georgia,serif;font-size:2.2rem;font-weight:700;
                        color:#0F1B2D;margin-bottom:8px;'>
                You are a
            </div>
            <div style='font-family:Georgia,serif;font-size:2.2rem;font-weight:700;
                        color:{color};margin-bottom:24px;'>
                {emoji} {summary}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # AI Personalized tip
        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#0F1B2D,#1E3A5F);
                    border-radius:14px;padding:20px 24px;margin:0 auto 24px;
                    max-width:560px;border-left:4px solid #C9A84C;'>
            <div style='color:#C9A84C;font-size:10px;text-transform:uppercase;
                        letter-spacing:0.12em;font-weight:600;margin-bottom:8px;'>
                🤖 AI Recommendation — Just for You
            </div>
            <div style='color:#FFFFFF;font-size:0.95rem;line-height:1.6;'>
                {ai_tip}
            </div>
        </div>
        """, unsafe_allow_html=True)

        _, col, _ = st.columns([1.5, 2, 1.5])
        with col:
            if st.button("🚀 Start Using Smriti!", use_container_width=True, key="ob_finish"):
                save_onboarding(
                    user_id,
                    st.session_state.ob_answers.get("user_type", ""),
                    detail
                )
                st.session_state.onboarding_done = True
                st.session_state.user_summary    = summary
                st.session_state.user_emoji      = emoji
                st.session_state.ai_tip          = ai_tip
                for k in ["ob_node","ob_answers","ob_done","ob_feedback"]:
                    st.session_state.pop(k, None)
                st.rerun()
        return

    # ── MICRO FEEDBACK ────────────────────────────────────
    if st.session_state.ob_feedback:
        fb = st.session_state.ob_feedback
        st.markdown(f"""
        <div style='text-align:center;padding:32px 24px 16px;'>
            <div style='font-size:3rem;margin-bottom:12px;'>{fb["emoji"]}</div>
            <div style='font-family:Georgia,serif;font-size:1.4rem;font-weight:700;
                        color:{fb["color"]};margin-bottom:8px;'>{fb["text"]}</div>
            <div style='color:#64748B;font-size:0.9rem;'>{fb["sub"]}</div>
        </div>
        """, unsafe_allow_html=True)

        import time
        time.sleep(1.2)
        st.session_state.ob_feedback = None
        st.rerun()
        return

    # ── QUESTION PAGE ─────────────────────────────────────
    node = ONBOARDING_TREE.get(st.session_state.ob_node)
    if not node:
        st.session_state.ob_done = True
        st.rerun()
        return

    total   = 2
    current = node["step"]
    pct     = int((current / total) * 100)

    # Progress bar
    st.markdown(f"""
    <div style='max-width:580px;margin:0 auto;padding:40px 16px 0;'>
        <div style='display:flex;justify-content:space-between;margin-bottom:8px;'>
            <span style='color:#64748B;font-size:12px;font-weight:500;'>
                Step {current + 1} of {total}
            </span>
            <span style='color:{node["color"]};font-size:12px;font-weight:600;'>
                {pct}% complete
            </span>
        </div>
        <div style='background:#E2E8F0;border-radius:999px;height:8px;margin-bottom:40px;'>
            <div style='background:{node["color"]};width:{max(5, pct)}%;
                        height:8px;border-radius:999px;transition:width 0.4s;'></div>
        </div>
        <div style='text-align:center;margin-bottom:36px;'>
            <div style='font-size:3.5rem;margin-bottom:16px;'>{node["emoji"]}</div>
            <div style='font-family:Georgia,serif;font-size:1.8rem;font-weight:700;
                        color:#0F1B2D;margin-bottom:8px;'>{node["title"]}</div>
            <div style='color:#64748B;font-size:0.9rem;'>{node["subtitle"]}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Options
    _, col, _ = st.columns([0.5, 3, 0.5])
    with col:
        options      = node["options"]
        cols_per_row = 2 if len(options) > 4 else 1

        if cols_per_row == 1:
            for item in options:
                emoji, label, next_node, feedback_msg = item
                if st.button(
                    f"{emoji}  {label}",
                    use_container_width=True,
                    key=f"ob_{node['key']}_{next_node}"
                ):
                    st.session_state.ob_answers[node["key"]] = next_node
                    # Set micro-feedback
                    st.session_state.ob_feedback = {
                        "text":  feedback_msg,
                        "emoji": "✨",
                        "sub":   "Loading next question...",
                        "color": node["color"],
                    }
                    if next_node not in ONBOARDING_TREE:
                        st.session_state.ob_done = True
                    else:
                        st.session_state.ob_node = next_node
                    st.rerun()
        else:
            # Grid
            for i in range(0, len(options), 2):
                c1, c2 = st.columns(2)
                for j, col_w in enumerate([c1, c2]):
                    if i + j < len(options):
                        emoji, label, next_node, feedback_msg = options[i + j]
                        with col_w:
                            if st.button(
                                f"{emoji}  {label}",
                                use_container_width=True,
                                key=f"ob_{node['key']}_{next_node}"
                            ):
                                st.session_state.ob_answers[node["key"]] = next_node
                                st.session_state.ob_feedback = {
                                    "text":  feedback_msg,
                                    "emoji": "✨",
                                    "sub":   "Loading next question...",
                                    "color": node["color"],
                                }
                                if next_node not in ONBOARDING_TREE:
                                    st.session_state.ob_done = True
                                else:
                                    st.session_state.ob_node = next_node
                                st.rerun()

    # Back button
    if current > 0:
        st.markdown("<br>", unsafe_allow_html=True)
        _, c, _ = st.columns([2, 1, 2])
        with c:
            if st.button("← Back", use_container_width=True, key="ob_back"):
                st.session_state.ob_node = "start"
                st.session_state.ob_answers.pop("user_detail", None)
                st.rerun()


# ════════════════════════════════════════════════════════
# DASHBOARD HOME MODULE (inline)
# ════════════════════════════════════════════════════════
# ── AI PERSONALIZATION ENGINE ─────────────────────────────
def get_personalized_insights(user_summary, topics, priority):
    """Generate AI insights based on user profile + data"""

    weak   = [t for t in priority if "Weak"    in t["label"]]
    atrisk = [t for t in priority if "At-Risk" in t["label"]]
    strong = [t for t in priority if "Strong"  in t["label"]]

    insights = []

    # Insight 1 — Profile based
    if "JEE" in user_summary:
        insights.append({
            "icon":  "⚗️",
            "title": "JEE Strategy",
            "text":  "Focus on Physics & Math weak topics first. Use Bloom's L3 Apply quizzes for problem solving practice.",
            "color": "#DC2626",
        })
    elif "NEET" in user_summary:
        insights.append({
            "icon":  "🩺",
            "title": "NEET Strategy",
            "text":  "Biology needs daily revision. Smriti's forgetting curve will help you retain cell biology and genetics.",
            "color": "#059669",
        })
    elif "UPSC" in user_summary:
        insights.append({
            "icon":  "🏛️",
            "title": "UPSC Strategy",
            "text":  "Add 5 topics daily from History, Polity, and Current Affairs. Revision within 3 days is critical.",
            "color": "#D97706",
        })
    elif "Class 10" in user_summary or "Class 12" in user_summary:
        insights.append({
            "icon":  "📋",
            "title": "Board Exam Strategy",
            "text":  "Board preparation needs chapter-wise mastery. Add each chapter and track retention weekly.",
            "color": "#6366F1",
        })
    elif "B.Tech" in user_summary:
        insights.append({
            "icon":  "💻",
            "title": "Engineering Strategy",
            "text":  "Engineering subjects need application skills. Use Bloom's L3 & L4 quizzes for your core subjects.",
            "color": "#0891B2",
        })
    else:
        insights.append({
            "icon":  "🎯",
            "title": "Study Strategy",
            "text":  "Add your study topics daily and take quizzes to strengthen memory. Consistency beats intensity!",
            "color": "#6366F1",
        })

    # Insight 2 — Data based
    if weak:
        insights.append({
            "icon":  "🚨",
            "title": "Urgent Action Required",
            "text":  f"**{weak[0]['topic_name']}** has only {weak[0]['retention']}% retention! Review it today before you forget completely.",
            "color": "#DC2626",
        })
    elif atrisk:
        insights.append({
            "icon":  "⚠️",
            "title": "Topics Fading Fast",
            "text":  f"**{atrisk[0]['topic_name']}** is at {atrisk[0]['retention']}% — review it in the next 2 days to prevent forgetting.",
            "color": "#D97706",
        })
    elif strong and len(topics) > 0:
        insights.append({
            "icon":  "🌟",
            "title": "Great Memory Health!",
            "text":  f"All {len(topics)} topics are in strong shape. Add new topics to keep growing your knowledge base!",
            "color": "#059669",
        })

    # Insight 3 — Quiz suggestion
    if len(topics) > 0:
        lowest = min(priority, key=lambda x: x["retention"])
        insights.append({
            "icon":  "🧪",
            "title": "Quiz Recommendation",
            "text":  f"Take a Bloom's L1 quiz on **{lowest['topic_name']}** — it has the lowest retention and needs urgent reinforcement.",
            "color": "#7C3AED",
        })

    return insights[:3]

# ── NEXT ACTION BANNER ────────────────────────────────────
def render_next_action(priority, topics):
    """Show the single most important action right now"""

    weak   = [t for t in priority if "Weak"    in t["label"]]
    atrisk = [t for t in priority if "At-Risk" in t["label"]]

    if not topics:
        action = {
            "emoji": "➕",
            "title": "Add your first topic!",
            "desc":  "Click 'Add Topic' above to start tracking your memory.",
            "color": "#6366F1",
        }
    elif weak:
        action = {
            "emoji": "🚨",
            "title": f"Review '{weak[0]['topic_name']}' NOW!",
            "desc":  f"Only {weak[0]['retention']}% retained — go to Review List immediately.",
            "color": "#DC2626",
        }
    elif atrisk:
        action = {
            "emoji": "⚠️",
            "title": f"'{atrisk[0]['topic_name']}' is fading!",
            "desc":  f"{atrisk[0]['retention']}% retained — review today to prevent forgetting.",
            "color": "#D97706",
        }
    else:
        action = {
            "emoji": "🎯",
            "title": "Take a quiz to strengthen memory!",
            "desc":  "All topics are strong. Quiz yourself to go deeper with Bloom's Taxonomy.",
            "color": "#059669",
        }

    st.markdown(f"""
    <div style='background:{action["color"]}12;border:1.5px solid {action["color"]}44;
                border-radius:12px;padding:16px 20px;margin-bottom:20px;
                display:flex;align-items:center;gap:14px;'>
        <span style='font-size:1.8rem;'>{action["emoji"]}</span>
        <div>
            <div style='font-weight:700;color:{action["color"]};font-size:0.95rem;'>
                👉 Next Action: {action["title"]}
            </div>
            <div style='color:#64748B;font-size:0.82rem;margin-top:3px;'>
                {action["desc"]}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── STREAK CARD ───────────────────────────────────────────
def render_streak_card(user_id, topics):
    streak     = get_streak(user_id=user_id)
    total_days = get_total_study_days(user_id=user_id)
    total_xp   = get_total_xp(user_id=user_id)
    today_xp   = get_today_xp(user_id=user_id)

    fire = "🔥🔥🔥" if streak >= 30 else "🔥🔥" if streak >= 14 else "🔥" if streak >= 7 else "⚡" if streak >= 1 else "💤"
    msg  = (
        "Legendary! 🏆"              if streak >= 30 else
        "On fire! Keep going!"        if streak >= 14 else
        "Great streak! Don't break it!" if streak >= 7 else
        "Building momentum!"          if streak >= 3 else
        "Day 1 — every streak starts here!" if streak == 1 else
        "Start your streak today!"
    )

    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#0F1B2D,#1E3A5F);
                border-radius:16px;padding:20px 24px;margin-bottom:20px;
                border:1px solid rgba(201,168,76,0.3);
                display:flex;align-items:center;
                justify-content:space-between;flex-wrap:wrap;gap:16px;'>
        <div style='display:flex;align-items:center;gap:16px;'>
            <div style='font-size:2.8rem;filter:drop-shadow(0 0 10px rgba(245,158,11,0.5));'>
                {fire}
            </div>
            <div>
                <div style='color:rgba(255,255,255,0.45);font-size:10px;
                            text-transform:uppercase;letter-spacing:0.12em;
                            font-weight:600;margin-bottom:3px;'>Study Streak</div>
                <div style='display:flex;align-items:baseline;gap:6px;'>
                    <span style='color:#C9A84C;font-size:2.2rem;font-weight:700;
                                 font-family:Georgia,serif;'>{streak}</span>
                    <span style='color:rgba(255,255,255,0.5);font-size:0.9rem;'>
                        day{"s" if streak != 1 else ""}
                    </span>
                </div>
                <div style='color:#C9A84C;font-size:0.8rem;margin-top:2px;'>{msg}</div>
            </div>
        </div>
        <div style='display:flex;gap:0;'>
            <div style='text-align:center;padding:0 20px;
                        border-left:1px solid rgba(255,255,255,0.1);'>
                <div style='color:#FFFFFF;font-size:1.5rem;font-weight:700;
                            font-family:Georgia,serif;'>{total_days}</div>
                <div style='color:rgba(255,255,255,0.35);font-size:10px;
                            text-transform:uppercase;letter-spacing:0.08em;'>Total Days</div>
            </div>
            <div style='text-align:center;padding:0 20px;
                        border-left:1px solid rgba(255,255,255,0.1);'>
                <div style='color:#C9A84C;font-size:1.5rem;font-weight:700;
                            font-family:Georgia,serif;'>{total_xp}</div>
                <div style='color:rgba(255,255,255,0.35);font-size:10px;
                            text-transform:uppercase;letter-spacing:0.08em;'>Total XP</div>
            </div>
            <div style='text-align:center;padding:0 20px;
                        border-left:1px solid rgba(255,255,255,0.1);'>
                <div style='color:#22C55E;font-size:1.5rem;font-weight:700;
                            font-family:Georgia,serif;'>+{today_xp}</div>
                <div style='color:rgba(255,255,255,0.35);font-size:10px;
                            text-transform:uppercase;letter-spacing:0.08em;'>Today XP</div>
            </div>
            <div style='text-align:center;padding:0 20px;
                        border-left:1px solid rgba(255,255,255,0.1);'>
                <div style='color:#60A5FA;font-size:1.5rem;font-weight:700;
                            font-family:Georgia,serif;'>{len(topics)}</div>
                <div style='color:rgba(255,255,255,0.35);font-size:10px;
                            text-transform:uppercase;letter-spacing:0.08em;'>Topics</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── BLOOM'S PROGRESS NODES ────────────────────────────────
def render_bloom_nodes():
    best_bloom = st.session_state.get("best_bloom_achieved", 1)
    bloom_data = [
        (1, "🧠", "Remember", "#6B7280"),
        (2, "💡", "Understand","#0891B2"),
        (3, "⚙️", "Apply",    "#059669"),
        (4, "🔍", "Analyze",  "#D97706"),
        (5, "⚖️", "Evaluate", "#DC2626"),
        (6, "🚀", "Create",   "#7C3AED"),
    ]

    nodes_html = "<div class='bloom-path'>"
    for i, (lvl, emoji, name, color) in enumerate(bloom_data):
        is_done    = lvl < best_bloom
        is_current = lvl == best_bloom
        is_locked  = lvl > best_bloom

        if is_done:
            bg, border, txt, opacity, lbl_col = color, color, "#FFFFFF", "1", color
        elif is_current:
            bg, border, txt, opacity, lbl_col = f"{color}20", color, color, "1", color
        else:
            bg, border, txt, opacity, lbl_col = "#F1F4F8", "#CBD5E1", "#94A3B8", "0.5", "#94A3B8"

        pulse = "animation:pulse 1.5s infinite;" if is_current else ""
        nodes_html += f"""
        <div class='bloom-node' style='opacity:{opacity};'>
            <div class='bloom-node-circle'
                 style='background:{bg};border-color:{border};color:{txt};{pulse}'>
                {'✓' if is_done else emoji}
            </div>
            <div class='bloom-node-label' style='color:{lbl_col};'>
                L{lvl}<br/>{name}
            </div>
        </div>"""

        if i < len(bloom_data) - 1:
            conn_color = color if is_done else "#E2E8F0"
            nodes_html += f"""
            <div class='bloom-connector'
                 style='background:{conn_color};margin-bottom:22px;'></div>"""

    nodes_html += "</div>"
    nodes_html += """
    <style>
    @keyframes pulse {
        0%   { box-shadow: 0 0 0 0 rgba(99,102,241,0.4); }
        70%  { box-shadow: 0 0 0 8px rgba(99,102,241,0); }
        100% { box-shadow: 0 0 0 0 rgba(99,102,241,0); }
    }
    </style>"""
    st.markdown(nodes_html, unsafe_allow_html=True)
    st.caption(f"Currently at L{best_bloom} — Take a quiz to advance! 🎯")

# ── MAIN RENDER ───────────────────────────────────────────
def render_home(topics, user_id, load_topics_fn):
    """Main home dashboard render function"""

    user_summary = st.session_state.get("user_summary", "Student")
    user_emoji   = st.session_state.get("user_emoji",   "🎓")
    ai_tip       = st.session_state.get("ai_tip",       "")

    # Page header
    st.markdown(f"""
    <div class='page-header'>
        <div style='display:flex;align-items:center;gap:12px;'>
            <div>
                <div class='page-title'>Memory Dashboard</div>
                <div class='page-subtitle'>
                    {user_emoji} {user_summary} · Your personal knowledge retention overview
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    priority = get_review_priority(topics) if topics else []
    weak     = [t for t in priority if "Weak"    in t["label"]]
    atrisk   = [t for t in priority if "At-Risk" in t["label"]]
    strong   = [t for t in priority if "Strong"  in t["label"]]

    # ── NEXT ACTION BANNER ────────────────────────────────
    render_next_action(priority, topics)

    # ── STREAK CARD ───────────────────────────────────────
    render_streak_card(user_id, topics)

    if not topics:
        st.info("👋 No topics yet! Click **➕ Add Topic** above to start tracking your memory.")
        return

    # ── METRICS ───────────────────────────────────────────
    avg_ret    = int(sum(t["retention"] for t in priority) / len(priority)) if priority else 0
    score_color = "#059669" if avg_ret >= 70 else "#D97706" if avg_ret >= 40 else "#DC2626"
    score_label = "Excellent 🌟" if avg_ret >= 70 else "Needs Attention ⚠️" if avg_ret >= 40 else "Critical 🚨"

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("📚 Topics",   len(topics))
    c2.metric("💪 Strong",   len(strong))
    c3.metric("⚠️ At-Risk",  len(atrisk))
    c4.metric("🔴 Weak",     len(weak))
    with c5:
        st.markdown(f"""
        <div style='background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;
                    padding:16px 20px;text-align:center;
                    box-shadow:0 1px 6px rgba(15,27,45,0.06);'>
            <div style='font-size:10px;color:#64748B;text-transform:uppercase;
                        letter-spacing:0.1em;font-weight:600;margin-bottom:6px;'>
                Memory Score
            </div>
            <div style='font-size:2rem;font-weight:700;color:{score_color};
                        font-family:Georgia,serif;'>{avg_ret}%</div>
            <div style='font-size:11px;color:{score_color};margin-top:4px;'>{score_label}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── ALERTS ────────────────────────────────────────────
    st.markdown("<div class='gold-line'></div>", unsafe_allow_html=True)
    if weak:
        st.error(f"🚨 **{len(weak)} topic(s) need urgent review today!**")
        for t in weak[:3]:
            st.markdown(f"→ **{t['topic_name']}** `{t['subject']}` — `{t['retention']}%` retained")
    if atrisk:
        st.warning(f"⚠️ **{len(atrisk)} topic(s)** are fading. Review soon!")
    if not weak and not atrisk:
        st.success("✅ All topics in great shape! Keep it up.")

    # ── AI PERSONALIZED INSIGHTS ──────────────────────────
    st.markdown("---")
    st.markdown("### 🤖 AI Insights — Personalized for You")

    insights = get_personalized_insights(user_summary, topics, priority)
    cols     = st.columns(len(insights))
    for i, ins in enumerate(insights):
        with cols[i]:
            st.markdown(f"""
            <div style='background:#FFFFFF;border:1px solid #E2E8F0;border-radius:14px;
                        padding:20px;height:100%;border-top:3px solid {ins["color"]};
                        box-shadow:0 2px 8px rgba(15,27,45,0.05);'>
                <div style='font-size:1.8rem;margin-bottom:10px;'>{ins["icon"]}</div>
                <div style='font-weight:700;color:#0F1B2D;font-size:0.9rem;
                            margin-bottom:8px;'>{ins["title"]}</div>
                <div style='color:#64748B;font-size:0.82rem;line-height:1.6;'>
                    {ins["text"]}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── BLOOM'S PROGRESS ──────────────────────────────────
    st.markdown("---")
    st.markdown("#### 🎓 Bloom's Taxonomy Journey")
    render_bloom_nodes()

    # ── CHARTS ────────────────────────────────────────────
    st.markdown("---")
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("#### 📂 Topics by Subject")
        subjects = {}
        for t in topics:
            subjects[t["subject"]] = subjects.get(t["subject"], 0) + 1
        fig = __import__("plotly.express", fromlist=["pie"]).pie(
            values=list(subjects.values()),
            names=list(subjects.keys()),
            hole=0.5,
            color_discrete_sequence=["#0F1B2D","#1E3A5F","#C9A84C","#2D6A4F","#8B1A1A","#374151"]
        )
        fig.update_layout(
            height=280,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#FFFFFF",
            margin=dict(t=30, b=0, l=0, r=0),
            font=dict(color="#64748B"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown("#### 🏆 Memory Health Gauge")
        total_xp = get_total_xp(user_id=user_id)
        fig2 = __import__("plotly.graph_objects", fromlist=["Figure"]).Figure(
            __import__("plotly.graph_objects", fromlist=["Indicator"]).Indicator(
                mode="gauge+number",
                value=avg_ret,
                title={"text": "Average Retention %", "font": {"color": "#64748B", "size": 12}},
                number={"font": {"color": "#0F1B2D", "family": "Georgia", "size": 36}, "suffix": "%"},
                gauge={
                    "axis":    {"range": [0, 100], "tickcolor": "#CBD5E1"},
                    "bar":     {"color": "#1E3A5F", "thickness": 0.28},
                    "bgcolor": "white",
                    "steps":   [
                        {"range": [0, 40],   "color": "#FEE2E2"},
                        {"range": [40, 70],  "color": "#FEF3C7"},
                        {"range": [70, 100], "color": "#DCFCE7"},
                    ],
                    "threshold": {"line": {"color": "#C9A84C", "width": 3}, "value": 70}
                }
            )
        )
        fig2.update_layout(height=280, paper_bgcolor="rgba(0,0,0,0)",
                           margin=dict(t=20, b=10, l=10, r=10))
        st.plotly_chart(fig2, use_container_width=True)


# ── ROUTE ─────────────────────────────────────────────────
if not st.session_state.user:
    if st.session_state.auth_mode == "landing":
        create_landing_page()
    else:
        create_auth_page()
    st.stop()

# ── ONBOARDING CHECK — one time only ──────────────────────
user_id = st.session_state.user.id

if "onboarding_done" not in st.session_state:
    # Check DB first
    ob_data = get_onboarding(user_id)
    if ob_data:
        st.session_state.onboarding_done = True
        st.session_state.user_summary    = SUMMARY_MAP.get(ob_data.get("user_detail",""), "Student")
    else:
        st.session_state.onboarding_done = False

if not st.session_state.onboarding_done:
    create_onboarding(user_id)
    st.stop()

# ── USER IS LOGGED IN ─────────────────────────────────────
# Mark today studied + streak XP
mark_today_studied(user_id=user_id)
if "streak_xp_given" not in st.session_state:
    add_xp("streak_daily", "Daily streak bonus", user_id=user_id)
    st.session_state.streak_xp_given = True

# ── SESSION STATE ─────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "Home"

# ── TOP NAVIGATION ────────────────────────────────────────
user_email = st.session_state.user.email
st.markdown(f"""
<div class='nav-wrapper'>
    <div class='nav-brand'>
        🧠 <span>Smriti</span>
        <span class='nav-tagline'>Memory Intelligence</span>
    </div>
    <div style='color:rgba(255,255,255,0.4);font-size:11px;'>
        {user_email}
    </div>
</div>
""", unsafe_allow_html=True)

# Nav buttons
c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([1.2, 1, 1, 1, 1, 1, 1, 0.8])
with c1:
    st.markdown("")
with c2:
    if st.button("🏠 Home",         use_container_width=True, key="nav_home"):   st.session_state.page = "Home"
with c3:
    if st.button("➕ Add Topic",    use_container_width=True, key="nav_add"):    st.session_state.page = "Add Topic"
with c4:
    if st.button("📊 Dashboard",   use_container_width=True, key="nav_dash"):   st.session_state.page = "Dashboard"
with c5:
    if st.button("📋 Review List", use_container_width=True, key="nav_review"): st.session_state.page = "Review List"
with c6:
    if st.button("🧪 Quiz",        use_container_width=True, key="nav_quiz"):   st.session_state.page = "Quiz"
with c7:
    if st.button("🏆 Leaderboard", use_container_width=True, key="nav_leader"): st.session_state.page = "Leaderboard"
with c8:
    if st.button("🚪 Logout",      use_container_width=True, key="nav_logout"):
        sign_out()
        st.session_state.user = None
        st.session_state.clear()
        st.rerun()

page = st.session_state.page

# ── HELPER ────────────────────────────────────────────────
def load_topics():
    raw = get_all_topics(user_id=user_id)
    return [{
        "id": r[0], "topic_name": r[1], "subject": r[2],
        "understanding_score": r[3], "date_learned": r[4],
        "last_reviewed": r[5], "review_count": r[6] if r[6] else 0
    } for r in raw]

def chart_layout(title=""):
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        font=dict(family="Inter", color="#64748B", size=12),
        title=dict(text=title, font=dict(family="Playfair Display", color="#0F1B2D", size=15)),
        xaxis=dict(gridcolor="#F1F4F8", zerolinecolor="#E2E8F0", linecolor="#E2E8F0"),
        yaxis=dict(gridcolor="#F1F4F8", zerolinecolor="#E2E8F0", linecolor="#E2E8F0"),
        margin=dict(t=50, b=40, l=40, r=20),
    )

CHART_COLORS = ["#0F1B2D","#1E3A5F","#C9A84C","#2D6A4F","#8B1A1A","#374151"]

# ════════════════════════════════════════════════════════
# PAGE 1 — HOME (Modular — see dashboard_home.py)
# ════════════════════════════════════════════════════════
if page == "Home":
    topics = load_topics()
    render_home(topics, user_id, load_topics)
# ════════════════════════════════════════════════════════
# PAGE 2 — ADD TOPIC
# ════════════════════════════════════════════════════════
elif page == "Add Topic":
    st.markdown("""
    <div class='page-header'>
        <div class='page-title'>Add New Topic</div>
        <div class='page-subtitle'>Track what you learn — Smriti predicts when you will forget it</div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("add_topic_form"):
        col1, col2 = st.columns(2)
        with col1:
            topic_name = st.text_input("Topic Name", placeholder="e.g. Photosynthesis, Newton's Laws")
            subject    = st.selectbox("Subject", [
                "Biology","Mathematics","Physics","Chemistry",
                "History","Geography","Computer Science","Other"
            ])
            from datetime import date as dt_date
            date_learned = st.date_input(
                "When did you study this topic?",
                value=dt_date.today(),
                max_value=dt_date.today(),
                help="Select today if studied now, or past date if studied earlier"
            )
        with col2:
            understanding_score = st.slider("How well did you understand? (1–10)", 1, 10, 7)
            if understanding_score >= 7:
                st.success(f"🟢 {understanding_score}/10 — Strong! Memory will last longer.")
            elif understanding_score >= 4:
                st.warning(f"🟡 {understanding_score}/10 — Average. Review sooner!")
            else:
                st.error(f"🔴 {understanding_score}/10 — Weak! Needs quick review.")

            # Show predicted retention based on selected date
            days_ago = (dt_date.today() - date_learned).days
            if days_ago > 0:
                pred_now = predict_future_retention(understanding_score, str(date_learned), 0, 0)
                st.info(f"📅 {days_ago} days ago — Current retention: ~{pred_now}%")

        notes     = st.text_area("Notes (optional)", placeholder="Any quick notes about this topic...")
        submitted = st.form_submit_button("➕ Add Topic", use_container_width=True)

        if submitted:
            if not topic_name.strip():
                st.error("Please enter a topic name!")
            else:
                add_topic(topic_name.strip(), subject, understanding_score, str(date_learned), user_id=user_id)
                xp_earned = add_xp("add_topic", topic_name.strip(), user_id=user_id)
                st.success(f"✅ **'{topic_name}'** added! +{xp_earned} XP 🌟")
                st.balloons()

                st.markdown("### 🔮 Predicted Memory Retention")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Now",           f"{predict_future_retention(understanding_score, str(date_learned), 0, 0)}%")
                c2.metric("After 3 days",  f"{predict_future_retention(understanding_score, str(date_learned), 0, 3)}%")
                c3.metric("After 7 days",  f"{predict_future_retention(understanding_score, str(date_learned), 0, 7)}%")
                c4.metric("After 30 days", f"{predict_future_retention(understanding_score, str(date_learned), 0, 30)}%")

# ════════════════════════════════════════════════════════
# PAGE 3 — DASHBOARD
# ════════════════════════════════════════════════════════
elif page == "Dashboard":
    st.markdown("""
    <div class='page-header'>
        <div class='page-title'>Forgetting Curve</div>
        <div class='page-subtitle'>Visualize your memory decay — know exactly when to review</div>
    </div>
    """, unsafe_allow_html=True)

    topics = load_topics()
    if not topics:
        st.info("No topics yet! Click **➕ Add Topic** to add some.")
    else:
        topic_names    = [f"{t['topic_name']} ({t['subject']})" for t in topics]
        selected       = st.selectbox("Select topic:", topic_names)
        selected_topic = topics[topic_names.index(selected)]

        ret        = current_retention(
            selected_topic["understanding_score"],
            selected_topic["date_learned"],
            selected_topic["review_count"]
        )
        label, color = classify_topic(ret, selected_topic["review_count"])

        # ── Classification color mapping ──
        if "Strong" in label:
            bg_color   = "#F0FDF4"
            bd_color   = "#059669"
            text_color = "#065F46"
            icon       = "💪"
            advice     = "Memory is strong! Review in 2-3 weeks."
        elif "At-Risk" in label:
            bg_color   = "#FFFBEB"
            bd_color   = "#D97706"
            text_color = "#92400E"
            icon       = "⚠️"
            advice     = "Memory fading! Review within 3-4 days."
        else:
            bg_color   = "#FEF2F2"
            bd_color   = "#DC2626"
            text_color = "#991B1B"
            icon       = "🔴"
            advice     = "Memory critical! Review TODAY."

        # ── 4 metric cards ──
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Current Retention",   f"{ret}%")
        c2.metric("Understanding",       f"{selected_topic['understanding_score']}/10")
        c3.metric("Reviews Done",        selected_topic["review_count"])
        c4.metric("Days Since Learned",
                  (pd.Timestamp.today() - pd.Timestamp(selected_topic["date_learned"])).days
                  if selected_topic["date_learned"] else 0)

        st.markdown("<div class='gold-line'></div>", unsafe_allow_html=True)

        # ── Classification Card ──
        st.markdown(f"""
        <div style='background:{bg_color};border:1.5px solid {bd_color};
                    border-left:5px solid {bd_color};border-radius:12px;
                    padding:18px 24px;margin-bottom:20px;
                    display:flex;align-items:center;justify-content:space-between;
                    flex-wrap:wrap;gap:12px;'>
            <div>
                <div style='font-size:10px;color:{bd_color};letter-spacing:0.12em;
                            text-transform:uppercase;font-weight:600;margin-bottom:4px;'>
                    Decision Tree Classification
                </div>
                <div style='font-size:1.2rem;font-weight:700;color:{text_color};'>
                    {icon} {label}
                </div>
                <div style='font-size:0.85rem;color:{text_color};opacity:0.75;margin-top:4px;'>
                    {advice}
                </div>
            </div>
            <div style='text-align:center;'>
                <div style='font-size:2.5rem;font-weight:700;color:{bd_color};
                            font-family:Georgia,serif;line-height:1;'>{ret}%</div>
                <div style='font-size:11px;color:{text_color};opacity:0.6;
                            text-transform:uppercase;letter-spacing:0.08em;margin-top:4px;'>
                    Memory Retained
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── All topics classification summary ──
        st.markdown("### 🌳 Classification Summary — All Topics")
        priority = get_review_priority(topics)

        col_s, col_a, col_w = st.columns(3)
        strong_topics = [t for t in priority if "Strong"  in t["label"]]
        risk_topics   = [t for t in priority if "At-Risk" in t["label"]]
        weak_topics   = [t for t in priority if "Weak"    in t["label"]]

        with col_s:
            st.markdown(f"""
            <div style='background:#F0FDF4;border:1px solid #059669;border-radius:10px;
                        padding:14px 18px;text-align:center;'>
                <div style='font-size:2rem;font-weight:700;color:#059669;
                            font-family:Georgia,serif;'>{len(strong_topics)}</div>
                <div style='font-size:11px;color:#065F46;text-transform:uppercase;
                            letter-spacing:0.1em;font-weight:600;'>💪 Strong</div>
                <div style='font-size:11px;color:#6B7280;margin-top:6px;'>
                    {'<br>'.join([f"• {t['topic_name']}" for t in strong_topics[:3]]) or 'None yet'}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_a:
            st.markdown(f"""
            <div style='background:#FFFBEB;border:1px solid #D97706;border-radius:10px;
                        padding:14px 18px;text-align:center;'>
                <div style='font-size:2rem;font-weight:700;color:#D97706;
                            font-family:Georgia,serif;'>{len(risk_topics)}</div>
                <div style='font-size:11px;color:#92400E;text-transform:uppercase;
                            letter-spacing:0.1em;font-weight:600;'>⚠️ At-Risk</div>
                <div style='font-size:11px;color:#6B7280;margin-top:6px;'>
                    {'<br>'.join([f"• {t['topic_name']}" for t in risk_topics[:3]]) or 'None'}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_w:
            st.markdown(f"""
            <div style='background:#FEF2F2;border:1px solid #DC2626;border-radius:10px;
                        padding:14px 18px;text-align:center;'>
                <div style='font-size:2rem;font-weight:700;color:#DC2626;
                            font-family:Georgia,serif;'>{len(weak_topics)}</div>
                <div style='font-size:11px;color:#991B1B;text-transform:uppercase;
                            letter-spacing:0.1em;font-weight:600;'>🔴 Weak</div>
                <div style='font-size:11px;color:#6B7280;margin-top:6px;'>
                    {'<br>'.join([f"• {t['topic_name']}" for t in weak_topics[:3]]) or 'None'}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div class='gold-line'></div>", unsafe_allow_html=True)

        # Forgetting curve
        curve_data = get_retention_curve(
            selected_topic["understanding_score"],
            selected_topic["date_learned"],
            selected_topic["review_count"]
        )
        df_curve = pd.DataFrame(curve_data)

        fig = go.Figure()
        fig.add_hrect(y0=0,  y1=40,  fillcolor="rgba(220,38,38,0.04)",  line_width=0)
        fig.add_hrect(y0=40, y1=70,  fillcolor="rgba(217,119,6,0.04)",  line_width=0)
        fig.add_hrect(y0=70, y1=105, fillcolor="rgba(5,150,105,0.04)",  line_width=0)

        fig.add_trace(go.Scatter(
            x=df_curve["day"], y=df_curve["retention"],
            mode="lines", name="Memory Retention",
            line=dict(color="#1E3A5F", width=3),
            fill="tozeroy", fillcolor="rgba(30,58,95,0.07)"
        ))
        fig.add_hline(y=40, line_dash="dash", line_color="rgba(220,38,38,0.6)",
                      annotation_text="Danger Zone (40%)", annotation_font_color="#DC2626")
        fig.add_hline(y=70, line_dash="dash", line_color="rgba(217,119,6,0.6)",
                      annotation_text="At-Risk (70%)",     annotation_font_color="#D97706")
        fig.add_vline(x=0,  line_dash="dot",  line_color="rgba(201,168,76,0.8)",
                      annotation_text="Today",             annotation_font_color="#C9A84C")

        layout = chart_layout(f"{selected_topic['topic_name']} — Memory Curve")
        layout["yaxis"]["range"] = [0, 105]
        layout["yaxis"]["title"] = "Retention %"
        layout["xaxis"]["title"] = "Days from today"
        fig.update_layout(height=420, hovermode="x unified", showlegend=False, **layout)
        st.plotly_chart(fig, use_container_width=True)

        # All topics bar
        st.markdown("### 📊 All Topics — Memory Health")
        priority = get_review_priority(topics)
        df_all   = pd.DataFrame([{
            "Topic":       t["topic_name"],
            "Subject":     t["subject"],
            "Retention %": t["retention"],
            "Status":      t["label"],
        } for t in priority])

        fig2 = px.bar(df_all, x="Topic", y="Retention %", color="Status",
                      color_discrete_map={
                          "Strong 💪":  "#059669",
                          "At-Risk ⚠️": "#D97706",
                          "Weak 🔴":    "#DC2626"
                      })
        fig2.update_layout(height=350, **chart_layout("All Topics — Current Retention"))
        st.plotly_chart(fig2, use_container_width=True)

# ════════════════════════════════════════════════════════
# PAGE 4 — REVIEW LIST
# ════════════════════════════════════════════════════════
elif page == "Review List":
    st.markdown("""
    <div class='page-header'>
        <div class='page-title'>Today's Review List</div>
        <div class='page-subtitle'>Most forgotten topics first — your personalized revision schedule</div>
    </div>
    """, unsafe_allow_html=True)

    topics = load_topics()
    if not topics:
        st.info("No topics yet! Click **➕ Add Topic** to add some.")
    else:
        priority = get_review_priority(topics)
        weak   = [t for t in priority if "Weak"    in t["label"]]
        atrisk = [t for t in priority if "At-Risk" in t["label"]]

        if weak:
            st.error(f"🚨 **{len(weak)} topic(s) need urgent review right now!**")
        if atrisk:
            st.warning(f"⚠️ **{len(atrisk)} topic(s)** are fading fast.")
        if not weak and not atrisk:
            st.success("✅ No urgent reviews today. You are on top of it!")

        st.markdown("<div class='gold-line'></div>", unsafe_allow_html=True)

        for topic in priority:
            icon = "🔴" if "Weak" in topic["label"] else "⚠️" if "At-Risk" in topic["label"] else "💪"
            with st.expander(
                f"{icon}  {topic['topic_name']}  ·  {topic['subject']}  ·  {topic['retention']}% retained"
            ):
                c1, c2, c3 = st.columns(3)
                c1.metric("Subject",      topic["subject"])
                c2.metric("Retention",    f"{topic['retention']}%")
                c3.metric("Review Count", topic["review_count"])

                st.progress(topic["retention"] / 100)
                st.markdown("**How much do you remember right now?**")

                review_score = st.slider(
                    "Rate your recall (1–10)", 1, 10, 7,
                    key=f"slider_{topic['id']}"
                )
                if st.button("✅ Mark as Reviewed", key=f"btn_{topic['id']}"):
                    add_review(topic["id"], review_score * 10, user_id=user_id)
                    xp = add_xp("review_topic", topic["topic_name"], user_id=user_id)
                    st.success(f"✅ Reviewed! +{xp} XP earned 🌟")
                    st.rerun()

# ════════════════════════════════════════════════════════
# PAGE 5 — QUIZ (Bloom's Taxonomy)
# ════════════════════════════════════════════════════════
elif page == "Quiz":
    from question_generator import (
        generate_questions, calculate_score,
        quiz_to_retention_boost, BLOOMS_LEVELS
    )

    st.markdown("""
    <div class='page-header'>
        <div class='page-title'>AI Quiz</div>
        <div class='page-subtitle'>Bloom's Taxonomy — 6 levels of understanding · Powered by Groq + Llama 3.3</div>
    </div>
    """, unsafe_allow_html=True)

    topics = load_topics()

    if not topics:
        st.info("No topics yet! Click **➕ Add Topic** to add some.")
    else:
        priority     = get_review_priority(topics)
        topic_names  = [f"{t['topic_name']} ({t['subject']}) — {t['retention']}% retained"
                        for t in priority]
        selected_idx = st.selectbox(
            "Select topic to quiz:",
            range(len(topic_names)),
            format_func=lambda i: topic_names[i]
        )
        selected = priority[selected_idx]

        c1, c2, c3 = st.columns(3)
        c1.metric("Topic",     selected["topic_name"])
        c2.metric("Retention", f"{selected['retention']}%")
        c3.metric("Status",    selected["label"])

        st.markdown("<div class='gold-line'></div>", unsafe_allow_html=True)

        # ── Bloom's Level Selector ──────────────────────
        st.markdown("### 🎓 Select Bloom's Taxonomy Level")
        st.caption("Higher levels = deeper understanding test")

        bloom_cols = st.columns(6)

        if "selected_bloom" not in st.session_state:
            st.session_state.selected_bloom = 1

        for i, (key, info) in enumerate(BLOOMS_LEVELS.items()):
            with bloom_cols[i]:
                is_active = st.session_state.selected_bloom == key
                border    = f"2px solid {info['color']}" if is_active else "1px solid #E2E8F0"
                bg        = f"{info['color']}15"        if is_active else "#FFFFFF"
                st.markdown(f"""
                <div style='background:{bg};border:{border};border-radius:10px;
                            padding:10px 6px;text-align:center;margin-bottom:6px;'>
                    <div style='font-size:1.4rem;'>{info['emoji']}</div>
                    <div style='font-size:11px;font-weight:700;color:{info['color']};'>L{key}</div>
                    <div style='font-size:10px;color:#374151;font-weight:600;'>{info['name']}</div>
                    <div style='font-size:9px;color:#64748B;margin-top:2px;'>{info['difficulty']}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Select", key=f"bloom_{key}", use_container_width=True):
                    st.session_state.selected_bloom  = key
                    st.session_state.quiz_questions  = None
                    st.session_state.quiz_answers    = {}
                    st.session_state.quiz_submitted  = False
                    st.session_state.quiz_result     = None
                    st.rerun()

        # Show selected level info
        sel_level = BLOOMS_LEVELS[st.session_state.selected_bloom]
        st.markdown(f"""
        <div style='background:{sel_level['color']}10;border-left:4px solid {sel_level['color']};
                    border-radius:8px;padding:12px 16px;margin:12px 0;'>
            <span style='font-weight:700;color:{sel_level['color']};'>
                {sel_level['emoji']} L{st.session_state.selected_bloom} — {sel_level['name']}
            </span>
            <span style='color:#374151;font-size:0.9rem;margin-left:8px;'>
                {sel_level['description']}
            </span><br/>
            <span style='color:#64748B;font-size:0.82rem;'>
                Keywords: {sel_level['keywords']}
            </span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='gold-line'></div>", unsafe_allow_html=True)

        # ── Session state ──────────────────────────────
        if "quiz_questions" not in st.session_state: st.session_state.quiz_questions = None
        if "quiz_topic_id"  not in st.session_state: st.session_state.quiz_topic_id  = None
        if "quiz_answers"   not in st.session_state: st.session_state.quiz_answers   = {}
        if "quiz_submitted" not in st.session_state: st.session_state.quiz_submitted = False
        if "quiz_result"    not in st.session_state: st.session_state.quiz_result    = None

        # Reset if topic or bloom level changed
        topic_bloom_key = f"{selected['id']}_{st.session_state.selected_bloom}"
        if st.session_state.quiz_topic_id != topic_bloom_key:
            st.session_state.quiz_questions = None
            st.session_state.quiz_answers   = {}
            st.session_state.quiz_submitted = False
            st.session_state.quiz_result    = None
            st.session_state.quiz_topic_id  = topic_bloom_key

        # ── GENERATE ───────────────────────────────────
        if not st.session_state.quiz_questions:
            st.markdown(f"""
            <div style='background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;
                        padding:24px;text-align:center;'>
                <div style='font-size:2rem;margin-bottom:8px;'>🤖</div>
                <div style='font-weight:700;color:#0F1B2D;font-size:1.1rem;'>
                    Generate {sel_level['emoji']} {sel_level['name']} Questions
                </div>
                <div style='color:#1E3A5F;font-size:1rem;font-weight:600;margin:4px 0;'>
                    {selected['topic_name']} · {selected['subject']}
                </div>
                <div style='color:#64748B;font-size:0.85rem;'>
                    3 questions · {sel_level['difficulty']} difficulty · Bloom's L{st.session_state.selected_bloom}
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("")
            if st.button("🚀 Generate Questions", use_container_width=True, key="quiz_generate"):
                with st.spinner(f"🔍 Fetching web content + generating {sel_level['name']} questions..."):
                    questions, context, error = generate_questions(
                        topic_name          = selected["topic_name"],
                        subject             = selected["subject"],
                        bloom_level         = st.session_state.selected_bloom,
                        understanding_score = selected["understanding_score"],
                        retention_pct       = selected["retention"],
                    )
                if error:
                    st.error(f"❌ {error}")
                else:
                    st.session_state.quiz_questions = questions
                    st.session_state.quiz_context   = context
                    st.session_state.quiz_answers   = {}
                    st.session_state.quiz_submitted = False
                    # Show source info
                    if context:
                        st.success(f"✅ {len(questions)} questions generated from web content!")
                    else:
                        st.info(f"✅ {len(questions)} questions generated from AI knowledge!")
                    st.rerun()

        # ── SHOW QUESTIONS ─────────────────────────────
        elif not st.session_state.quiz_submitted:
            ctx      = st.session_state.get("quiz_context")
            src_text = "📡 Web content based" if ctx else "🤖 AI knowledge based"
            n_q      = len(st.session_state.quiz_questions)

            st.markdown(f"""
            <div style='display:flex;align-items:center;justify-content:space-between;
                        margin-bottom:12px;flex-wrap:wrap;gap:8px;'>
                <div style='display:flex;align-items:center;gap:10px;'>
                    <span style='font-size:1.5rem;'>{sel_level['emoji']}</span>
                    <div>
                        <div style='font-weight:700;color:#0F1B2D;font-size:1.1rem;'>
                            {sel_level['name']} Level Quiz — {selected['topic_name']}
                        </div>
                        <div style='color:#64748B;font-size:0.82rem;'>
                            Bloom's L{st.session_state.selected_bloom} · {sel_level['difficulty']} · {n_q} questions
                        </div>
                    </div>
                </div>
                <div style='background:#F1F4F8;border-radius:8px;padding:6px 12px;
                            font-size:11px;color:#64748B;'>
                    {src_text}
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("---")

            for q in st.session_state.quiz_questions:
                st.markdown(f"**Q{q['id']}. {q['question']}**")
                options = q["options"]
                choice  = st.radio(
                    f"Q{q['id']}",
                    options          = list(options.keys()),
                    format_func      = lambda k, opts=options: f"{k}.  {opts[k]}",
                    key              = f"q_{q['id']}",
                    index            = None,
                    label_visibility = "collapsed"
                )
                if choice:
                    st.session_state.quiz_answers[str(q["id"])] = choice
                st.markdown("")

            all_answered = len(st.session_state.quiz_answers) == len(st.session_state.quiz_questions)
            if not all_answered:
                remaining = len(st.session_state.quiz_questions) - len(st.session_state.quiz_answers)
                st.warning(f"⚠️ {remaining} question(s) remaining")

            col_sub, col_new = st.columns(2)
            with col_sub:
                if st.button("✅ Submit Quiz", use_container_width=True, disabled=not all_answered, key="quiz_submit"):
                    result = calculate_score(
                        st.session_state.quiz_questions,
                        st.session_state.quiz_answers
                    )
                    st.session_state.quiz_result    = result
                    st.session_state.quiz_submitted = True
                    st.rerun()
            with col_new:
                if st.button("🔄 New Questions", use_container_width=True, key="quiz_new"):
                    st.session_state.quiz_questions = None
                    st.session_state.quiz_answers   = {}
                    st.session_state.quiz_submitted = False
                    st.rerun()

        # ── RESULTS ────────────────────────────────────
        elif st.session_state.quiz_submitted and st.session_state.quiz_result:
            result  = st.session_state.quiz_result
            score   = result["score_pct"]
            correct = result["correct"]
            total   = result["total"]

            if score >= 80:
                bg_col = "#F0FDF4"; bd_col = "#059669"; emoji = "🎉"
                msg    = f"Excellent {sel_level['name']} level understanding!"
            elif score >= 60:
                bg_col = "#FFFBEB"; bd_col = "#D97706"; emoji = "👍"
                msg    = f"Good! Keep practicing {sel_level['name']} level."
            else:
                bg_col = "#FEF2F2"; bd_col = "#DC2626"; emoji = "📚"
                msg    = f"Need more practice at {sel_level['name']} level."

            st.markdown(f"""
            <div style='background:{bg_col};border:2px solid {bd_col};
                        border-radius:14px;padding:24px;text-align:center;margin-bottom:20px;'>
                <div style='font-size:2.5rem;'>{emoji}</div>
                <div style='font-size:2.5rem;font-weight:700;color:{bd_col};
                            font-family:Georgia,serif;'>{score}%</div>
                <div style='font-size:1rem;color:{bd_col};font-weight:600;'>
                    {correct}/{total} correct · Bloom's L{st.session_state.selected_bloom} — {sel_level['name']}
                </div>
                <div style='font-size:0.85rem;color:{bd_col};opacity:0.8;margin-top:4px;'>
                    {msg}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Update retention
            boost = quiz_to_retention_boost(score, st.session_state.selected_bloom)
            add_review(selected["id"], boost * 10, user_id=user_id)

            # Add XP for quiz completion
            quiz_activity = f"quiz_l{st.session_state.selected_bloom}"
            xp_earned     = add_xp(quiz_activity, selected["topic_name"], user_id=user_id)
            # Bonus XP for perfect score
            if score == 100:
                bonus_xp  = add_xp("quiz_100_bonus", "Perfect score!", user_id=user_id)
                xp_earned += bonus_xp
                st.success(f"✅ Retention updated! +{xp_earned} XP earned (including perfect score bonus!) 🌟")
            else:
                st.success(f"✅ Retention updated! +{xp_earned} XP earned! Bloom's L{st.session_state.selected_bloom} recorded.")

            # Update best bloom level achieved
            if score >= 70:
                current_best = st.session_state.get("best_bloom_achieved", 1)
                new_best     = min(6, st.session_state.selected_bloom + 1)
                if new_best > current_best:
                    st.session_state.best_bloom_achieved = new_best
                    st.balloons()
                    st.success(f"🎉 Level Up! You reached Bloom's L{new_best} — {BLOOMS_LEVELS[new_best]['name']}!")

            # Detailed results
            st.markdown("### 📊 Question Analysis")
            for r in result["results"]:
                icon = "✅" if r["is_correct"] else "❌"
                with st.expander(f"{icon} Q{r['id']}. {r['question']}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        ans_text = r['options'].get(r['user_answer'], 'Not answered')
                        color    = "#059669" if r["is_correct"] else "#DC2626"
                        st.markdown(
                            f"**Your answer:** <span style='color:{color}'>{r['user_answer']}. {ans_text}</span>",
                            unsafe_allow_html=True
                        )
                    with c2:
                        st.markdown(f"**Correct:** {r['correct_ans']}. {r['options'].get(r['correct_ans'], '')}")
                    if r.get("bloom_keyword"):
                        st.caption(f"Bloom's keyword: {r['bloom_keyword']}")
                    if r["explanation"]:
                        st.info(f"💡 {r['explanation']}")

            # Suggest next level
            next_level_num = min(st.session_state.selected_bloom + 1, 6)
            next_info      = BLOOMS_LEVELS[next_level_num]

            if score >= 70 and next_level_num != st.session_state.selected_bloom:
                st.markdown(f"""
                <div style='background:#F0F9FF;border:1px solid #0891B2;border-radius:10px;
                            padding:14px 18px;margin:16px 0;'>
                    <span style='font-weight:700;color:#0891B2;'>🎯 Ready for next level?</span>
                    <span style='color:#374151;'> Try
                        {next_info['emoji']} L{next_level_num} — {next_info['name']}
                    </span>
                </div>
                """, unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔄 Try Again", use_container_width=True, key="quiz_try_again"):
                    st.session_state.quiz_questions = None
                    st.session_state.quiz_answers   = {}
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_result    = None
                    st.rerun()
            with col2:
                if score >= 70 and next_level_num != st.session_state.selected_bloom:
                    if st.button(f"⬆️ Try L{next_level_num}", use_container_width=True, key="quiz_next_level"):
                        st.session_state.selected_bloom  = next_level_num
                        st.session_state.quiz_questions  = None
                        st.session_state.quiz_answers    = {}
                        st.session_state.quiz_submitted  = False
                        st.session_state.quiz_result     = None
                        st.rerun()
            with col3:
                if st.button("📋 Review List", use_container_width=True, key="quiz_review_list"):
                    st.session_state.page = "Review List"
                    st.rerun()

# ════════════════════════════════════════════════════════
# PAGE 6 — LEADERBOARD
# ════════════════════════════════════════════════════════
elif page == "Leaderboard":

    st.markdown("""
    <div class='page-header'>
        <div class='page-title'>🏆 Leaderboard</div>
        <div class='page-subtitle'>Your XP ranking · Subject performance · League progress</div>
    </div>
    """, unsafe_allow_html=True)

    topics     = load_topics()
    total_xp   = get_total_xp(user_id=user_id)
    today_xp   = get_today_xp(user_id=user_id)
    league     = get_league(total_xp)
    streak     = get_streak(user_id=user_id)
    xp_history = get_xp_history(7, user_id=user_id)

    _, league_name, league_color = league

    # ── Next league info ──────────────────────────────
    next_league    = None
    xp_to_next     = 0
    for i, (thresh, name, color) in enumerate(LEAGUE_THRESHOLDS):
        if total_xp < thresh:
            next_league = (thresh, name, color)
            xp_to_next  = thresh - total_xp
            break

    # ── LEAGUE CARD ───────────────────────────────────
    progress_pct = 0
    if next_league:
        cur_thresh   = league[0]
        nxt_thresh   = next_league[0]
        progress_pct = min(100, int(((total_xp - cur_thresh) / (nxt_thresh - cur_thresh)) * 100))

    league_color_fade = league_color + "99"

    # Build progress bar HTML separately to avoid nested f-string issues
    if next_league:
        next_league_name = next_league[1]
        progress_html = (
            "<div style='margin-top:16px;'>"
            "<div style='display:flex;justify-content:space-between;margin-bottom:6px;'>"
            "<span style='color:rgba(255,255,255,0.5);font-size:11px;'>" + league_name + "</span>"
            "<span style='color:rgba(255,255,255,0.5);font-size:11px;'>" + next_league_name + "</span>"
            "</div>"
            "<div style='background:rgba(255,255,255,0.1);border-radius:999px;height:8px;'>"
            "<div style='background:linear-gradient(90deg," + league_color + "," + league_color_fade + ");"
            "width:" + str(progress_pct) + "%;height:8px;border-radius:999px;transition:width 0.5s;'></div>"
            "</div>"
            "<div style='color:rgba(255,255,255,0.4);font-size:10px;margin-top:4px;text-align:right;'>"
            + str(progress_pct) + "% to next league</div>"
            "</div>"
        )
        next_text = "Next: " + next_league_name + " in " + str(xp_to_next) + " XP"
    else:
        progress_html = ""
        next_text     = "Maximum League Reached! 🏆"

    st.markdown(
        "<div style='background:linear-gradient(135deg,#0F1B2D,#1E3A5F);"
        "border-radius:16px;padding:24px 28px;margin-bottom:24px;"
        "border:1px solid rgba(201,168,76,0.3);'>"
        "<div style='display:flex;align-items:center;"
        "justify-content:space-between;flex-wrap:wrap;gap:16px;'>"
        "<div>"
        "<div style='color:rgba(255,255,255,0.45);font-size:10px;"
        "text-transform:uppercase;letter-spacing:0.12em;"
        "font-weight:600;margin-bottom:6px;'>Current League</div>"
        "<div style='font-size:2rem;font-weight:700;color:" + league_color + ";"
        "font-family:Georgia,serif;'>" + league_name + "</div>"
        "<div style='color:rgba(255,255,255,0.5);font-size:0.85rem;margin-top:4px;'>"
        + next_text + "</div>"
        "</div>"
        "<div style='display:flex;gap:28px;'>"
        "<div style='text-align:center;'>"
        "<div style='color:#C9A84C;font-size:2rem;font-weight:700;"
        "font-family:Georgia,serif;'>" + str(total_xp) + "</div>"
        "<div style='color:rgba(255,255,255,0.4);font-size:10px;"
        "text-transform:uppercase;letter-spacing:0.1em;'>Total XP</div>"
        "</div>"
        "<div style='text-align:center;'>"
        "<div style='color:#22C55E;font-size:2rem;font-weight:700;"
        "font-family:Georgia,serif;'>+" + str(today_xp) + "</div>"
        "<div style='color:rgba(255,255,255,0.4);font-size:10px;"
        "text-transform:uppercase;letter-spacing:0.1em;'>Today XP</div>"
        "</div>"
        "<div style='text-align:center;'>"
        "<div style='color:#F59E0B;font-size:2rem;font-weight:700;"
        "font-family:Georgia,serif;'>🔥" + str(streak) + "</div>"
        "<div style='color:rgba(255,255,255,0.4);font-size:10px;"
        "text-transform:uppercase;letter-spacing:0.1em;'>Streak</div>"
        "</div>"
        "</div>"
        "</div>"
        + progress_html +
        "</div>",
        unsafe_allow_html=True
    )

    # ── ALL LEAGUES DISPLAY ───────────────────────────
    st.markdown("### 🎯 League Tiers")
    league_cols = st.columns(5)
    league_info = [
        ("🥉", "Bronze",  "#CD7F32", "0",    "100"),
        ("🥈", "Silver",  "#94A3B8", "101",  "300"),
        ("🥇", "Gold",    "#C9A84C", "301",  "600"),
        ("💎", "Diamond", "#60A5FA", "601",  "1000"),
        ("🏆", "Legend",  "#7C3AED", "1000+", "∞"),
    ]
    for i, (icon, name, color, low, high) in enumerate(league_info):
        is_current = league_name.endswith(name)
        with league_cols[i]:
            st.markdown(f"""
            <div style='background:{"linear-gradient(135deg,"+color+"22,"+color+"11)" if is_current else "#FFFFFF"};
                        border:{"2px solid "+color if is_current else "1px solid #E2E8F0"};
                        border-radius:12px;padding:14px 8px;text-align:center;
                        box-shadow:{"0 4px 12px "+color+"44" if is_current else "none"};'>
                <div style='font-size:1.8rem;'>{icon}</div>
                <div style='font-weight:700;color:{color};font-size:0.9rem;'>{name}</div>
                <div style='color:#64748B;font-size:10px;margin-top:4px;'>{low}–{high} XP</div>
                {f"<div style='color:{color};font-size:10px;font-weight:600;'>← You are here</div>" if is_current else ""}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div class='gold-line'></div>", unsafe_allow_html=True)

    # ── SUBJECT LEADERBOARD ───────────────────────────
    st.markdown("### 📊 Subject Ranking — Who's on Top?")

    if not topics:
        st.info("Add some topics to see subject rankings!")
    else:
        priority    = get_review_priority(topics)
        subject_xp  = get_xp_by_subject(topics, user_id=user_id)

        # Build subject stats
        subject_stats = {}
        for t in priority:
            s = t["subject"]
            if s not in subject_stats:
                subject_stats[s] = {
                    "topics":    0,
                    "retention": [],
                    "xp":        subject_xp.get(s, 0),
                }
            subject_stats[s]["topics"]    += 1
            subject_stats[s]["retention"].append(t["retention"])

        # Calculate averages and sort by XP
        ranked = []
        for subj, data in subject_stats.items():
            avg_ret = int(sum(data["retention"]) / len(data["retention"]))
            ranked.append({
                "subject":   subj,
                "avg_ret":   avg_ret,
                "topics":    data["topics"],
                "xp":        data["xp"],
            })
        ranked = sorted(ranked, key=lambda x: x["xp"], reverse=True)

        # Medal icons
        medals = ["🥇", "🥈", "🥉"]

        for i, item in enumerate(ranked):
            medal     = medals[i] if i < 3 else f"{i+1}."
            ret       = item["avg_ret"]
            ret_color = "#059669" if ret >= 70 else "#D97706" if ret >= 40 else "#DC2626"
            bar_w     = max(5, ret)

            ret_color_fade = ret_color + "88"
            st.markdown(f"""
            <div style='background:#FFFFFF;border:1px solid #E2E8F0;
                        border-radius:12px;padding:16px 20px;margin-bottom:10px;
                        box-shadow:0 1px 4px rgba(15,27,45,0.05);
                        {"border-left:4px solid #C9A84C;" if i == 0 else ""}'>
                <div style='display:flex;align-items:center;
                            justify-content:space-between;flex-wrap:wrap;gap:12px;'>
                    <div style='display:flex;align-items:center;gap:14px;'>
                        <span style='font-size:1.8rem;'>{medal}</span>
                        <div>
                            <div style='font-weight:700;color:#0F1B2D;font-size:1rem;'>
                                {item["subject"]}
                            </div>
                            <div style='color:#64748B;font-size:12px;'>
                                {item["topics"]} topic{"s" if item["topics"] != 1 else ""}
                            </div>
                        </div>
                    </div>
                    <div style='display:flex;align-items:center;gap:24px;'>
                        <div style='text-align:center;'>
                            <div style='font-weight:700;color:{ret_color};font-size:1.2rem;
                                        font-family:Georgia,serif;'>{ret}%</div>
                            <div style='color:#64748B;font-size:10px;
                                        text-transform:uppercase;'>Retention</div>
                        </div>
                        <div style='text-align:center;'>
                            <div style='font-weight:700;color:#C9A84C;font-size:1.2rem;
                                        font-family:Georgia,serif;'>{item["xp"]}</div>
                            <div style='color:#64748B;font-size:10px;
                                        text-transform:uppercase;'>XP</div>
                        </div>
                    </div>
                </div>
                <div style='margin-top:10px;background:#F1F4F8;
                            border-radius:999px;height:6px;'>
                    <div style='background:linear-gradient(90deg,{ret_color},{ret_color_fade});
                                width:{bar_w}%;height:6px;border-radius:999px;'></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── XP CHART ─────────────────────────────────
        st.markdown("### 📈 XP Earned — Last 7 Days")
        if xp_history:
            df_xp = pd.DataFrame(xp_history, columns=["Date", "XP"])
            df_xp = df_xp.sort_values("Date")
            fig = px.bar(
                df_xp, x="Date", y="XP",
                color_discrete_sequence=["#1E3A5F"]
            )
            fig.update_layout(
                height      = 280,
                paper_bgcolor = "rgba(0,0,0,0)",
                plot_bgcolor  = "#FFFFFF",
                font          = dict(color="#64748B", size=11),
                xaxis         = dict(gridcolor="#F1F4F8"),
                yaxis         = dict(gridcolor="#F1F4F8"),
                margin        = dict(t=20, b=40, l=40, r=20),
                showlegend    = False,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Complete activities to see your XP history!")

        # ── XP GUIDE ─────────────────────────────────
        st.markdown("### 💡 How to Earn XP")
        xp_guide = [
            ("📖 Add a Topic",           "+10 XP"),
            ("📋 Review a Topic",        "+15 XP"),
            ("🧪 Quiz L1 (Remember)",    "+20 XP"),
            ("🧪 Quiz L2 (Understand)",  "+25 XP"),
            ("🧪 Quiz L3 (Apply)",       "+30 XP"),
            ("🧪 Quiz L4 (Analyze)",     "+35 XP"),
            ("🧪 Quiz L5 (Evaluate)",    "+40 XP"),
            ("🧪 Quiz L6 (Create)",      "+50 XP"),
            ("💯 Perfect Quiz Score",    "+10 XP bonus"),
            ("🔥 Daily Streak",          "+5 XP/day"),
        ]
        cols = st.columns(2)
        for i, (act, xp) in enumerate(xp_guide):
            with cols[i % 2]:
                st.markdown(f"""
                <div style='background:#F8FAFC;border:1px solid #E2E8F0;
                            border-radius:8px;padding:10px 14px;margin-bottom:8px;
                            display:flex;justify-content:space-between;align-items:center;'>
                    <span style='color:#374151;font-size:0.88rem;'>{act}</span>
                    <span style='color:#C9A84C;font-weight:700;font-size:0.9rem;'>{xp}</span>
                </div>
                """, unsafe_allow_html=True)