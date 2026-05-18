"""
Startup Success Prediction Pipeline
Crunchbase dataset — binary classification: acquired/IPO (1) vs rest (0)
"""

import warnings
warnings.filterwarnings("ignore")

import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    roc_auc_score, f1_score, precision_score, recall_score,
    confusion_matrix, classification_report,
)
from sklearn.model_selection import StratifiedKFold, RandomizedSearchCV, train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from imblearn.over_sampling import SMOTE

# ─── paths ────────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent

TOP_UNIVERSITIES = {
    "mit", "stanford", "harvard", "caltech", "carnegie mellon", "cmu",
    "princeton", "yale", "columbia", "cornell", "upenn", "berkeley",
    "uc berkeley", "oxford", "cambridge", "imperial", "eth zurich",
    "georgia tech", "michigan", "illinois", "ucla", "ucsd",
}

# ─── helpers ──────────────────────────────────────────────────────────────────
def read(name):
    return pd.read_csv(BASE / name, low_memory=False)


def shape(df, label):
    print(f"  {label}: {df.shape}")


def class_balance(y, label=""):
    vc = y.value_counts()
    print(f"  {label} class balance — 0:{vc.get(0,0)}  1:{vc.get(1,0)}  "
          f"ratio={vc.get(0,0)/max(vc.get(1,0),1):.1f}:1")


# ─── 1. LOAD RAW DATA ─────────────────────────────────────────────────────────
print("\n[1] Loading raw data...")

objects      = read("objects.csv")
funding      = read("funding_rounds.csv")
investments  = read("investments.csv")
relationships = read("relationships.csv")
people       = read("people.csv")
degrees      = read("degrees.csv")
milestones   = read("milestones.csv")
offices      = read("offices.csv")
acquisitions = read("acquisitions.csv")
ipos         = read("ipos.csv")

for df, name in [
    (objects, "objects"), (funding, "funding_rounds"),
    (investments, "investments"), (relationships, "relationships"),
    (people, "people"), (degrees, "degrees"), (milestones, "milestones"),
    (offices, "offices"), (acquisitions, "acquisitions"), (ipos, "ipos"),
]:
    shape(df, name)

# ─── 2. BUILD COMPANY BASE ────────────────────────────────────────────────────
print("\n[2] Building company base table...")

companies = objects[objects["entity_type"] == "Company"].copy()
shape(companies, "companies after entity_type filter")

# ─── 3. TARGET VARIABLE ───────────────────────────────────────────────────────
print("\n[3] Building target variable...")

acquired_ids = set(acquisitions["acquired_object_id"].dropna())
ipo_ids      = set(ipos["object_id"].dropna())
status_success = {"acquired", "ipo"}

def make_label(row):
    if row["id"] in acquired_ids or row["id"] in ipo_ids:
        return 1
    if str(row.get("status", "")).lower() in status_success:
        return 1
    return 0

companies["label"] = companies.apply(make_label, axis=1)
class_balance(companies["label"], "companies")

# ─── 4. FEATURES FROM objects.csv ─────────────────────────────────────────────
print("\n[4] Base features from objects.csv...")

companies["founded_at"] = pd.to_datetime(companies["founded_at"], errors="coerce")
companies["founded_year"] = companies["founded_at"].dt.year

feat = companies[["id", "label", "founded_year", "category_code",
                   "country_code", "state_code"]].copy()
feat.rename(columns={"id": "company_id"}, inplace=True)

shape(feat, "base feature table")

# ─── 5. FEATURES FROM funding_rounds.csv ──────────────────────────────────────
print("\n[5] Funding features...")

funding["raised_amount_usd"] = pd.to_numeric(funding["raised_amount_usd"], errors="coerce")
funding["funded_at"] = pd.to_datetime(funding["funded_at"], errors="coerce")

fund_grp = funding.groupby("object_id")

funding_feat = pd.DataFrame({
    "company_id"       : fund_grp["object_id"].first().index,
    "total_funding_usd": fund_grp["raised_amount_usd"].sum(),
    "num_funding_rounds": fund_grp["id"].count(),
    "avg_funding_per_round": fund_grp["raised_amount_usd"].mean(),
    "first_funded_at"  : fund_grp["funded_at"].min(),
}).reset_index(drop=True)

# time from founded_at to first funding
company_dates = companies[["id", "founded_at"]].rename(columns={"id": "company_id"})
funding_feat = funding_feat.merge(company_dates, on="company_id", how="left")
funding_feat["days_to_first_funding"] = (
    (funding_feat["first_funded_at"] - funding_feat["founded_at"])
    .dt.days.clip(lower=0)
)
funding_feat.drop(columns=["first_funded_at", "founded_at"], inplace=True)

feat = feat.merge(funding_feat, on="company_id", how="left")
shape(feat, "after funding features")

# ─── 6. FEATURES FROM investments.csv ─────────────────────────────────────────
print("\n[6] Investor features...")

inv_grp = investments.groupby("funded_object_id")

inv_feat = pd.DataFrame({
    "company_id"          : inv_grp["funded_object_id"].first().index,
    "num_unique_investors": inv_grp["investor_object_id"].nunique(),
}).reset_index(drop=True)

