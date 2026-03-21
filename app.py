import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from database import init_db, add_topic, get_all_topics, add_review
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
</style>
""", unsafe_allow_html=True)

# ── INIT DB ───────────────────────────────────────────────
init_db()

# ── SESSION STATE ─────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "Home"

# ── TOP NAVIGATION ────────────────────────────────────────
st.markdown("""
<div class='nav-wrapper'>
    <div class='nav-brand'>
        🧠 <span>Smriti</span>
        <span class='nav-tagline'>Memory Intelligence</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Nav buttons
c1, c2, c3, c4, c5, c6 = st.columns([2, 1, 1, 1, 1, 1])
with c1:
    st.markdown("")
with c2:
    if st.button("🏠 Home",         use_container_width=True): st.session_state.page = "Home"
with c3:
    if st.button("➕ Add Topic",    use_container_width=True): st.session_state.page = "Add Topic"
with c4:
    if st.button("📊 Dashboard",   use_container_width=True): st.session_state.page = "Dashboard"
with c5:
    if st.button("📋 Review List", use_container_width=True): st.session_state.page = "Review List"
with c6:
    if st.button("🧪 Quiz",        use_container_width=True): st.session_state.page = "Quiz"

page = st.session_state.page

# ── HELPER ────────────────────────────────────────────────
def load_topics():
    raw = get_all_topics()
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

    if not topics:
        st.info("👋 Welcome to Smriti! Click **➕ Add Topic** above to start tracking your memory.")
    else:
        priority = get_review_priority(topics)
        weak   = [t for t in priority if "Weak"    in t["label"]]
        atrisk = [t for t in priority if "At-Risk" in t["label"]]
        strong = [t for t in priority if "Strong"  in t["label"]]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📚 Total Topics", len(topics))
        c2.metric("💪 Strong",       len(strong))
        c3.metric("⚠️ At-Risk",      len(atrisk))
        c4.metric("🔴 Weak",         len(weak))

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
                add_topic(topic_name.strip(), subject, understanding_score, str(date_learned))
                st.success(f"✅ **'{topic_name}'** added to Smriti!")
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
                    add_review(topic["id"], review_score * 10)
                    st.success("✅ Reviewed! Your curve has been updated.")
                    st.rerun()

