# Startup Success Prediction — ML Pipeline

Binary classification model that predicts whether a startup will be **acquired or go public (IPO)** using the Crunchbase dataset.

---

## Overview

| | |
|---|---|
| **Task** | Binary classification (success = acquired or IPO) |
| **Model** | LightGBM with `class_weight=balanced` |
| **ROC-AUC** | 0.839 |
| **Recall** | 0.795 |
| **Dataset** | Crunchbase (196,553 companies) |
| **Class ratio** | 17.7:1 (imbalanced) |

---

## Dataset

Place the following CSV files in the `model/` directory:

| File | Description |
|---|---|
| `objects.csv` | Core entity table — companies, people, financial orgs |
| `funding_rounds.csv` | Funding events per company |
| `investments.csv` | Investor → company relationships |
| `relationships.csv` | Person → company role mappings |
| `people.csv` | Founder/executive profiles |
| `degrees.csv` | Education records per person |
| `milestones.csv` | Company milestone events |
| `offices.csv` | Office locations per company |
| `acquisitions.csv` | Acquisition events (used to build labels) |
| `ipos.csv` | IPO events (used to build labels) |

---

## Target Variable

A company is labeled **success (1)** if:
- It appears in `acquisitions.csv` (as the acquired company), **or**
- It appears in `ipos.csv`, **or**
- Its `status` field in `objects.csv` is `"acquired"` or `"ipo"`

Everything else is **failure (0)**.

---

## Features (16 total)

| Feature | Source |
|---|---|
| `category_code` | objects.csv — industry category |
| `founded_year` | objects.csv — year founded |
| `country_code` | objects.csv / offices.csv |
| `state_code` | objects.csv / offices.csv |
| `total_funding_usd` | funding_rounds.csv |
| `num_funding_rounds` | funding_rounds.csv |
| `avg_funding_per_round` | funding_rounds.csv |
| `days_to_first_funding` | funding_rounds.csv + objects.csv |
| `num_unique_investors` | investments.csv |
| `num_founders` | relationships.csv (title contains founder/ceo) |
| `num_founders_with_deg` | degrees.csv + relationships.csv |
| `num_mba` | degrees.csv |
| `num_cs_deg` | degrees.csv |
| `any_top_uni` | degrees.csv (MIT, Stanford, Harvard, etc.) |
| `num_milestones` | milestones.csv |
| `days_to_first_milestone` | milestones.csv + objects.csv |

---

## Pipeline Steps

```
1. Load raw CSVs
2. Filter companies (entity_type == "Company")
3. Build binary labels from acquisitions + ipos + status
4. Engineer features from all tables
5. Encode categoricals (LabelEncoder)
6. Train/test split — 80/20 stratified
7. Train LightGBM with RandomizedSearchCV (5-fold CV, 5 iterations)
8. Evaluate: ROC-AUC, F1, Precision, Recall, confusion matrix
9. Print feature importances
10. Save best_model.pkl and features.csv
```

---

## Results

```
LightGBM — Best params: num_leaves=63, n_estimators=100, max_depth=10, learning_rate=0.05

ROC-AUC : 0.8390
F1      : 0.2367
Precision: 0.1391
Recall  : 0.7953

Confusion matrix:
[[26836  10369]
 [  431   1675]]
```

### Feature Importances (top 5)

| Feature | Importance |
|---|---|
| `category_code` | 1247 |
| `founded_year` | 965 |
| `days_to_first_funding` | 575 |
| `country_code` | 423 |
| `num_founders_with_deg` | 413 |

---

## Setup

```bash
cd model/
python3 -m venv venv
source venv/bin/activate
pip install pandas scikit-learn xgboost lightgbm imbalanced-learn
python3 startup_success_pipeline.py
```

---

## Output Files

| File | Description |
|---|---|
| `features.csv` | Full feature table (196,553 rows × 18 cols) |
| `best_model.pkl` | Serialized LightGBM model + feature names |

### Loading the model

```python
import pickle

with open("best_model.pkl", "rb") as f:
    artifact = pickle.load(f)

model = artifact["model"]
feature_names = artifact["feature_names"]

# predict on new data
proba = model.predict_proba(X_new)[:, 1]
```

---

## Notes

- The dataset is heavily imbalanced (17.7:1). `class_weight="balanced"` is used instead of SMOTE for speed.
- High recall (0.795) is prioritized — the model catches 80% of actual successes at the cost of false positives, which is acceptable for a screening/ranking use case.
- `best_model.pkl` is consumed by the main capAI API to score founders.
