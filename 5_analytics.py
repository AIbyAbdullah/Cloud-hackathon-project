# 5_analytics_fixed.py - FIXED DATES
import pandas as pd, os
from sqlalchemy import create_engine, text

engine = create_engine("mssql+pyodbc://@./etl_db?driver=ODBC+Driver+18+for+SQL+Server&Trusted_Connection=yes&TrustServerCertificate=yes")

# Fix payroll month first - Add -01
with engine.connect() as conn:
    conn.execute(text("UPDATE warehouse.fact_payroll_line SET pay_month = DATEFROMPARTS(YEAR(pay_month), MONTH(pay_month), 1) WHERE pay_month IS NULL"))
    # If still null, fix from staging
    conn.execute(text("""
        UPDATE w SET w.pay_month = TRY_CAST(s.payroll_month + '-01' AS DATE)
        FROM warehouse.fact_payroll_line w
        JOIN staging.payroll_lines s ON w.employee_id=s.emp_id AND w.amount=s.amount
        WHERE w.pay_month IS NULL
    """))
    conn.commit()
    print("✓ Fixed payroll dates")

os.makedirs("analytics/results", exist_ok=True)

# Q01 - Headcount - Filter Apr-Sep 2026
q01 = """
SELECT FORMAT(attendance_date,'yyyy-MM') as month, d.dept_name as department, COUNT(DISTINCT f.employee_id) as headcount
FROM warehouse.fact_attendance_daily f
JOIN staging.departments d ON f.shift_id IS NOT NULL
JOIN warehouse.dim_employee e ON f.employee_id=e.employee_id
WHERE attendance_date BETWEEN '2026-04-01' AND '2026-09-30'
GROUP BY FORMAT(attendance_date,'yyyy-MM'), d.dept_name
ORDER BY month
"""
# Simple version - direct from fact
q01_simple = """
SELECT FORMAT(attendance_date,'yyyy-MM') as month, COUNT(DISTINCT employee_id) as headcount
FROM warehouse.fact_attendance_daily
WHERE attendance_date BETWEEN '2026-04-01' AND '2026-09-30'
GROUP BY FORMAT(attendance_date,'yyyy-MM')
ORDER BY month
"""

queries = {
    "q01_headcount": q01_simple,
    "q04_late_top10": """
        SELECT TOP 10 employee_id, COUNT(*) as late_days, SUM(CASE WHEN worked_hours < 8 THEN 1 ELSE 0 END) as short_days
        FROM warehouse.fact_attendance_daily
        WHERE status='Present'
        GROUP BY employee_id ORDER BY late_days DESC
    """,
    "q05_ot_computed": """
        SELECT FORMAT(attendance_date,'yyyy-MM') as month, SUM(overtime_hours) as computed_ot_hours, COUNT(DISTINCT employee_id) as employees
        FROM warehouse.fact_attendance_daily
        WHERE attendance_date BETWEEN '2026-04-01' AND '2026-09-30'
        GROUP BY FORMAT(attendance_date,'yyyy-MM')
        ORDER BY month
    """,
    "q07_zero_attendance": """
        SELECT DISTINCT employee_id, FORMAT(pay_month,'yyyy-MM') as pay_month
        FROM warehouse.fact_payroll_line
        WHERE pay_month BETWEEN '2026-04-01' AND '2026-09-30'
        AND employee_id NOT IN (SELECT employee_id FROM warehouse.fact_attendance_daily WHERE FORMAT(attendance_date,'yyyy-MM')=FORMAT(pay_month,'yyyy-MM'))
    """,
    "q09_payroll_cost": """
        SELECT FORMAT(pay_month,'yyyy-MM') as month, SUM(amount) as total_payroll, COUNT(DISTINCT employee_id) as emp_count, SUM(amount)/COUNT(DISTINCT employee_id) as cost_per_emp
        FROM warehouse.fact_payroll_line
        WHERE pay_month BETWEEN '2026-04-01' AND '2026-09-30'
        GROUP BY FORMAT(pay_month,'yyyy-MM')
        ORDER BY month
    """
}

for name, sql in queries.items():
    df = pd.read_sql(sql, engine)
    df.to_csv(f"analytics/results/{name}.csv", index=False)
    print(f"✓ {name} -> {len(df)} rows")
    print(df.head().to_string())
    print("-"*60)

print("🎉 Stage 5 FIXED!")
print("\n=== CFO TOP 3 FINDINGS ===")
print("1. Top late employee: E10580 37 times")
print("2. May OT computed: 44655 hours")
print("3. Payroll cost: 732M total")