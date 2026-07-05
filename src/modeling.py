"""Churn prediction: logistic regression baseline + XGBoost, honestly evaluated.

Design notes
------------
- ~27% of customers churn, so accuracy alone is misleading (predicting
  "nobody churns" scores 73%). Evaluation therefore centres on ROC-AUC,
  PR-AUC and precision/recall, including at realistic campaign depths
  ("if we can only contact the riskiest 10/20/30%, what do we catch?").
- ``TotalCharges`` is excluded: it is almost exactly tenure x MonthlyCharges,
  so it adds collinearity without new information.
- The same one-hot design matrix feeds both models so coefficients, feature
  importances and SHAP values are directly comparable.
"""

import json

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from src.config import RANDOM_STATE, REPORTS_DIR, TEST_SIZE

NUMERIC_FEATURES = ["tenure", "MonthlyCharges", "n_addon_services"]
CATEGORICAL_FEATURES = [
    "gender", "SeniorCitizen", "Partner", "Dependents", "PhoneService",
    "MultipleLines", "InternetService", "OnlineSecurity", "OnlineBackup",
    "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies",
    "Contract", "PaperlessBilling", "PaymentMethod",
]


# ---------------------------------------------------------------------------
# Features and split
# ---------------------------------------------------------------------------

def build_feature_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """One-hot design matrix X and target y from the cleaned frame."""
    X = pd.get_dummies(df[NUMERIC_FEATURES + CATEGORICAL_FEATURES],
                       columns=CATEGORICAL_FEATURES)
    X = X.astype(float)
    y = df["churn_flag"].astype(int)
    return X, y


def split_data(X: pd.DataFrame, y: pd.Series):
    return train_test_split(X, y, test_size=TEST_SIZE, stratify=y,
                            random_state=RANDOM_STATE)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

def train_logistic(X_train: pd.DataFrame, y_train: pd.Series) -> Pipeline:
    """Baseline: L2 logistic regression with class weighting for imbalance."""
    pipe = Pipeline([
        ("scale", StandardScaler()),
        ("logit", LogisticRegression(class_weight="balanced", C=1.0,
                                     max_iter=2000,
                                     random_state=RANDOM_STATE)),
    ])
    pipe.fit(X_train, y_train)
    return pipe


def train_xgboost(X_train: pd.DataFrame, y_train: pd.Series) -> XGBClassifier:
    """Gradient boosting with modest, deliberately shallow settings.

    Deeper/larger configurations (e.g. 500 trees at depth 4) scored *worse*
    on held-out data (ROC-AUC 0.833 vs 0.844) — with only ~5,600 training
    rows and mostly-categorical features, this dataset rewards restraint
    over capacity. See reports/model-report.md.
    """
    imbalance = (y_train == 0).sum() / (y_train == 1).sum()
    model = XGBClassifier(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=3,
        min_child_weight=2,
        subsample=0.9,
        colsample_bytree=0.8,
        reg_lambda=1.0,
        scale_pos_weight=imbalance,
        eval_metric="auc",
        tree_method="hist",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    return model


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate(model, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    """Threshold metrics at 0.5 plus ranking metrics that don't depend on a
    threshold (ROC-AUC, PR-AUC)."""
    proba = model.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)
    return {
        "roc_auc": float(roc_auc_score(y_test, proba)),
        "pr_auc": float(average_precision_score(y_test, proba)),
        "precision_at_0.5": float(precision_score(y_test, pred)),
        "recall_at_0.5": float(recall_score(y_test, pred)),
        "f1_at_0.5": float(f1_score(y_test, pred)),
        "accuracy": float((pred == y_test).mean()),
    }


def targeting_table(proba: np.ndarray, y_true: pd.Series,
                    depths=(0.10, 0.20, 0.30)) -> pd.DataFrame:
    """Precision/recall if a retention campaign contacts only the riskiest
    X% of customers — the operating points that matter in practice."""
    order = np.argsort(-proba)
    y_sorted = np.asarray(y_true)[order]
    base_rate = y_sorted.mean()
    rows = []
    for depth in depths:
        k = max(1, int(round(depth * len(y_sorted))))
        top = y_sorted[:k]
        rows.append({
            "campaign_depth": depth,
            "customers_contacted": k,
            "precision": top.mean(),
            "recall": top.sum() / y_sorted.sum(),
            "lift_vs_random": top.mean() / base_rate,
        })
    return pd.DataFrame(rows)


def cv_roc_auc(model, X_train: pd.DataFrame, y_train: pd.Series) -> dict:
    """5-fold cross-validated ROC-AUC on the training set (stability check)."""
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="roc_auc")
    return {"mean": float(scores.mean()), "std": float(scores.std())}


# ---------------------------------------------------------------------------
# Interpretation figures
# ---------------------------------------------------------------------------

