-- Q07: Employees paid in a month with zero attendance
SELECT DISTINCT
    p.employee_id,
    FORMAT(p.pay_month,'yyyy-MM') AS pay_month
FROM warehouse.fact_payroll_line p
WHERE NOT EXISTS (
    SELECT 1 FROM warehouse.fact_attendance_daily a 
    WHERE a.employee_id=p.employee_id 
    AND FORMAT(a.attendance_date,'yyyy-MM')=FORMAT(p.pay_month,'yyyy-MM')
)
ORDER BY pay_month, p.employee_id;  