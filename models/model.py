"""
Smriti — ML Model Layer
Uses same features as train_model.py
"""

import numpy as np
import pickle
import os
from datetime import datetime, date

# ── LOAD TRAINED MODELS ───────────────────────────────────
_models = None

def load_models():
    global _models
    if _models is not None:
        return _models
    path = "models/smriti_models.pkl"
    if os.path.exists(path):
        with open(path, "rb") as f:
            _models = pickle.load(f)
    return _models

# ── BUILD FEATURES — same as train_model.py ──────────────
def build_features(days_elapsed, understanding_score, review_count):
    """
    Build feature vector matching training features:
    - half_life_feature = log1p(delta_days)
    - correct_ratio     = past accuracy
    - session_ratio     = current accuracy proxy
    - history_seen      = total exposures
    """
    delta_days     = max(0, days_elapsed)
    correct_ratio  = min(understanding_score / 10.0, 1.0)
    session_ratio  = correct_ratio
    history_seen   = max(review_count, 1)

    return np.array([[
        np.log1p(delta_days),   # half_life_feature
        correct_ratio,           # correct_ratio
        session_ratio,           # session_ratio
        float(history_seen),     # history_seen
    ]])

# ── EBBINGHAUS FALLBACK ───────────────────────────────────
def personal_stability(understanding_score, review_count=0):
    return max(0.5, (understanding_score / 10) + review_count * 0.15)

def ebbinghaus_retention(t, stability=1.5):
    return round(100 * np.exp(-t / (stability * 10)))

# ── CURRENT RETENTION ─────────────────────────────────────
def current_retention(understanding_score, date_learned, review_count=0):
    try:
        learned = datetime.strptime(date_learned, "%Y-%m-%d").date()
    except Exception:
        learned = date.today()

    days = (date.today() - learned).days
    models = load_models()

    if models:
        try:
            X    = build_features(days, understanding_score, review_count)
            pred = np.clip(models["regression"].predict(X)[0], 0, 1)
            return max(5, min(100, round(pred * 100)))
        except Exception:
            pass

    stab = personal_stability(understanding_score, review_count)
    return max(5, min(100, ebbinghaus_retention(days, stab)))

# ── PREDICT FUTURE RETENTION ─────────────────────────────
def predict_future_retention(understanding_score, date_learned, review_count=0, days_ahead=7):
    try:
        learned = datetime.strptime(date_learned, "%Y-%m-%d").date()
    except Exception:
        learned = date.today()

    days   = (date.today() - learned).days + days_ahead
    models = load_models()

    if models:
        try:
            X    = build_features(days, understanding_score, review_count)
            pred = np.clip(models["regression"].predict(X)[0], 0, 1)
            return max(5, min(100, round(pred * 100)))
        except Exception:
            pass

    stab = personal_stability(understanding_score, review_count)
    return max(5, min(100, ebbinghaus_retention(days, stab)))

# ── GET 30-DAY CURVE ──────────────────────────────────────
def get_retention_curve(understanding_score, date_learned, review_count=0):
    try:
        learned = datetime.strptime(date_learned, "%Y-%m-%d").date()
    except Exception:
        learned = date.today()

    days_passed = (date.today() - learned).days
    models      = load_models()
    curve       = []

    for day in range(0, 31):
        t = days_passed + day
        if models:
            try:
                X   = build_features(t, understanding_score, review_count)
                ret = np.clip(models["regression"].predict(X)[0], 0, 1)
                ret = max(5, min(100, round(ret * 100)))
            except Exception:
                stab = personal_stability(understanding_score, review_count)
                ret  = max(5, min(100, ebbinghaus_retention(t, stab)))
        else:
            stab = personal_stability(understanding_score, review_count)
            ret  = max(5, min(100, ebbinghaus_retention(t, stab)))

        curve.append({"day": day, "retention": ret})

    return curve

# ── CLASSIFY TOPIC ────────────────────────────────────────
def classify_topic(retention_pct, review_count):
    # Runtime topic status is derived from current retention bands.
    # The bundled classifier was trained on richer features than we
    # reliably have at inference time inside the app UI.
    if retention_pct >= 70:
        return "Strong 💪", "green"
    elif retention_pct >= 40:
        return "At-Risk ⚠️", "orange"
    else:
        return "Weak 🔴", "red"

# ── CLUSTERING ────────────────────────────────────────────
def cluster_topics(topics_data):
    if len(topics_data) < 3:
        return [0] * len(topics_data)
    try:
        from sklearn.cluster import KMeans
        X      = np.array(topics_data)
        n      = min(3, len(topics_data))
        kmeans = KMeans(n_clusters=n, random_state=42, n_init=10)
        return kmeans.fit_predict(X).tolist()
    except Exception:
        return [0] * len(topics_data)

# ── REVIEW PRIORITY ───────────────────────────────────────
def get_review_priority(topics):
    priority_list = []
    for topic in topics:
        ret          = current_retention(
            topic["understanding_score"],
            topic["date_learned"],
            topic["review_count"]
        )
        label, color = classify_topic(ret, topic["review_count"])
        priority_list.append({
            **topic,
            "retention": ret,
            "label":     label,
            "color":     color,
            "urgency":   100 - ret
        })
    return sorted(priority_list, key=lambda x: x["urgency"], reverse=True)

# ── MODEL STATUS ──────────────────────────────────────────
def get_model_status():
    models = load_models()
    if models:
        return {
            "loaded":   True,
            "r2_score": round(models.get("r2_score", 0), 4),
            "rmse":     round(models.get("rmse", 0), 4),
        }
    return {"loaded": False, "r2_score": None, "rmse": None}