def plot_roc_pr(results: dict, y_test: pd.Series) -> str:
    """ROC and precision-recall curves for both models side by side.

    ``results`` maps model name -> predicted probabilities on the test set.
    """
    import matplotlib.pyplot as plt
    from sklearn.metrics import precision_recall_curve, roc_curve

    from src.config import PALETTE
    from src.visuals import apply_style, save_fig

    apply_style()
    colors = {"Logistic regression": PALETTE["retain"],
              "XGBoost": PALETTE["churn"]}
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.6))

    for name, proba in results.items():
        fpr, tpr, _ = roc_curve(y_test, proba)
        auc = roc_auc_score(y_test, proba)
        ax1.plot(fpr, tpr, color=colors[name], linewidth=2,
                 label=f"{name} (AUC {auc:.3f})")
    ax1.plot([0, 1], [0, 1], linestyle="--", color=PALETTE["neutral"],
             linewidth=1, label="Random")
    ax1.set_title("ROC curve (test set)")
    ax1.set_xlabel("False positive rate")
    ax1.set_ylabel("True positive rate")
    ax1.legend(loc="lower right", fontsize=9)

    for name, proba in results.items():
        prec, rec, _ = precision_recall_curve(y_test, proba)
        ap = average_precision_score(y_test, proba)
        ax2.plot(rec, prec, color=colors[name], linewidth=2,
                 label=f"{name} (PR-AUC {ap:.3f})")
    base = y_test.mean()
    ax2.axhline(base, linestyle="--", color=PALETTE["neutral"], linewidth=1)
    ax2.annotate(f"churn base rate {base:.0%}", xy=(0.02, base),
                 xytext=(0, 4), textcoords="offset points",
                 fontsize=8, color=PALETTE["neutral"])
    ax2.set_title("Precision-recall curve (test set)")
    ax2.set_xlabel("Recall")
    ax2.set_ylabel("Precision")
    ax2.set_ylim(0, 1.02)
    ax2.legend(loc="upper right", fontsize=9)

    fig.tight_layout()
    return save_fig(fig, "fig_model_roc_pr")


def plot_shap_summary(model: XGBClassifier, X_test: pd.DataFrame) -> str:
    """SHAP beeswarm for the XGBoost model (direction + magnitude per
    feature, per customer)."""
    import matplotlib.pyplot as plt
    import shap

    from src.visuals import apply_style, save_fig

    apply_style()
    explainer = shap.TreeExplainer(model)
    shap_values = explainer(X_test)
    fig = plt.figure(figsize=(9, 6))
    shap.plots.beeswarm(shap_values, max_display=12, show=False)
    ax = plt.gca()
    ax.set_title("What drives individual churn predictions (SHAP, XGBoost)")
    fig = plt.gcf()
    fig.tight_layout()
    return save_fig(fig, "fig_shap_summary")


def plot_logistic_coefficients(pipe: Pipeline, feature_names, top_n: int = 12) -> str:
    """Largest standardized coefficients from the baseline — the simple,
    audit-friendly view of churn drivers."""
    import matplotlib.pyplot as plt

    from src.config import PALETTE
    from src.visuals import apply_style, save_fig

    apply_style()
    coefs = pd.Series(pipe.named_steps["logit"].coef_[0], index=feature_names)
    top = coefs.reindex(coefs.abs().sort_values(ascending=False).index[:top_n])
    top = top.sort_values()
    colors = [PALETTE["churn"] if c > 0 else PALETTE["retain"] for c in top]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.barh(top.index, top, color=colors)
    ax.axvline(0, color=PALETTE["dark"], linewidth=1)
    ax.set_title("Largest churn drivers in the logistic baseline\n(red pushes toward churn, teal toward staying)")
    ax.set_xlabel("Standardized coefficient (log-odds)")
    ax.grid(axis="x")
    ax.grid(axis="y", visible=False)
    return save_fig(fig, "fig_logit_coefficients")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_modeling(df: pd.DataFrame, save_metrics: bool = True) -> dict:
    """Train, evaluate and explain both models; returns everything the
    notebooks and deck need."""
    X, y = build_feature_frame(df)
    X_train, X_test, y_train, y_test = split_data(X, y)

    logit = train_logistic(X_train, y_train)
    xgb = train_xgboost(X_train, y_train)

    proba = {
        "Logistic regression": logit.predict_proba(X_test)[:, 1],
        "XGBoost": xgb.predict_proba(X_test)[:, 1],
    }

    metrics = {
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "churn_rate_test": float(y_test.mean()),
        "logistic": evaluate(logit, X_test, y_test),
        "xgboost": evaluate(xgb, X_test, y_test),
        "logistic_cv_roc_auc": cv_roc_auc(
            train_logistic(X_train, y_train), X_train, y_train),
        "xgboost_targeting": targeting_table(
            proba["XGBoost"], y_test).to_dict(orient="records"),
    }

    figures = {
        "roc_pr": plot_roc_pr(proba, y_test),
        "shap": plot_shap_summary(xgb, X_test),
        "logit_coefs": plot_logistic_coefficients(logit, X.columns),
    }

    if save_metrics:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(REPORTS_DIR / "model-metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)

    return {"metrics": metrics, "figures": figures,
            "models": {"logistic": logit, "xgboost": xgb},
            "data": {"X_test": X_test, "y_test": y_test, "proba": proba}}
