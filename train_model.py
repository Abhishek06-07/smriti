"""
Smriti — ML Model Training Script (Fixed)
Run this ONCE:
    python3 train_model.py
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error, classification_report
from sklearn.pipeline import Pipeline
import pickle
import os

print("=" * 55)
print("  Smriti — ML Model Training (Fixed)")
print("=" * 55)

DATASET_PATH = "/Users/abhi_shake/Downloads/learning_traces.13m.csv"

# ── STEP 1: LOAD ──────────────────────────────────────────
print("\n📂 Step 1 — Loading dataset...")
df = pd.read_csv(DATASET_PATH)
print(f"   ✅ Loaded {len(df):,} rows")
print(f"   Columns: {list(df.columns)}")

# ── STEP 2: CLEAN ─────────────────────────────────────────
print("\n🧹 Step 2 — Cleaning...")
df = df.dropna()
df = df[(df['p_recall'] >= 0) & (df['p_recall'] <= 1)]

# ── STEP 3: FIX DELTA — Convert seconds → days ───────────
print("\n⚙️  Step 3 — Feature Engineering...")
print(f"   Raw delta sample: {df['delta'].head(3).values}")

# delta is in SECONDS — convert to days
df['delta_days'] = df['delta'] / 86400.0
print(f"   delta_days sample: {df['delta_days'].head(3).values.round(2)}")

# Remove extreme outliers
df = df[df['delta_days'] <= 365]   # max 1 year gap
df = df[df['delta_days'] >= 0]
print(f"   After outlier removal: {len(df):,} rows")

# ── STEP 4: FEATURE SELECTION ────────────────────────────
print("\n🎯 Step 4 — Selecting features...")

# Key features from Ebbinghaus Half-Life paper
df['half_life_feature'] = np.log1p(df['delta_days'])
df['correct_ratio']     = (df['history_correct'] + 1) / (df['history_seen'] + 2)
df['session_ratio']     = (df['session_correct'] + 1) / (df['session_seen'] + 2)

feature_cols = [
    'half_life_feature',   # log(days) — key for forgetting curve
    'correct_ratio',       # past accuracy
    'session_ratio',       # current session accuracy
    'history_seen',        # total exposures
]

print(f"   Features: {feature_cols}")
print(f"   Sample data:")
print(df[feature_cols + ['p_recall']].head(3).to_string())

# ── STEP 5: SAMPLE ────────────────────────────────────────
print("\n✂️  Step 5 — Sampling 500K rows...")
df_sample = df.sample(n=min(500_000, len(df)), random_state=42)

X = df_sample[feature_cols].values
y = df_sample['p_recall'].values

print(f"   X shape: {X.shape}")
print(f"   y range: {y.min():.3f} — {y.max():.3f}")

# ── STEP 6: TRAIN/TEST SPLIT ─────────────────────────────
print("\n✂️  Step 6 — Train/test split (80/20)...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print(f"   Train: {len(X_train):,} | Test: {len(X_test):,}")

# ── STEP 7: REGRESSION MODEL ─────────────────────────────
print("\n🤖 Step 7 — Training Polynomial Regression...")

regression_pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('poly',   PolynomialFeatures(degree=2, include_bias=False)),
    ('model',  LinearRegression())
])

regression_pipeline.fit(X_train, y_train)
y_pred = np.clip(regression_pipeline.predict(X_test), 0, 1)

r2   = r2_score(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))

print(f"   ✅ R² Score : {r2:.4f}")
print(f"   ✅ RMSE     : {rmse:.4f}")

if r2 >= 0.4:
    print(f"   🎯 Model quality: GOOD")
elif r2 >= 0.2:
    print(f"   ⚠️  Model quality: ACCEPTABLE")
else:
    print(f"   ❌ Still low — using Ebbinghaus fallback")

# ── STEP 8: CLASSIFICATION ───────────────────────────────
print("\n🌳 Step 8 — Training Decision Tree Classifier...")

def label_p(p):
    if p >= 0.70: return "Strong"
    elif p >= 0.40: return "At-Risk"
    else: return "Weak"

y_labels_train = np.array([label_p(p) for p in y_train])
y_labels_test  = np.array([label_p(p) for p in y_test])

clf = DecisionTreeClassifier(max_depth=8, min_samples_leaf=50, random_state=42)
clf.fit(X_train, y_labels_train)
y_clf_pred = clf.predict(X_test)

print(classification_report(y_labels_test, y_clf_pred, zero_division=0))

# ── STEP 9: CLUSTERING ───────────────────────────────────
print("\n🗂️  Step 9 — Training K-Means Clustering...")
X_cluster = X[:50_000]
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
kmeans.fit(X_cluster)
print(f"   ✅ K-Means trained — 3 clusters")

# ── STEP 10: SAVE ────────────────────────────────────────
print("\n💾 Step 10 — Saving models...")
os.makedirs("models", exist_ok=True)

model_data = {
    "regression":   regression_pipeline,
    "classifier":   clf,
    "kmeans":       kmeans,
    "feature_cols": feature_cols,
    "r2_score":     r2,
    "rmse":         rmse,
}

with open("models/smriti_models.pkl", "wb") as f:
    pickle.dump(model_data, f)

print(f"   ✅ Saved to: models/smriti_models.pkl")

# ── STEP 11: QUICK TEST ───────────────────────────────────
print("\n🔍 Step 11 — Quick test...")

# Simulate: reviewed 7 days ago, 70% accuracy, 5 seen
test_delta_days   = 7.0
test_correct_ratio = 0.7
test_session_ratio = 0.8
test_history_seen  = 5.0

test_X = np.array([[
    np.log1p(test_delta_days),
    test_correct_ratio,
    test_session_ratio,
    test_history_seen
]])

pred  = np.clip(regression_pipeline.predict(test_X)[0], 0, 1)
label = clf.predict(test_X)[0]

print(f"   Input: 7 days ago, 70% accuracy, 5 exposures")
print(f"   Predicted retention : {pred*100:.1f}%")
print(f"   Classification      : {label}")

print("\n" + "=" * 55)
print(f"  ✅ Training Complete!")
print(f"  R² Score : {r2:.4f}")
print(f"  RMSE     : {rmse:.4f}")
print("=" * 55)
print("\n  Run: streamlit run app.py")
