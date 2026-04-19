import pickle
import numpy as np

with open("models/smriti_models.pkl", "rb") as f:
    bundle = pickle.load(f)

print("=== BUNDLE INSPECTION ===\n")
for k, v in bundle.items():
    print(f"Key: '{k}'")
    print(f"  Type: {type(v).__name__}")
    if k == "feature_cols":
        print(f"  Value: {v}")
    elif k in ["r2_score", "rmse"]:
        print(f"  Value: {v}")
    elif hasattr(v, "feature_names_in_"):
        print(f"  Feature names: {list(v.feature_names_in_)}")
    elif hasattr(v, "n_features_in_"):
        print(f"  n_features_in_: {v.n_features_in_}")
    print()

# Pipeline steps
reg = bundle["regression"]
print("=== PIPELINE STEPS ===")
for name, step in reg.steps:
    print(f"  Step: '{name}' → {type(step).__name__}")
    if hasattr(step, "n_output_features_"):
        print(f"    n_output_features_: {step.n_output_features_}")
    if hasattr(step, "feature_names_in_"):
        print(f"    feature_names_in_: {list(step.feature_names_in_)}")

# Classifier classes
clf = bundle["classifier"]
print(f"\n=== CLASSIFIER ===")
print(f"  Classes: {clf.classes_}")
print(f"  n_features_in_: {clf.n_features_in_}")

# KMeans
km = bundle["kmeans"]
print(f"\n=== KMEANS ===")
print(f"  n_clusters: {km.n_clusters}")
print(f"  n_features_in_: {km.n_features_in_}")
print(f"  labels_ sample: {km.labels_[:10] if hasattr(km, 'labels_') else 'N/A'}")
