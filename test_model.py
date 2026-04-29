"""
Digital Dravyaguna — Model Accuracy Tester
==========================================
Tests the trained GNN model and shows detailed accuracy metrics.

Run: python test_model.py
"""

import pickle, json, numpy as np, pandas as pd
from sklearn.metrics import (
    roc_auc_score, f1_score, accuracy_score, precision_score,
    recall_score, confusion_matrix, classification_report
)
from itertools import combinations
import random
random.seed(42)

print("=" * 60)
print("  DIGITAL DRAVYAGUNA — MODEL ACCURACY TEST")
print("=" * 60)

# ── Load model and graph ───────────────────────────────────────────────────────
print("\n[1] Loading model and graph...")
with open("synergy_model.pkl", "rb") as f:
    md = pickle.load(f)
with open("ayurvedic_graph.pkl", "rb") as f:
    G = pickle.load(f)

model    = md["model"]
node2vec = md["node2vec"]
print("    Model type  :", md.get("model_name", "MLP"))
print("    Model AUC   :", round(md.get("best_auc", 0), 4))
print("    Herbs loaded:", len([n for n,d in G.nodes(data=True) if d.get("type")=="herb"]))
print("    Graph edges :", G.number_of_edges())

# ── Helper: make feature vector for a pair ────────────────────────────────────
def make_features(h1, h2):
    if h1 not in node2vec or h2 not in node2vec:
        return None
    v1, v2 = node2vec[h1], node2vec[h2]
    return np.concatenate([v1, v2, v1*v2, np.abs(v1-v2)]).reshape(1, -1)

def predict_score(h1, h2):
    f = make_features(h1, h2)
    if f is None: return None
    return float(model.predict_proba(f)[0][1])

# ══════════════════════════════════════════════════════════════════════════════
# TEST 1: Classical Yoga Pairs (should all score HIGH)
# These are verified synergistic pairs from classical Ayurveda
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("[TEST 1] Classical Yoga Pairs (expected: score > 0.7)")
print("=" * 60)

classical_yogas = [
    ("Amla",        "Haritaki",    "Triphala group"),
    ("Amla",        "Bibhitaki",   "Triphala group"),
    ("Haritaki",    "Bibhitaki",   "Triphala group"),
    ("Ardraka",     "Pippali",     "Trikatu group"),
    ("Maricha",     "Pippali",     "Trikatu group"),
    ("Ardraka",     "Maricha",     "Trikatu group"),
    ("Ashwagandha", "Shatavari",   "Adaptogenic duo"),
    ("Ashwagandha", "Brahmi",      "Nervine adaptogen"),
    ("Tulsi",       "Ardraka",     "Respiratory"),
    ("Amla",        "Ashwagandha", "Rasayana pair"),
    ("Punarnava",   "Gokshura",    "Kidney support"),
    ("Brahmi",      "Jatamansi",   "Neurological"),
    ("Arjuna",      "Punarnava",   "Cardiac"),
]

t1_results = []
for h1, h2, group in classical_yogas:
    score = predict_score(h1, h2)
    if score is not None:
        passed = score >= 0.7
        status = "PASS" if passed else "FAIL"
        t1_results.append({"pair": h1 + " + " + h2, "group": group,
                            "score": round(score, 4), "expected": ">0.7", "status": status})
    else:
        t1_results.append({"pair": h1 + " + " + h2, "group": group,
                            "score": "N/A", "expected": ">0.7", "status": "SKIP (not in graph)"})

df1 = pd.DataFrame(t1_results)
print(df1.to_string(index=False))
valid1 = [r for r in t1_results if r["score"] != "N/A"]
pass1  = sum(1 for r in valid1 if r["status"] == "PASS")
print("\nResult: " + str(pass1) + "/" + str(len(valid1)) + " classical pairs scored > 0.7")
print("Accuracy on classical pairs: " + str(round(100*pass1/len(valid1), 1)) + "%")

# ══════════════════════════════════════════════════════════════════════════════
# TEST 2: Viruddha (Antagonistic) Pairs (should all score LOW)
# Opposing Virya pairs are contraindicated in Ayurveda
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("[TEST 2] Viruddha / Opposing Pairs (expected: score < 0.5)")
print("=" * 60)

# Get Ushna and Sheeta herbs from graph
ushna_herbs  = [n for n,d in G.nodes(data=True)
                if d.get("type")=="herb" and d.get("virya","").lower()=="ushna"
                and n in node2vec][:10]
