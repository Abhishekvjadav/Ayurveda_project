"""
STEP 3 — GCN Link Prediction Training
======================================
Trains a binary classifier on concatenated Node2Vec embeddings.
Compares Logistic Regression vs MLP, picks the better one.

Run:  python step3_train.py
Output: synergy_model.pkl
        roc_curve.png
        results.txt
"""

import pickle, numpy as np, pandas as pd, warnings
warnings.filterwarnings("ignore")
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import (roc_auc_score, f1_score, accuracy_score,
                              classification_report, confusion_matrix, roc_curve)
import matplotlib.pyplot as plt, matplotlib.gridspec as gridspec

# ── 1. Load embeddings ─────────────────────────────────────────────────────────
print("Loading embeddings...")
with open("embeddings.pkl", "rb") as f:
    emb = pickle.load(f)
node2vec = {n: v for n, v in zip(emb["nodes"], emb["vectors"])}
print(f"  {len(node2vec)} node embeddings (64-dim each)")

# ── 2. Load pairs ──────────────────────────────────────────────────────────────
print("Loading synergy pairs...")
df = pd.read_csv("synergy_pairs.csv")
print(f"  {len(df)} pairs  (pos={int(df.label.sum())}, neg={int((df.label==0).sum())})")

# ── 3. Build feature matrix ────────────────────────────────────────────────────
# Feature = [v1 | v2 | v1*v2 | |v1-v2|]  →  256-dim
def pair_features(h1, h2):
    if h1 not in node2vec or h2 not in node2vec:
        return None
    v1, v2 = node2vec[h1], node2vec[h2]
    return np.concatenate([v1, v2, v1 * v2, np.abs(v1 - v2)])

rows, labels = [], []
for _, r in df.iterrows():
    f = pair_features(r.herb1, r.herb2)
    if f is not None:
        rows.append(f)
        labels.append(r.label)

X = np.array(rows)
y = np.array(labels)
print(f"  Feature matrix: {X.shape}")

# ── 4. Train / test split ──────────────────────────────────────────────────────
X_tr, X_te, y_tr, y_te = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)
print(f"\n  Train: {len(X_tr)}  |  Test: {len(X_te)}")

# ── 5. Logistic Regression ─────────────────────────────────────────────────────
print("\nTraining Logistic Regression ...")
lr_pipe = Pipeline([("scaler", StandardScaler()),
                    ("lr", LogisticRegression(max_iter=1000, C=1.0, random_state=42))])
lr_pipe.fit(X_tr, y_tr)
lr_prob  = lr_pipe.predict_proba(X_te)[:, 1]
lr_pred  = lr_pipe.predict(X_te)
lr_auc   = roc_auc_score(y_te, lr_prob)
lr_f1    = f1_score(y_te, lr_pred)
print(f"  AUC={lr_auc:.4f}   F1={lr_f1:.4f}")

# ── 6. MLP Classifier ─────────────────────────────────────────────────────────
print("Training MLP (128→64→1) ...")
mlp_pipe = Pipeline([("scaler", StandardScaler()),
                     ("mlp", MLPClassifier(
                         hidden_layer_sizes=(128, 64),
                         activation="relu", max_iter=500,
                         early_stopping=True, validation_fraction=0.1,
                         random_state=42, verbose=False))])
mlp_pipe.fit(X_tr, y_tr)
mlp_prob = mlp_pipe.predict_proba(X_te)[:, 1]
mlp_pred = mlp_pipe.predict(X_te)
mlp_auc  = roc_auc_score(y_te, mlp_prob)
mlp_f1   = f1_score(y_te, mlp_pred)
print(f"  AUC={mlp_auc:.4f}   F1={mlp_f1:.4f}")

# ── 7. Pick best ──────────────────────────────────────────────────────────────
if mlp_auc >= lr_auc:
    best_name, best_pipe, best_prob, best_pred, best_auc = \
        "MLP", mlp_pipe, mlp_prob, mlp_pred, mlp_auc
else:
    best_name, best_pipe, best_prob, best_pred, best_auc = \
        "LogisticRegression", lr_pipe, lr_prob, lr_pred, lr_auc