# ════════════════════════════════════════════════════════
# PAGE 5 — QUIZ
# ════════════════════════════════════════════════════════
elif page == "Quiz":
    from question_generator import generate_questions, calculate_score, quiz_to_retention_boost

    st.markdown("""
    <div class='page-header'>
        <div class='page-title'>AI Quiz</div>
        <div class='page-subtitle'>Test your understanding — powered by Groq + Llama 3.3</div>
    </div>
    """, unsafe_allow_html=True)

    topics = load_topics()

    if not topics:
        st.info("No topics yet! Click **➕ Add Topic** to add some.")
    else:
        # ── Topic selector
        priority     = get_review_priority(topics)
        topic_names  = [f"{t['topic_name']} ({t['subject']}) — {t['retention']}% retained" for t in priority]
        selected_idx = st.selectbox("Select topic to quiz:", range(len(topic_names)),
                                    format_func=lambda i: topic_names[i])
        selected     = priority[selected_idx]

        # ── Topic info
        c1, c2, c3 = st.columns(3)
        c1.metric("Topic",       selected["topic_name"])
        c2.metric("Retention",   f"{selected['retention']}%")
        c3.metric("Status",      selected["label"])

        st.markdown("<div class='gold-line'></div>", unsafe_allow_html=True)

        # ── Generate button
        if "quiz_questions"   not in st.session_state: st.session_state.quiz_questions   = None
        if "quiz_topic_id"    not in st.session_state: st.session_state.quiz_topic_id    = None
        if "quiz_answers"     not in st.session_state: st.session_state.quiz_answers     = {}
        if "quiz_submitted"   not in st.session_state: st.session_state.quiz_submitted   = False
        if "quiz_result"      not in st.session_state: st.session_state.quiz_result      = None

        # Reset quiz if topic changed
        if st.session_state.quiz_topic_id != selected["id"]:
            st.session_state.quiz_questions = None
            st.session_state.quiz_answers   = {}
            st.session_state.quiz_submitted = False
            st.session_state.quiz_result    = None
            st.session_state.quiz_topic_id  = selected["id"]

        # ── Generate Questions
        if not st.session_state.quiz_questions:
            st.markdown(f"""
            <div style='background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;
                        padding:20px 24px;text-align:center;'>
                <div style='font-size:2rem;margin-bottom:8px;'>🤖</div>
                <div style='font-weight:600;color:#0F1B2D;font-size:1rem;'>
                    AI will generate 3 questions on
                </div>
                <div style='color:#1E3A5F;font-size:1.2rem;font-weight:700;margin:6px 0;'>
                    {selected['topic_name']}
                </div>
                <div style='color:#64748B;font-size:0.85rem;'>
                    Difficulty adapts to your retention: {selected['retention']}%
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("")
            if st.button("🚀 Generate Quiz Questions", use_container_width=True):
                with st.spinner("🤖 AI generating questions..."):
                    questions, error = generate_questions(
                        topic_name          = selected["topic_name"],
                        subject             = selected["subject"],
                        understanding_score = selected["understanding_score"],
                        retention_pct       = selected["retention"]
                    )
                if error:
                    st.error(f"❌ Error: {error}")
                else:
                    st.session_state.quiz_questions = questions
                    st.session_state.quiz_answers   = {}
                    st.session_state.quiz_submitted = False
                    st.rerun()

        # ── Show Questions
        elif not st.session_state.quiz_submitted:
            st.markdown(f"### 📝 Quiz — {selected['topic_name']}")
            st.caption(f"Answer all 3 questions · Difficulty based on {selected['retention']}% retention")
            st.markdown("---")

            for q in st.session_state.quiz_questions:
                st.markdown(f"**Q{q['id']}. {q['question']}**")
                options = q["options"]
                choice  = st.radio(
                    f"Select answer for Q{q['id']}:",
                    options = list(options.keys()),
                    format_func = lambda k, opts=options: f"{k}.  {opts[k]}",
                    key     = f"q_{q['id']}",
                    index   = None,
                    label_visibility = "collapsed"
                )
                if choice:
                    st.session_state.quiz_answers[str(q["id"])] = choice
                st.markdown("")

            # Submit
            all_answered = len(st.session_state.quiz_answers) == len(st.session_state.quiz_questions)
            if not all_answered:
                st.warning(f"⚠️ {len(st.session_state.quiz_questions) - len(st.session_state.quiz_answers)} question(s) remaining")

            col_sub, col_new = st.columns(2)
            with col_sub:
                if st.button("✅ Submit Quiz", use_container_width=True, disabled=not all_answered):
                    result = calculate_score(
                        st.session_state.quiz_questions,
                        st.session_state.quiz_answers
                    )
                    st.session_state.quiz_result    = result
                    st.session_state.quiz_submitted = True
                    st.rerun()
            with col_new:
                if st.button("🔄 New Questions", use_container_width=True):
                    st.session_state.quiz_questions = None
                    st.session_state.quiz_answers   = {}
                    st.session_state.quiz_submitted = False
                    st.rerun()

        # ── Show Results
        elif st.session_state.quiz_submitted and st.session_state.quiz_result:
            result   = st.session_state.quiz_result
            score    = result["score_pct"]
            correct  = result["correct"]
            total    = result["total"]

            # Score card
            if score >= 80:
                bg_col   = "#F0FDF4"; bd_col = "#059669"
                emoji    = "🎉"; msg = "Excellent! Memory is strong!"
            elif score >= 60:
                bg_col   = "#FFFBEB"; bd_col = "#D97706"
                emoji    = "👍"; msg = "Good job! Keep reviewing."
            else:
                bg_col   = "#FEF2F2"; bd_col = "#DC2626"
                emoji    = "📚"; msg = "Need more practice! Review this topic."

            st.markdown(f"""
            <div style='background:{bg_col};border:2px solid {bd_col};
                        border-radius:14px;padding:24px;text-align:center;
                        margin-bottom:24px;'>
                <div style='font-size:3rem;'>{emoji}</div>
                <div style='font-size:2.5rem;font-weight:700;color:{bd_col};
                            font-family:Georgia,serif;'>{score}%</div>
                <div style='font-size:1rem;color:{bd_col};font-weight:600;'>
                    {correct}/{total} correct — {msg}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Update retention via review
            boost = quiz_to_retention_boost(score)
            add_review(selected["id"], boost * 10)
            st.success(f"✅ Retention updated based on quiz score!")

            # Detailed results
            st.markdown("### 📊 Detailed Results")
            for r in result["results"]:
                icon = "✅" if r["is_correct"] else "❌"
                with st.expander(f"{icon} Q{r['id']}. {r['question']}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"**Your answer:** {r['user_answer']}. {r['options'].get(r['user_answer'], 'Not answered')}")
                    with c2:
                        st.markdown(f"**Correct answer:** {r['correct_ans']}. {r['options'].get(r['correct_ans'], '')}")
                    if r["explanation"]:
                        st.info(f"💡 {r['explanation']}")

            # Try again buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Try Again", use_container_width=True):
                    st.session_state.quiz_questions = None
                    st.session_state.quiz_answers   = {}
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_result    = None
                    st.rerun()
            with col2:
                if st.button("📋 Go to Review List", use_container_width=True):
                    st.session_state.page = "Review List"
                    st.rerun()
