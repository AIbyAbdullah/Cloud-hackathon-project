# 2_staging_clean.py - FIXED VERSION
import pandas as pd, json
from sqlalchemy import create_engine
engine = create_engine("mssql+pyodbc://@./etl_db?driver=ODBC+Driver+18+for+SQL+Server&Trusted_Connection=yes&TrustServerCertificate=yes")

def clean_cols(df):
    for c in df.columns:
        if not c.startswith('_'):
            df[c]=df[c].astype(str).str.strip()
    return df

def find_col(df, keywords):
    for c in df.columns:
        cl=c.lower()
        if all(k in cl for k in keywords):
            return c
    return None

print("=== Stage 2: Cleaning ===")

# employees
df=pd.read_sql("SELECT * FROM raw.employees", engine, dtype=str)
print("employees columns:", list(df.columns))
df=clean_cols(df)
emp_id_col=find_col(df,['emp','id']) or df.columns[0]
print(f"emp_id_col = {emp_id_col}")
df['updated_at']=pd.to_datetime(df['updated_at'], errors='coerce')
df=df.sort_values('updated_at', ascending=False).drop_duplicates(emp_id_col, keep='first')
df=df.rename(columns={emp_id_col:'employee_id'})
df.to_sql('employees', con=engine, schema='staging', if_exists='replace', index=False)
print(f"✓ staging.employees {len(df)}")

# departments
df=pd.read_sql("SELECT * FROM raw.departments", engine, dtype=str)
df=clean_cols(df)
df.to_sql('departments', con=engine, schema='staging', if_exists='replace', index=False)
print(f"✓ staging.departments {len(df)}")

# shifts
df=pd.read_sql("SELECT * FROM raw.shifts", engine, dtype=str)
df.to_sql('shifts', con=engine, schema='staging', if_exists='replace', index=False)
print(f"✓ staging.shifts {len(df)}")

# shift_roster
df=pd.read_sql("SELECT * FROM raw.shift_roster", engine, dtype=str)
df.to_sql('shift_roster', con=engine, schema='staging', if_exists='replace', index=False)
print(f"✓ staging.shift_roster {len(df)}")

# device_mapping
df=pd.read_sql("SELECT * FROM raw.device_mapping", engine, dtype=str)
print("device_mapping columns:", list(df.columns))
df=clean_cols(df)
df.to_sql('device_mapping', con=engine, schema='staging', if_exists='replace', index=False)
print(f"✓ staging.device_mapping {len(df)}")

# biometric_punches
print("Cleaning biometric_punches...")
df=pd.read_sql("SELECT * FROM raw.biometric_punches", engine, dtype=str)
print("biometric columns:", list(df.columns))
df['punch_time']=pd.to_datetime(df['punch_time'] if 'punch_time' in df.columns else df['punch_timestamp'], errors='coerce')
map_df=pd.read_sql("SELECT * FROM staging.device_mapping", engine, dtype=str)
print("map columns:", list(map_df.columns))
# Auto join
user_col=find_col(df,['user','id']) or 'user_id'
map_user=find_col(map_df,['user','id']) or 'device_user_id'
map_emp=find_col(map_df,['emp','id']) or 'employee_id'
print(f"Joining {user_col} -> {map_user} -> {map_emp}")
df=pd.merge(df, map_df[[map_user,map_emp]], left_on=user_col, right_on=map_user, how='left')
# rejected
rej=df[df[map_emp].isna()].copy()
rej['reject_reason']='not mapped'
if len(rej)>0:
    rej.to_sql('rejected_punches', con=engine, schema='staging', if_exists='replace', index=False)
    print(f"  ⚠️ {len(rej)} rejected")
df=df[df[map_emp].notna()].sort_values([map_emp,'punch_time'])
df['prev']=df.groupby(map_emp)['punch_time'].shift(1)
df['diff']=(df['punch_time']-df['prev']).dt.total_seconds()/60
df=df[df['diff'].isna() | (df['diff']>2)]
df=df.drop(columns=['prev','diff',map_user])
df=df.rename(columns={map_emp:'employee_id'})
df.to_sql('biometric_punches', con=engine, schema='staging', if_exists='replace', index=False)
print(f"✓ staging.biometric_punches {len(df)}")

# holidays
df=pd.read_sql("SELECT * FROM raw.holidays", engine, dtype=str)
df.to_sql('holidays', con=engine, schema='staging', if_exists='replace', index=False)
print(f"✓ staging.holidays {len(df)}")

# 2_staging_clean.py ke neeche wale hisse me ye line change karo:
try:
    # Try both paths
    path = None
    for p in ['data-hackathon/leave_requests.json', 'data/raw/data-hackathon/leave_requests.json', 'data_hackathon/leave_requests.json']:
        import os
        if os.path.exists(p):
            path = p
            break
    with open(path,'r') as f:
        data=json.load(f)
    flat=[]
    for r in data:
        req_id=r.get('request_id')
        emp_id=r.get('employee_id') or r.get('emp_id')
        l_type=r.get('leave_type')
        from_d=r.get('from_date')
        to_d=r.get('to_date')
        for a in r.get('approvals',[]) or [{}]:
            flat.append({
                "request_id":req_id,
                "employee_id":emp_id,
                "leave_type":l_type,
                "from_date":from_d,
                "to_date":to_d,
                "approval_level":a.get('level'),
                "approver":a.get('approver_id'),
                "approval_status":a.get('status', r.get('status'))
            })
    pd.DataFrame(flat).to_sql('leave_requests_flat', con=engine, schema='staging', if_exists='replace', index=False)
    print(f"✓ staging.leave_requests_flat {len(flat)}")

    # Expand per day - approved only + both approvals
    expanded=[]
    for r in data:
        # PDF Rule: Leave counts only if both Manager + HR say Approved and never cancelled
        approvals = r.get('approvals',[])
        statuses = [a.get('status') for a in approvals]
        if statuses.count('Approved') >= 2 and r.get('status')!='Cancelled':
            try:
                start=pd.to_datetime(r['from_date'])
                end=pd.to_datetime(r['to_date'])
                for d in pd.date_range(start,end):
                    # Skip Sundays? PDF says leave spanning Sundays and holidays is messy - count only working days later
                    expanded.append({
                        "employee_id":r.get('employee_id') or r.get('emp_id'),
                        "leave_date":d.date(),
                        "leave_type":r.get('leave_type'),
                        "request_id":r.get('request_id')
                    })
            except: pass
    if expanded:
        pd.DataFrame(expanded).to_sql('leave_days', con=engine, schema='staging', if_exists='replace', index=False)
        print(f"✓ staging.leave_days {len(expanded)}")

except Exception as e:
    print(f"leave error {e}")

# overtime
df=pd.read_sql("SELECT * FROM raw.overtime_requests", engine, dtype=str)
df.to_sql('overtime_requests', con=engine, schema='staging', if_exists='replace', index=False)
print(f"✓ staging.overtime_requests {len(df)}")

# payroll
df=pd.read_sql("SELECT * FROM raw.payroll_lines", engine, dtype=str)
df.to_sql('payroll_lines', con=engine, schema='staging', if_exists='replace', index=False)
print(f"✓ staging.payroll_lines {len(df)}")

# applications
df=pd.read_sql("SELECT * FROM raw.applications", engine, dtype=str)
df.to_sql('applications', con=engine, schema='staging', if_exists='replace', index=False)
print(f"✓ staging.applications {len(df)}")

print("🎉 Stage 2 DONE!")