import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from database import (
    init_db, add_topic, get_all_topics, add_review, delete_topic,
    init_streak_table, mark_today_studied,
    get_streak, get_total_study_days,
    init_xp_table, add_xp, get_total_xp,
    get_today_xp, get_xp_by_subject,
    get_league, get_xp_history, LEAGUE_THRESHOLDS,
    sign_up, sign_in, sign_out, get_supabase,
    submit_feedback, save_quiz_mistakes, get_mistake_book,
    snooze_mistake, mark_mistake_mastered, delete_mistake
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
.block-container {
    padding-top: 0 !important;
    padding-bottom: 2rem !important;
}
section.main > div {
    padding-top: 0 !important;
}

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
    min-height: 76px;
    box-shadow: 0 2px 16px rgba(15,27,45,0.18);
    position: sticky;
    top: 0;
    z-index: 999;
}
.nav-brand-shell {
    display: flex;
    align-items: center;
    gap: 14px;
}
.nav-brand-mark {
    width: 46px;
    height: 46px;
    border-radius: 14px;
    background: linear-gradient(135deg, rgba(201,168,76,0.25), rgba(255,255,255,0.08));
    border: 1px solid rgba(201,168,76,0.35);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.4rem;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.05);
}
.nav-brand-copy {
    display: flex;
    flex-direction: column;
    gap: 2px;
}
.nav-brand {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 1.5rem;
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
.nav-meta {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
}
.nav-context-chip {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 999px;
    padding: 6px 12px;
    color: rgba(255,255,255,0.72);
    font-size: 0.78rem;
}
.nav-context-sub {
    color: rgba(255,255,255,0.42);
    font-size: 11px;
}
.profile-anchor {
    margin-top: -128px;
    margin-bottom: -46px;
    position: relative;
    z-index: 1000;
}
.profile-card {
    background: transparent;
    border: none;
    box-shadow: none;
    padding: 0;
}
.profile-mini {
    display: flex;
    align-items: center;
    gap: 10px;
}
.profile-avatar {
    width: 42px;
    height: 42px;
    border-radius: 50%;
    background: linear-gradient(135deg, #0F1B2D, #2D5A8E);
    color: #FFFFFF;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.95rem;
    border: 2px solid rgba(201,168,76,0.45);
}
.profile-mini-copy {
    min-width: 0;
}
.profile-mini-label {
    color: #64748B;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 600;
}
.profile-mini-email {
    color: #0F1B2D;
    font-size: 0.82rem;
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 180px;
}
.profile-popover-trigger {
    display: flex;
    align-items: center;
    justify-content: flex-end;
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
    background: #FFFFFF !important;
}
details summary:hover,
details[open] summary,
details[open] summary:hover {
    color: #0F1B2D !important;
    background: #FFFFFF !important;
}
details summary * ,
details[open] summary * {
    color: #0F1B2D !important;
}
details summary::marker,
details summary::-webkit-details-marker {
    color: #64748B !important;
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
input[type="radio"] { accent-color: #64748B !important; }
[data-testid="stRadio"] label {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
[data-testid="stRadio"] label:has(input:checked) {
    background: transparent !important;
    color: #0F1B2D !important;
}

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
        margin: 0 -1rem 0 -1rem;
        text-align: center;
        position: relative;
        overflow: hidden;
        border-bottom-left-radius: 22px;
        border-bottom-right-radius: 22px;
        box-shadow: 0 24px 60px rgba(15,27,45,0.18);
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
    .landing-hero::after {
        content: '';
        position: absolute;
        inset: auto -10% -35% auto;
        width: 380px;
        height: 380px;
        border-radius: 50%;
        background:
            radial-gradient(circle, rgba(201,168,76,0.12) 0%, rgba(201,168,76,0.04) 38%, transparent 68%);
        filter: blur(10px);
        pointer-events: none;
    }
    .hero-grid {
        position: absolute;
        inset: 0;
        background-image:
            linear-gradient(rgba(255,255,255,0.035) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.035) 1px, transparent 1px);
        background-size: 42px 42px;
        mask-image: linear-gradient(to bottom, rgba(0,0,0,0.55), transparent 82%);
        pointer-events: none;
    }
    .hero-content {
        position: relative;
        z-index: 2;
    }
    @keyframes pulse-bg {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }
    .hero-badge {
        display: inline-block;
        background: rgba(201,168,76,0.12);
        border: 1px solid rgba(201,168,76,0.32);
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
        text-shadow: 0 10px 30px rgba(0,0,0,0.22);
    }
    .hero-title span { color: #C9A84C; }
    .hero-tagline {
        font-size: 1.25rem;
        color: rgba(255,255,255,0.72);
        max-width: 560px;
        margin: 0 auto 40px;
        line-height: 1.6;
    }
    .hero-actions {
        display: flex;
        justify-content: center;
        gap: 14px;
        flex-wrap: wrap;
        margin-top: 8px;
    }
    .hero-pill {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 999px;
        padding: 10px 16px;
        color: rgba(255,255,255,0.72);
        font-size: 0.84rem;
        backdrop-filter: blur(8px);
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
        position: relative;
        overflow: hidden;
    }
    .feature-card::after {
        content: '';
        position: absolute;
        inset: auto -30px -30px auto;
        width: 120px;
        height: 120px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(15,27,45,0.05), transparent 70%);
        pointer-events: none;
    }
    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 14px 32px rgba(15,27,45,0.10);
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
        position: relative;
        overflow: hidden;
        box-shadow: 0 20px 50px rgba(15,27,45,0.14);
    }
    .cta-section::before {
        content: '';
        position: absolute;
        inset: 0;
        background:
            radial-gradient(circle at 20% 20%, rgba(201,168,76,0.12), transparent 30%),
            radial-gradient(circle at 80% 80%, rgba(255,255,255,0.08), transparent 22%);
        pointer-events: none;
    }
    .footer {
        text-align: center;
        padding: 32px;
        color: #94A3B8;
        font-size: 13px;
        border-top: 1px solid #E2E8F0;
        margin-top: 40px;
    }
    @media (max-width: 768px) {
        .landing-hero {
            padding: 64px 22px 44px;
            border-bottom-left-radius: 18px;
            border-bottom-right-radius: 18px;
        }
        .hero-title {
            font-size: 2.8rem;
        }
        .hero-tagline {
            font-size: 1rem;
            margin-bottom: 28px;
        }
        .hero-stats {
            gap: 24px;
            padding-top: 28px;
            margin-top: 32px;
        }
        .cta-section {
            padding: 40px 24px;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    # ── HERO ─────────────────────────────────────────────
    st.markdown("""
    <div class='landing-hero'>
        <div class='hero-grid'></div>
        <div class='hero-content'>
            <div class='hero-badge'>🧠 AI-Powered Memory Science</div>
            <div class='hero-title'>Never Forget<br>What You <span>Learn</span></div>
            <div class='hero-tagline'>
                Smriti uses Machine Learning to predict exactly when you'll forget —
                and reminds you to review before it happens.
            </div>
            <div class='hero-actions'>
                <div class='hero-pill'>13M+ learning records behind the model</div>
                <div class='hero-pill'>Bloom's Taxonomy quizzes with real depth</div>
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
    review_now  = weak[:3]
    review_soon = atrisk[:2]
    recent_topics = sorted(
        topics,
        key=lambda t: str(t.get("date_learned") or ""),
        reverse=True
    )[:4]

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

    # ── TODAY'S STUDY PLAN ───────────────────────────────
    st.markdown("---")
    st.markdown("### 📅 Today's Study Plan")

    plan_col_l, plan_col_r = st.columns([1.4, 1])

    with plan_col_l:
        total_plan_items = len(review_now) + len(review_soon)
        estimated_minutes = max(10, total_plan_items * 8)

        st.markdown(f"""
        <div style='background:#FFFFFF;border:1px solid #E2E8F0;border-radius:14px;
                    padding:20px 22px;box-shadow:0 2px 8px rgba(15,27,45,0.05);'>
            <div style='display:flex;justify-content:space-between;align-items:center;
                        gap:12px;flex-wrap:wrap;margin-bottom:16px;'>
                <div>
                    <div style='font-size:10px;color:#64748B;text-transform:uppercase;
                                letter-spacing:0.12em;font-weight:600;margin-bottom:6px;'>
                        Smart Revision Queue
                    </div>
                    <div style='font-weight:700;color:#0F1B2D;font-size:1.05rem;'>
                        {total_plan_items if total_plan_items else len(priority[:3])} topic(s) worth touching today
                    </div>
                </div>
                <div style='background:#EEF2FF;border:1px solid #C7D2FE;border-radius:999px;
                            padding:8px 12px;color:#3730A3;font-size:0.8rem;font-weight:600;'>
                    ~ {estimated_minutes} min study block
                </div>
            </div>
        """, unsafe_allow_html=True)

        if review_now:
            st.markdown("**Review Now**")
            for idx, topic in enumerate(review_now, start=1):
                st.markdown(f"""
                <div style='background:#FEF2F2;border:1px solid #FECACA;border-radius:10px;
                            padding:12px 14px;margin-bottom:10px;'>
                    <div style='display:flex;justify-content:space-between;gap:10px;align-items:center;'>
                        <div>
                            <div style='font-weight:700;color:#991B1B;font-size:0.92rem;'>
                                {idx}. {topic["topic_name"]}
                            </div>
                            <div style='color:#7F1D1D;font-size:0.8rem;'>
                                {topic["subject"]} · {topic["retention"]}% retained · needs rescue today
                            </div>
                        </div>
                        <div style='color:#DC2626;font-weight:700;font-size:0.9rem;'>Urgent</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        if review_soon:
            st.markdown("**Review Soon**")
            for topic in review_soon:
                st.markdown(f"""
                <div style='background:#FFFBEB;border:1px solid #FDE68A;border-radius:10px;
                            padding:12px 14px;margin-bottom:10px;'>
                    <div style='display:flex;justify-content:space-between;gap:10px;align-items:center;'>
                        <div>
                            <div style='font-weight:700;color:#92400E;font-size:0.92rem;'>
                                {topic["topic_name"]}
                            </div>
                            <div style='color:#A16207;font-size:0.8rem;'>
                                {topic["subject"]} · {topic["retention"]}% retained · revise before it drops further
                            </div>
                        </div>
                        <div style='color:#D97706;font-weight:700;font-size:0.9rem;'>Soon</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        if not review_now and not review_soon:
            strongest_topic = max(priority, key=lambda x: x["retention"])
            st.markdown(f"""
            <div style='background:#F0FDF4;border:1px solid #BBF7D0;border-radius:10px;
                        padding:14px 16px;margin-bottom:8px;'>
                <div style='font-weight:700;color:#166534;font-size:0.96rem;'>
                    Everything looks stable today
                </div>
                <div style='color:#15803D;font-size:0.84rem;margin-top:4px;line-height:1.6;'>
                    Your best-held topic is <strong>{strongest_topic["topic_name"]}</strong> at
                    {strongest_topic["retention"]}% retention. This is a great day to add a fresh topic
                    or attempt a higher Bloom's level quiz.
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with plan_col_r:
        strongest_topic = max(priority, key=lambda x: x["retention"])
        weakest_topic   = min(priority, key=lambda x: x["retention"])
        avg_reviews     = round(sum(t["review_count"] for t in topics) / len(topics), 1) if topics else 0

        st.markdown(f"""
        <div style='background:#FFFFFF;border:1px solid #E2E8F0;border-radius:14px;
                    padding:20px;box-shadow:0 2px 8px rgba(15,27,45,0.05);height:100%;'>
            <div style='font-size:10px;color:#64748B;text-transform:uppercase;
                        letter-spacing:0.12em;font-weight:600;margin-bottom:10px;'>
                Snapshot
            </div>
            <div style='background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;
                        padding:14px 16px;margin-bottom:12px;'>
                <div style='color:#64748B;font-size:11px;text-transform:uppercase;letter-spacing:0.08em;'>
                    Best Held Topic
                </div>
                <div style='font-weight:700;color:#0F1B2D;font-size:1rem;margin-top:4px;'>
                    {strongest_topic["topic_name"]}
                </div>
                <div style='color:#059669;font-size:0.84rem;margin-top:4px;'>
                    {strongest_topic["retention"]}% retained · {strongest_topic["subject"]}
                </div>
            </div>
            <div style='background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;
                        padding:14px 16px;margin-bottom:12px;'>
                <div style='color:#64748B;font-size:11px;text-transform:uppercase;letter-spacing:0.08em;'>
                    Needs Rescue First
                </div>
                <div style='font-weight:700;color:#0F1B2D;font-size:1rem;margin-top:4px;'>
                    {weakest_topic["topic_name"]}
                </div>
                <div style='color:#DC2626;font-size:0.84rem;margin-top:4px;'>
                    {weakest_topic["retention"]}% retained · {weakest_topic["subject"]}
                </div>
            </div>
            <div style='display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px;'>
                <div style='background:#EEF2FF;border-radius:10px;padding:12px;text-align:center;'>
                    <div style='font-family:Georgia,serif;font-size:1.5rem;font-weight:700;color:#3730A3;'>
                        {len(set(t["subject"] for t in topics))}
                    </div>
                    <div style='color:#6366F1;font-size:11px;text-transform:uppercase;'>Subjects</div>
                </div>
                <div style='background:#ECFDF5;border-radius:10px;padding:12px;text-align:center;'>
                    <div style='font-family:Georgia,serif;font-size:1.5rem;font-weight:700;color:#047857;'>
                        {avg_reviews}
                    </div>
                    <div style='color:#059669;font-size:11px;text-transform:uppercase;'>Avg Reviews</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── RECENT TOPICS + SUBJECT MOMENTUM ────────────────
    st.markdown("---")
    recent_col, momentum_col = st.columns([1.1, 1.2])

    with recent_col:
        st.markdown("#### 🆕 Recently Added Topics")
        for topic in recent_topics:
            ret = next((item["retention"] for item in priority if item["id"] == topic["id"]), 0)
            badge_bg = "#F0FDF4" if ret >= 70 else "#FFFBEB" if ret >= 40 else "#FEF2F2"
            badge_fg = "#059669" if ret >= 70 else "#D97706" if ret >= 40 else "#DC2626"
            st.markdown(f"""
            <div style='background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;
                        padding:14px 16px;margin-bottom:10px;box-shadow:0 1px 4px rgba(15,27,45,0.05);'>
                <div style='display:flex;justify-content:space-between;gap:12px;align-items:flex-start;'>
                    <div>
                        <div style='font-weight:700;color:#0F1B2D;font-size:0.94rem;'>
                            {topic["topic_name"]}
                        </div>
                        <div style='color:#64748B;font-size:0.8rem;margin-top:4px;'>
                            {topic["subject"]} · learned on {topic["date_learned"]} · understanding {topic["understanding_score"]}/10
                        </div>
                    </div>
                    <div style='background:{badge_bg};color:{badge_fg};border-radius:999px;
                                padding:6px 10px;font-size:0.78rem;font-weight:700;white-space:nowrap;'>
                        {ret}% retained
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with momentum_col:
        st.markdown("#### 📈 Subject Momentum")
        subject_stats = {}
        for item in priority:
            subject_stats.setdefault(item["subject"], {"count": 0, "retentions": []})
            subject_stats[item["subject"]]["count"] += 1
            subject_stats[item["subject"]]["retentions"].append(item["retention"])

        ranked_subjects = sorted(
            [
                {
                    "subject": subject,
                    "count": stats["count"],
                    "avg_ret": int(sum(stats["retentions"]) / len(stats["retentions"])),
                }
                for subject, stats in subject_stats.items()
            ],
            key=lambda x: x["avg_ret"],
            reverse=True
        )[:4]

        for item in ranked_subjects:
            bar_color = "#059669" if item["avg_ret"] >= 70 else "#D97706" if item["avg_ret"] >= 40 else "#DC2626"
            bar_fade = "#BBF7D0" if item["avg_ret"] >= 70 else "#FDE68A" if item["avg_ret"] >= 40 else "#FECACA"
            st.markdown(f"""
            <div style='background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;
                        padding:14px 16px;margin-bottom:10px;box-shadow:0 1px 4px rgba(15,27,45,0.05);'>
                <div style='display:flex;justify-content:space-between;align-items:center;gap:10px;'>
                    <div>
                        <div style='font-weight:700;color:#0F1B2D;font-size:0.92rem;'>{item["subject"]}</div>
                        <div style='color:#64748B;font-size:0.8rem;margin-top:4px;'>
                            {item["count"]} topic{"s" if item["count"] != 1 else ""} tracked
                        </div>
                    </div>
                    <div style='font-weight:700;color:{bar_color};font-size:1rem;'>{item["avg_ret"]}%</div>
                </div>
                <div style='margin-top:10px;background:#F1F4F8;border-radius:999px;height:8px;'>
                    <div style='background:linear-gradient(90deg,{bar_color},{bar_fade});
                                width:{max(6, item["avg_ret"])}%;height:8px;border-radius:999px;'></div>
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
if "delete_confirm_topic_id" not in st.session_state:
    st.session_state.delete_confirm_topic_id = None

# ── TOP NAVIGATION ────────────────────────────────────────
user_email = st.session_state.user.email
def navigate_to(page_name):
    if st.session_state.page != page_name:
        st.session_state.page = page_name
        st.rerun()

# Compact sticky nav
nav_topics_raw = get_all_topics(user_id=user_id)
nav_topics = [{
    "id": r[0], "topic_name": r[1], "subject": r[2],
    "understanding_score": r[3], "date_learned": r[4],
    "last_reviewed": r[5], "review_count": r[6] if r[6] else 0
} for r in nav_topics_raw]
nav_priority = get_review_priority(nav_topics) if nav_topics else []
nav_review_count = len([t for t in nav_priority if "Weak" in t["label"] or "At-Risk" in t["label"]])
nav_mistakes, _nav_mistake_error = get_mistake_book(user_id=user_id)
nav_mistake_count = len(nav_mistakes) if nav_mistakes else 0
current_page = st.session_state.page
page_titles = {
    "Home": "Home",
    "Dashboard": "Dashboard",
    "Add Topic": "Add Topic",
    "Review List": "Review List",
    "Quiz": "Quiz",
    "Mistake Book": "Mistake Book",
    "Progress Report": "Progress Report",
    "Leaderboard": "Leaderboard",
    "Feedback": "Feedback",
}
current_page_title = page_titles.get(current_page, current_page)
user_summary = st.session_state.get("user_summary", "Student")
email_local = user_email.split("@")[0] if user_email else "User"
initial_parts = [part[0].upper() for part in email_local.replace(".", " ").replace("_", " ").split() if part]
profile_initials = "".join(initial_parts[:2]) if initial_parts else "SM"

st.markdown(f"""
<div class='nav-wrapper'>
    <div class='nav-brand-shell'>
        <div class='nav-brand-mark'>🧠</div>
        <div class='nav-brand-copy'>
            <div class='nav-brand'>
                <span>Smriti</span>
                <span class='nav-tagline'>Memory Intelligence</span>
            </div>
            <div class='nav-meta'>
                <div class='nav-context-chip'>Now Viewing: {current_page_title}</div>
                <div class='nav-context-sub'>Built for smarter revision, stronger recall, and daily momentum</div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.compact-nav {
    position: sticky;
    top: 60px;
    z-index: 998;
    background: rgba(241,244,248,0.92);
    backdrop-filter: blur(10px);
    padding: 10px 0 14px;
    margin-bottom: 12px;
}
.compact-nav-shell {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 14px 16px;
    box-shadow: 0 8px 28px rgba(15,27,45,0.08);
}
.compact-nav-label {
    font-size: 10px;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-weight: 600;
    margin-bottom: 4px;
}
.compact-nav-page {
    font-family: Georgia, serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: #0F1B2D;
}
</style>
""", unsafe_allow_html=True)
more_options = [
    "More",
    f"Review ({nav_review_count})",
    "Dashboard",
    f"Mistakes ({nav_mistake_count})",
    "Leaderboard",
    "Feedback",
]
more_to_page = {
    f"Review ({nav_review_count})": "Review List",
    "Dashboard": "Dashboard",
    f"Mistakes ({nav_mistake_count})": "Mistake Book",
    "Leaderboard": "Leaderboard",
    "Feedback": "Feedback",
}
current_more_label = next(
    (label for label, page_name in more_to_page.items() if page_name == current_page),
    "More"
)

profile_spacer, profile_col = st.columns([4.7, 1.45])
with profile_col:
    st.markdown("<div class='profile-anchor'><div class='profile-card'>", unsafe_allow_html=True)
    if hasattr(st, "popover"):
        st.markdown("<div class='profile-popover-trigger'>", unsafe_allow_html=True)
        with st.popover(f"{profile_initials}  Account", use_container_width=True):
            st.markdown(f"""
            <div class='profile-mini' style='margin-bottom:14px;'>
                <div class='profile-avatar'>{profile_initials}</div>
                <div class='profile-mini-copy'>
                    <div class='profile-mini-label'>Account</div>
                    <div class='profile-mini-email'>{user_email}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.caption(f"{user_summary} · Currently on {current_page_title}")
            if st.button("Logout", use_container_width=True, key="profile_logout"):
                sign_out()
                st.session_state.user = None
                st.session_state.clear()
                st.rerun()
    else:
        with st.expander("Account", expanded=False):
            st.markdown(f"**{user_email}**")
            st.caption(f"{user_summary} · Currently on {current_page_title}")
            if st.button("Logout", use_container_width=True, key="profile_logout_fallback"):
                sign_out()
                st.session_state.user = None
                st.session_state.clear()
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

st.markdown("<div class='compact-nav'><div class='compact-nav-shell'>", unsafe_allow_html=True)
nav_meta_col, nav_tab1, nav_tab2, nav_tab3, nav_tab4, nav_more_col = st.columns([1.4, 1, 1.05, 1, 1, 1.2])
with nav_meta_col:
    st.markdown(
        f"""
        <div class='compact-nav-label'>Smriti</div>
        <div class='compact-nav-page'>{page_titles.get(current_page, current_page)}</div>
        """,
        unsafe_allow_html=True
    )
with nav_tab1:
    home_label = "Home •" if current_page == "Home" else "Home"
    if st.button(home_label, use_container_width=True, key="nav_home"):
        navigate_to("Home")
with nav_tab2:
    add_label = "Add Topic •" if current_page == "Add Topic" else "Add Topic"
    if st.button(add_label, use_container_width=True, key="nav_add"):
        navigate_to("Add Topic")
with nav_tab3:
    quiz_label = "Quiz •" if current_page == "Quiz" else "Quiz"
    if st.button(quiz_label, use_container_width=True, key="nav_quiz"):
        navigate_to("Quiz")
with nav_tab4:
    report_label = "Report •" if current_page == "Progress Report" else "Report"
    if st.button(report_label, use_container_width=True, key="nav_report"):
        navigate_to("Progress Report")
with nav_more_col:
    selected_more = st.selectbox(
        "More",
        options=more_options,
        index=more_options.index(current_more_label) if current_more_label in more_options else 0,
        key="nav_more_select",
        label_visibility="collapsed",
    )
    if selected_more != "More" and more_to_page.get(selected_more) != current_page:
        navigate_to(more_to_page[selected_more])

st.markdown("</div></div>", unsafe_allow_html=True)

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

def get_subject_report(priority):
    if not priority:
        return None, None, []

    subject_stats = {}
    for item in priority:
        subject_stats.setdefault(item["subject"], {"retentions": [], "topics": 0})
        subject_stats[item["subject"]]["retentions"].append(item["retention"])
        subject_stats[item["subject"]]["topics"] += 1

    subject_rows = []
    for subject, stats in subject_stats.items():
        avg_ret = int(sum(stats["retentions"]) / len(stats["retentions"]))
        subject_rows.append({
            "subject": subject,
            "avg_ret": avg_ret,
            "topics": stats["topics"],
        })

    subject_rows = sorted(subject_rows, key=lambda x: x["avg_ret"], reverse=True)
    best_subject = subject_rows[0]
    weakest_subject = subject_rows[-1]
    return best_subject, weakest_subject, subject_rows

def format_mistake_answer(result_item):
    q_type = result_item.get("type", "mcq")

    if q_type == "mcq":
        options = result_item.get("options", {})
        correct_key = str(result_item.get("correct_ans", "")).strip()
        if correct_key and correct_key in options:
            return f"{correct_key}. {options.get(correct_key, '')}".strip()
        return correct_key

    if q_type == "match":
        pairs = result_item.get("pairs", [])
        if pairs:
            return ", ".join(
                f"{pair.get('term', '').strip()} -> {pair.get('match', '').strip()}"
                for pair in pairs
            )
        return str(result_item.get("correct_ans", "")).strip()

    return str(result_item.get("correct_ans", "")).strip()

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
            subject_options = [
                "Select from common subjects",
                "Biology","Mathematics","Physics","Chemistry",
                "History","Geography","Computer Science"
            ]
            subject_choice = st.selectbox("Choose a common subject (optional)", subject_options)
            custom_subject = st.text_input(
                "Subject name",
                placeholder="e.g. Economics, Political Science, English Literature"
            )
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
                final_subject = (
                    custom_subject.strip()
                    if custom_subject.strip()
                    else subject_choice
                )
                if final_subject == "Select from common subjects":
                    st.error("Please select a subject or type your subject name!")
                    st.stop()
                add_topic(topic_name.strip(), final_subject, understanding_score, str(date_learned), user_id=user_id)
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

        st.markdown("<br>", unsafe_allow_html=True)
        delete_col1, delete_col2, delete_col3 = st.columns([1.4, 1, 1.6])
        with delete_col2:
            if st.button("🗑️ Delete Topic", use_container_width=True, key=f"dash_delete_{selected_topic['id']}"):
                st.session_state.delete_confirm_topic_id = selected_topic["id"]
        with delete_col3:
            if st.session_state.delete_confirm_topic_id == selected_topic["id"]:
                if st.button("⚠️ Confirm Delete", use_container_width=True, key=f"dash_confirm_delete_{selected_topic['id']}"):
                    delete_topic(selected_topic["id"])
                    st.session_state.delete_confirm_topic_id = None
                    st.success(f"✅ '{selected_topic['topic_name']}' deleted successfully.")
                    st.rerun()

        if st.session_state.delete_confirm_topic_id == selected_topic["id"]:
            st.warning("This will permanently delete the topic and its reviews.")

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
                action_col1, action_col2, action_col3 = st.columns(3)
                with action_col1:
                    if st.button("✅ Mark as Reviewed", key=f"btn_{topic['id']}"):
                        add_review(topic["id"], review_score * 10, user_id=user_id)
                        xp = add_xp("review_topic", topic["topic_name"], user_id=user_id)
                        st.session_state.delete_confirm_topic_id = None
                        st.success(f"✅ Reviewed! +{xp} XP earned 🌟")
                        st.rerun()
                with action_col2:
                    if st.button("🗑️ Delete", key=f"delete_{topic['id']}"):
                        st.session_state.delete_confirm_topic_id = topic["id"]
                with action_col3:
                    if st.session_state.delete_confirm_topic_id == topic["id"]:
                        if st.button("⚠️ Confirm Delete", key=f"confirm_delete_{topic['id']}"):
                            delete_topic(topic["id"])
                            st.session_state.delete_confirm_topic_id = None
                            st.success(f"✅ '{topic['topic_name']}' deleted successfully.")
                            st.rerun()

                if st.session_state.delete_confirm_topic_id == topic["id"]:
                    st.warning("This will permanently delete the topic and all related reviews.")

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
                {sel_level.get('description', sel_level.get('hint', ''))}
            </span><br/>
            <span style='color:#64748B;font-size:0.82rem;'>
                Keywords: {sel_level.get('keywords', sel_level.get('hint', ''))}
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
                q_type = q.get("type", "mcq")

                if q_type == "mcq":
                    options = q.get("options", {})
                    if options:
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
                    else:
                        st.warning("This MCQ is missing options, so it cannot be answered right now.")

                elif q_type == "true_false":
                    choice = st.radio(
                        f"Q{q['id']}",
                        options=["True", "False"],
                        key=f"q_{q['id']}",
                        index=None,
                        label_visibility="collapsed"
                    )
                    if choice:
                        st.session_state.quiz_answers[str(q["id"])] = choice

                elif q_type in ["fill_blank", "one_word"]:
                    answer = st.text_input(
                        f"Q{q['id']} answer",
                        key=f"q_{q['id']}",
                        placeholder="Type your answer here",
                        label_visibility="collapsed"
                    )
                    if answer.strip():
                        st.session_state.quiz_answers[str(q["id"])] = answer.strip()
                    else:
                        st.session_state.quiz_answers.pop(str(q["id"]), None)

                elif q_type == "match":
                    pairs = q.get("pairs", [])
                    if pairs:
                        st.caption("Match each term with the correct option.")
                        match_choices = [str(p.get("match", "")).strip() for p in pairs if str(p.get("match", "")).strip()]
                        user_match_answers = {}
                        for idx, pair in enumerate(pairs):
                            term = str(pair.get("term", "")).strip()
                            if not term:
                                continue
                            selected_match = st.selectbox(
                                f"{term}",
                                options=["Select"] + match_choices,
                                key=f"q_{q['id']}_pair_{idx}"
                            )
                            if selected_match != "Select":
                                user_match_answers[term] = selected_match
                        if len(user_match_answers) == len([p for p in pairs if str(p.get("term", "")).strip()]):
                            st.session_state.quiz_answers[str(q["id"])] = user_match_answers
                        else:
                            st.session_state.quiz_answers.pop(str(q["id"]), None)
                    else:
                        st.warning("This match question is missing pairs, so it cannot be answered right now.")

                else:
                    answer = st.text_input(
                        f"Q{q['id']} answer",
                        key=f"q_{q['id']}",
                        placeholder="Type your answer here",
                        label_visibility="collapsed"
                    )
                    if answer.strip():
                        st.session_state.quiz_answers[str(q["id"])] = answer.strip()
                    else:
                        st.session_state.quiz_answers.pop(str(q["id"]), None)
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

            # Save wrong answers into mistake book
            mistakes_to_save = []
            for item in result["results"]:
                if item["is_correct"]:
                    continue
                user_answer = item.get("user_answer", "")
                if isinstance(user_answer, dict):
                    user_answer = ", ".join(
                        f"{term} -> {match}" for term, match in user_answer.items()
                    )
                mistakes_to_save.append({
                    "question": item.get("question", ""),
                    "type": item.get("type", "mcq"),
                    "user_answer": str(user_answer).strip() or "Not answered",
                    "correct_answer": format_mistake_answer(item),
                    "explanation": item.get("explanation", ""),
                })

            saved_mistakes = 0
            mistake_error = None
            if mistakes_to_save:
                saved_mistakes, mistake_error = save_quiz_mistakes(
                    topic_id=selected["id"],
                    topic_name=selected["topic_name"],
                    subject=selected["subject"],
                    bloom_level=st.session_state.selected_bloom,
                    mistakes=mistakes_to_save,
                    user_id=user_id,
                )

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

            if saved_mistakes:
                st.info(f"📓 {saved_mistakes} wrong answer(s) saved to your Mistake Book for retry later.")
            elif mistake_error:
                st.warning("Mistake Book could not be saved right now. Please check the `mistake_book` table in Supabase.")
                st.caption(f"Technical details: {mistake_error}")

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
                    q_type = r.get("type", "mcq")

                    if q_type == "mcq":
                        user_answer_label = (
                            f"{r['user_answer']}. {r['options'].get(r['user_answer'], '')}"
                            if r["user_answer"] else "Not answered"
                        )
                        correct_answer_label = (
                            f"{r['correct_ans']}. {r['options'].get(r['correct_ans'], '')}"
                            if r["correct_ans"] else "-"
                        )
                    elif q_type == "true_false":
                        user_answer_label = r["user_answer"] if r["user_answer"] else "Not answered"
                        correct_answer_label = r["correct_ans"] if r["correct_ans"] else "-"
                    elif q_type in ["fill_blank", "one_word"]:
                        user_answer_label = r["user_answer"] if r["user_answer"] else "Not answered"
                        correct_answer_label = r["correct_ans"] if r["correct_ans"] else "-"
                    elif q_type == "match":
                        if isinstance(r["user_answer"], dict) and r["user_answer"]:
                            user_answer_label = ", ".join(
                                [f"{term} -> {match}" for term, match in r["user_answer"].items()]
                            )
                        else:
                            user_answer_label = "Not answered"
                        if r.get("pairs"):
                            correct_answer_label = ", ".join(
                                [f"{pair.get('term', '')} -> {pair.get('match', '')}" for pair in r["pairs"]]
                            )
                        else:
                            correct_answer_label = "-"
                    else:
                        user_answer_label = r["user_answer"] if r["user_answer"] else "Not answered"
                        correct_answer_label = r["correct_ans"] if r["correct_ans"] else "-"

                    with c1:
                        st.markdown(
                            f"**Your answer:** <span style='color:#0F1B2D'>{user_answer_label}</span>",
                            unsafe_allow_html=True
                        )
                    with c2:
                        st.markdown(f"**Correct:** {correct_answer_label}")
                    st.caption("Result: Correct" if r["is_correct"] else "Result: Incorrect")
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
# PAGE 6 — MISTAKE BOOK
# ════════════════════════════════════════════════════════
elif page == "Mistake Book":
    st.markdown("""
    <div class='page-header'>
        <div class='page-title'>Mistake Book</div>
        <div class='page-subtitle'>Every wrong answer, saved with explanation so you can retry and improve</div>
    </div>
    """, unsafe_allow_html=True)

    mistakes, error = get_mistake_book(user_id=user_id)

    if error:
        st.error("Mistake Book could not be loaded from Supabase.")
        st.caption("Create a `mistake_book` table and verify your policies/columns, then refresh the app.")
        st.caption(f"Technical details: {error}")
    elif not mistakes:
        st.info("No saved mistakes yet. Take a quiz and any incorrect answers will appear here automatically.")
    else:
        today_str = datetime.now().strftime("%Y-%m-%d")
        due_now = [m for m in mistakes if (m.get("review_after") or today_str) <= today_str]
        later = [m for m in mistakes if (m.get("review_after") or today_str) > today_str]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📓 Total Mistakes", len(mistakes))
        c2.metric("🔥 Due Now", len(due_now))
        c3.metric("⏳ Retry Later", len(later))
        c4.metric("🎯 Subjects", len(set(m.get("subject", "General") for m in mistakes)))

        st.markdown("<div class='gold-line'></div>", unsafe_allow_html=True)

        if due_now:
            st.markdown("### 🔥 Retry Today")
            for item in due_now:
                with st.expander(
                    f"❌ {item.get('topic_name', 'Topic')} · L{item.get('bloom_level', 1)} · {item.get('subject', 'General')}"
                ):
                    st.markdown(f"**Question:** {item.get('question_text', '-')}")
                    st.markdown(f"**Your answer:** {item.get('user_answer', 'Not answered')}")
                    st.markdown(f"**Correct answer:** {item.get('correct_answer', '-')}")
                    if item.get("explanation"):
                        st.info(f"💡 {item['explanation']}")

                    btn1, btn2, btn3 = st.columns(3)
                    with btn1:
                        if st.button("⏳ Retry Later", key=f"snooze_due_{item['id']}", use_container_width=True):
                            ok, action_error = snooze_mistake(item["id"])
                            if ok:
                                st.success("Moved to retry later.")
                                st.rerun()
                            st.error(action_error)
                    with btn2:
                        if st.button("✅ Mark Mastered", key=f"master_due_{item['id']}", use_container_width=True):
                            ok, action_error = mark_mistake_mastered(item["id"])
                            if ok:
                                st.success("Marked as mastered.")
                                st.rerun()
                            st.error(action_error)
                    with btn3:
                        if st.button("🗑️ Remove", key=f"delete_due_{item['id']}", use_container_width=True):
                            ok, action_error = delete_mistake(item["id"])
                            if ok:
                                st.success("Removed from mistake book.")
                                st.rerun()
                            st.error(action_error)

        if later:
            st.markdown("### ⏳ Scheduled For Later")
            for item in later:
                with st.expander(
                    f"🕒 {item.get('topic_name', 'Topic')} · review after {item.get('review_after', '-')}"
                ):
                    st.markdown(f"**Question:** {item.get('question_text', '-')}")
                    st.markdown(f"**Correct answer:** {item.get('correct_answer', '-')}")
                    if item.get("explanation"):
                        st.info(f"💡 {item['explanation']}")
                    st.caption(
                        f"Bloom's L{item.get('bloom_level', 1)} · {item.get('subject', 'General')} · Snoozed {item.get('retry_count', 0)} time(s)"
                    )

                    btn1, btn2 = st.columns(2)
                    with btn1:
                        if st.button("✅ Mark Mastered", key=f"master_later_{item['id']}", use_container_width=True):
                            ok, action_error = mark_mistake_mastered(item["id"])
                            if ok:
                                st.success("Marked as mastered.")
                                st.rerun()
                            st.error(action_error)
                    with btn2:
                        if st.button("🗑️ Remove", key=f"delete_later_{item['id']}", use_container_width=True):
                            ok, action_error = delete_mistake(item["id"])
                            if ok:
                                st.success("Removed from mistake book.")
                                st.rerun()
                            st.error(action_error)

# ════════════════════════════════════════════════════════
# PAGE 7 — PROGRESS REPORT
# ════════════════════════════════════════════════════════
elif page == "Progress Report":

    st.markdown("""
    <div class='page-header'>
        <div class='page-title'>Progress Report</div>
        <div class='page-subtitle'>A clean summary of your learning progress, ready to screenshot and share</div>
    </div>
    """, unsafe_allow_html=True)

    topics = load_topics()
    total_xp = get_total_xp(user_id=user_id)
    streak = get_streak(user_id=user_id)

    if not topics:
        st.info("No topics yet. Add some topics first and your progress report will appear here.")
    else:
        priority = get_review_priority(topics)
        avg_ret = int(sum(t["retention"] for t in priority) / len(priority)) if priority else 0
        best_subject, weakest_subject, subject_rows = get_subject_report(priority)

        report_color = "#059669" if avg_ret >= 70 else "#D97706" if avg_ret >= 40 else "#DC2626"
        report_status = (
            "Memory health is excellent" if avg_ret >= 70 else
            "Memory health is improving" if avg_ret >= 40 else
            "Memory health needs attention"
        )

        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#0F1B2D,#1E3A5F);
                    border-radius:20px;padding:28px 30px;margin-bottom:24px;
                    border:1px solid rgba(201,168,76,0.24);box-shadow:0 18px 50px rgba(15,27,45,0.14);'>
            <div style='display:flex;justify-content:space-between;align-items:flex-start;gap:18px;flex-wrap:wrap;'>
                <div>
                    <div style='font-size:10px;color:rgba(255,255,255,0.45);text-transform:uppercase;
                                letter-spacing:0.12em;font-weight:600;margin-bottom:8px;'>
                        Smriti Shareable Snapshot
                    </div>
                    <div style='font-family:Georgia,serif;font-size:2rem;font-weight:700;color:#FFFFFF;'>
                        Your learning progress at a glance
                    </div>
                    <div style='color:rgba(255,255,255,0.62);font-size:0.92rem;margin-top:10px;max-width:620px;line-height:1.7;'>
                        {report_status}. You are tracking <strong style='color:#FFFFFF;'>{len(topics)}</strong> topic(s),
                        holding an average retention of <strong style='color:{report_color};'>{avg_ret}%</strong>,
                        and building a <strong style='color:#C9A84C;'>{streak}-day streak</strong>.
                    </div>
                </div>
                <div style='background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.08);
                            border-radius:16px;padding:18px 20px;min-width:220px;'>
                    <div style='color:rgba(255,255,255,0.45);font-size:10px;text-transform:uppercase;
                                letter-spacing:0.1em;'>Current Status</div>
                    <div style='font-size:2.3rem;font-weight:700;color:{report_color};font-family:Georgia,serif;margin-top:4px;'>
                        {avg_ret}%
                    </div>
                    <div style='color:rgba(255,255,255,0.62);font-size:0.84rem;'>Average Retention</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📚 Total Topics", len(topics))
        m2.metric("🧠 Average Retention", f"{avg_ret}%")
        m3.metric("🔥 Study Streak", f"{streak} days")
        m4.metric("🏆 Total XP", total_xp)

        st.markdown("<div class='gold-line'></div>", unsafe_allow_html=True)

        top_col, weak_col = st.columns(2)
        with top_col:
            st.markdown(f"""
            <div style='background:#F0FDF4;border:1px solid #BBF7D0;border-radius:16px;
                        padding:20px 22px;height:100%;box-shadow:0 2px 8px rgba(15,27,45,0.05);'>
                <div style='font-size:10px;color:#059669;text-transform:uppercase;letter-spacing:0.12em;font-weight:600;'>
                    Best Subject
                </div>
                <div style='font-family:Georgia,serif;font-size:1.8rem;font-weight:700;color:#166534;margin-top:8px;'>
                    {best_subject["subject"]}
                </div>
                <div style='color:#15803D;font-size:0.92rem;margin-top:6px;line-height:1.6;'>
                    Average retention: <strong>{best_subject["avg_ret"]}%</strong><br/>
                    Topics tracked: <strong>{best_subject["topics"]}</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with weak_col:
            weak_bg = "#FFFBEB" if weakest_subject["avg_ret"] >= 40 else "#FEF2F2"
            weak_border = "#FDE68A" if weakest_subject["avg_ret"] >= 40 else "#FECACA"
            weak_text = "#A16207" if weakest_subject["avg_ret"] >= 40 else "#991B1B"
            st.markdown(f"""
            <div style='background:{weak_bg};border:1px solid {weak_border};border-radius:16px;
                        padding:20px 22px;height:100%;box-shadow:0 2px 8px rgba(15,27,45,0.05);'>
                <div style='font-size:10px;color:{weak_text};text-transform:uppercase;letter-spacing:0.12em;font-weight:600;'>
                    Weakest Subject
                </div>
                <div style='font-family:Georgia,serif;font-size:1.8rem;font-weight:700;color:{weak_text};margin-top:8px;'>
                    {weakest_subject["subject"]}
                </div>
                <div style='color:{weak_text};font-size:0.92rem;margin-top:6px;line-height:1.6;'>
                    Average retention: <strong>{weakest_subject["avg_ret"]}%</strong><br/>
                    Topics tracked: <strong>{weakest_subject["topics"]}</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 📊 Subject Performance Summary")

        subject_cols = st.columns(min(3, len(subject_rows)))
        for idx, item in enumerate(subject_rows[:3]):
            with subject_cols[idx]:
                tone = "#059669" if item["avg_ret"] >= 70 else "#D97706" if item["avg_ret"] >= 40 else "#DC2626"
                tone_bg = "#F0FDF4" if item["avg_ret"] >= 70 else "#FFFBEB" if item["avg_ret"] >= 40 else "#FEF2F2"
                st.markdown(f"""
                <div style='background:#FFFFFF;border:1px solid #E2E8F0;border-radius:14px;
                            padding:18px;height:100%;box-shadow:0 2px 8px rgba(15,27,45,0.05);border-top:3px solid {tone};'>
                    <div style='font-weight:700;color:#0F1B2D;font-size:1rem;'>{item["subject"]}</div>
                    <div style='display:inline-block;background:{tone_bg};color:{tone};
                                border-radius:999px;padding:6px 10px;font-size:0.78rem;font-weight:700;margin-top:10px;'>
                        {item["avg_ret"]}% retained
                    </div>
                    <div style='color:#64748B;font-size:0.84rem;margin-top:12px;line-height:1.6;'>
                        {item["topics"]} topic{"s" if item["topics"] != 1 else ""} tracked in this subject.
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 📝 Share Text")
        share_text = (
            f"I am tracking {len(topics)} topics on Smriti with {avg_ret}% average retention, "
            f"a {streak}-day study streak, and {total_xp} XP. "
            f"My best subject is {best_subject['subject']} and the subject needing the most attention is {weakest_subject['subject']}."
        )
        st.code(share_text, language="text")
        st.caption("This block is ready to copy or use in a screenshot-friendly progress update.")

# ════════════════════════════════════════════════════════
# PAGE 8 — LEADERBOARD
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

# ════════════════════════════════════════════════════════
# PAGE 9 — FEEDBACK
# ════════════════════════════════════════════════════════
elif page == "Feedback":
    st.markdown("""
    <div class='page-header'>
        <div class='page-title'>Feedback</div>
        <div class='page-subtitle'>Tell us what feels great, what breaks, and what Smriti should improve next</div>
    </div>
    """, unsafe_allow_html=True)

    topics = load_topics()
    total_xp = get_total_xp(user_id=user_id)

    intro_c1, intro_c2 = st.columns([1.4, 1])
    with intro_c1:
        st.markdown("""
        <div style='background:#FFFFFF;border:1px solid #E2E8F0;border-radius:14px;
                    padding:20px 24px;box-shadow:0 2px 8px rgba(15,27,45,0.05);'>
            <div style='font-size:10px;color:#64748B;text-transform:uppercase;
                        letter-spacing:0.12em;font-weight:600;margin-bottom:8px;'>
                Why this matters
            </div>
            <div style='font-weight:700;color:#0F1B2D;font-size:1.05rem;margin-bottom:8px;'>
                Your feedback shapes the next version of Smriti
            </div>
            <div style='color:#64748B;font-size:0.9rem;line-height:1.7;'>
                Share bugs, confusing flows, missing features, or even one small thing you loved.
                Short and honest feedback is perfect.
            </div>
        </div>
        """, unsafe_allow_html=True)
    with intro_c2:
        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#0F1B2D,#1E3A5F);
                    border-radius:14px;padding:20px 24px;color:#FFFFFF;
                    border:1px solid rgba(201,168,76,0.24);'>
            <div style='color:rgba(255,255,255,0.45);font-size:10px;text-transform:uppercase;
                        letter-spacing:0.12em;font-weight:600;margin-bottom:10px;'>
                Your Usage Snapshot
            </div>
            <div style='display:flex;justify-content:space-between;gap:16px;'>
                <div>
                    <div style='font-family:Georgia,serif;font-size:1.8rem;font-weight:700;color:#C9A84C;'>{len(topics)}</div>
                    <div style='font-size:11px;color:rgba(255,255,255,0.45);'>Topics</div>
                </div>
                <div>
                    <div style='font-family:Georgia,serif;font-size:1.8rem;font-weight:700;color:#22C55E;'>{total_xp}</div>
                    <div style='font-size:11px;color:rgba(255,255,255,0.45);'>XP</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div class='gold-line'></div>", unsafe_allow_html=True)

    with st.form("feedback_form"):
        col1, col2 = st.columns(2)
        with col1:
            feedback_category = st.selectbox(
                "What kind of feedback is this?",
                [
                    "General Feedback",
                    "Bug Report",
                    "Feature Request",
                    "UI / Design",
                    "Quiz Quality",
                    "Performance Issue",
                ],
            )
            rating = st.slider("Overall experience", 1, 5, 4, help="1 = poor, 5 = excellent")
            active_context = st.selectbox(
                "Which area were you using?",
                ["Home", "Add Topic", "Dashboard", "Review List", "Quiz", "Leaderboard", "Overall App"],
                index=6,
            )
        with col2:
            st.info(
                "Tip: the most useful feedback includes what you expected, what happened, and what should improve."
            )
            st.markdown(
                f"""
                <div style='background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;
                            padding:14px 16px;color:#64748B;font-size:0.85rem;line-height:1.6;'>
                    This feedback will be saved as <strong style='color:#0F1B2D;'>"{feedback_category}"</strong>
                    for the <strong style='color:#0F1B2D;'>"{active_context}"</strong> area.
                    Add the context directly in your message so it is easier to review later.
                </div>
                """,
                unsafe_allow_html=True
            )

        message = st.text_area(
            "What happened or what would you like to share?",
            height=180,
            placeholder="Example: In Quiz, the questions were good, but I want an easier way to retry only wrong answers.",
        )

        submitted = st.form_submit_button("Send Feedback", use_container_width=True)

        if submitted:
            if len(message.strip()) < 10:
                st.error("Please write at least a short feedback message so it is actionable.")
            else:
                ok, error = submit_feedback(
                    category=feedback_category,
                    rating=rating,
                    message=f"[{active_context}] {message.strip()}",
                    user_id=user_id,
                )
                if ok:
                    st.success("✅ Feedback sent successfully. Thank you for helping improve Smriti.")
                    st.balloons()
                else:
                    st.error(
                        "Feedback could not be saved to Supabase. Please recheck your feedback table columns and policies."
                    )
                    st.caption(f"Technical details: {error}")
