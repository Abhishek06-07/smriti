import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from database import (
    init_db, add_topic, get_all_topics, add_review,
    init_streak_table, mark_today_studied,
    get_streak, get_total_study_days,
    init_xp_table, add_xp, get_total_xp,
    get_today_xp, get_xp_by_subject,
    get_league, get_xp_history, LEAGUE_THRESHOLDS,
    sign_up, sign_in, sign_out
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

# ── MIDNIGHT NAVY PROFESSIONAL THEME ─────────────────────
# Psychology:
#   Navy   #0F1B2D = authority, depth, premium
#   Steel  #1E3A5F = trust, intelligence
#   Gold   #C9A84C = achievement, excellence
#   Slate  #F1F4F8 = clean content bg, readable
#   White  #FFFFFF = pure content area
#   Red    #DC2626 = urgent/danger
#   Amber  #D97706 = at-risk/warning
#   Green  #059669 = strong/success

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@300;400;500;600&display=swap');

/* ── GLOBAL ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}
#MainMenu, footer, header { visibility: hidden; }
section[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"]  { display: none !important; }

/* ── APP BACKGROUND — light slate ── */
.stApp {
    background-color: #F1F4F8 !important;
}

/* ── TOP NAV BAR ── */
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
    letter-spacing: -0.01em;
    display: flex;
    align-items: center;
    gap: 8px;
}
.nav-brand span {
    color: #C9A84C;
}
.nav-tagline {
    font-size: 10px;
    color: rgba(255,255,255,0.4);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-left: 4px;
}

/* ── PAGE TITLE AREA ── */
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
    letter-spacing: 0.03em;
}

/* ── CONTENT CARD ── */
.content-card {
    background: #FFFFFF;
    border-radius: 12px;
    border: 1px solid #E2E8F0;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 1px 6px rgba(15,27,45,0.06);
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
[data-testid="stMetricDelta"] { font-size: 0.8rem !important; }

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
/* Button text always white */
.stButton > button p,
.stButton > button span {
    color: #FFFFFF !important;
}
[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #0F1B2D, #1E3A5F) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 12px 24px !important;
}
[data-testid="stFormSubmitButton"] > button:hover {
    opacity: 0.9 !important;
}

/* ── FORM INPUTS ── */
.stTextInput > div > div > input {
    background: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 8px !important;
    color: #0F1B2D !important;
    font-size: 0.9rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: #1E3A5F !important;
}

/* ── SELECTBOX ── */
div[data-baseweb="select"] > div {
    background: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 8px !important;
    color: #0F1B2D !important;
}
div[data-baseweb="select"] span,
div[data-baseweb="select"] div {
    color: #0F1B2D !important;
}
/* Dropdown options */
ul[data-testid="stSelectboxVirtualDropdown"] li {
    color: #0F1B2D !important;
    background: #FFFFFF !important;
}
li[role="option"] {
    color: #0F1B2D !important;
    background: #FFFFFF !important;
}
li[role="option"]:hover {
    background: #F1F4F8 !important;
}
    color: #0F1B2D !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: #1E3A5F !important;
    box-shadow: 0 0 0 3px rgba(30,58,95,0.1) !important;
}
.stTextArea > div > div > textarea {
    background: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 8px !important;
    color: #0F1B2D !important;
}
div[data-baseweb="select"] > div {
    background: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 8px !important;
    color: #0F1B2D !important;
}

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
    font-family: 'Inter', sans-serif !important;
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

/* ── ALERTS ── */
.stAlert { border-radius: 10px !important; border-left-width: 4px !important; }