sheeta_herbs = [n for n,d in G.nodes(data=True)
                if d.get("type")=="herb" and d.get("virya","").lower()=="sheeta"
                and n in node2vec][:10]

t2_results = []
for h1 in ushna_herbs[:5]:
    for h2 in sheeta_herbs[:5]:
        score = predict_score(h1, h2)
        if score is not None:
            passed = score < 0.5
            status = "PASS" if passed else "FAIL"
            t2_results.append({
                "Herb 1 (Ushna)": h1, "Herb 2 (Sheeta)": h2,
                "Score": round(score, 4), "Expected": "<0.5", "Status": status})

df2 = pd.DataFrame(t2_results)
print(df2.to_string(index=False))
pass2 = sum(1 for r in t2_results if r["Status"] == "PASS")
print("\nResult: " + str(pass2) + "/" + str(len(t2_results)) + " viruddha pairs scored < 0.5")
print("Accuracy on antagonistic pairs: " + str(round(100*pass2/max(len(t2_results),1), 1)) + "%")

# ══════════════════════════════════════════════════════════════════════════════
# TEST 3: Dosha-specific synergy test
# Herbs that pacify the SAME dosha should score higher than
# herbs that pacify DIFFERENT doshas
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("[TEST 3] Dosha Consistency Test")
print("  Herbs pacifying same Dosha should score higher than")
print("  herbs pacifying opposing Doshas")
print("=" * 60)

def get_doshas(herb):
    return {v.replace("dosha_","") for u,v,d in G.edges(data=True)
            if u==herb and d.get("relation")=="PACIFIES"}

# Get herbs per dosha
dosha_herb_map = {}
for dosha in ["vata", "pitta", "kapha"]:
    node = "dosha_" + dosha
    herbs_for_dosha = [u for u,v,d in G.edges(data=True)
                       if v==node and d.get("relation")=="PACIFIES"
                       and G.nodes[u].get("type")=="herb" and u in node2vec]
    dosha_herb_map[dosha] = herbs_for_dosha[:20]

same_dosha_scores = []
diff_dosha_scores = []

for dosha in ["vata", "pitta", "kapha"]:
    herbs = dosha_herb_map[dosha][:10]
    other_doshas = [d for d in ["vata","pitta","kapha"] if d != dosha]
    # Other herbs that DON'T pacify this dosha
    other_herbs = []
    for od in other_doshas:
        other_herbs += [h for h in dosha_herb_map[od][:5]
                        if h not in herbs]

    for h1, h2 in list(combinations(herbs, 2))[:15]:
        s = predict_score(h1, h2)
        if s: same_dosha_scores.append(s)

    for h1 in herbs[:5]:
        for h2 in other_herbs[:5]:
            s = predict_score(h1, h2)
            if s: diff_dosha_scores.append(s)

avg_same = np.mean(same_dosha_scores) if same_dosha_scores else 0
avg_diff = np.mean(diff_dosha_scores) if diff_dosha_scores else 0
passed3  = avg_same > avg_diff

print("  Avg score — same Dosha herbs : " + str(round(avg_same, 4)))
print("  Avg score — diff Dosha herbs : " + str(round(avg_diff, 4)))
print("  Separation gap               : " + str(round(avg_same - avg_diff, 4)))
print("  Result: " + ("PASS — same-Dosha herbs score higher" if passed3
      else "FAIL — no clear separation"))

# ══════════════════════════════════════════════════════════════════════════════
# TEST 4: Large-scale balanced evaluation
# Build a balanced test set from graph structure and measure full metrics
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("[TEST 4] Full Metrics Evaluation (balanced test set)")
print("=" * 60)

herb_nodes = [n for n,d in G.nodes(data=True)
              if d.get("type")=="herb" and n in node2vec]

# Positive: herbs sharing 2+ pacified doshas
dosha_pacify = {}
for d in ["vata","pitta","kapha"]:
    node = "dosha_" + d
    dosha_pacify[d] = {u for u,v,ed in G.edges(data=True)
                       if v==node and ed.get("relation")=="PACIFIES"
                       and G.nodes[u].get("type")=="herb" and u in node2vec}

positives = []
for h1, h2 in combinations(herb_nodes, 2):
    shared = sum(1 for d in ["vata","pitta","kapha"]
                 if h1 in dosha_pacify[d] and h2 in dosha_pacify[d])
    if shared >= 2:
        positives.append((h1, h2, 1))

# Negative: opposing Virya
ushna_set  = set(ushna_herbs)
sheeta_set = set(sheeta_herbs)
negatives  = [(h1, h2, 0) for h1 in ushna_herbs for h2 in sheeta_herbs]

