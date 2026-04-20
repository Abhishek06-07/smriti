"""
Smriti — Database Layer
Uses Supabase (PostgreSQL) with user authentication
"""

import os
from datetime import datetime, date, timedelta
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False

# Load .env
load_dotenv()
load_dotenv(dotenv_path=Path(__file__).parent / ".env")
load_dotenv(dotenv_path=Path.cwd() / ".env")

# ── SUPABASE CLIENT ───────────────────────────────────────
def get_supabase():
    # Try Streamlit secrets first (cloud deployment)
    try:
        import streamlit as st
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
        if url and key:
            from supabase import create_client
            return create_client(url, key)
    except Exception:
        pass

    # Try environment variables
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    # Try reading directly from .env file
    if not url or not key:
        for env_path in [Path(__file__).parent / ".env", Path.cwd() / ".env"]:
            if env_path.exists():
                with open(env_path) as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("SUPABASE_URL="):
                            url = line.split("=", 1)[1].strip()
                        elif line.startswith("SUPABASE_KEY="):
                            key = line.split("=", 1)[1].strip()

    if not url or not key:
        raise ValueError("SUPABASE_URL or SUPABASE_KEY not found!")

    from supabase import create_client
    return create_client(url, key)

# ── AUTH FUNCTIONS ────────────────────────────────────────
def sign_up(email, password):
    try:
        sb  = get_supabase()
        res = sb.auth.sign_up({"email": email, "password": password})
        if res.user:
            return res.user, None
        return None, "Signup failed"
    except Exception as e:
        return None, str(e)

def sign_in(email, password):
    try:
        sb  = get_supabase()
        res = sb.auth.sign_in_with_password({"email": email, "password": password})
        if res.user:
            return res.user, None
        return None, "Invalid email or password"
    except Exception as e:
        return None, "Invalid email or password"

def sign_out():
    try:
        sb = get_supabase()
        sb.auth.sign_out()
    except Exception:
        pass

# ── INIT DB ───────────────────────────────────────────────
def init_db():
    try:
        sb = get_supabase()
        sb.table("topics").select("id").limit(1).execute()
    except Exception as e:
        print(f"Supabase: {e}")

# ── TOPICS ────────────────────────────────────────────────
def add_topic(topic_name, subject, understanding_score,
              date_learned=None, user_id=None):
    if date_learned is None:
        date_learned = datetime.now().strftime("%Y-%m-%d")
    sb = get_supabase()
    sb.table("topics").insert({
        "topic_name":          topic_name,
        "subject":             subject,
        "understanding_score": understanding_score,
        "date_learned":        str(date_learned),
        "review_count":        0,
        "user_id":             user_id,
    }).execute()

def get_all_topics(user_id=None):
    sb = get_supabase()
    q  = sb.table("topics").select("*").order("date_learned", desc=True)
    if user_id:
        q = q.eq("user_id", user_id)
    res = q.execute()
    return [
        (
            r["id"], r["topic_name"], r["subject"],
            r["understanding_score"], r["date_learned"],
            r.get("last_reviewed"), r.get("review_count", 0),
        )
        for r in res.data
    ]

def add_review(topic_id, retention_score, user_id=None):
    today = datetime.now().strftime("%Y-%m-%d")
    sb    = get_supabase()
    sb.table("reviews").insert({
        "topic_id":        topic_id,
        "review_date":     today,
        "retention_score": retention_score,
        "user_id":         user_id,
    }).execute()
    res   = sb.table("topics").select("review_count").eq("id", topic_id).execute()
    count = res.data[0]["review_count"] if res.data else 0
    sb.table("topics").update({
        "last_reviewed": today,
        "review_count":  count + 1,
    }).eq("id", topic_id).execute()

def get_reviews(topic_id):
    sb  = get_supabase()
    res = sb.table("reviews").select("*").eq("topic_id", topic_id).execute()
    return res.data

def delete_topic(topic_id):
    sb = get_supabase()
    sb.table("reviews").delete().eq("topic_id", topic_id).execute()
    sb.table("topics").delete().eq("id", topic_id).execute()

# ── STREAK ────────────────────────────────────────────────
def init_streak_table():
    pass

def mark_today_studied(user_id=None):
    today = datetime.now().strftime("%Y-%m-%d")
    sb    = get_supabase()
    try:
        sb.table("streaks").insert({
            "study_date": today,
            "user_id":    user_id,
        }).execute()
    except Exception:
        pass

def get_streak(user_id=None):
    sb = get_supabase()
    q  = sb.table("streaks").select("study_date").order("study_date", desc=True)
    if user_id:
        q = q.eq("user_id", user_id)
    dates = [r["study_date"] for r in q.execute().data]
    if not dates:
        return 0
    streak = 0
    check  = date.today()
    for d in dates:
        day = date.fromisoformat(d)
        if day == check or day == check - timedelta(days=1):
            streak += 1
            check   = day - timedelta(days=1)
        else:
            break
    return streak

def get_total_study_days(user_id=None):
    sb = get_supabase()
    q  = sb.table("streaks").select("id", count="exact")
    if user_id:
        q = q.eq("user_id", user_id)
    return q.execute().count or 0

# ── XP SYSTEM ─────────────────────────────────────────────
XP_REWARDS = {
    "add_topic":      10,
    "review_topic":   15,
    "quiz_l1":        20,
    "quiz_l2":        25,
    "quiz_l3":        30,
    "quiz_l4":        35,
    "quiz_l5":        40,
    "quiz_l6":        50,
    "quiz_100_bonus": 10,
    "streak_daily":    5,
}

