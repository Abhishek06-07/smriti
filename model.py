import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.cluster import KMeans
from datetime import datetime, date

# ── FORGETTING CURVE ──────────────────────────────────────
def ebbinghaus_retention(t, stability=1.5):
    """
    Ebbinghaus forgetting curve formula
    t         = days since learned
    stability = personal memory strength (higher = stronger)
    returns   = retention % (0 to 100)
    """
    return round(100 * np.exp(-t / (stability * 10)))

def personal_stability(understanding_score, review_count=0):
    """
    Calculate personal stability based on understanding score
    Higher score + more reviews = stronger memory
    """
    base = understanding_score / 10
    boost = review_count * 0.15
    return max(0.5, base + boost)

def get_retention_curve(understanding_score, date_learned, review_count=0):
    """
    Generate 30-day retention curve for a topic
    Returns list of (day, retention%) pairs
    """
    try:
        learned = datetime.strptime(date_learned, "%Y-%m-%d").date()
    except Exception:
        learned = date.today()

    days_passed = (date.today() - learned).days
    stability = personal_stability(understanding_score, review_count)

    curve = []
    for day in range(0, 31):
        t = days_passed + day
        retention = ebbinghaus_retention(t, stability)
        retention = max(5, min(100, retention))
        curve.append({"day": day, "retention": retention})
    return curve

def current_retention(understanding_score, date_learned, review_count=0):
    """Get today's retention % for a topic"""
    try:
        learned = datetime.strptime(date_learned, "%Y-%m-%d").date()
    except Exception:
        return 50
    days_passed = (date.today() - learned).days
    stability = personal_stability(understanding_score, review_count)
    return max(5, min(100, ebbinghaus_retention(days_passed, stability)))

# ── CLASSIFICATION — Weak / At-Risk / Strong ──────────────
def classify_topic(retention_pct, review_count):
    """
    Classify topic strength based on retention and review count
    Returns: Strong / At-Risk / Weak with emoji
    """
    if retention_pct >= 70:
        return "Strong 💪", "green"
    elif retention_pct >= 40:
        return "At-Risk ⚠️", "orange"
    else:
        return "Weak 🔴", "red"

# ── REGRESSION — Predict future retention ────────────────
def predict_future_retention(understanding_score, date_learned, review_count, days_ahead=7):
    """
    Predict retention % after N days from today
    """
    try:
        learned = datetime.strptime(date_learned, "%Y-%m-%d").date()
    except Exception:
        learned = date.today()

    days_passed = (date.today() - learned).days + days_ahead
    stability = personal_stability(understanding_score, review_count)
    return max(5, min(100, ebbinghaus_retention(days_passed, stability)))

# ── CLUSTERING — Group similar topics ────────────────────
def cluster_topics(topics_data):
    """
    Group topics by retention similarity
    topics_data = list of [retention, understanding_score]
    Returns cluster labels
    """
    if len(topics_data) < 3:
        return [0] * len(topics_data)
    X = np.array(topics_data)
    n_clusters = min(3, len(topics_data))
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    return labels.tolist()

# ── REVIEW SCHEDULER ──────────────────────────────────────
def get_review_priority(topics):
    """
    Sort topics by urgency — lowest retention first
    topics = list of topic dicts
    Returns sorted list with priority score
    """
    priority_list = []
    for topic in topics:
        ret = current_retention(
            topic["understanding_score"],
            topic["date_learned"],
            topic["review_count"]
        )
        label, color = classify_topic(ret, topic["review_count"])
        priority_list.append({
            **topic,
            "retention": ret,
            "label": label,
            "color": color,
            "urgency": 100 - ret
        })
    return sorted(priority_list, key=lambda x: x["urgency"], reverse=True)