feat = feat.merge(inv_feat, on="company_id", how="left")
shape(feat, "after investor features")

# ─── 7. FEATURES FROM relationships.csv + people.csv ─────────────────────────
print("\n[7] Founder/team features...")

rel = relationships.copy()
rel["title_lower"] = rel["title"].fillna("").str.lower()

# founders = rows where title contains founder or ceo
is_founder = rel["title_lower"].str.contains(r"founder|co-founder|ceo", regex=True)
founders = rel[is_founder].copy()

rel_grp = founders.groupby("relationship_object_id")

rel_feat = pd.DataFrame({
    "company_id"   : rel_grp["relationship_object_id"].first().index,
    "num_founders" : rel_grp["person_object_id"].nunique(),
}).reset_index(drop=True)

feat = feat.merge(rel_feat, on="company_id", how="left")
shape(feat, "after founder count features")

# ─── 8. FEATURES FROM degrees.csv ─────────────────────────────────────────────
print("\n[8] Education features...")

# map person object_id → company via relationships (any role)
person_to_companies = (
    relationships[["person_object_id", "relationship_object_id"]]
    .dropna()
    .drop_duplicates()
)

deg = degrees.copy()
deg["degree_type_lower"] = deg["degree_type"].fillna("").str.lower()
deg["subject_lower"]     = deg["subject"].fillna("").str.lower()
deg["institution_lower"] = deg["institution"].fillna("").str.lower()

deg["has_mba"] = deg["degree_type_lower"].str.contains("mba", na=False).astype(int)
deg["has_cs"]  = deg["subject_lower"].str.contains(
    r"computer|software|engineering|cs\b|electrical", regex=True, na=False).astype(int)
deg["top_uni"] = deg["institution_lower"].apply(
    lambda x: int(any(u in x for u in TOP_UNIVERSITIES))
)

deg_merged = deg.merge(
    person_to_companies,
    left_on="object_id", right_on="person_object_id",
    how="inner"
)

deg_grp = deg_merged.groupby("relationship_object_id")

deg_feat = pd.DataFrame({
    "company_id"           : deg_grp["relationship_object_id"].first().index,
    "num_founders_with_deg": deg_grp["object_id"].nunique(),
    "num_mba"              : deg_grp["has_mba"].sum(),
    "num_cs_deg"           : deg_grp["has_cs"].sum(),
    "any_top_uni"          : deg_grp["top_uni"].max(),
}).reset_index(drop=True)

feat = feat.merge(deg_feat, on="company_id", how="left")
shape(feat, "after education features")

# ─── 9. FEATURES FROM milestones.csv ──────────────────────────────────────────
print("\n[9] Milestone features...")

milestones["milestone_at"] = pd.to_datetime(milestones["milestone_at"], errors="coerce")
ms_grp = milestones.groupby("object_id")

ms_feat = pd.DataFrame({
    "company_id"     : ms_grp["object_id"].first().index,
    "num_milestones" : ms_grp["id"].count(),
    "first_milestone": ms_grp["milestone_at"].min(),
}).reset_index(drop=True)

ms_feat = ms_feat.merge(company_dates, on="company_id", how="left")
ms_feat["days_to_first_milestone"] = (
    (ms_feat["first_milestone"] - ms_feat["founded_at"])
    .dt.days.clip(lower=0)
)
ms_feat.drop(columns=["first_milestone", "founded_at"], inplace=True)

feat = feat.merge(ms_feat, on="company_id", how="left")
shape(feat, "after milestone features")

# ─── 10. FEATURES FROM offices.csv ────────────────────────────────────────────
print("\n[10] Office/HQ features...")

# take one row per company (first office = HQ proxy)
hq = offices.drop_duplicates("object_id")[["object_id", "country_code", "state_code"]].copy()
hq.rename(columns={
    "object_id"    : "company_id",
    "country_code" : "hq_country",
    "state_code"   : "hq_state",
}, inplace=True)

# office country overrides objects.csv country where missing
feat = feat.merge(hq, on="company_id", how="left")
feat["country_code"] = feat["country_code"].fillna(feat["hq_country"])
feat["state_code"]   = feat["state_code"].fillna(feat["hq_state"])
feat.drop(columns=["hq_country", "hq_state"], inplace=True)

shape(feat, "after office features")

# ─── 11. FINAL FEATURE TABLE ──────────────────────────────────────────────────
print("\n[11] Finalising feature table...")

# fill numeric NAs with 0 (absence of data = 0 activity)
numeric_cols = [
    "total_funding_usd", "num_funding_rounds", "avg_funding_per_round",
    "days_to_first_funding", "num_unique_investors",
    "num_founders", "num_founders_with_deg", "num_mba", "num_cs_deg", "any_top_uni",
    "num_milestones", "days_to_first_milestone",
]
for col in numeric_cols:
    if col in feat.columns:
        feat[col] = feat[col].fillna(0)

feat["founded_year"] = feat["founded_year"].fillna(feat["founded_year"].median())

# encode categoricals
cat_cols = ["category_code", "country_code", "state_code"]
for col in cat_cols:
    feat[col] = feat[col].fillna("unknown")
    le = LabelEncoder()
    feat[col] = le.fit_transform(feat[col].astype(str))