# Balance
n = min(len(positives), len(negatives), 500)
pos_sample = random.sample(positives, n)
neg_sample = random.sample(negatives, n)
all_pairs  = pos_sample + neg_sample
random.shuffle(all_pairs)

print("  Building test set: " + str(len(all_pairs)) + " pairs (" + str(n) + " pos + " + str(n) + " neg)")

X_list, y_list = [], []
for h1, h2, label in all_pairs:
    f = make_features(h1, h2)
    if f is not None:
        X_list.append(f[0]); y_list.append(label)

X = np.array(X_list); y = np.array(y_list)
y_prob = model.predict_proba(X)[:, 1]
y_pred = (y_prob >= 0.5).astype(int)

auc       = roc_auc_score(y, y_prob)
acc       = accuracy_score(y, y_pred)
f1        = f1_score(y, y_pred)
precision = precision_score(y, y_pred)
recall    = recall_score(y, y_pred)
cm        = confusion_matrix(y, y_pred)

print("\n  METRICS:")
print("  ROC-AUC   : " + str(round(auc, 4)))
print("  Accuracy  : " + str(round(acc * 100, 2)) + "%")
print("  F1 Score  : " + str(round(f1, 4)))
print("  Precision : " + str(round(precision, 4)))
print("  Recall    : " + str(round(recall, 4)))
print("\n  Confusion Matrix:")
print("                 Pred Antag.  Pred Synerg.")
print("  True Antag.  |  " + str(cm[0][0]).rjust(6) + "    |  " + str(cm[0][1]).rjust(6) + "   |")
print("  True Synerg. |  " + str(cm[1][0]).rjust(6) + "    |  " + str(cm[1][1]).rjust(6) + "   |")

print("\n  Classification Report:")
print(classification_report(y, y_pred, target_names=["Antagonistic","Synergistic"]))

# ══════════════════════════════════════════════════════════════════════════════
# TEST 5: Embedding quality — similarity check
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 60)
print("[TEST 5] Embedding Quality — Top Similar Herbs")
print("=" * 60)

probe_herbs = ["Ashwagandha", "Tulsi", "Amla", "Pippali", "Arjuna"]
for probe in probe_herbs:
    if probe not in node2vec:
        print("  " + probe + ": not in graph, skipping")
        continue
    v_probe = node2vec[probe]
    # Cosine similarity with all other herb embeddings
    scores = {}
    for h in herb_nodes:
        if h == probe: continue
        v = node2vec[h]
        cos = float(np.dot(v_probe, v) / (np.linalg.norm(v_probe) * np.linalg.norm(v) + 1e-9))
        scores[h] = cos
    top5 = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
    top5_str = ", ".join(h + "(" + str(round(s,3)) + ")" for h, s in top5)
    print("  " + probe.ljust(15) + " -> " + top5_str)

# ══════════════════════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  FINAL SUMMARY")
print("=" * 60)
print("  Test 1 — Classical Yoga pairs   : " + str(pass1) + "/" + str(len(valid1)) +
      " (" + str(round(100*pass1/max(len(valid1),1), 1)) + "%)")
print("  Test 2 — Viruddha pairs         : " + str(pass2) + "/" + str(len(t2_results)) +
      " (" + str(round(100*pass2/max(len(t2_results),1), 1)) + "%)")
print("  Test 3 — Dosha consistency      : " + ("PASS" if passed3 else "FAIL"))
print("  Test 4 — ROC-AUC                : " + str(round(auc, 4)))
print("  Test 4 — Accuracy               : " + str(round(acc * 100, 2)) + "%")
print("  Test 4 — F1 Score               : " + str(round(f1, 4)))
print("\n  Saved model AUC (from training) : " + str(round(md.get("best_auc", 0), 4)))
print("=" * 60)

# Save results to CSV
rows = []
for r in t1_results:
    rows.append({"Test":"Classical Yoga","Herb 1+2":r["pair"],
                 "Score":r["score"],"Expected":r["expected"],"Status":r["status"]})
for r in t2_results:
    rows.append({"Test":"Viruddha","Herb 1+2":r["Herb 1 (Ushna)"]+" + "+r["Herb 2 (Sheeta)"],
                 "Score":r["Score"],"Expected":r["Expected"],"Status":r["Status"]})
pd.DataFrame(rows).to_csv("test_results.csv", index=False)
print("\n  Detailed results saved to: test_results.csv")
print("=" * 60)
