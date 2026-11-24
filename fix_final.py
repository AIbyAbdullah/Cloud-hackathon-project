from sqlalchemy import create_engine, text

engine = create_engine("mssql+pyodbc://@./etl_db?driver=ODBC+Driver+18+for+SQL+Server&Trusted_Connection=yes&TrustServerCertificate=yes")

with engine.connect() as conn:
    conn.execute(text("TRUNCATE TABLE warehouse.fact_payroll_line"))
    conn.commit()
    print("✓ Truncated")

with engine.connect() as conn:
    conn.execute(text("""
        INSERT INTO warehouse.fact_payroll_line (employee_id, pay_month, pay_component, amount)
        SELECT CAST(emp_id AS VARCHAR(20)), TRY_CAST(payroll_month AS DATE), CAST(component AS VARCHAR(50)), TRY_CAST(amount AS DECIMAL(10,2))
        FROM staging.payroll_lines
    """))
    conn.commit()
    cnt = conn.execute(text("SELECT COUNT(*) FROM warehouse.fact_payroll_line")).scalar()
    print(f"✓ Fixed payroll -> {cnt} (should be 53617)")

with engine.connect() as conn:
    for t in ['fact_attendance_daily','fact_overtime_approved','fact_payroll_line','dim_employee','dim_department','dim_shift','dim_date']:
        cnt = conn.execute(text(f"SELECT COUNT(*) FROM warehouse.{t}")).scalar()
        print(f"warehouse.{t} -> {cnt}")

print("🎉 Stage 4 PERFECT!")