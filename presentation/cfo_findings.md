# CFO Findings - Top 3

1. **July OT Peak 42% Up**: 63471 hrs in July vs 44655 in May
   Evidence: analytics/results/q05_overtime_compare.csv
   Action: Audit night shifts, limit OT to 8hrs/day

2. **Headcount Decline + Ghost Payments**: 1213->1197 but 5 employees paid with zero attendance, 20 paid after separation
   Evidence: q01_headcount.csv, q07_zero_attendance_paid.csv (5 rows), q08_pay_after_separation.csv (20 rows)
   Action: Stop payroll for separated employees, link payroll to attendance

3. **Late Arrival Culture**: Top 10 employees 140+ days late (E10670 143 days)
   Evidence: q04_late_arrivals.csv
   Action: Enforce grace 10 min rule (PDF Rule: Late >10 min)

## ER Diagram: warehouse schema star - dim_employee SCD2 -> fact_attendance_daily