feat.to_csv(BASE / "features.csv", index=False)
print(f"  Saved features.csv  shape={feat.shape}")

X = feat.drop(columns=["company_id", "label"])
y = feat["label"]

print(f"\n  Feature count: {X.shape[1]}")
class_balance(y, "full dataset")
print(f"  Features: {list(X.columns)}")

# ─── 12. TRAIN / TEST SPLIT ───────────────────────────────────────────────────
print("\n[12] Train/test split (80/20 stratified)...")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
class_balance(y_train, "train")
class_balance(y_test,  "test")

# ─── 13. Skip SMOTE — use class_weight="balanced" in models instead ───────────
print("\n[13] Skipping SMOTE — using class_weight=balanced in models (faster)...")
X_train_sm, y_train_sm = X_train, y_train
class_balance(y_train_sm, "train (no resampling)")

# ─── 14. MODEL DEFINITIONS ────────────────────────────────────────────────────
print("\n[14] Defining models and hyperparameter grids...")

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

MODELS = {
    "LightGBM": (
        LGBMClassifier(
            class_weight="balanced", random_state=42,
            n_jobs=-1, verbose=-1,
        ),
        {
            "n_estimators": [100, 200],
            "max_depth": [6, 10],
            "learning_rate": [0.05, 0.1],
            "num_leaves": [31, 63],
        },
    ),
}

# ─── 15. TRAIN + TUNE ─────────────────────────────────────────────────────────
print("\n[15] Training and tuning models (RandomizedSearchCV, 5-fold)...")

results = {}

for name, (estimator, param_grid) in MODELS.items():
    print(f"\n  → {name}")
    search = RandomizedSearchCV(
        estimator,
        param_distributions=param_grid,
        n_iter=5,
        scoring="roc_auc",
        cv=cv,
        refit=True,
        random_state=42,
        n_jobs=1,  # avoid deadlock with LightGBM's internal threading
    )
    search.fit(X_train_sm, y_train_sm)
    best = search.best_estimator_

    y_pred  = best.predict(X_test)
    y_proba = best.predict_proba(X_test)[:, 1]

    metrics = {
        "roc_auc"  : roc_auc_score(y_test, y_proba),
        "f1"       : f1_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "recall"   : recall_score(y_test, y_pred),
        "model"    : best,
        "cv_score" : search.best_score_,
    }
    results[name] = metrics

    print(f"    CV ROC-AUC : {metrics['cv_score']:.4f}")
    print(f"    Test ROC-AUC: {metrics['roc_auc']:.4f}  "
          f"F1: {metrics['f1']:.4f}  "
          f"P: {metrics['precision']:.4f}  "
          f"R: {metrics['recall']:.4f}")
    print(f"    Best params: {search.best_params_}")
    print("    Confusion matrix:")
    print(confusion_matrix(y_test, y_pred))


# ─── 17. PICK BEST MODEL ──────────────────────────────────────────────────────
print("\n[17] Model comparison (sorted by ROC-AUC):")

final_ranked = sorted(results.items(), key=lambda x: x[1]["roc_auc"], reverse=True)
print(f"  {'Model':<22} {'ROC-AUC':>9} {'F1':>7} {'Precision':>10} {'Recall':>8}")
print("  " + "-" * 60)
for name, m in final_ranked:
    print(f"  {name:<22} {m['roc_auc']:>9.4f} {m['f1']:>7.4f} "
          f"{m['precision']:>10.4f} {m['recall']:>8.4f}")

best_name, best_metrics = final_ranked[0]
best_model = best_metrics["model"]
print(f"\n  Best model: {best_name}  (ROC-AUC={best_metrics['roc_auc']:.4f})")

# ─── 18. FEATURE IMPORTANCES ─────────────────────────────────────────────────
print("\n[18] Feature importances for best model...")

feature_names = list(X.columns)

def get_importances(model, names):
    # VotingClassifier — average importances of tree-based estimators
    if hasattr(model, "estimators_"):
        imps = []
        for est in model.estimators_:
            if hasattr(est, "feature_importances_"):
                imps.append(est.feature_importances_)
        if imps:
            return np.mean(imps, axis=0)
    if hasattr(model, "feature_importances_"):
        return model.feature_importances_
    if hasattr(model, "coef_"):
        return np.abs(model.coef_[0])
    return None

importances = get_importances(best_model, feature_names)
if importances is not None:
    imp_df = pd.DataFrame({"feature": feature_names, "importance": importances})
    imp_df = imp_df.sort_values("importance", ascending=False)
    print(imp_df.to_string(index=False))
else:
    print("  No feature importances available for this model type.")

# ─── 19. SAVE ARTIFACTS ───────────────────────────────────────────────────────
print("\n[19] Saving artifacts...")

model_path = BASE / "best_model.pkl"
with open(model_path, "wb") as f:
    pickle.dump({"model": best_model, "feature_names": feature_names, "model_name": best_name}, f)
print(f"  Saved best_model.pkl  ({best_name})")

print("\n✓ Pipeline complete.")
