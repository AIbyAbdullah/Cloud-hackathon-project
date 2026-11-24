# 4_payroll_fix.py - Auto detect payroll
from sqlalchemy import create_engine, text
import pandas as pd

engine = create_engine("mssql+pyodbc://@./etl_db?driver=ODBC+Driver+18+for+SQL+Server&Trusted_Connection=yes&TrustServerCertificate=yes")

print("=== Payroll Fix ===")

with engine.connect() as conn:
    # Get real columns
    df = pd.read_sql("SELECT TOP 5 * FROM staging.payroll_lines", conn)
    print("Payroll columns:", list(df.columns))
    print(df.head(2).to_string())

with engine.connect() as conn:
    # Try all possible names
    # Common names: payroll_month, month, pay_period, component, pay_component, amount, total
    conn.execute(text("""
        INSERT INTO warehouse.fact_payroll_line (employee_id, pay_month, pay_component, amount)
        SELECT 
            CAST(emp_id AS VARCHAR(20)),
            TRY_CAST(payroll_month AS DATE),
            CAST(component AS VARCHAR(50)),
            TRY_CAST(amount AS DECIMAL(10,2))
        FROM staging.payroll_lines
        WHERE TRY_CAST(amount AS DECIMAL(10,2)) IS NOT NULL
    """))
    conn.commit()
    print("✓ fact_payroll_line - Attempt 1")

# If fails, try alternative
try:
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO warehouse.fact_payroll_line (employee_id, pay_month, pay_component, amount)
            SELECT 
                CAST(emp_id AS VARCHAR(20)),
                TRY_CAST(month AS DATE),
                CAST(pay_component AS VARCHAR(50)),
                TRY_CAST(amount AS DECIMAL(10,2))
            FROM staging.payroll_lines
            WHERE TRY_CAST(amount AS DECIMAL(10,2)) IS NOT NULL
        """))
        conn.commit()
        print("✓ fact_payroll_line - Attempt 2")
except Exception as e:
    print(f"Attempt 2 failed: {e}")
    # Last try - generic
    with engine.connect() as conn:
        df = pd.read_sql("SELECT * FROM staging.payroll_lines", conn)
        # Find columns
        emp_col = [c for c in df.columns if 'emp' in c.lower()][0]
        month_col = [c for c in df.columns if 'month' in c.lower() or 'period' in c.lower()][0]
        comp_col = [c for c in df.columns if 'component' in c.lower() or 'comp' in c.lower()][0] if any('component' in c.lower() for c in df.columns) else df.columns[2]
        amt_col = [c for c in df.columns if 'amount' in c.lower() or 'amt' in c.lower()][0]
        
        print(f"Using: {emp_col}, {month_col}, {comp_col}, {amt_col}")
        
        df_final = pd.DataFrame()
        df_final['employee_id'] = df[emp_col].astype(str)
        df_final['pay_month'] = pd.to_datetime(df[month_col]).dt.date
        df_final['pay_component'] = df[comp_col].astype(str)
        df_final['amount'] = pd.to_numeric(df[amt_col], errors='coerce').fillna(0)
        
        df_final.to_sql('fact_payroll_line', con=engine, schema='warehouse', if_exists='append', index=False, chunksize=5000)
        print(f"✓ fact_payroll_line {len(df_final)} via pandas")

with engine.connect() as conn:
    for t in ['fact_attendance_daily','fact_overtime_approved','fact_payroll_line']:
        cnt = conn.execute(text(f"SELECT COUNT(*) FROM warehouse.{t}")).scalar()
        print(f"warehouse.{t} -> {cnt}")

print("🎉 Stage 4 DONE!")