/* ── DIVIDER ── */
hr { border-color: #E2E8F0 !important; }

/* ── SELECTBOX LABEL ── */
label { color: #374151 !important; font-weight: 500 !important; }

/* ── HEADINGS ── */
h1, h2, h3 {
    font-family: 'Playfair Display', serif !important;
    color: #0F1B2D !important;
}

/* ── QUIZ TEXT FIX ── */
/* Question text */
.stMarkdown p { color: #0F1B2D !important; font-size: 0.95rem !important; }
.stMarkdown strong { color: #0F1B2D !important; font-weight: 700 !important; }

/* Radio button labels — options text */
.stRadio label {
    color: #0F1B2D !important;
    font-size: 0.9rem !important;
    font-weight: 400 !important;
}
.stRadio > div > label {
    color: #0F1B2D !important;
}
/* Radio option text */
[data-testid="stRadio"] label p {
    color: #0F1B2D !important;
    font-size: 0.9rem !important;
}
/* All paragraph text */
p { color: #0F1B2D !important; }

/* Caption text */
.stCaption p {
    color: #64748B !important;
    font-size: 0.8rem !important;
}

/* General text color */
[data-testid="stMarkdownContainer"] p {
    color: #0F1B2D !important;
}
[data-testid="stMarkdownContainer"] {
    color: #0F1B2D !important;
}

/* ── GOLD ACCENT LINE ── */
.gold-line {
    height: 3px;
    background: linear-gradient(90deg, #C9A84C, #E8C96D, #C9A84C);
    border-radius: 2px;
    margin: 16px 0 24px 0;
}

/* ── STATUS BADGE ── */
.badge-strong { background:#DCFCE7; color:#166534; padding:3px 10px; border-radius:999px; font-size:11px; font-weight:600; }
.badge-risk   { background:#FEF3C7; color:#92400E; padding:3px 10px; border-radius:999px; font-size:11px; font-weight:600; }
.badge-weak   { background:#FEE2E2; color:#991B1B; padding:3px 10px; border-radius:999px; font-size:11px; font-weight:600; }

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
.streak-fire {
    font-size: 3rem;
    line-height: 1;
    filter: drop-shadow(0 0 12px rgba(245,158,11,0.6));
}
.streak-number {
    font-size: 3rem;
    font-weight: 700;
    color: #C9A84C;
    font-family: Georgia, serif;
    line-height: 1;
}
.streak-label {
    font-size: 11px;
    color: rgba(255,255,255,0.5);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 4px;
}
.streak-stat {
    text-align: center;
    padding: 0 16px;
    border-left: 1px solid rgba(255,255,255,0.1);
}

/* ── BLOOM PROGRESS NODES ── */
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
.bloom-node {
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    min-width: 80px;
}
.bloom-node-circle {
    width: 52px;
    height: 52px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.4rem;
    font-weight: 700;
    border: 3px solid;
    transition: all 0.3s;
    position: relative;
    z-index: 2;
}
.bloom-node-label {
    font-size: 9px;
    font-weight: 600;
    margin-top: 6px;
    text-align: center;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.bloom-connector {
    width: 40px;
    height: 3px;
    margin-top: -26px;
    position: relative;
    z-index: 1;
}

/* ── MEMORY SCORE CARD ── */
.memory-score-card {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 20px 24px;
    border: 1px solid #E2E8F0;
    box-shadow: 0 2px 8px rgba(15,27,45,0.06);
    text-align: center;
}
.memory-score-title {
    font-size: 11px;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 600;
    margin-bottom: 8px;
}
.memory-score-value {
    font-size: 3.5rem;
    font-weight: 700;
    font-family: Georgia, serif;
    line-height: 1;
}
.memory-score-label {
    font-size: 12px;
    color: #64748B;
    margin-top: 6px;
}
</style>
""", unsafe_allow_html=True)

# ── INIT DB ───────────────────────────────────────────────
init_db()
init_streak_table()
init_xp_table()

# ── AUTH GATE ─────────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user    = None
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"

# ── LOGIN / SIGNUP PAGE ───────────────────────────────────
if not st.session_state.user:
    st.markdown("""
    <div style='max-width:420px;margin:60px auto;'>
        <div style='text-align:center;margin-bottom:32px;'>
            <div style='font-size:3.5rem;'>🧠</div>
            <div style='font-family:Georgia,serif;font-size:2rem;
                        font-weight:700;color:#0F1B2D;'>Smriti</div>
            <div style='color:#64748B;font-size:0.9rem;margin-top:4px;'>
                AI-Powered Memory Intelligence
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Center the form
    _, col, _ = st.columns([1, 2, 1])
    with col:
        # Toggle Login / Signup
        mode_col1, mode_col2 = st.columns(2)
        with mode_col1:
            if st.button("🔑 Login", use_container_width=True, key="mode_login"):
                st.session_state.auth_mode = "login"
        with mode_col2:
            if st.button("📝 Sign Up", use_container_width=True, key="mode_signup"):
                st.session_state.auth_mode = "signup"

        st.markdown("---")

        if st.session_state.auth_mode == "login":
            st.markdown("#### Welcome back!")
            email    = st.text_input("Email", placeholder="you@example.com", key="login_email")
            password = st.text_input("Password", type="password", key="login_pass")

            if st.button("Login →", use_container_width=True, key="do_login"):
                if not email or not password:
                    st.error("Please enter email and password!")
                else:
                    with st.spinner("Logging in..."):
                        user, error = sign_in(email, password)
                    if user:
                        st.session_state.user = user
                        st.success("✅ Welcome back!")
                        st.rerun()
                    else:
                        st.error(f"❌ {error}")

        else:
            st.markdown("#### Create Account")
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
                        st.session_state.user = user
                        st.success("✅ Account created! Welcome to Smriti!")
                        st.rerun()
                    else:
                        st.error(f"❌ {error}")

    st.stop()  # Stop here if not logged in

# ── USER IS LOGGED IN ─────────────────────────────────────
user_id = st.session_state.user.id

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
    if st.button("🏆 Leaderboard", use_container_width=True, key="nav_leader"): st.session_state.page = "Leaderboard"

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
# PAGE 1 — HOME
# ════════════════════════════════════════════════════════
if page == "Home":
    st.markdown("""
    <div class='page-header'>
        <div class='page-title'>Memory Dashboard</div>
        <div class='page-subtitle'>Your personal knowledge retention overview</div>
    </div>
    """, unsafe_allow_html=True)

    topics = load_topics()

    # ── IMPROVEMENT 1: STREAK CARD ────────────────────────
    streak      = get_streak(user_id=user_id)
    total_days  = get_total_study_days(user_id=user_id)

    # Streak emoji based on count
    if streak >= 30:   fire = "🔥🔥🔥"
    elif streak >= 14: fire = "🔥🔥"
    elif streak >= 7:  fire = "🔥"
    elif streak >= 1:  fire = "⚡"
    else:              fire = "💤"

    streak_msg = (
        "Legendary! 🏆" if streak >= 30 else
        "On fire! Keep going!" if streak >= 14 else
        "Great streak! Don't break it!" if streak >= 7 else
        "Building momentum!" if streak >= 3 else
        "Day 1 — every streak starts here!" if streak == 1 else
        "Start your streak today!"
    )

    st.markdown(f"""
    <div class='streak-card'>
        <div style='display:flex;align-items:center;gap:16px;'>
            <div class='streak-fire'>{fire}</div>
            <div>
                <div style='color:rgba(255,255,255,0.5);font-size:10px;
                            text-transform:uppercase;letter-spacing:0.12em;font-weight:600;'>
                    Study Streak
                </div>
                <div style='display:flex;align-items:baseline;gap:6px;'>
                    <span class='streak-number'>{streak}</span>
                    <span style='color:rgba(255,255,255,0.6);font-size:0.9rem;'>
                        day{'s' if streak != 1 else ''}
                    </span>
                </div>
                <div style='color:#C9A84C;font-size:0.82rem;margin-top:2px;'>
                    {streak_msg}
                </div>
            </div>
        </div>
        <div style='display:flex;gap:0;'>
            <div class='streak-stat'>
                <div style='color:#FFFFFF;font-size:1.6rem;font-weight:700;
                            font-family:Georgia,serif;'>{total_days}</div>
                <div class='streak-label'>Total Days</div>
            </div>
            <div class='streak-stat'>
                <div style='color:#22C55E;font-size:1.6rem;font-weight:700;
                            font-family:Georgia,serif;'>{len(topics) if topics else 0}</div>
                <div class='streak-label'>Topics</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── IMPROVEMENT 2: BLOOM'S PROGRESS NODES ────────────
    st.markdown("#### 🎓 Bloom's Taxonomy — Your Level Journey")

    # Get best bloom level achieved from session state
    best_bloom  = st.session_state.get("best_bloom_achieved", 1)
    bloom_data  = [
        (1, "🧠", "Remember", "#6B7280"),
        (2, "💡", "Understand", "#0891B2"),
        (3, "⚙️", "Apply", "#059669"),
        (4, "🔍", "Analyze", "#D97706"),
        (5, "⚖️", "Evaluate", "#DC2626"),
        (6, "🚀", "Create", "#7C3AED"),
    ]

    nodes_html = "<div class='bloom-path'>"
    for i, (lvl, emoji, name, color) in enumerate(bloom_data):
        is_done    = lvl < best_bloom
        is_current = lvl == best_bloom
        is_locked  = lvl > best_bloom

        if is_done:
            bg       = color
            border   = color
            txt      = "#FFFFFF"
            opacity  = "1"
            lbl_col  = color
        elif is_current:
            bg       = f"{color}20"
            border   = color
            txt      = color
            opacity  = "1"
            lbl_col  = color
        else:
            bg       = "#F1F4F8"
            border   = "#CBD5E1"
            txt      = "#94A3B8"
            opacity  = "0.5"
            lbl_col  = "#94A3B8"

        pulse = "animation:pulse 1.5s infinite;" if is_current else ""

        nodes_html += f"""
        <div class='bloom-node' style='opacity:{opacity};'>
            <div class='bloom-node-circle'
                 style='background:{bg};border-color:{border};
                        color:{txt};{pulse}'>
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
                 style='background:{conn_color};
                        margin-bottom:22px;'></div>"""

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
    st.caption(f"Currently at L{best_bloom} — Take a quiz to advance levels! 🎯")
    st.markdown("<div class='gold-line'></div>", unsafe_allow_html=True)

    if not topics:
        st.info("👋 Welcome to Smriti! Click **➕ Add Topic** above to start tracking your memory.")
    else:
        priority = get_review_priority(topics)
        weak   = [t for t in priority if "Weak"    in t["label"]]
        atrisk = [t for t in priority if "At-Risk" in t["label"]]
        strong = [t for t in priority if "Strong"  in t["label"]]

        # ── IMPROVEMENT 3: MEMORY HEALTH SCORE ───────────
        avg_ret    = int(sum(t["retention"] for t in priority) / len(priority))
        if avg_ret >= 70:
            score_color = "#059669"; score_label = "Excellent Memory Health! 🌟"
        elif avg_ret >= 40:
            score_color = "#D97706"; score_label = "Memory Needs Attention ⚠️"
        else:
            score_color = "#DC2626"; score_label = "Critical — Review Now! 🚨"

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("📚 Topics",  len(topics))
        c2.metric("💪 Strong",  len(strong))
        c3.metric("⚠️ At-Risk", len(atrisk))
        c4.metric("🔴 Weak",    len(weak))

        with c5:
            st.markdown(f"""
            <div class='memory-score-card'>
                <div class='memory-score-title'>Memory Score</div>
                <div class='memory-score-value' style='color:{score_color};'>
                    {avg_ret}%
                </div>
                <div class='memory-score-label'>{score_label}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div class='gold-line'></div>", unsafe_allow_html=True)

        if weak:
            st.error(f"🚨 **{len(weak)} topic(s) need urgent review today!**")
            for t in weak[:3]:
                st.markdown(f"→ **{t['topic_name']}** `{t['subject']}` — `{t['retention']}%` retained")
        if atrisk:
            st.warning(f"⚠️ **{len(atrisk)} topic(s)** are fading. Review soon!")
        if not weak and not atrisk:
            st.success("✅ All topics in great shape! Keep it up.")

        st.markdown("---")

        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("### 📂 Topics by Subject")
            subjects = {}
            for t in topics:
                subjects[t["subject"]] = subjects.get(t["subject"], 0) + 1
            fig = px.pie(
                values=list(subjects.values()),
                names=list(subjects.keys()),
                hole=0.5,
                color_discrete_sequence=CHART_COLORS
            )
            fig.update_traces(textfont_color="#0F1B2D")
            fig.update_layout(height=300, **chart_layout("Topics by Subject"))
            st.plotly_chart(fig, use_container_width=True)

        with col_r:
            st.markdown("### 🏆 Memory Health Score")
            avg_ret = int(sum(t["retention"] for t in priority) / len(priority))
            fig2 = go.Figure(go.Indicator(
                mode="gauge+number",
                value=avg_ret,
                title={"text": "Average Retention %",
                       "font": {"color": "#64748B", "family": "Inter", "size": 13}},
                number={"font": {"color": "#0F1B2D", "family": "Playfair Display", "size": 42},
                        "suffix": "%"},
                gauge={
                    "axis": {"range": [0,100], "tickcolor": "#CBD5E1",
                             "tickfont": {"color": "#94A3B8"}},
                    "bar": {"color": "#1E3A5F", "thickness": 0.28},
                    "bgcolor": "white",
                    "bordercolor": "#E2E8F0",
                    "steps": [
                        {"range": [0,40],  "color": "#FEE2E2"},
                        {"range": [40,70], "color": "#FEF3C7"},
                        {"range": [70,100],"color": "#DCFCE7"},
                    ],
                    "threshold": {
                        "line": {"color": "#C9A84C", "width": 3},
                        "value": 70
                    }
                }
            ))
            fig2.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)",
                               margin=dict(t=30, b=10, l=20, r=20))
            st.plotly_chart(fig2, use_container_width=True)

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
