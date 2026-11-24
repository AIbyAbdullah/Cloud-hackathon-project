-- Q06: Departments where paid > computed by 15%
WITH q05 AS (
    SELECT FORMAT(a.attendance_date,'yyyy-MM') AS month, e.department_id, SUM(a.overtime_hours) AS computed_ot
    FROM warehouse.fact_attendance_daily a
    JOIN warehouse.dim_employee e ON a.employee_id=e.employee_id AND a.attendance_date BETWEEN e.valid_from AND e.valid_to
    GROUP BY FORMAT(a.attendance_date,'yyyy-MM'), e.department_id
),
paid AS (
    SELECT FORMAT(p.pay_month,'yyyy-MM') AS month, e.department_id, SUM(p.amount) AS paid_ot
    FROM warehouse.fact_payroll_line p
    JOIN warehouse.dim_employee e ON p.employee_id=e.employee_id
    WHERE p.pay_component LIKE '%OT%'
    GROUP BY FORMAT(p.pay_month,'yyyy-MM'), e.department_id
)
SELECT 
    p.month, p.department_id, p.paid_ot, q.computed_ot,
    (p.paid_ot - q.computed_ot) / NULLIF(q.computed_ot,0) * 100 AS pct_excess
FROM paid p
JOIN q05 q ON p.month=q.month AND p.department_id=q.department_id
WHERE p.paid_ot > q.computed_ot * 1.15
ORDER BY pct_excess DESC;