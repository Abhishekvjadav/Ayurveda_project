import sqlite3

con = sqlite3.connect('clinic.db')

cols = [
    ('composite_score', 'REAL DEFAULT 0'),
    ('gnn_score',       'REAL DEFAULT 0'),
    ('dosha_score',     'REAL DEFAULT 0'),
    ('virya_score',     'REAL DEFAULT 0'),
    ('prabhav_score',   'REAL DEFAULT 0'),
    ('why_text',        'TEXT'),
]

for col, dtype in cols:
    try:
        con.execute(f'ALTER TABLE prescriptions ADD COLUMN {col} {dtype}')
        print(f'Added: {col}')
    except Exception as e:
        print(f'Skip {col}: {e}')

con.commit()
con.close()
print('Done!')
```

Then in PowerShell run:
```
python fix_db.py
streamlit run dravyaguna_pro.py