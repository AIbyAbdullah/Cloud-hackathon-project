# 1_raw_load.py
import os, json, hashlib
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

DATA_FOLDER = "data/raw/data-hackathon"  # Tumhara real data path
engine = create_engine("mssql+pyodbc://@./etl_db?driver=ODBC+Driver+18+for+SQL+Server&Trusted_Connection=yes&TrustServerCertificate=yes")

with engine.connect() as conn:
    for s in ['raw','staging','warehouse']:
        conn.execute(text(f"IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = '{s}') EXEC('CREATE SCHEMA {s}')"))
    conn.commit()
print("✓ Schemas raw,staging,warehouse ready!")

def add_audit(df, file):
    df['_source_file']=file
    df['_loaded_at']=datetime.now()
    df['_row_hash']=df.apply(lambda r: hashlib.md5(str(r.values).encode()).hexdigest(), axis=1)
    return df

files = ["employees.csv","employment_history.csv","departments.csv","shifts.json","shift_roster.csv","device_mapping.csv","biometric_punches.csv","holidays.csv","leave_requests.json","overtime_requests.csv","payroll_lines.csv","applications.csv"]

for f in files:
    p=os.path.join(DATA_FOLDER,f)
    if not os.path.exists(p): print(f"Missing {f}"); continue
    table=f.split('.')[0]
    if f.endswith('.csv'):
        df=pd.read_csv(p, dtype=str, keep_default_na=False)
    else:
        df=pd.DataFrame(json.load(open(p, encoding='utf-8')))
        for c in df.columns:
            if df[c].apply(lambda x: isinstance(x,(list,dict))).any():
                df[c]=df[c].astype(str)
    df=add_audit(df,f)
    df.to_sql(table, con=engine, schema='raw', if_exists='replace', index=False)
    print(f"✓ raw.{table} -> {len(df)} rows")

print("🎉 Stage 1 DONE!")