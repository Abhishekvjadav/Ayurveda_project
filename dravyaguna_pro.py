"""
Digital Dravyaguna PRO — Complete AYUSH Practitioner System
Integrated: Dual Login, PDF Export, WhatsApp Share, Dark/Light Mode, Patient Portal
Run: streamlit run dravyaguna_pro.py
"""

import streamlit as st
import sqlite3
import pickle
import json
import numpy as np
import pandas as pd
import hashlib
import urllib.parse
from datetime import datetime, date, timedelta
from itertools import combinations

try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False

st.set_page_config(page_title="Digital Dravyaguna", page_icon="🌿",
                   layout="wide", initial_sidebar_state="expanded")

# ── Theme ─────────────────────────────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = False

DARK = st.session_state["dark_mode"]

if DARK:
    THEME = {
        "bg":        "#0e1117",
        "card":      "#1a1f2e",
        "card_border":"#2d3550",
        "text":      "#e8f0fe",
        "subtext":   "#8892b0",
        "green":     "#4ade80",
        "green_dark":"#16a34a",
        "sidebar_bg":"linear-gradient(180deg,#060d1a 0%,#0a1628 60%,#0f2040 100%)",
    }
else:
    THEME = {
        "bg":        "#f4faf6",
        "card":      "#ffffff",
        "card_border":"#e8f5e9",
        "text":      "#0a3d2e",
        "subtext":   "#555555",
        "green":     "#0f5132",
        "green_dark":"#0a3d2e",
        "sidebar_bg":"linear-gradient(180deg,#0a3d2e 0%,#0f5132 60%,#1a6b42 100%)",
    }

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@400;600;700&family=DM+Sans:wght@300;400;500;600&display=swap');
html,body,[class*="css"]{{font-family:'DM Sans',sans-serif;background:{THEME["bg"]};}}
[data-testid="stSidebar"]{{background:{THEME["sidebar_bg"]};}}
[data-testid="stSidebar"] *{{color:#e8f5e9 !important;}}
[data-testid="stSidebar"] .stRadio label{{background:rgba(255,255,255,0.08);border-radius:8px;
  padding:10px 14px;margin:3px 0;display:block;transition:background 0.2s;cursor:pointer;}}
[data-testid="stSidebar"] .stRadio label:hover{{background:rgba(255,255,255,0.15);}}
.metric-card{{background:{THEME["card"]};border-radius:12px;padding:20px;border-left:4px solid #0f5132;
  box-shadow:0 2px 8px rgba(0,0,0,0.06);text-align:center;}}
.metric-num{{font-size:32px;font-weight:700;color:#0f5132;font-family:'Crimson Pro',serif;}}
.metric-label{{font-size:13px;color:{THEME["subtext"]};margin-top:4px;}}
.patient-card{{background:{THEME["card"]};border-radius:12px;padding:16px;border:1px solid {THEME["card_border"]};
  box-shadow:0 2px 6px rgba(15,81,50,0.06);margin-bottom:10px;}}
.patient-name{{font-size:17px;font-weight:600;color:{THEME["green"]};font-family:'Crimson Pro',serif;}}
.rx-card{{background:{THEME["card"]};border:2px solid #0f5132;border-radius:12px;padding:20px;}}
.dosha-vata{{background:#7c4dff;color:white;padding:3px 12px;border-radius:20px;font-size:12px;font-weight:500;}}
.dosha-pitta{{background:#f4511e;color:white;padding:3px 12px;border-radius:20px;font-size:12px;font-weight:500;}}
.dosha-kapha{{background:#0f5132;color:white;padding:3px 12px;border-radius:20px;font-size:12px;font-weight:500;}}
.chip{{display:inline-block;border-radius:20px;padding:3px 10px;font-size:11px;font-weight:500;margin:2px;}}
.chip-gnn{{background:#e3f2fd;color:#1565c0;}}
.chip-virya{{background:#fff3e0;color:#e65100;}}
.chip-prabhav{{background:#f3e5f5;color:#6a1b9a;}}
.form-badge{{display:inline-block;background:#0f5132;color:white;border-radius:6px;
  padding:4px 12px;font-size:12px;font-weight:600;margin-bottom:8px;}}
.timeline-week{{background:{THEME["card"]};border-left:4px solid;border-radius:8px;
  padding:16px;margin-bottom:12px;box-shadow:0 2px 6px rgba(0,0,0,0.04);}}
.stButton>button{{background:linear-gradient(135deg,#0f5132,#1a6b42) !important;
  color:white !important;border:none !important;border-radius:8px !important;
  font-weight:500 !important;transition:all 0.2s !important;}}
.stButton>button:hover{{opacity:0.9 !important;transform:translateY(-1px) !important;}}
.stTabs [aria-selected="true"]{{background:#0f5132 !important;color:white !important;}}
.login-card{{background:{THEME["card"]};border-radius:16px;padding:32px;
  box-shadow:0 8px 32px rgba(0,0,0,0.08);max-width:440px;margin:auto;border:1px solid {THEME["card_border"]};}}
.role-badge-doctor{{background:linear-gradient(135deg,#0f5132,#1a6b42);color:white;
  border-radius:20px;padding:4px 14px;font-size:12px;font-weight:600;}}
.role-badge-patient{{background:linear-gradient(135deg,#1565c0,#1976d2);color:white;
  border-radius:20px;padding:4px 14px;font-size:12px;font-weight:600;}}
.share-btn{{display:inline-block;background:#25D366;color:white;padding:8px 18px;
  border-radius:8px;text-decoration:none;font-size:13px;font-weight:600;margin-right:8px;}}
.share-btn:hover{{opacity:0.88;}}
h1,h2,h3,h4{{font-family:'Crimson Pro',serif;color:{THEME["text"]};}}
</style>
""", unsafe_allow_html=True)

# ── Knowledge base ─────────────────────────────────────────────────────────────
FORMULATION_FORMS = {
    "vata": [
        {"name":"Churna (Powder)","prep":"Mix equal parts, grind to fine powder.",
         "dose":"5g with warm milk or sesame oil","shelf":"3 months"},
        {"name":"Ghrita (Medicated Ghee)","prep":"Simmer herbs in ghee on low flame 30 min, strain.",
         "dose":"1 tsp with warm milk at bedtime","shelf":"6 months"},
        {"name":"Kwath (Decoction)","prep":"Boil 10g in 400ml water, reduce to 100ml, strain.",
         "dose":"50ml warm twice daily","shelf":"Fresh daily"},
    ],
    "pitta": [
        {"name":"Churna (Powder)","prep":"Mix herbs, grind to fine powder.",
         "dose":"5g with cool water or coconut water","shelf":"3 months"},
        {"name":"Kwath (Decoction)","prep":"Boil 10g in 400ml water, cool to room temp.",
         "dose":"50ml cool twice daily","shelf":"Fresh daily"},
        {"name":"Arishta (Fermented)","prep":"Available as classical preparation.",
         "dose":"15-30ml diluted with equal water after meals","shelf":"1 year"},
    ],
    "kapha": [
        {"name":"Churna (Powder)","prep":"Mix herbs with small amount of honey.",
         "dose":"3-5g with warm water and honey","shelf":"3 months"},
        {"name":"Kwath (Decoction)","prep":"Boil 10g in 400ml water, reduce to 100ml.",
         "dose":"50ml warm before meals","shelf":"Fresh daily"},
        {"name":"Vati (Tablet)","prep":"Available as classical preparation from pharmacy.",
         "dose":"2 tablets twice daily with warm water","shelf":"1 year"},
    ],
}

DIET_CHART = {
    "vata": {
        "Favour":["Warm cooked foods","Sweet sour salty tastes","Ghee and oils",
                  "Root vegetables","Warm milk and dairy","Sesame seeds","Dates and figs"],
        "Avoid":["Cold raw foods","Dry or light foods","Bitter astringent pungent",
                 "Excess beans and legumes","Carbonated drinks","Leftover food"],
        "Timing":"Eat at fixed times. Never skip meals. Main meal at noon.",
        "Lifestyle":"Daily oil massage (Abhyanga). Gentle yoga. Early sleep by 10pm. Avoid wind and cold.",
    },
    "pitta": {
        "Favour":["Cool refreshing foods","Sweet bitter astringent tastes","Coconut water",
                  "Fresh sweet fruits","Leafy greens","Cooling ghee","Coriander and fennel"],
        "Avoid":["Spicy sour salty foods","Alcohol","Red meat","Vinegar and fermented foods",
                 "Excess coffee and tea","Eating when angry or stressed"],
        "Timing":"Eat when calm. Largest meal at noon. Avoid eating late at night.",
        "Lifestyle":"Moon walks. Swimming. Cooling pranayama (Sheetali). Avoid direct midday sun.",
    },
    "kapha": {
        "Favour":["Light dry warm foods","Pungent bitter astringent tastes","Honey",
                  "Barley millet rye","Ginger tea","Spices like pepper and turmeric",
                  "Leafy greens","Pomegranate"],
        "Avoid":["Heavy oily sweet foods","Cold food and drinks","Excessive dairy",
                 "White flour and white rice","Sleeping after meals","Daytime napping"],
        "Timing":"Eat light. Skip lunch if not hungry. Dinner before 7pm. Fasting is beneficial.",
        "Lifestyle":"Vigorous daily exercise. Dry brushing. Avoid cold damp weather. Wake before sunrise.",
    },
}

ANUPANA = {
    "vata":  "Warm milk or sesame oil",
    "pitta": "Cool water or coconut water",
    "kapha": "Warm water with honey",
}
DETOX_HERBS = {
    "vata":  ("Haritaki",    "3g at bedtime with warm water - gentle Vata laxative"),
    "pitta": ("Amla",        "5g in cool water morning - cooling Pitta detox"),
    "kapha": ("Trikatu",     "2g before meals with honey - Kapha digestive detox"),
}
RASAYANA_HERBS = {
    "vata":  ("Ashwagandha", "5g with warm milk - Vata Rasayana rejuvenation"),
    "pitta": ("Amla",        "5g with ghee - Pitta Rasayana rejuvenation"),
    "kapha": ("Giloy",       "3g with honey - Kapha Rasayana immunity"),
}
SYMPTOMS = {
    "Vata": {
        "Anxiety / restlessness":3,"Dry skin / hair":2,"Constipation":3,
        "Joint pain / cracking sounds":3,"Insomnia / disturbed sleep":2,
        "Bloating / gas":3,"Underweight / weight loss":2,
        "Cold intolerance":2,"Irregular appetite":2,"Tremors / twitching":3,
    },
    "Pitta": {
        "Fever / burning sensations":3,"Acidity / heartburn":3,
        "Skin rashes / inflammation":2,"Excessive hunger / thirst":2,
        "Anger / irritability":2,"Loose stools / diarrhea":3,
        "Excessive sweating":2,"Eye redness / sensitivity":2,
        "Premature greying":2,"Bitter taste in mouth":2,
    },
    "Kapha": {
        "Chest congestion / mucus":3,"Obesity / weight gain":3,
        "Lethargy / excessive sleep":2,"Slow digestion / nausea":2,
        "Depression / low motivation":2,"Oily skin / cold cough":2,
        "Swelling / water retention":3,"White coated tongue":2,
        "Slow metabolism":2,"Excessive attachment":1,
    },
}

# ── Database ───────────────────────────────────────────────────────────────────
DB = "clinic.db"

def init_db():
    """Initialize database with proper schema and text handling"""
    con = sqlite3.connect(DB)
    con.text_factory = str  # Prevent LargeUft8 issues
    
    # Create tables with proper schema
    con.executescript("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'Doctor',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    
    CREATE TABLE IF NOT EXISTS patients(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pid TEXT UNIQUE,
        name TEXT NOT NULL,
        age INTEGER,
        gender TEXT,
        phone TEXT,
        address TEXT,
        blood_group TEXT,
        allergies TEXT,
        user_id INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    
    CREATE TABLE IF NOT EXISTS visits(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT,
        visit_date TEXT,
        chief_complaints TEXT,
        symptoms TEXT,
        doshas TEXT,
        vata_score INTEGER DEFAULT 0,
        pitta_score INTEGER DEFAULT 0,
        kapha_score INTEGER DEFAULT 0,
        prakriti TEXT,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    
    CREATE TABLE IF NOT EXISTS prescriptions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        visit_id INTEGER,
        patient_id TEXT,
        herb1 TEXT,
        herb2 TEXT,
        herb3 TEXT,
        composite_score REAL DEFAULT 0,
        gnn_score REAL DEFAULT 0,
        dosha_score REAL DEFAULT 0,
        virya_score REAL DEFAULT 0,
        prabhav_score REAL DEFAULT 0,
        formulation_form TEXT,
        dosage TEXT,
        duration TEXT,
        timing TEXT,
        anupana TEXT,
        why_text TEXT,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    """)
    
    con.commit()
    con.close()

def hash_pw(x):
    return hashlib.sha256(x.encode()).hexdigest()

def register_user(name, phone, password, role):
    try:
        con = sqlite3.connect(DB)
        con.text_factory = str
        con.execute("INSERT INTO users(name,phone,password,role) VALUES(?,?,?,?)",
                    (name, phone, hash_pw(password), role))
        con.commit()
        con.close()
        return True
    except Exception:
        return False

def login_user(phone, password):
    con = sqlite3.connect(DB)
    con.text_factory = str
    row = con.execute(
        "SELECT id,name,role FROM users WHERE phone=? AND password=?",
        (phone, hash_pw(password))).fetchone()
    con.close()
    return row

def gen_pid():
    return "AYU-" + datetime.now().strftime("%y%m%d%H%M%S")

def add_patient(name, age, gender, phone, address, blood_group, allergies, user_id=None):
    pid = gen_pid()
    con = sqlite3.connect(DB)
    con.text_factory = str
    con.execute(
        "INSERT INTO patients(pid,name,age,gender,phone,address,blood_group,allergies,user_id) "
        "VALUES(?,?,?,?,?,?,?,?,?)",
        (pid, name, age, gender, phone, address, blood_group, allergies, user_id))
    con.commit()
    con.close()
    return pid

def get_patients(search=""):
    con = sqlite3.connect(DB)
    con.text_factory = str
    df = pd.read_sql(
        "SELECT * FROM patients WHERE name LIKE ? OR pid LIKE ? ORDER BY created_at DESC",
        con, params=("%" + search + "%", "%" + search + "%"))
    con.close()
    return df

def get_patient(pid):
    con = sqlite3.connect(DB)
    con.text_factory = str
    df = pd.read_sql("SELECT * FROM patients WHERE pid=?", con, params=(pid,))
    con.close()
    return df.iloc[0] if not df.empty else None

def get_patient_by_user(user_id):
    con = sqlite3.connect(DB)
    con.text_factory = str
    df = pd.read_sql("SELECT * FROM patients WHERE user_id=?", con, params=(int(user_id),))
    con.close()
    return df.iloc[0] if not df.empty else None

def add_visit(patient_id, complaints, symptoms, doshas, v, p, k, prakriti, notes):
    con = sqlite3.connect(DB)
    con.text_factory = str
    
    # Truncate long strings to prevent database issues
    symptoms_json = json.dumps(symptoms, ensure_ascii=False)[:10000] if symptoms else "[]"
    doshas_json = json.dumps(doshas, ensure_ascii=False)[:1000] if doshas else "[]"
    
    cur = con.execute(
        "INSERT INTO visits(patient_id,visit_date,chief_complaints,symptoms,doshas,"
        "vata_score,pitta_score,kapha_score,prakriti,notes) VALUES(?,?,?,?,?,?,?,?,?,?)",
        (patient_id, date.today().isoformat(),
         str(complaints)[:2000] if complaints else "",
         symptoms_json, doshas_json,
         int(v) if v else 0, int(p) if p else 0, int(k) if k else 0,
         str(prakriti)[:100] if prakriti else "",
         str(notes)[:2000] if notes else ""))
    vid = cur.lastrowid
    con.commit()
    con.close()
    return vid

def save_prescription(visit_id, patient_id, h1, h2, h3, score,
                      form_name, dosage, duration, timing, anupana, why, notes):
    con = sqlite3.connect(DB)
    con.text_factory = str
    
    # Helper to truncate strings
    def safe_str(s, max_len=5000):
        if s is None:
            return ""
        return str(s)[:max_len]
    
    con.execute(
        "INSERT INTO prescriptions(visit_id,patient_id,herb1,herb2,herb3,"
        "composite_score,gnn_score,dosha_score,virya_score,prabhav_score,"
        "formulation_form,dosage,duration,timing,anupana,why_text,notes) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (visit_id, patient_id, safe_str(h1, 200), safe_str(h2, 200), safe_str(h3, 200),
         float(score), float(score), 0, 0, 0,
         safe_str(form_name, 200), safe_str(dosage, 200), safe_str(duration, 200),
         safe_str(timing, 200), safe_str(anupana, 200), safe_str(why, 2000),
         safe_str(notes, 2000)))
    con.commit()
    con.close()

def get_visits(pid):
    con = sqlite3.connect(DB)
    con.text_factory = str
    df = pd.read_sql(
        "SELECT * FROM visits WHERE patient_id=? ORDER BY visit_date DESC",
        con, params=(pid,))
    con.close()
    return df

def get_prescriptions(pid):
    con = sqlite3.connect(DB)
    con.text_factory = str
    df = pd.read_sql(
        "SELECT * FROM prescriptions WHERE patient_id=? ORDER BY created_at DESC",
        con, params=(pid,))
    con.close()
    return df

def clinic_stats():
    con = sqlite3.connect(DB)
    con.text_factory = str
    s = {}
    try:
        s["patients"] = pd.read_sql("SELECT COUNT(*) c FROM patients", con).iloc[0]["c"]
        s["today"]    = pd.read_sql(
            "SELECT COUNT(*) c FROM visits WHERE visit_date=?",
            con, params=(date.today().isoformat(),)).iloc[0]["c"]
        s["visits"]   = pd.read_sql("SELECT COUNT(*) c FROM visits", con).iloc[0]["c"]
        s["rx"]       = pd.read_sql("SELECT COUNT(*) c FROM prescriptions", con).iloc[0]["c"]
    except:
        s = {"patients": 0, "today": 0, "visits": 0, "rx": 0}
    con.close()
    return s

# ── PDF Generator ──────────────────────────────────────────────────────────────
def _pdf_safe(text: str) -> str:
    """Replace characters outside Latin-1 range so fpdf core fonts don't crash."""
    if text is None:
        return ""
    text = str(text)
    replacements = {
        "\u2014": "-", "\u2013": "-", "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"', "\u2022": "*", "\u2026": "...",
        "\u00a0": " ", "\u2212": "-",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", errors="replace").decode("latin-1")

def make_pdf(patient_name, patient_id, prakriti, herbs, form_name, dosage,
             duration, timing, anupana, why, diet, notes=""):
    if not HAS_FPDF:
        return None
    
    s = lambda v: _pdf_safe(str(v) if v else "")
    patient_name = s(patient_name)
    patient_id = s(patient_id)
    prakriti = s(prakriti)
    form_name = s(form_name)
    dosage = s(dosage)
    duration = s(duration)
    timing = s(timing)
    anupana = s(anupana)
    why = s(why)
    notes = s(notes)

    from fpdf.enums import XPos, YPos
    LM = 12
    RM = 12
    PW = 210
    CW = PW - LM - RM

    pdf = FPDF()
    pdf.set_margins(LM, LM, RM)
    pdf.add_page()

    def row(text, h=7, bold=False, size=10, color=(0,0,0), fill=False, fc=None):
        pdf.set_x(LM)
        pdf.set_font("Helvetica", "B" if bold else "", size)
        pdf.set_text_color(*color)
        if fill and fc:
            pdf.set_fill_color(*fc)
        pdf.cell(CW, h, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=fill)

    def wrap(text, h=6, size=10):
        pdf.set_x(LM)
        pdf.set_font("Helvetica", "", size)
        pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(CW, h, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Header
    pdf.set_fill_color(15, 81, 50)
    pdf.rect(0, 0, PW, 30, "F")
    pdf.set_xy(LM, 8)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(CW, 10, "Digital Dravyaguna - AYUSH Prescription",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_xy(LM, 20)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(CW, 6, "GNN-powered Ayurvedic Herb Synergy System",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Patient info
    pdf.set_xy(LM, 36)
    row(f"Patient: {patient_name}   |   ID: {patient_id}   |   Date: {date.today().isoformat()}",
        h=8, bold=True, size=11, fill=True, fc=(240, 255, 244))
    row(f"Prakriti: {prakriti}", h=6, size=10)
    pdf.ln(5)

    # Prescription
    row("Prescription (Rx)", h=8, bold=True, size=14, color=(15, 81, 50))
    for i, herb in enumerate(herbs[:3], 1):
        if herb:
            row(f"  {i}. {herb}  -  {dosage}  |  {timing}", h=7, size=11)
    pdf.ln(3)

    # Formulation
    row("Formulation Details:", h=7, bold=True, size=11)
    row(f"  Form: {form_name}", h=6, size=10)
    row(f"  Duration: {duration}", h=6, size=10)
    row(f"  Anupana (vehicle): {anupana}", h=6, size=10)
    if why:
        wrap(f"  Clinical rationale: {why}", size=10)
    if notes:
        wrap(f"  Instructions: {notes}", size=10)
    pdf.ln(4)

    # Diet & Lifestyle
    row("Diet and Lifestyle Guidance:", h=7, bold=True, size=11, color=(15, 81, 50))
    if diet:
        favour = _pdf_safe(', '.join(diet.get('Favour', [])[:4]))
        avoid = _pdf_safe(', '.join(diet.get('Avoid', [])[:4]))
        timing_text = _pdf_safe(diet.get('Timing', ''))
        lifestyle = _pdf_safe(diet.get('Lifestyle', ''))
        wrap(f"  Favour: {favour}")
        wrap(f"  Avoid: {avoid}")
        wrap(f"  Timing: {timing_text}")
        wrap(f"  Lifestyle: {lifestyle}")
    pdf.ln(8)

    # Footer
    pdf.set_x(LM)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(CW, 6, "GNN-assisted decision support. Clinical judgment takes precedence.",
             align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(CW, 6, "Digital Dravyaguna | AYUSH Practitioner System",
             align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(10)
    pdf.set_x(130)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(60, 0, "", border="T", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(130)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(60, 5, "Doctor Signature", align="C")

    import tempfile
    import os
    path = os.path.join(tempfile.gettempdir(), "dravyaguna_rx.pdf")
    pdf.output(path)
    return path

# ── GNN engine ─────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_and_precompute():
    try:
        with open("synergy_model.pkl", "rb") as f:
            md = pickle.load(f)
        with open("ayurvedic_graph.pkl", "rb") as f:
            G = pickle.load(f)
    except FileNotFoundError:
        st.error("Model files not found. Please ensure synergy_model.pkl and ayurvedic_graph.pkl exist.")
        st.stop()
    
    model = md["model"]
    n2v = md["node2vec"]
    herbs = [n for n, d in G.nodes(data=True)
             if d.get("type") == "herb" and n in n2v]
    pairs = list(combinations(herbs, 2))
    v_all = np.array([n2v[h] for h in herbs])
    idx = {h: i for i, h in enumerate(herbs)}
    all_scores = []
    
    for start in range(0, len(pairs), 50000):
        batch = pairs[start:start+50000]
        i1 = np.array([idx[a] for a, b in batch])
        i2 = np.array([idx[b] for a, b in batch])
        v1, v2 = v_all[i1], v_all[i2]
        feats = np.concatenate([v1, v2, v1*v2, np.abs(v1-v2)], axis=1)
        all_scores.append(model.predict_proba(feats)[:, 1])
    
    all_scores = np.concatenate(all_scores)
    cache = {(min(h1, h2), max(h1, h2)): float(s)
             for (h1, h2), s in zip(pairs, all_scores)}
    
    dosha_herbs = {}
    for d in ["vata", "pitta", "kapha"]:
        node = "dosha_" + d
        dosha_herbs[d] = {u for u, v, ed in G.edges(data=True)
                          if v == node and ed.get("relation") == "PACIFIES"
                          and G.nodes[u].get("type") == "herb" and u in n2v}
    
    prabhav_map = {h: {v for u, v, ed in G.edges(data=True)
                       if u == h and ed.get("relation") == "HAS_SPECIAL_EFFECT"}
                   for h in herbs}
    
    return dict(md=md, G=G, herbs=herbs, cache=cache,
                dosha_herbs=dosha_herbs, prabhav_map=prabhav_map)

def cscore(h1, h2, doshas, R):
    G, cache = R["G"], R["cache"]
    dh, pm = R["dosha_herbs"], R["prabhav_map"]
    gnn = cache.get((min(h1, h2), max(h1, h2)), 0.0)
    ds = (sum(1 for d in doshas
               if h1 in dh.get(d, set()) and h2 in dh.get(d, set()))
           / (len(doshas) if doshas else 1))
    v1 = G.nodes[h1].get("virya", "")
    v2 = G.nodes[h2].get("virya", "")
    vs = 1.0 if (v1 and v1 == v2) else (0.2 if (v1 and v2) else 0.5)
    p1, p2 = pm.get(h1, set()), pm.get(h2, set())
    sh = p1 & p2
    ps = min(len(sh) / 3, 1.0)
    comp = 0.40*gnn + 0.30*ds + 0.15*vs + 0.15*ps
    why = []
    if gnn >= 0.8:
        why.append("High GNN synergy")
    if ds == 1.0:
        why.append("Both pacify target Doshas")
    if v1 == v2 and v1:
        why.append("Same Virya (" + v1 + ")")
    if len(sh) >= 2:
        why.append(str(len(sh)) + " shared Prabhav")
    return {
        "Composite": round(comp, 3),
        "GNN": round(gnn, 3),
        "Dosha": round(ds, 3),
        "Virya": round(vs, 3),
        "Prabhav": round(ps, 3),
        "V1": v1 or "-",
        "V2": v2 or "-",
        "Why": " | ".join(why) if why else "Compatible profile",
        "SFx": ", ".join(list(sh)[:3]) if sh else "-",
    }

def recommend_pairs(doshas, R, top_k=10):
    dh, cache = R["dosha_herbs"], R["cache"]
    if not doshas:
        return pd.DataFrame(), []
    cands = None
    for d in doshas:
        h = dh.get(d, set())
        cands = h if cands is None else cands & h
    cands = sorted(cands) if cands else []
    if len(cands) < 2:
        return pd.DataFrame(), cands
    rows = []
    for h1, h2 in combinations(cands, 2):
        if cache.get((min(h1, h2), max(h1, h2)), 0) < 0.45:
            continue
        s = cscore(h1, h2, doshas, R)
        rows.append({"Herb 1": h1, "Herb 2": h2, **s})
    if not rows:
        return pd.DataFrame(), cands
    df = (pd.DataFrame(rows)
          .sort_values("Composite", ascending=False)
          .head(top_k).reset_index(drop=True))
    return df, cands

def find_triplets(pair_df, cands, R, top_k=5):
    if pair_df.empty or len(cands) < 3:
        return pd.DataFrame()
    cache, G, pm = R["cache"], R["G"], R["prabhav_map"]
    results = []
    for _, pair in pair_df.head(3).iterrows():
        h1, h2 = pair["Herb 1"], pair["Herb 2"]
        for h3 in cands:
            if h3 in [h1, h2]:
                continue
            s13 = cache.get((min(h1, h3), max(h1, h3)), 0.0)
            s23 = cache.get((min(h2, h3), max(h2, h3)), 0.0)
            if s13 < 0.45 or s23 < 0.45:
                continue
            s12 = cache.get((min(h1, h2), max(h1, h2)), 0.0)
            tg = (s12 + s13 + s23) / 3
            p1 = pm.get(h1, set())
            p2 = pm.get(h2, set())
            p3 = pm.get(h3, set())
            sh3 = p1 & p2 & p3
            v3 = G.nodes[h3].get("virya", "-")
            ts = round(0.7*tg + 0.3*min(len(sh3)/2, 1.0), 3)
            why = []
            if tg >= 0.8:
                why.append("All three highly synergistic")
            if sh3:
                why.append("Shared: " + ", ".join(list(sh3)[:2]))
            if v3 == pair.get("V1", ""):
                why.append("Matching Virya (" + v3 + ")")
            results.append({
                "Herb 1": h1,
                "Herb 2": h2,
                "Herb 3": h3,
                "Score": ts,
                "GNN Avg": round(tg, 3),
                "Shared Prabhav": len(sh3),
                "Virya 3": v3,
                "Why": " | ".join(why) if why else "Complementary triplet",
            })
    if not results:
        return pd.DataFrame()
    return (pd.DataFrame(results)
            .sort_values("Score", ascending=False)
            .drop_duplicates(subset=["Herb 3"])
            .head(top_k).reset_index(drop=True))

def build_timeline(doshas, h1, h2, h3, dosage, anupana):
    pd0 = doshas[0] if doshas else "vata"
    dn, dd = DETOX_HERBS.get(pd0, ("Triphala", "3g at bedtime"))
    rn, rd = RASAYANA_HERBS.get(pd0, ("Ashwagandha", "5g with milk"))
    t = date.today()
    combo = h1 + (" + " + h2 if h2 else "") + (" + " + h3 if h3 else "")
    return [
        {"week": "Week 1", "phase": "Detox and Prepare (Shodhana)",
         "color": "#1565c0", "icon": "Detox",
         "start": t.isoformat(), "end": (t + timedelta(6)).isoformat(),
         "herbs": dn, "dose": dd, "anupana": anupana,
         "goal": "Cleanse channels (Srotas), prepare body to absorb main formulation.",
         "do": "Light diet, warm water throughout, early bedtime.",
         "avoid": "Heavy meals, cold food, stress."},
        {"week": "Week 2", "phase": "Main Formulation - Begin (Shamana)",
         "color": "#0f5132", "icon": "Begin",
         "start": (t + timedelta(7)).isoformat(), "end": (t + timedelta(13)).isoformat(),
         "herbs": combo, "dose": dosage + " (half dose)", "anupana": anupana,
         "goal": "Introduce formulation gently. Monitor sensitivity.",
         "do": "Follow diet chart strictly. Practise lifestyle routine.",
         "avoid": "Foods that aggravate the imbalanced Dosha."},
        {"week": "Week 3", "phase": "Main Formulation - Full Dose (Shamana)",
         "color": "#0f5132", "icon": "Full",
         "start": (t + timedelta(14)).isoformat(), "end": (t + timedelta(20)).isoformat(),
         "herbs": combo, "dose": dosage + " (full dose)", "anupana": anupana,
         "goal": "Full therapeutic action. Main healing occurs this week.",
         "do": "Continue diet. Add gentle yoga or pranayama. Note improvements.",
         "avoid": "Skipping doses. Incompatible food combinations."},
        {"week": "Week 4", "phase": "Rasayana and Consolidation",
         "color": "#6a1b9a", "icon": "Rejuvenate",
         "start": (t + timedelta(21)).isoformat(), "end": (t + timedelta(27)).isoformat(),
         "herbs": rn, "dose": rd, "anupana": anupana,
         "goal": "Rejuvenate and consolidate the therapeutic effect.",
         "do": "Gradually return to normal diet. Continue healthy habits.",
         "avoid": "Sudden dietary changes. Overexertion."},
    ]

def build_rx_html(rx, dosha_str, p, rows_html):
    notes_line = ("<b>Instructions:</b> " + str(rx.get("notes", "")) + "<br>") if rx.get("notes") else ""
    patient_name = str(p.get("name", ""))
    patient_age = str(p.get("age", ""))
    patient_gender = str(p.get("gender", ""))
    patient_pid = str(p.get("pid", ""))
    rx_date = str(rx.get("date", date.today().isoformat()))
    rx_form_name = str(rx.get("form_name", ""))
    rx_anupana = str(rx.get("anupana", ""))
    rx_duration = str(rx.get("duration", ""))
    rx_score = str(round(rx.get("score", 0), 3))
    rx_why = str(rx.get("why", ""))
    
    return (
        "<!DOCTYPE html><html><body style='margin:0;padding:16px;font-family:Georgia,serif'>"
        "<div style='background:white;border:1px solid #ddd;border-radius:12px;padding:36px;"
        "max-width:680px;box-shadow:0 4px 20px rgba(0,0,0,0.08)'>"
        "<div style='display:flex;justify-content:space-between;border-bottom:3px solid #0f5132;"
        "padding-bottom:16px;margin-bottom:20px'>"
        "<div>"
        "<div style='font-size:22px;font-weight:700;color:#0f5132'>Digital Dravyaguna</div>"
        "<div style='font-size:12px;color:#888;margin-top:2px'>AYUSH Practitioner System - GNN-powered</div>"
        "</div>"
        "<div style='text-align:right;font-size:13px;color:#555'>"
        "<b>Date:</b> " + rx_date + "<br>"
        "<b>Prakriti:</b> " + dosha_str +
        "</div></div>"
        "<div style='background:#f9fffe;border:1px solid #e8f5e9;border-radius:8px;"
        "padding:12px 16px;margin-bottom:20px;font-size:14px'>"
        "<b>Patient:</b> " + patient_name +
        " &nbsp; <b>Age:</b> " + patient_age +
        " &nbsp; <b>Gender:</b> " + patient_gender +
        " &nbsp; <b>ID:</b> " + patient_pid +
        "</div>"
        "<div style='display:flex;align-items:flex-start;gap:20px;margin-bottom:20px'>"
        "<div style='font-size:56px;font-weight:700;color:#0f5132;line-height:1;font-family:Georgia'>Rx</div>"
        "<table style='flex:1;border-collapse:collapse;font-size:14px;width:100%'>"
        "<thead><tr style='background:#0f5132;color:white;font-size:13px'>"
        "<th style='padding:8px 14px;text-align:left;width:30px'>#</th>"
        "<th style='padding:8px 14px;text-align:left'>Herb / Medicine</th>"
        "<th style='padding:8px 14px;text-align:left'>Dosage</th>"
        "<th style='padding:8px 14px;text-align:left'>Timing</th>"
        "</tr></thead>"
        "<tbody>" + rows_html + "</tbody>"
        "</table></div>"
        "<div style='border-top:1px solid #eee;padding-top:14px;font-size:13px;color:#555;line-height:2'>"
        "<b>Preparation:</b> " + rx_form_name + "<br>"
        "<b>Method:</b> " + str(rx.get("fd", {}).get("prep", "")) + "<br>"
        "<b>Anupana:</b> " + rx_anupana + "<br>"
        "<b>Duration:</b> " + rx_duration + "<br>" +
        notes_line +
        "<b>GNN Score:</b> " + rx_score + " - " + rx_why +
        "</div>"
        "<div style='display:flex;justify-content:space-between;margin-top:30px;"
        "padding-top:16px;border-top:2px solid #0f5132'>"
        "<div style='font-size:13px;color:#555'><b>Follow-up:</b> After " + rx_duration + "</div>"
        "<div style='text-align:center'>"
        "<div style='border-bottom:1px solid #333;width:160px;margin-bottom:4px'></div>"
        "<div style='font-size:12px;color:#888'>Doctor Signature</div>"
        "</div></div>"
        "<div style='margin-top:14px;font-size:11px;color:#aaa;text-align:center'>"
        "GNN-assisted decision support. Clinical judgment takes precedence."
        "</div></div></body></html>"
    )

def whatsapp_link(patient_name, herbs, dosage, timing, anupana, duration, diet):
    herb_str = " + ".join([str(h) for h in herbs if h])
    favour = ", ".join(diet.get("Favour", [])[:3])
    avoid = ", ".join(diet.get("Avoid", [])[:3])
    msg = (
        f"🌿 *Digital Dravyaguna — Your Prescription*\n\n"
        f"Dear {patient_name},\n\n"
        f"*Herbs:* {herb_str}\n"
        f"*Dosage:* {dosage}\n"
        f"*Timing:* {timing}\n"
        f"*Anupana:* {anupana}\n"
        f"*Duration:* {duration}\n\n"
        f"*Diet:* Favour — {favour}\n"
        f"Avoid — {avoid}\n\n"
        f"_GNN-assisted Ayurvedic prescription. Follow doctor's guidance._"
    )
    return "https://wa.me/?text=" + urllib.parse.quote(msg)

# ── Startup ────────────────────────────────────────────────────────────────────
init_db()

# Session state defaults
for k in ["logged_in","user_id","user_name","user_role",
          "selected_patient","current_visit_id","current_doshas",
          "rx_pairs","rx_triplets","final_rx", "R"]:
    if k not in st.session_state:
        st.session_state[k] = None

if "logged_in" not in st.session_state or st.session_state["logged_in"] is None:
    st.session_state["logged_in"] = False

# ── Auth Wall ──────────────────────────────────────────────────────────────────
if not st.session_state["logged_in"]:
    # Sidebar branding
    with st.sidebar:
        st.markdown(
            "<div style='text-align:center;padding:30px 0 16px'>"
            "<div style='font-size:40px'>🌿</div>"
            "<div style='font-size:18px;font-weight:700'>Digital Dravyaguna</div>"
            "<div style='font-size:11px;color:#a5d6a7;margin-top:4px'>AYUSH Practitioner System</div>"
            "</div>",
            unsafe_allow_html=True)
        auth_page = st.radio("", ["Login", "Register"], label_visibility="collapsed")

    st.markdown(
        "<div style='text-align:center;padding:40px 0 24px'>"
        "<div style='font-size:48px'>🌿</div>"
        "<h1 style='font-family:Crimson Pro,serif;font-size:36px;color:#0f5132;"
        "margin:8px 0 4px'>Digital Dravyaguna</h1>"
        "<p style='color:#666;font-size:15px'>AYUSH GNN-powered Herb Synergy Platform</p>"
        "</div>",
        unsafe_allow_html=True)

    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        if auth_page == "Login":
            st.markdown("<div class='login-card'>", unsafe_allow_html=True)
            st.markdown("### Sign In")
            phone = st.text_input("Phone / Username", placeholder="Your registered phone")
            password = st.text_input("Password", type="password")
            if st.button("Login →", use_container_width=True):
                row = login_user(phone, password)
                if row:
                    st.session_state.update({
                        "logged_in": True, "user_id": row[0],
                        "user_name": row[1], "user_role": row[2]})
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please try again.")
            st.markdown(
                "<p style='text-align:center;font-size:12px;color:#aaa;margin-top:12px'>"
                "New here? Switch to Register in the sidebar.</p>",
                unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='login-card'>", unsafe_allow_html=True)
            st.markdown("### Create Account")
            reg_name = st.text_input("Full Name")
            reg_phone = st.text_input("Phone (used as username)")
            reg_pw = st.text_input("Password", type="password")
            reg_role = st.selectbox("Role", ["Doctor", "Patient"])
            if st.button("Register →", use_container_width=True):
                if not reg_name or not reg_phone or not reg_pw:
                    st.error("All fields required.")
                elif register_user(reg_name, reg_phone, reg_pw, reg_role):
                    st.success("Account created! Please login.")
                else:
                    st.error("Phone already registered.")
            st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ── Logged-in shell ────────────────────────────────────────────────────────────
ROLE = st.session_state["user_role"]
USER = st.session_state["user_name"]

# Load GNN model (only for Doctor)
if ROLE == "Doctor":
    if st.session_state.get("R") is None:
        ph = st.empty()
        with ph.container():
            st.markdown(
                "<div style='text-align:center;padding:80px 20px'>"
                "<div style='font-size:52px'>🌿</div>"
                "<h2 style='color:#0f5132;margin:10px 0'>Digital Dravyaguna</h2>"
                "<p style='color:#666;font-size:16px'>Pre-computing synergy scores for all herb pairs...</p>"
                "<p style='color:#aaa;font-size:13px'>Runs once. All future lookups will be instant.</p>"
                "</div>",
                unsafe_allow_html=True)
            bar = st.progress(0, text="Loading model...")
        try:
            R = load_and_precompute()
            bar.progress(100, text="Ready!")
            ph.empty()
            st.session_state["R"] = R
            st.rerun()
        except Exception as e:
            bar.empty()
            ph.empty()
            st.error(f"Error loading model: {e}")
            st.info("Please ensure synergy_model.pkl and ayurvedic_graph.pkl exist in the same directory.")
            st.stop()
    R = st.session_state["R"]
    md = R["md"]

# ── Sidebar (logged in) ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<div style='text-align:center;padding:20px 0 10px'>"
        "<div style='font-size:36px'>🌿</div>"
        "<div style='font-size:18px;font-weight:700'>Digital Dravyaguna</div>"
        "<div style='font-size:11px;color:#a5d6a7;margin-top:4px'>AYUSH Practitioner System</div>"
        "</div>"
        "<hr style='border-color:rgba(255,255,255,0.2);margin:10px 0 16px'>",
        unsafe_allow_html=True)

    badge = "role-badge-doctor" if ROLE == "Doctor" else "role-badge-patient"
    st.markdown(
        f"<div style='text-align:center;margin-bottom:14px'>"
        f"<span class='{badge}'>{'👨‍⚕️ Doctor' if ROLE=='Doctor' else '🧑‍💼 Patient'}</span>"
        f"<div style='font-size:13px;margin-top:6px;color:#c8e6c9'>{USER}</div>"
        f"</div>",
        unsafe_allow_html=True)

    if ROLE == "Doctor":
        page = st.radio("Nav",
            ["Dashboard","New Patient","Patient Lookup","Consultation","Prescriptions"],
            label_visibility="collapsed")
    else:
        page = st.radio("Nav",
            ["My Profile","My Prescriptions","My Health"],
            label_visibility="collapsed")

    s = clinic_stats()
    if ROLE == "Doctor":
        st.markdown(
            "<hr style='border-color:rgba(255,255,255,0.2);margin:16px 0'>"
            "<div style='padding:0 4px;font-size:13px'>"
            "<div style='color:#a5d6a7;font-size:11px;font-weight:600;text-transform:uppercase;"
            "letter-spacing:1px;margin-bottom:8px'>Clinic</div>"
            "<div style='display:flex;justify-content:space-between;margin-bottom:5px'>"
            "<span style='color:#e8f5e9'>Patients</span>"
            "<b style='color:white'>" + str(int(s["patients"])) + "</b></div>"
            "<div style='display:flex;justify-content:space-between;margin-bottom:5px'>"
            "<span style='color:#e8f5e9'>Today</span>"
            "<b style='color:#a5d6a7'>" + str(int(s["today"])) + "</b></div>"
            "<div style='display:flex;justify-content:space-between'>"
            "<span style='color:#e8f5e9'>Prescriptions</span>"
            "<b style='color:#e8f5e9'>" + str(int(s["rx"])) + "</b></div>"
            "</div>",
            unsafe_allow_html=True)

    st.markdown("<hr style='border-color:rgba(255,255,255,0.2);margin:16px 0'>",
                unsafe_allow_html=True)

    # Dark mode toggle
    dm_label = "☀️ Light Mode" if DARK else "🌙 Dark Mode"
    if st.button(dm_label, use_container_width=True):
        st.session_state["dark_mode"] = not DARK
        st.rerun()

    if st.button("Logout", use_container_width=True):
        for k in list(st.session_state.keys()):
            st.session_state[k] = None
        st.session_state["logged_in"] = False
        st.session_state["dark_mode"] = DARK
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PATIENT PORTAL
# ══════════════════════════════════════════════════════════════════════════════
if ROLE == "Patient":
    uid = st.session_state["user_id"]
    patient_rec = get_patient_by_user(uid)

    # Self-service account linking
    if patient_rec is None:
        st.markdown("## Link Your Clinic Record")
        st.divider()
        st.markdown(
            "<div style='background:#fff8e1;border:1px solid #ffe082;border-radius:10px;"
            "padding:20px;margin-bottom:20px'>"
            "<div style='font-weight:600;color:#f57c00;font-size:15px;margin-bottom:8px'>"
            "Your account is not linked to a clinic record yet</div>"
            "<div style='font-size:13px;color:#555'>"
            "Ask your doctor for your <b>Patient ID</b> (looks like <code>AYU-260424062528</code>) "
            "and enter it below to connect your account to your health records."
            "</div></div>",
            unsafe_allow_html=True)

        link_col, _ = st.columns([2, 1])
        with link_col:
            entered_pid = st.text_input("Enter your Patient ID",
                                         placeholder="e.g. AYU-260424062528")
            if st.button("Link My Account", use_container_width=True):
                if not entered_pid.strip():
                    st.error("Please enter your Patient ID.")
                else:
                    con = sqlite3.connect(DB)
                    con.text_factory = str
                    row = con.execute(
                        "SELECT id, name, user_id FROM patients WHERE pid=?",
                        (entered_pid.strip(),)).fetchone()
                    con.close()
                    if row is None:
                        st.error("Patient ID not found. Please check with your doctor.")
                    elif row[2] is not None and row[2] != uid:
                        st.error("This Patient ID is already linked to another account.")
                    else:
                        con = sqlite3.connect(DB)
                        con.text_factory = str
                        con.execute(
                            "UPDATE patients SET user_id=? WHERE pid=?",
                            (uid, entered_pid.strip()))
                        con.commit()
                        con.close()
                        st.success(f"Linked successfully! Welcome, {row[1]}.")
                        st.rerun()
        st.stop()

    # Patient is linked
    if page == "My Profile":
        st.markdown("## My Profile")
        st.divider()
        p = patient_rec
        st.markdown(
            f"<div class='patient-card'>"
            f"<div class='patient-name'>{p['name']}</div>"
            f"<div style='font-size:13px;color:{THEME['subtext']};margin-top:6px;line-height:2'>"
            f"<b>Patient ID:</b> {p['pid']}<br>"
            f"<b>Age:</b> {p['age']} | <b>Gender:</b> {p['gender']}<br>"
            f"<b>Phone:</b> {p['phone'] or '-'}<br>"
            f"<b>Blood Group:</b> {p['blood_group'] or '-'}<br>"
            f"<b>Allergies:</b> {p['allergies'] or 'None recorded'}"
            f"</div></div>",
            unsafe_allow_html=True)
        vdf = get_visits(p["pid"])
        st.markdown(f"### Visit History ({len(vdf)} visits)")
        if vdf.empty:
            st.info("No visits recorded yet.")
        else:
            for _, v in vdf.iterrows():
                doshas = json.loads(v.doshas) if v.doshas else []
                badges = " ".join(
                    "<span class='dosha-" + d + "'>" + d.upper() + "</span>"
                    for d in doshas)
                st.markdown(
                    "<div class='patient-card'>"
                    "<b>" + str(v.visit_date) + "</b> " + badges +
                    "<div style='font-size:13px;color:#444;margin-top:8px'>"
                    "<b>Complaints:</b> " + str(v.chief_complaints or "-") +
                    "</div></div>",
                    unsafe_allow_html=True)

    elif page == "My Prescriptions":
        st.markdown("## My Prescriptions")
        st.divider()
        pid_to_use = patient_rec["pid"]
        rxdf = get_prescriptions(pid_to_use)

        st.caption(f"Patient ID: {pid_to_use} | Prescriptions found: {len(rxdf)}")

        if rxdf.empty:
            st.info("No prescriptions found for your account yet. "
                    "Your doctor will prescribe after your consultation.")
        else:
            try:
                vdf_tmp = get_visits(pid_to_use)
                last_visit = vdf_tmp.iloc[0] if not vdf_tmp.empty else None
                dosha_val = (json.loads(last_visit["doshas"])[0]
                             if last_visit is not None
                             and last_visit["doshas"] else "vata")
            except Exception:
                dosha_val = "vata"
            diet_wa = DIET_CHART.get(dosha_val, {})

            for idx_r, r in rxdf.iterrows():
                try:
                    h1 = str(r.herb1 or "")
                    h2 = str(r.herb2 or "")
                    h3 = str(r.herb3 or "")
                    herbs_str = " + ".join(h for h in [h1, h2, h3] if h.strip())
                    herbs_list = [h1, h2, h3]
                    score_str = str(round(float(r.composite_score or 0), 3))
                    form_str = str(r.formulation_form or "Churna")
                    dosage_str = str(r.dosage or "-")
                    dur_str = str(r.duration or "-")
                    tim_str = str(r.timing or "-")
                    anu_str = str(r.anupana or "-")
                    why_str = str(r.why_text or "")
                    date_str = str(r.created_at or "")[:16]

                    st.markdown(
                        "<div class='patient-card'>"
                        "<div style='display:flex;justify-content:space-between;"
                        "align-items:flex-start;margin-bottom:10px'>"
                        "<div class='form-badge'>" + form_str + "</div>"
                        "<div style='font-size:11px;color:#aaa'>" + date_str + "</div>"
                        "</div>"
                        "<div class='patient-name' style='font-size:18px'>"
                        + herbs_str + "</div>"
                        "<div style='margin-top:12px;display:grid;"
                        "grid-template-columns:1fr 1fr;gap:8px;font-size:13px;color:#555'>"
                        "<div><b>Dosage</b><br>" + dosage_str + "</div>"
                        "<div><b>Duration</b><br>" + dur_str + "</div>"
                        "<div><b>Timing</b><br>" + tim_str + "</div>"
                        "<div><b>Anupana</b><br>" + anu_str + "</div>"
                        "</div>"
                        "<div style='margin-top:10px;background:#f1f8e9;border-radius:6px;"
                        "padding:8px 12px;font-size:12px;color:#0f5132'>"
                        "<b>GNN Score: " + score_str + "</b>"
                        + (" &nbsp;|&nbsp; <i>" + why_str + "</i>" if why_str else "") +
                        "</div></div>",
                        unsafe_allow_html=True)

                    try:
                        wa = whatsapp_link(
                            patient_rec["name"], herbs_list,
                            dosage_str, tim_str, anu_str, dur_str, diet_wa)
                        st.markdown(
                            f"<a href='{wa}' target='_blank' class='share-btn'>"
                            f"📲 Share on WhatsApp</a>",
                            unsafe_allow_html=True)
                    except Exception:
                        pass

                    st.markdown("<br>", unsafe_allow_html=True)

                except Exception as card_err:
                    st.warning(f"Could not display prescription #{idx_r + 1}: {card_err}")

    elif page == "My Health":
        st.markdown("## My Health Overview")
        st.divider()
        rxdf = get_prescriptions(patient_rec["pid"])
        vdf = get_visits(patient_rec["pid"])
        col1, col2, col3 = st.columns(3)
        col1.markdown(
            "<div class='metric-card'><div class='metric-num'>" + str(len(vdf)) + "</div>"
            "<div class='metric-label'>Total Visits</div></div>",
            unsafe_allow_html=True)
        col2.markdown(
            "<div class='metric-card'><div class='metric-num'>" + str(len(rxdf)) + "</div>"
            "<div class='metric-label'>Prescriptions</div></div>",
            unsafe_allow_html=True)
        if not vdf.empty and "prakriti" in vdf.columns:
            latest = str(vdf.iloc[0]["prakriti"] or "-")
        else:
            latest = "-"
        col3.markdown(
            "<div class='metric-card'><div class='metric-num' style='font-size:20px'>" +
            latest + "</div><div class='metric-label'>Last Prakriti</div></div>",
            unsafe_allow_html=True)
        if not vdf.empty:
            st.markdown("#### Dosha Score History")
            vdf["visit_date"] = pd.to_datetime(vdf["visit_date"])
            chart_df = vdf.set_index("visit_date")[
                ["vata_score","pitta_score","kapha_score"]]
            chart_df.columns = ["Vata","Pitta","Kapha"]
            st.line_chart(chart_df)

    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# DOCTOR PORTAL BELOW
# ══════════════════════════════════════════════════════════════════════════════
s = clinic_stats()

# DASHBOARD
if page == "Dashboard":
    st.markdown(f"## Good day, Dr. {USER}")
    st.markdown("*" + datetime.now().strftime("%A, %B %d %Y") + "*")
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    for col, num, label, color in [
        (c1, int(s["patients"]), "Total Patients",  "#0f5132"),
        (c2, int(s["today"]),    "Today's Visits",  "#1565c0"),
        (c3, int(s["visits"]),   "Total Visits",    "#6a1b9a"),
        (c4, int(s["rx"]),       "Prescriptions",   "#bf360c"),
    ]:
        col.markdown(
            "<div class='metric-card' style='border-left-color:" + color + "'>"
            "<div class='metric-num' style='color:" + color + "'>" + str(num) + "</div>"
            "<div class='metric-label'>" + label + "</div></div>",
            unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    la, lb = st.columns([2, 1])
    with la:
        st.markdown("#### Recent Patients")
        rec = get_patients().head(6)
        if rec.empty:
            st.info("No patients yet.")
        else:
            for _, p in rec.iterrows():
                g = "M" if p.gender == "Male" else "F" if p.gender == "Female" else "O"
                st.markdown(
                    "<div class='patient-card'>"
                    "<div class='patient-name'>" + g + " " + str(p["name"]) + "</div>"
                    "<div style='font-size:13px;color:#666;margin-top:4px'>"
                    "ID: " + str(p.pid) + " | Age: " + str(p.age) +
                    " | " + str(p.phone or "No phone") +
                    " | <span style='color:#aaa'>" + str(p.created_at[:10]) + "</span>"
                    "</div></div>",
                    unsafe_allow_html=True)
    with lb:
        st.markdown("#### Dosha Distribution")
        con = sqlite3.connect(DB)
        con.text_factory = str
        try:
            ddf = pd.read_sql(
                "SELECT prakriti,COUNT(*) cnt FROM visits WHERE prakriti!='' GROUP BY prakriti", con)
        except:
            ddf = pd.DataFrame()
        con.close()
        if not ddf.empty:
            st.bar_chart(ddf.set_index("prakriti")["cnt"])
        else:
            st.info("No visits yet.")

    # Growth chart
    st.markdown("#### Clinic Growth")
    con = sqlite3.connect(DB)
    con.text_factory = str
    try:
        growth = pd.read_sql(
            "SELECT visit_date, COUNT(*) visits FROM visits "
            "GROUP BY visit_date ORDER BY visit_date DESC LIMIT 14", con)
        growth = growth.set_index("visit_date").sort_index()
        if not growth.empty:
            st.line_chart(growth)
    except:
        pass
    con.close()

# NEW PATIENT
elif page == "New Patient":
    st.markdown("## Register New Patient")
    st.divider()
    with st.form("new_pt"):
        c1, c2, c3 = st.columns(3)
        with c1:
            name = st.text_input("Full Name *")
            phone = st.text_input("Phone")
        with c2:
            age = st.number_input("Age *", 1, 120, 30)
            bg = st.selectbox("Blood Group",
                ["Unknown","A+","A-","B+","B-","AB+","AB-","O+","O-"])
        with c3:
            gender = st.selectbox("Gender *", ["Male","Female","Other"])
            addr = st.text_input("City / Area")
        allergies = st.text_area("Known Allergies / Medical History", height=80)
        link_account = st.checkbox("Link to existing Patient account (if they registered)",
                                   value=False)
        linked_phone = ""
        if link_account:
            linked_phone = st.text_input("Patient's registered phone")
        if st.form_submit_button("Register Patient", use_container_width=True):
            if not name:
                st.error("Name is required.")
            else:
                uid = None
                if link_account and linked_phone:
                    con = sqlite3.connect(DB)
                    con.text_factory = str
                    row = con.execute(
                        "SELECT id FROM users WHERE phone=? AND role='Patient'",
                        (linked_phone,)).fetchone()
                    con.close()
                    uid = row[0] if row else None
                pid = add_patient(name, age, gender, phone, addr, bg, allergies, uid)
                st.success("Registered! Patient ID: " + pid)
                st.balloons()

# PATIENT LOOKUP
elif page == "Patient Lookup":
    st.markdown("## Patient Lookup")
    st.divider()
    search = st.text_input("Search by name or Patient ID")
    patients = get_patients(search)
    if patients.empty:
        st.info("No patients found.")
    else:
        for _, p in patients.iterrows():
            g = "M" if p.gender == "Male" else "F" if p.gender == "Female" else "O"
            ca, cb = st.columns([5, 1])
            with ca:
                allergy_line = ("<br><span style='color:#c62828'>Allergies: " +
                                str(p.allergies) + "</span>") if p.allergies else ""
                st.markdown(
                    "<div class='patient-card'>"
                    "<div class='patient-name'>" + g + " " + str(p["name"]) + "</div>"
                    "<div style='font-size:13px;color:#666;margin-top:4px'>"
                    "ID: " + str(p.pid) + " | Age: " + str(p.age) +
                    " | " + str(p.gender) + " | " + str(p.blood_group or "-") +
                    " | " + str(p.phone or "-") + allergy_line +
                    "</div></div>",
                    unsafe_allow_html=True)
            with cb:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Select", key="s_" + p.pid):
                    st.session_state["selected_patient"] = p.pid

    pid = st.session_state.get("selected_patient")
    if pid:
        patient = get_patient(pid)
        if patient is not None:
            st.divider()
            st.markdown("### Records — **" + str(patient["name"]) + "** (" + pid + ")")
            tv, tp = st.tabs(["Visit History", "Prescription History"])
            with tv:
                vdf = get_visits(pid)
                if vdf.empty:
                    st.info("No visits yet.")
                else:
                    for _, v in vdf.iterrows():
                        doshas = json.loads(v.doshas) if v.doshas else []
                        badges = " ".join(
                            "<span class='dosha-" + d + "'>" + d.upper() + "</span>"
                            for d in doshas)
                        st.markdown(
                            "<div class='patient-card'>"
                            "<div style='display:flex;justify-content:space-between'>"
                            "<div><b>" + str(v.visit_date) + "</b> " + badges + "</div>"
                            "<div style='font-size:12px;color:#888'>Prakriti: " +
                            str(v.prakriti or "-") + "</div></div>"
                            "<div style='font-size:13px;color:#444;margin-top:8px'>"
                            "<b>Complaints:</b> " + str(v.chief_complaints or "-") +
                            "</div></div>",
                            unsafe_allow_html=True)
            with tp:
                rxdf = get_prescriptions(pid)
                if rxdf.empty:
                    st.info("No prescriptions yet.")
                else:
                    for _, r in rxdf.iterrows():
                        herbs_list = [str(r.herb1), str(r.herb2 or ""), str(r.herb3 or "")]
                        herbs = " + ".join(h for h in herbs_list if h)
                        why_line = ("<div style='font-size:12px;color:#666;margin-top:4px;"
                                    "font-style:italic'>" + str(r.why_text) + "</div>"
                                    ) if r.why_text else ""
                        st.markdown(
                            "<div class='patient-card'>"
                            "<div class='form-badge'>" +
                            str(r.formulation_form or "Churna") + "</div><br>"
                            "<div class='patient-name'>" + herbs + "</div>"
                            "<div style='font-size:13px;color:#555;margin-top:6px'>"
                            "Score: " + str(round(r.composite_score, 3)) +
                            " | " + str(r.dosage or "-") +
                            " | " + str(r.duration or "-") +
                            " | " + str(r.timing or "-") + "</div>" +
                            why_line +
                            "<div style='font-size:11px;color:#aaa;margin-top:4px'>" +
                            str(r.created_at[:16]) + "</div></div>",
                            unsafe_allow_html=True)

# CONSULTATION
elif page == "Consultation":
    st.markdown("## Patient Consultation")
    patients = get_patients()
    if patients.empty:
        st.warning("No patients registered. Go to New Patient first.")
        st.stop()
    opts = {r["name"] + " (" + r.pid + ")": r.pid
            for _, r in patients.iterrows()}
    pid = opts[st.selectbox("Select Patient", list(opts.keys()))]
    patient = get_patient(pid)
    if patient is not None:
        al = (" | <span style='color:#c62828'>Allergies: " +
              str(patient.allergies) + "</span>") if patient.allergies else ""
        st.markdown(
            "<div style='background:#e8f5e9;border-radius:8px;padding:12px 16px;margin:8px 0'>"
            "<b>" + str(patient["name"]) + "</b> | Age: " + str(patient.age) +
            " | " + str(patient.gender) + " | " + pid + al + "</div>",
            unsafe_allow_html=True)
    st.divider()
    t1, t2, t3 = st.tabs([
        "Step 1 — Symptoms", "Step 2 — GNN Analysis", "Step 3 — Prescription"])

    # STEP 1
    with t1:
        complaints = st.text_area("Chief Complaints",
            placeholder="Describe the patient's main complaints...", height=70)
        st.markdown("#### Symptom Checklist")
        v_score = p_score = k_score = 0
        selected_symptoms = []
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                "<div style='background:#ede7f6;border-radius:8px;padding:10px 14px;"
                "font-weight:600;color:#4527a0;margin-bottom:10px'>Vata symptoms</div>",
                unsafe_allow_html=True)
            for sym, wt in SYMPTOMS["Vata"].items():
                if st.checkbox(sym, key="v_" + sym):
                    v_score += wt
                    selected_symptoms.append(sym)
        with c2:
            st.markdown(
                "<div style='background:#fbe9e7;border-radius:8px;padding:10px 14px;"
                "font-weight:600;color:#bf360c;margin-bottom:10px'>Pitta symptoms</div>",
                unsafe_allow_html=True)
            for sym, wt in SYMPTOMS["Pitta"].items():
                if st.checkbox(sym, key="p_" + sym):
                    p_score += wt
                    selected_symptoms.append(sym)
        with c3:
            st.markdown(
                "<div style='background:#e8f5e9;border-radius:8px;padding:10px 14px;"
                "font-weight:600;color:#1b5e20;margin-bottom:10px'>Kapha symptoms</div>",
                unsafe_allow_html=True)
            for sym, wt in SYMPTOMS["Kapha"].items():
                if st.checkbox(sym, key="k_" + sym):
                    k_score += wt
                    selected_symptoms.append(sym)

        total = max(v_score + p_score + k_score, 1)
        st.markdown("<br>#### Dosha Imbalance", unsafe_allow_html=True)
        for label, score, color in [
            ("Vata",  v_score, "#7c4dff"),
            ("Pitta", p_score, "#f4511e"),
            ("Kapha", k_score, "#0f5132"),
        ]:
            pct = max(100 * score // total, 2)
            st.markdown(
                "<div style='display:flex;align-items:center;margin-bottom:8px'>"
                "<div style='width:60px;font-size:13px;font-weight:500'>" + label + "</div>"
                "<div style='flex:1;background:#eee;border-radius:4px;height:20px'>"
                "<div style='width:" + str(pct) + "%;background:" + color + ";"
                "border-radius:4px;height:100%;display:flex;align-items:center;"
                "padding-left:8px;font-size:11px;color:white;font-weight:500'>" +
                str(score) + "</div></div></div>",
                unsafe_allow_html=True)

        sm = {"vata": v_score, "pitta": p_score, "kapha": k_score}
        mx = max(sm.values()) if sm else 0
        auto_doshas = [d for d, sc in sm.items() if sc >= mx * 0.7 and sc > 0]
        prakriti = "-".join(d.capitalize() for d in auto_doshas) if auto_doshas else "Balanced"
        if auto_doshas:
            badges = " ".join(
                "<span class='dosha-" + d + "'>" + d.upper() + "</span>"
                for d in auto_doshas)
            st.markdown("<br><b>Detected Prakriti:</b> " + badges,
                        unsafe_allow_html=True)
        doc_notes = st.text_area("Doctor's Notes",
            placeholder="Pulse, tongue, eyes...", height=60)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Save and Run GNN Analysis", use_container_width=True):
            if not selected_symptoms:
                st.warning("Select at least one symptom.")
            else:
                vid = add_visit(pid, complaints, selected_symptoms,
                                auto_doshas, v_score, p_score, k_score, prakriti, doc_notes)
                st.session_state.update({
                    "current_visit_id": vid, "current_doshas": auto_doshas,
                    "rx_pairs": None, "rx_triplets": None})
                st.success("Saved. Switch to Step 2.")

    # STEP 2
    with t2:
        doshas = st.session_state.get("current_doshas") or []
        if not doshas:
            st.info("Complete Step 1 first.")
        else:
            badges = " ".join(
                "<span class='dosha-" + d + "'>" + d.upper() + "</span>"
                for d in doshas)
            st.markdown("Target: " + badges, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            pair_df, cands = recommend_pairs(doshas, R, top_k=10)
            triplet_df = find_triplets(pair_df, cands, R, top_k=5)
            st.session_state["rx_pairs"] = pair_df
            st.session_state["rx_triplets"] = triplet_df
            st.markdown(
                "**" + str(len(cands)) + "** candidate herbs  |  "
                "**" + str(len(pair_df)) + "** pairs  |  "
                "**" + str(len(triplet_df)) + "** triplets")
            if pair_df.empty:
                st.warning("No synergistic pairs found. Try fewer Doshas.")
            else:
                st.markdown("#### Top Herb Pairs")
                top3 = pair_df.head(3)
                cols = st.columns(3)
                for i, (_, row) in enumerate(top3.iterrows()):
                    c = row["Composite"]
                    color = "#0f5132" if c >= 0.75 else "#f57c00"
                    cols[i].markdown(
                        "<div class='rx-card' style='border-color:" + color + "'>"
                        "<div style='font-size:11px;color:" + color + ";font-weight:600;"
                        "text-transform:uppercase'>Pair #" + str(i+1) + "</div>"
                        "<div style='font-size:17px;font-weight:600;color:#0a3d2e;margin:4px 0'>" +
                        str(row["Herb 1"]) + "</div>"
                        "<div style='color:#555;font-size:13px'>+ " + str(row["Herb 2"]) + "</div>"
                        "<div style='font-size:26px;font-weight:700;color:" + color + ";margin:8px 0'>" +
                        str(c) + "</div>"
                        "<div style='background:#eee;border-radius:4px;height:6px;margin:4px 0'>"
                        "<div style='width:" + str(int(c*100)) + "%;background:" + color + ";"
                        "border-radius:4px;height:6px'></div></div>"
                        "<div style='margin-top:8px'>"
                        "<span class='chip chip-gnn'>GNN " + str(round(row["GNN"],2)) + "</span>"
                        "<span class='chip chip-virya'>Virya " + str(round(row["Virya"],2)) + "</span>"
                        "<span class='chip chip-prabhav'>Prabhav " + str(round(row["Prabhav"],2)) + "</span>"
                        "</div>"
                        "<div style='font-size:11px;color:#555;margin-top:6px;font-style:italic'>" +
                        str(row["Why"]) + "</div></div>",
                        unsafe_allow_html=True)

                if not triplet_df.empty:
                    st.markdown("<br>#### 3-Herb Classical Combinations")
                    st.markdown(
                        "<small>Like Triphala (3 fruits) or Trikatu (3 pungents)</small>",
                        unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    tcols = st.columns(3)
                    for i, (_, row) in enumerate(triplet_df.head(3).iterrows()):
                        sc = row["Score"]
                        color = "#0f5132" if sc >= 0.75 else "#f57c00"
                        tcols[i].markdown(
                            "<div style='background:linear-gradient(135deg,#f1f8e9,#fafff8);"
                            "border:2px solid " + color + ";border-radius:12px;padding:18px'>"
                            "<div style='font-size:11px;color:" + color + ";font-weight:600;"
                            "text-transform:uppercase'>Triplet #" + str(i+1) + "</div>"
                            "<div style='font-size:15px;font-weight:600;color:#0a3d2e;margin:8px 0 4px'>" +
                            str(row["Herb 1"]) + "</div>"
                            "<div style='color:#555;font-size:13px'>+ " + str(row["Herb 2"]) + "</div>"
                            "<div style='color:#0f5132;font-size:14px;font-weight:600;margin-top:4px'>"
                            "+ " + str(row["Herb 3"]) + "</div>"
                            "<div style='font-size:24px;font-weight:700;color:" + color + ";"
                            "margin:10px 0 4px'>" + str(sc) + "</div>"
                            "<div style='font-size:11px;color:#555;font-style:italic'>" +
                            str(row["Why"]) + "</div></div>",
                            unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                st.dataframe(
                    pair_df[["Herb 1","Herb 2","Composite","GNN","Dosha","Virya","Prabhav","Why"]]
                    .style.background_gradient(
                        subset=["Composite","GNN"], cmap="RdYlGn", vmin=0.4, vmax=1.0)
                    .format({"Composite":"{:.3f}","GNN":"{:.3f}","Dosha":"{:.2f}",
                             "Virya":"{:.2f}","Prabhav":"{:.2f}"}),
                    hide_index=True, use_container_width=True)
                st.success("Done. Go to Step 3.")

    # STEP 3
    with t3:
        pair_df = st.session_state.get("rx_pairs")
        triplet_df = st.session_state.get("rx_triplets")
        doshas = st.session_state.get("current_doshas") or []
        if pair_df is None or pair_df.empty:
            st.info("Complete Steps 1 and 2 first.")
        else:
            pd0 = doshas[0] if doshas else "vata"
            forms = FORMULATION_FORMS.get(pd0, FORMULATION_FORMS["vata"])
            diet = DIET_CHART.get(pd0, {})
            st.markdown("### Build Prescription")
            st.markdown("<br>", unsafe_allow_html=True)

            rx_type = st.radio("Formulation type",
                ["2-herb pair", "3-herb classical combination"], horizontal=True)
            if rx_type == "2-herb pair":
                lbls = [str(r["Herb 1"]) + " + " + str(r["Herb 2"]) +
                        "  (score " + str(round(r["Composite"], 3)) + ")"
                        for _, r in pair_df.head(5).iterrows()]
                chosen = st.selectbox("Select combination", lbls)
                row = pair_df.iloc[lbls.index(chosen)]
                h1, h2, h3 = row["Herb 1"], row["Herb 2"], ""
                score, why = row["Composite"], row.get("Why", "")
            else:
                if triplet_df is None or triplet_df.empty:
                    st.warning("No triplets found. Use 2-herb pair.")
                    st.stop()
                lbls = [str(r["Herb 1"]) + " + " + str(r["Herb 2"]) + " + " + str(r["Herb 3"]) +
                        "  (score " + str(round(r["Score"], 3)) + ")"
                        for _, r in triplet_df.iterrows()]
                chosen = st.selectbox("Select 3-herb combination", lbls)
                row = triplet_df.iloc[lbls.index(chosen)]
                h1, h2, h3 = row["Herb 1"], row["Herb 2"], row["Herb 3"]
                score, why = row["Score"], row.get("Why", "")

            combo = h1 + (" + " + h2 if h2 else "") + (" + " + h3 if h3 else "")
            st.markdown("<br>#### Formulation Form", unsafe_allow_html=True)
            form_names = [f["name"] for f in forms]
            chosen_form = st.selectbox("Preparation method", form_names)
            fd = next(f for f in forms if f["name"] == chosen_form)
            st.markdown(
                "<div style='background:#f1f8e9;border-radius:10px;padding:16px;"
                "margin:10px 0;border-left:4px solid #0f5132'>"
                "<div class='form-badge'>" + fd["name"] + "</div>"
                "<div style='font-size:14px;color:#333;margin-top:8px'>"
                "<b>Preparation:</b> " + fd["prep"] + "</div>"
                "<div style='font-size:14px;color:#333;margin-top:6px'>"
                "<b>Standard dose:</b> " + fd["dose"] + "</div>"
                "<div style='font-size:13px;color:#666;margin-top:6px'>"
                "<b>Shelf life:</b> " + fd["shelf"] + "</div></div>",
                unsafe_allow_html=True)

            st.markdown("#### Dosage Details", unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                dosage = st.text_input("Dosage", value=fd["dose"].split(" with")[0])
            with c2:
                duration = st.text_input("Duration", value="4 weeks")
            with c3:
                timing = st.selectbox("Timing",
                    ["Before meals","After meals","Morning empty stomach","Bedtime","With meals"])
            anupana = st.text_input("Anupana (vehicle)",
                                      value=ANUPANA.get(pd0, "Warm water"))
            rx_notes = st.text_area("Additional Instructions", height=60)
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Generate Complete Prescription", use_container_width=True):
                vid = st.session_state.get("current_visit_id")
                save_prescription(vid, pid, h1, h2, h3, score,
                                  chosen_form, dosage, duration, timing,
                                  anupana, why, rx_notes)
                st.session_state["final_rx"] = {
                    "patient": patient, "h1": h1, "h2": h2, "h3": h3,
                    "combo": combo, "score": score, "why": why,
                    "fd": fd, "form_name": chosen_form, "dosage": dosage,
                    "duration": duration, "timing": timing, "anupana": anupana,
                    "notes": rx_notes, "date": date.today().isoformat(),
                    "doshas": doshas, "diet": diet,
                }
                st.success("Prescription generated!")

            rx = st.session_state.get("final_rx")
            if rx:
                st.divider()
                oa, ob, oc, od = st.tabs([
                    "Prescription Slip", "Formulation Card",
                    "Diet and Lifestyle", "4-Week Timeline"])
                h1, h2, h3 = rx["h1"], rx["h2"], rx["h3"]
                combo = rx["combo"]
                dosha_str = " + ".join(d.capitalize() for d in rx["doshas"])
                p = rx["patient"]
                herbs_list = [h1, h2, h3]

                # TAB A — Rx Slip
                with oa:
                    st.markdown("*Press Ctrl+P / Cmd+P to print*")
                    rows_html = ""
                    for herb, num in [(h1, "1"), (h2, "2"), (h3, "3")]:
                        if herb and str(herb).strip():
                            rows_html += (
                                "<tr>"
                                "<td style='padding:10px 14px;border-bottom:1px solid #f0f0f0;"
                                "color:#555'>" + num + "</td>"
                                "<td style='padding:10px 14px;border-bottom:1px solid #f0f0f0;"
                                "font-weight:600'>" + str(herb) + "</td>"
                                "<td style='padding:10px 14px;border-bottom:1px solid #f0f0f0'>" +
                                str(rx["dosage"]) + "</td>"
                                "<td style='padding:10px 14px;border-bottom:1px solid #f0f0f0'>" +
                                str(rx["timing"]) + "</td>"
                                "</tr>")
                    rx_html = build_rx_html(rx, dosha_str, p, rows_html)
                    st.components.v1.html(rx_html, height=680, scrolling=True)

                    # PDF Download
                    st.markdown("---")
                    col_pdf, col_wa = st.columns([1, 1])
                    with col_pdf:
                        if HAS_FPDF:
                            prakriti_str = " + ".join(d.capitalize() for d in rx["doshas"])
                            pdf_path = make_pdf(
                                str(p["name"]), str(p["pid"]), prakriti_str,
                                [h1, h2, h3], rx["form_name"], rx["dosage"],
                                rx["duration"], rx["timing"], rx["anupana"],
                                rx["why"], rx["diet"], rx["notes"])
                            if pdf_path:
                                try:
                                    with open(pdf_path, "rb") as f:
                                        pdf_bytes = f.read()
                                    st.download_button(
                                        "📄 Download PDF Prescription",
                                        pdf_bytes,
                                        file_name="dravyaguna_prescription.pdf",
                                        mime="application/pdf",
                                        use_container_width=True)
                                except Exception as pdf_err:
                                    st.error(f"PDF error: {pdf_err}")
                        else:
                            st.info("Install fpdf2 for PDF export: `pip install fpdf2`")
                    with col_wa:
                        wa_url = whatsapp_link(
                            str(p["name"]), herbs_list, str(rx["dosage"]),
                            str(rx["timing"]), str(rx["anupana"]), str(rx["duration"]), rx["diet"])
                        st.markdown(
                            f"<a href='{wa_url}' target='_blank' class='share-btn'>"
                            f"📲 Share on WhatsApp</a>",
                            unsafe_allow_html=True)

                # TAB B — Formulation Card
                with ob:
                    st.markdown("#### Formulation Details")
                    st.markdown(
                        "<div style='background:linear-gradient(135deg,#0f5132,#1a6b42);"
                        "color:white;border-radius:12px;padding:24px;margin-bottom:20px'>"
                        "<div style='font-size:13px;color:#a5d6a7;text-transform:uppercase;"
                        "letter-spacing:1px;font-weight:600'>Prescribed Formulation</div>"
                        "<div style='font-size:26px;font-weight:700;margin:8px 0;font-family:Crimson Pro,serif'>" + str(combo) + "</div>"
                        "<div style='font-size:14px;color:#c8e6c9'>" +
                        str(rx["form_name"]) + " | " + dosha_str +
                        " | Score: " + str(round(rx["score"], 3)) + "</div></div>",
                        unsafe_allow_html=True)
                    ca, cb = st.columns(2)
                    with ca:
                        st.markdown(
                            "<div style='background:#f9fffe;border:1px solid #c8e6c9;"
                            "border-radius:10px;padding:20px'>"
                            "<div style='font-weight:600;color:#0f5132;font-size:15px;"
                            "margin-bottom:12px'>Preparation Method</div>"
                            "<div style='font-size:14px;color:#333;line-height:2'>"
                            "<b>Form:</b> " + str(rx["fd"]["name"]) + "<br>"
                            "<b>Method:</b> " + str(rx["fd"]["prep"]) + "<br>"
                            "<b>Dose:</b> " + str(rx["fd"]["dose"]) + "<br>"
                            "<b>Shelf life:</b> " + str(rx["fd"]["shelf"]) + "<br>"
                            "<b>Anupana:</b> " + str(rx["anupana"]) + "</div></div>",
                            unsafe_allow_html=True)
                    with cb:
                        st.markdown(
                            "<div style='background:#fff8e1;border:1px solid #ffe082;"
                            "border-radius:10px;padding:20px'>"
                            "<div style='font-weight:600;color:#f57c00;font-size:15px;"
                            "margin-bottom:12px'>Why This Combination?</div>"
                            "<div style='font-size:14px;color:#333;line-height:2'>" +
                            str(rx["why"]) + "<br><br>"
                            "<b>Score:</b> " + str(round(rx["score"], 3)) + "<br>"
                            "<b>Doshas:</b> " + dosha_str + "<br>"
                            "<b>Duration:</b> " + str(rx["duration"]) + "<br>"
                            "<b>Timing:</b> " + str(rx["timing"]) + "</div></div>",
                            unsafe_allow_html=True)

                # TAB C — Diet
                with oc:
                    st.markdown("#### Diet and Lifestyle for " + dosha_str + " Imbalance")
                    st.markdown("<br>", unsafe_allow_html=True)
                    di, dj = st.columns(2)
                    with di:
                        items = "".join(
                            "<li style='padding:4px 0'>" + str(item) + "</li>"
                            for item in rx["diet"].get("Favour", []))
                        st.markdown(
                            "<div style='background:#e8f5e9;border-radius:10px;padding:20px'>"
                            "<div style='font-weight:600;color:#0f5132;font-size:15px;"
                            "margin-bottom:12px'>Favour These Foods</div>"
                            "<ul style='color:#333;font-size:14px;line-height:1.8;"
                            "padding-left:20px;margin:0'>" + items + "</ul></div>",
                            unsafe_allow_html=True)
                    with dj:
                        items = "".join(
                            "<li style='padding:4px 0'>" + str(item) + "</li>"
                            for item in rx["diet"].get("Avoid", []))
                        st.markdown(
                            "<div style='background:#ffebee;border-radius:10px;padding:20px'>"
                            "<div style='font-weight:600;color:#c62828;font-size:15px;"
                            "margin-bottom:12px'>Avoid These Foods</div>"
                            "<ul style='color:#333;font-size:14px;line-height:1.8;"
                            "padding-left:20px;margin:0'>" + items + "</ul></div>",
                            unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    dk, dl = st.columns(2)
                    with dk:
                        st.markdown(
                            "<div style='background:#fff3e0;border-radius:10px;padding:20px'>"
                            "<div style='font-weight:600;color:#e65100;font-size:15px;"
                            "margin-bottom:8px'>Meal Timing</div>"
                            "<div style='font-size:14px;color:#333'>" +
                            str(rx["diet"].get("Timing", "")) + "</div></div>",
                            unsafe_allow_html=True)
                    with dl:
                        st.markdown(
                            "<div style='background:#f3e5f5;border-radius:10px;padding:20px'>"
                            "<div style='font-weight:600;color:#6a1b9a;font-size:15px;"
                            "margin-bottom:8px'>Lifestyle Recommendations</div>"
                            "<div style='font-size:14px;color:#333'>" +
                            str(rx["diet"].get("Lifestyle", "")) + "</div></div>",
                            unsafe_allow_html=True)

                # TAB D — Timeline
                with od:
                    st.markdown("#### 4-Week Treatment Plan")
                    tl = build_timeline(rx["doshas"], h1, h2, h3,
                                        rx["dosage"], rx["anupana"])
                    colors = ["#1565c0","#0f5132","#0f5132","#6a1b9a"]
                    for i, wk in enumerate(tl):
                        color = colors[i]
                        st.markdown(
                            "<div class='timeline-week' style='border-left-color:" + color + "'>"
                            "<div style='display:flex;justify-content:space-between;align-items:center'>"
                            "<div>"
                            "<span style='background:" + color + ";color:white;border-radius:4px;"
                            "padding:2px 8px;font-size:11px;font-weight:600'>" + wk["icon"] + "</span>"
                            "<span style='font-weight:700;color:" + color + ";font-size:16px;"
                            "margin-left:8px'>" + wk["week"] + "</span>"
                            "<span style='font-size:13px;color:#666;margin-left:10px'>" +
                            wk["phase"] + "</span>"
                            "</div>"
                            "<div style='font-size:12px;color:#aaa'>" +
                            wk["start"] + " to " + wk["end"] + "</div>"
                            "</div>"
                            "<div style='margin-top:14px;display:flex;gap:16px;flex-wrap:wrap'>"
                            "<div style='flex:1;min-width:180px'>"
                            "<div style='font-size:11px;color:" + color + ";font-weight:600;"
                            "text-transform:uppercase;letter-spacing:1px'>Herb</div>"
                            "<div style='font-size:15px;font-weight:600;color:#0a3d2e;"
                            "margin-top:4px'>" + wk["herbs"] + "</div>"
                            "<div style='font-size:13px;color:#555;margin-top:2px'>" +
                            wk["dose"] + "</div>"
                            "<div style='font-size:12px;color:#888;margin-top:2px'>Anupana: " +
                            wk["anupana"] + "</div>"
                            "</div>"
                            "<div style='flex:1;min-width:180px'>"
                            "<div style='font-size:11px;color:" + color + ";font-weight:600;"
                            "text-transform:uppercase;letter-spacing:1px'>Goal</div>"
                            "<div style='font-size:13px;color:#444;margin-top:4px'>" +
                            wk["goal"] + "</div>"
                            "</div>"
                            "<div style='flex:1;min-width:140px'>"
                            "<div style='font-size:11px;color:#2e7d32;font-weight:600;"
                            "text-transform:uppercase;letter-spacing:1px'>Do</div>"
                            "<div style='font-size:13px;color:#444;margin-top:4px'>" +
                            wk["do"] + "</div>"
                            "<div style='font-size:11px;color:#c62828;font-weight:600;"
                            "text-transform:uppercase;letter-spacing:1px;margin-top:8px'>Avoid</div>"
                            "<div style='font-size:13px;color:#444;margin-top:4px'>" +
                            wk["avoid"] + "</div>"
                            "</div>"
                            "</div></div>",
                            unsafe_allow_html=True)

# PRESCRIPTIONS PAGE
elif page == "Prescriptions":
    st.markdown("## All Prescriptions")
    st.divider()
    con = sqlite3.connect(DB)
    con.text_factory = str
    try:
        all_rx = pd.read_sql(
            "SELECT p.name patient, p.pid, pr.herb1, pr.herb2, pr.herb3, "
            "pr.composite_score score, pr.formulation_form form, pr.dosage, "
            "pr.duration, pr.timing, pr.why_text reason, pr.created_at date "
            "FROM prescriptions pr "
            "JOIN patients p ON p.pid=pr.patient_id "
            "ORDER BY pr.created_at DESC", con)
    except Exception as e:
        st.error(f"Error loading prescriptions: {e}")
        all_rx = pd.DataFrame()
    con.close()
    if all_rx.empty:
        st.info("No prescriptions yet.")
    else:
        srch = st.text_input("Search by patient name")
        if srch:
            all_rx = all_rx[all_rx["patient"].str.contains(srch, case=False)]
        st.markdown("*" + str(len(all_rx)) + " prescriptions*")
        st.dataframe(all_rx, hide_index=True, use_container_width=True)