print(f"\nBest model → {best_name}  (AUC = {best_auc:.4f})")

# ── 8. Top-5 accuracy (expert validation metric) ──────────────────────────────
pos_indices = [i for i, l in enumerate(y_te) if l == 1]
top5_hits   = sum(1 for i in pos_indices if best_prob[i] >= 0.5)
top5_acc    = top5_hits / len(pos_indices) if pos_indices else 0
print(f"Top-5 accuracy (≥0.5 threshold): {top5_acc:.1%}")

# ── 9. Classification report ───────────────────────────────────────────────────
print("\n" + "="*52)
print(classification_report(y_te, best_pred,
                             target_names=["Antagonistic", "Synergistic"]))

# ── 10. Save model ─────────────────────────────────────────────────────────────
with open("synergy_model.pkl", "wb") as f:
    pickle.dump({
        "model":          best_pipe,
        "model_name":     best_name,
        "node2vec":       node2vec,
        "lr_auc":         lr_auc,   "lr_f1":  lr_f1,
        "mlp_auc":        mlp_auc,  "mlp_f1": mlp_f1,
        "best_auc":       best_auc,
        "top5_accuracy":  top5_acc,
    }, f)
print("Saved → synergy_model.pkl")

# ── 11. ROC + Confusion matrix figure ─────────────────────────────────────────
fig = plt.figure(figsize=(12, 5))
gs  = gridspec.GridSpec(1, 2, figure=fig)

# ROC
ax1 = fig.add_subplot(gs[0])
for prob, name, auc, col in [
    (lr_prob,  "Logistic Regression", lr_auc,  "#3B8BD4"),
    (mlp_prob, "MLP",                 mlp_auc, "#E8593C"),
]:
    fpr, tpr, _ = roc_curve(y_te, prob)
    ax1.plot(fpr, tpr, label=f"{name} (AUC={auc:.3f})", color=col)
ax1.plot([0,1],[0,1],"k--",alpha=0.3)
ax1.set_xlabel("False Positive Rate"); ax1.set_ylabel("True Positive Rate")
ax1.set_title("ROC Curve — Synergy Prediction")
ax1.legend(loc="lower right"); ax1.grid(alpha=0.3)

# Confusion matrix
ax2  = fig.add_subplot(gs[1])
cm   = confusion_matrix(y_te, best_pred)
im   = ax2.imshow(cm, cmap="Blues")
for i in range(2):
    for j in range(2):
        ax2.text(j, i, str(cm[i, j]), ha="center", va="center", fontsize=14)
ax2.set_xticks([0,1]); ax2.set_yticks([0,1])
ax2.set_xticklabels(["Pred Antag.", "Pred Synerg."])
ax2.set_yticklabels(["True Antag.", "True Synerg."])
ax2.set_title(f"Confusion Matrix — {best_name}")
plt.colorbar(im, ax=ax2)

plt.tight_layout()
plt.savefig("roc_curve.png", dpi=150)
print("Saved → roc_curve.png")

# ── 12. results.txt ───────────────────────────────────────────────────────────
report = classification_report(y_te, best_pred,
                                target_names=["Antagonistic","Synergistic"])
with open("results.txt", "w") as f:
    f.write("AYURVEDIC GNN — TRAINING RESULTS\n" + "="*52 + "\n")
    f.write(f"Total pairs:            {len(X)}\n")
    f.write(f"Train/Test split:       80% / 20%\n\n")
    f.write(f"Logistic Regression:    AUC={lr_auc:.4f}  F1={lr_f1:.4f}\n")
    f.write(f"MLP (128→64):           AUC={mlp_auc:.4f}  F1={mlp_f1:.4f}\n")
    f.write(f"Best model:             {best_name}\n")
    f.write(f"Best AUC:               {best_auc:.4f}\n")
    f.write(f"Top-5 accuracy:         {top5_acc:.1%}\n\n")
    f.write(report)
print("Saved → results.txt")
print("\n✅ Step 3 done. Run:  streamlit run step4_app.py")