LEAGUE_THRESHOLDS = [
    (0,    "🥉 Bronze",  "#CD7F32"),
    (101,  "🥈 Silver",  "#94A3B8"),
    (301,  "🥇 Gold",    "#C9A84C"),
    (601,  "💎 Diamond", "#60A5FA"),
    (1001, "🏆 Legend",  "#7C3AED"),
]

def init_xp_table():
    pass

def add_xp(activity, note="", user_id=None):
    xp = XP_REWARDS.get(activity, 0)
    if xp == 0:
        return 0
    sb    = get_supabase()
    today = datetime.now().strftime("%Y-%m-%d")
    sb.table("xp_log").insert({
        "activity":    activity,
        "xp_earned":   xp,
        "earned_date": today,
        "note":        note,
        "user_id":     user_id,
    }).execute()
    return xp

def get_total_xp(user_id=None):
    sb = get_supabase()
    q  = sb.table("xp_log").select("xp_earned")
    if user_id:
        q = q.eq("user_id", user_id)
    res = q.execute()
    return sum(r["xp_earned"] for r in res.data) if res.data else 0

def get_today_xp(user_id=None):
    today = datetime.now().strftime("%Y-%m-%d")
    sb    = get_supabase()
    q     = sb.table("xp_log").select("xp_earned").eq("earned_date", today)
    if user_id:
        q = q.eq("user_id", user_id)
    res = q.execute()
    return sum(r["xp_earned"] for r in res.data) if res.data else 0

def get_xp_by_subject(topics, user_id=None):
    sb         = get_supabase()
    subject_xp = {}
    for topic in topics:
        subj      = topic["subject"]
        base      = XP_REWARDS["add_topic"]
        q         = sb.table("reviews").select("id", count="exact").eq("topic_id", topic["id"])
        if user_id:
            q = q.eq("user_id", user_id)
        reviews   = q.execute().count or 0
        review_xp = reviews * XP_REWARDS["review_topic"]
        subject_xp[subj] = subject_xp.get(subj, 0) + base + review_xp
    return subject_xp

def get_league(total_xp):
    league = LEAGUE_THRESHOLDS[0]
    for threshold, name, color in LEAGUE_THRESHOLDS:
        if total_xp >= threshold:
            league = (threshold, name, color)
    return league

def get_xp_history(days=7, user_id=None):
    sb = get_supabase()
    q  = sb.table("xp_log").select("earned_date, xp_earned").order("earned_date", desc=True)
    if user_id:
        q = q.eq("user_id", user_id)
    res = q.execute()
    from collections import defaultdict
    daily = defaultdict(int)
    for r in res.data:
        daily[r["earned_date"]] += r["xp_earned"]
    return sorted(daily.items(), reverse=True)[:days]

def submit_feedback(
    category,
    rating,
    message,
    user_id=None,
):
    try:
        sb = get_supabase()
        payload = {
            "category": category,
            "rating": int(rating),
            "message": message.strip(),
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
        }
        sb.table("feedback").insert(payload).execute()
        return True, None
    except Exception as e:
        return False, str(e)

def save_quiz_mistakes(
    topic_id,
    topic_name,
    subject,
    bloom_level,
    mistakes,
    user_id=None,
):
    try:
        if not mistakes:
            return 0, None

        sb = get_supabase()
        today = datetime.now().strftime("%Y-%m-%d")
        now = datetime.utcnow().isoformat()
        payload = []

        for item in mistakes:
            payload.append({
                "topic_id": topic_id,
                "topic_name": topic_name,
                "subject": subject,
                "bloom_level": int(bloom_level),
                "question_text": item.get("question", "").strip(),
                "question_type": item.get("type", "mcq"),
                "user_answer": str(item.get("user_answer", "")).strip(),
                "correct_answer": str(item.get("correct_answer", "")).strip(),
                "explanation": item.get("explanation", "").strip(),
                "user_id": user_id,
                "status": "open",
                "review_after": today,
                "retry_count": 0,
                "created_at": now,
                "updated_at": now,
            })

        sb.table("mistake_book").insert(payload).execute()
        return len(payload), None
    except Exception as e:
        return 0, str(e)

def get_mistake_book(user_id=None, include_resolved=False):
    try:
        sb = get_supabase()
        q = sb.table("mistake_book").select("*").order("review_after").order("created_at", desc=True)
        if user_id:
            q = q.eq("user_id", user_id)
        if not include_resolved:
            q = q.neq("status", "mastered")
        res = q.execute()
        return res.data or [], None
    except Exception as e:
        return [], str(e)

def snooze_mistake(mistake_id, retry_days=2):
    try:
        sb = get_supabase()
        res = sb.table("mistake_book").select("retry_count").eq("id", mistake_id).limit(1).execute()
        current_retry = res.data[0]["retry_count"] if res.data else 0
        next_review = (date.today() + timedelta(days=retry_days)).isoformat()
        sb.table("mistake_book").update({
            "review_after": next_review,
            "retry_count": current_retry + 1,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", mistake_id).execute()
        return True, None
    except Exception as e:
        return False, str(e)

def mark_mistake_mastered(mistake_id):
    try:
        sb = get_supabase()
        sb.table("mistake_book").update({
            "status": "mastered",
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", mistake_id).execute()
        return True, None
    except Exception as e:
        return False, str(e)

def delete_mistake(mistake_id):
    try:
        sb = get_supabase()
        sb.table("mistake_book").delete().eq("id", mistake_id).execute()
        return True, None
    except Exception as e:
        return False, str(e)
