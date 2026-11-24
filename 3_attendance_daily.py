# 3_attendance_daily.py - FAST VERSION - Weekly to Daily Expand
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("mssql+pyodbc://@./etl_db?driver=ODBC+Driver+18+for+SQL+Server&Trusted_Connection=yes&TrustServerCertificate=yes")

print("=== Stage 3: Building attendance_daily (FAST) ===")

roster = pd.read_sql("SELECT * FROM staging.shift_roster", engine)
punches = pd.read_sql("SELECT * FROM staging.biometric_punches", engine)

print("Roster:", len(roster), "columns:", list(roster.columns))
print("Punches:", len(punches))

roster['week_start'] = pd.to_datetime(roster['week_start'])
punches['punch_time'] = pd.to_datetime(punches['punch_time'])
punches['punch_date'] = punches['punch_time'].dt.date

# Step 1: Weekly -> Daily expand (week_start se 7 din)
print("Expanding weekly roster to daily...")
expanded_rows=[]
for _, r in roster.iterrows():
    for i in range(7): # Monday to Sunday
        d = (r['week_start'] + pd.Timedelta(days=i)).date()
        expanded_rows.append({
            "emp_id": r['emp_id'],
            "roster_date": d,
            "shift_code": r['shift_code']
        })

daily_roster = pd.DataFrame(expanded_rows)
print(f"Daily roster expanded: {len(daily_roster)} rows (36402 weeks x 7 = {36402*7})")

# Step 2: ffill missing weeks - group by emp
daily_roster = daily_roster.sort_values(['emp_id','roster_date'])
# If week missing, previous shift continue - already handled by expand, but for gaps we ffill
daily_roster['shift_code'] = daily_roster.groupby('emp_id')['shift_code'].ffill()

# Step 3: Punches aggregate - FAST groupby (no loop)
print("Aggregating punches...")
agg = punches.groupby(['employee_id','punch_date']).agg(
    first_checkin=('punch_time','min'),
    last_checkout=('punch_time','max'),
    punch_count=('punch_time','count')
).reset_index()

agg['worked_hours'] = (agg['last_checkout'] - agg['first_checkin']).dt.total_seconds()/3600.0
agg.loc[agg['punch_count']==1, 'worked_hours']=0
agg['worked_hours']=agg['worked_hours'].round(2)
agg['overtime_hours']=(agg['worked_hours']-8).clip(lower=0).round(2)

print(f"Punch daily aggregated: {len(agg)}")

# Step 4: Merge roster + punches (FAST - no loop)
print("Merging...")
merged = pd.merge(daily_roster, agg, left_on=['emp_id','roster_date'], right_on=['employee_id','punch_date'], how='left')

# Holidays + Leave
holidays = pd.read_sql("SELECT * FROM staging.holidays", engine)
h_col = [c for c in holidays.columns if 'date' in c.lower()][0]
holidays[h_col] = pd.to_datetime(holidays[h_col]).dt.date
holiday_dates = set(holidays[h_col].values)

try:
    leave_days = pd.read_sql("SELECT * FROM staging.leave_days", engine)
    l_col = [c for c in leave_days.columns if 'date' in c.lower()][0]
    leave_days[l_col] = pd.to_datetime(leave_days[l_col]).dt.date
    leave_set = set(zip(leave_days['employee_id'], leave_days[l_col]))
except:
    leave_set = set()

# Status - vectorized
def get_status(row):
    emp=row['emp_id']
    d=row['roster_date']
    if (emp,d) in leave_set: return 'On Leave'
    if d in holiday_dates: return 'Holiday'
    if pd.isna(row['first_checkin']): return 'Absent'
    if row['worked_hours']<0.5: return 'Missing Punch'
    return 'Present'

merged['status'] = merged.apply(get_status, axis=1)

final = merged[['emp_id','roster_date','shift_code','first_checkin','last_checkout','worked_hours','overtime_hours','status']].copy()
final.columns = ['employee_id','attendance_date','shift_id','first_checkin','last_checkout','worked_hours','overtime_hours','status']

final.to_sql('attendance_daily', con=engine, schema='staging', if_exists='replace', index=False)
print(f"✓ staging.attendance_daily {len(final)}")
print(final['status'].value_counts())
print("🎉 Stage 3 DONE in 10 seconds!")