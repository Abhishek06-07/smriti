"""
Smriti — Database Layer
Uses Supabase (PostgreSQL) for cloud persistence
Falls back to SQLite for local development
"""

import os
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from pathlib import Path

# Load .env
load_dotenv()
load_dotenv(dotenv_path=Path(__file__).parent / ".env")
load_dotenv(dotenv_path=Path.cwd() / ".env")

# ── SUPABASE CLIENT ───────────────────────────────────────
def get_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    # Also try reading directly from .env file
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
        raise ValueError("SUPABASE_URL or SUPABASE_KEY not found in .env!")

    from supabase import create_client
    return create_client(url, key)

# ── INIT DB — Just verify connection ─────────────────────
def init_db():
    """Verify Supabase connection"""
    try:
        sb = get_supabase()
        sb.table("topics").select("id").limit(1).execute()
        print("✅ Supabase connected!")
    except Exception as e:
        print(f"⚠️ Supabase connection issue: {e}")

# ── TOPICS ────────────────────────────────────────────────
def add_topic(topic_name, subject, understanding_score, date_learned=None):
    if date_learned is None:
        date_learned = datetime.now().strftime("%Y-%m-%d")
    sb = get_supabase()
    sb.table("topics").insert({
        "topic_name":          topic_name,
        "subject":             subject,
        "understanding_score": understanding_score,
        "date_learned":        str(date_learned),
        "review_count":        0,
    }).execute()

def get_all_topics():
    sb   = get_supabase()
    res  = sb.table("topics").select("*").order("date_learned", desc=True).execute()
    rows = res.data
    # Convert to tuple format matching old SQLite format
    return [
        (
            r["id"],
            r["topic_name"],
            r["subject"],
            r["understanding_score"],
            r["date_learned"],
            r.get("last_reviewed"),
            r.get("review_count", 0),
        )
        for r in rows
    ]

def add_review(topic_id, retention_score):
    today = datetime.now().strftime("%Y-%m-%d")
    sb    = get_supabase()

    # Insert review
    sb.table("reviews").insert({
        "topic_id":        topic_id,
        "review_date":     today,
        "retention_score": retention_score,
    }).execute()

    # Get current review count
    res   = sb.table("topics").select("review_count").eq("id", topic_id).execute()
    count = res.data[0]["review_count"] if res.data else 0

    # Update topic
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
    """No-op for Supabase — table already created via SQL"""
    pass

def mark_today_studied():
    today = datetime.now().strftime("%Y-%m-%d")
    sb    = get_supabase()
    try:
        sb.table("streaks").insert({"study_date": today}).execute()
    except Exception:
        pass  # Already exists — unique constraint

def get_streak():
    sb    = get_supabase()
    res   = sb.table("streaks").select("study_date").order("study_date", desc=True).execute()
    dates = [r["study_date"] for r in res.data]

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

def get_total_study_days():
    sb  = get_supabase()
    res = sb.table("streaks").select("id", count="exact").execute()
    return res.count or 0

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
    """No-op for Supabase — table already created via SQL"""
    pass

def add_xp(activity, note=""):
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
    }).execute()
    return xp

def get_total_xp():
    sb  = get_supabase()
    res = sb.table("xp_log").select("xp_earned").execute()
    return sum(r["xp_earned"] for r in res.data) if res.data else 0

def get_today_xp():
    today = datetime.now().strftime("%Y-%m-%d")
    sb    = get_supabase()
    res   = sb.table("xp_log").select("xp_earned").eq("earned_date", today).execute()
    return sum(r["xp_earned"] for r in res.data) if res.data else 0

def get_xp_by_subject(topics):
    sb         = get_supabase()
    subject_xp = {}
    for topic in topics:
        subj      = topic["subject"]
        base      = XP_REWARDS["add_topic"]
        res       = sb.table("reviews").select("id", count="exact").eq("topic_id", topic["id"]).execute()
        reviews   = res.count or 0
        review_xp = reviews * XP_REWARDS["review_topic"]
        subject_xp[subj] = subject_xp.get(subj, 0) + base + review_xp
    return subject_xp

def get_league(total_xp):
    league = LEAGUE_THRESHOLDS[0]
    for threshold, name, color in LEAGUE_THRESHOLDS:
        if total_xp >= threshold:
            league = (threshold, name, color)
    return league

def get_xp_history(days=7):
    sb  = get_supabase()
    res = sb.table("xp_log").select("earned_date, xp_earned").order("earned_date", desc=True).execute()

    # Group by date manually
    from collections import defaultdict
    daily = defaultdict(int)
    for r in res.data:
        daily[r["earned_date"]] += r["xp_earned"]

    # Sort and limit
    sorted_days = sorted(daily.items(), reverse=True)[:days]
    return [(d, xp) for d, xp in sorted_days]
