"""
STEP 2 — Synergy Pair Generation
=================================
Builds labelled (herb1, herb2, label) pairs for classifier training.
  label = 1  →  Synergistic  (classical Yoga / shared Dosha)
  label = 0  →  Antagonistic (opposing Virya / random non-paired)

Run:  python step2_synergy_pairs.py
Output: synergy_pairs.csv
"""

import pickle, random, pandas as pd
random.seed(42)

# ── 1. Load graph ──────────────────────────────────────────────────────────────
with open("ayurvedic_graph.pkl", "rb") as f:
    G = pickle.load(f)

herb_nodes = [n for n, d in G.nodes(data=True) if d.get("type") == "herb"]
herb_set   = set(herb_nodes)
print(f"Herb nodes in graph: {len(herb_nodes)}")

# ── 2. Positive pairs — Classical Yogas (verified against YOUR graph) ──────────
# These pairs use EXACT names as they appear in your graph
classical_yogas = [
    # Triphala group (three fruits)
    ("Amla",     "Haritaki"),
    ("Amla",     "Bibhitaki"),
    ("Haritaki", "Bibhitaki"),

    # Trikatu group (three pungents — using Ayurvedic names)
    ("Ardraka",  "Pippali"),           # Ginger + Long pepper
    ("Maricha",  "Pippali"),           # Black pepper + Long pepper
    ("Ardraka",  "Maricha"),

    # Famous adaptogenic pairs
    ("Ashwagandha", "Shatavari"),
    ("Ashwagandha", "Brahmi"),
    ("Ashwagandha", "Arjuna"),
    ("Ashwagandha", "Bala"),
    ("Ashwagandha", "Kapikacchu"),

    # Neurological / medhya herbs
    ("Brahmi",       "Shankhpushpi"),
    ("Brahmi",       "Jatamansi"),
    ("Brahmi",       "Mandukaparni"),

    # Respiratory / Kapha
    ("Tulsi",   "Ardraka"),
    ("Tulsi",   "Pippali"),
    ("Tulsi",   "Maricha"),
    ("Pippali", "Haritaki"),

    # Rasayana (rejuvenative) pairs
    ("Amla",       "Ashwagandha"),
    ("Amla",       "Brahmi"),
    ("Haritaki",   "Ardraka"),
    ("Guduchi",    "Amla"),
    ("Guduchi",    "Punarnava"),
    ("Shatavari",  "Vidari"),
    ("Shatavari",  "Lodhra"),
    ("Shatavari",  "Licorice"),

    # Cardiac / Circulatory
    ("Arjuna",  "Punarnava"),
    ("Arjuna",  "Guggulu"),

    # Kidney / Diuretic
    ("Punarnava", "Gokshura"),
    ("Gokshura",  "Varuna"),

    # Digestive
    ("Ajwain",    "Ardraka"),
    ("Ajmoda",    "Pippali"),
    ("Haritaki",  "Saindhava"),        # rock salt + haritaki (classic)
    ("Ardraka",   "Guduchi"),

    # Anti-inflammatory
    ("Haridra",   "Neem"),             # Turmeric + Neem
    ("Haridra",   "Guduchi"),
    ("Neem",      "Guduchi"),

    # Hair / Skin
    ("Bhringaraj",  "Brahmi"),
    ("Haridra",     "Neem"),
    ("Kumari",      "Shatavari"),      # Aloe + Shatavari
]

# Filter to pairs where BOTH herbs are actually in the graph
valid_pos, skipped = [], []
for h1, h2 in classical_yogas:
    if h1 in herb_set and h2 in herb_set:
        valid_pos.append((h1, h2, 1))
    else:
        missing = [h for h in [h1, h2] if h not in herb_set]
        skipped.append((h1, h2, missing))

print(f"Classical yoga pairs valid   : {len(valid_pos)}")
if skipped:
    print(f"Skipped (not in graph)       : {len(skipped)}")
    for h1, h2, m in skipped:
        print(f"  {h1} + {h2}  ← missing: {m}")

# ── 3. Positive pairs — Auto-generated (shared Dosha pacification) ────────────
def pacified_doshas(herb):
    return {v for v in G.neighbors(herb)
            if G[herb][v].get("relation") == "PACIFIES"}

auto_pos = []
for i, h1 in enumerate(herb_nodes):
    for h2 in herb_nodes[i+1:]:
        shared = pacified_doshas(h1) & pacified_doshas(h2)
        if len(shared) >= 2:          # share 2+ Dosha targets → synergistic
            auto_pos.append((h1, h2, 1))

print(f"Auto positive (shared dosha) : {len(auto_pos)}")

all_positive = list({(a, b): (a, b, 1) for a, b, _ in valid_pos + auto_pos}.values())
print(f"Total positive pairs         : {len(all_positive)}")

# ── 4. Negative pairs — Viruddha (opposing Virya) ─────────────────────────────
ushna  = [n for n in herb_nodes if G.nodes[n].get("virya") == "ushna"]
sheeta = [n for n in herb_nodes if G.nodes[n].get("virya") == "sheeta"]

pos_set = {(a, b) for a, b, _ in all_positive} | {(b, a) for a, b, _ in all_positive}

viruddha = [(h1, h2, 0) for h1 in ushna for h2 in sheeta
             if (h1, h2) not in pos_set]
print(f"Viruddha negative pairs      : {len(viruddha)}")

# ── 5. Negative pairs — Random non-co-occurring ───────────────────────────────
viruddha_set = {(a, b) for a, b, _ in viruddha} | {(b, a) for a, b, _ in viruddha}
target_random = len(all_positive) * 2
random_neg, attempts = [], 0
while len(random_neg) < target_random and attempts < 200_000:
    h1, h2 = random.sample(herb_nodes, 2)
    if (h1, h2) not in pos_set and (h1, h2) not in viruddha_set:
        random_neg.append((h1, h2, 0))
    attempts += 1
print(f"Random negative pairs        : {len(random_neg)}")

# ── 6. Balance and save ────────────────────────────────────────────────────────
n_pos    = len(all_positive)
neg_vir  = random.sample(viruddha, min(n_pos, len(viruddha)))
neg_rand = random.sample(random_neg, min(n_pos, len(random_neg)))
all_data = all_positive + neg_vir + neg_rand
random.shuffle(all_data)

df = pd.DataFrame(all_data, columns=["herb1", "herb2", "label"])
df.to_csv("synergy_pairs.csv", index=False)

print(f"\nFinal dataset:")
print(f"  Total pairs  : {len(df)}")
print(f"  Positive (1) : {df['label'].sum()}")
print(f"  Negative (0) : {(df['label']==0).sum()}")
print(f"  Balance      : {df['label'].mean():.2f}")
print("\n✅ Step 2 done. Run step3_train.py next.")
