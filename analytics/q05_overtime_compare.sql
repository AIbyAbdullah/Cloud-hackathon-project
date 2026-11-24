-- Q05: Overtime computed vs approved vs paid
WITH computed AS (
    SELECT FORMAT(attendance_date,'yyyy-MM') AS month, e.department_id, SUM(overtime_hours) AS computed_ot
    FROM warehouse.fact_attendance_daily a
    JOIN warehouse.dim_employee e ON a.employee_id=e.employee_id AND a.attendance_date BETWEEN e.valid_from AND e.valid_to
    GROUP BY FORMAT(attendance_date,'yyyy-MM'), e.department_id
),
approved AS (
    SELECT FORMAT(ot_date,'yyyy-MM') AS month, e.department_id, SUM(approved_hours) AS approved_ot
    FROM warehouse.fact_overtime_approved o
    JOIN warehouse.dim_employee e ON o.employee_id=e.employee_id AND o.ot_date BETWEEN e.valid_from AND e.valid_to
    GROUP BY FORMAT(ot_date,'yyyy-MM'), e.department_id
),
paid AS (
    SELECT FORMAT(pay_month,'yyyy-MM') AS month, e.department_id, SUM(amount) AS paid_ot_amount
    FROM warehouse.fact_payroll_line p
    JOIN warehouse.dim_employee e ON p.employee_id=e.employee_id
    WHERE pay_component LIKE '%OT%' OR pay_component LIKE '%Overtime%'
    GROUP BY FORMAT(pay_month,'yyyy-MM'), e.department_id
)
SELECT 
    COALESCE(c.month, ap.month, pa.month) AS month,
    COALESCE(c.department_id, ap.department_id, pa.department_id) AS department_id,
    ISNULL(c.computed_ot,0) AS computed_ot,
    ISNULL(ap.approved_ot,0) AS approved_ot,
    ISNULL(pa.paid_ot_amount,0) AS paid_ot_amount
FROM computed c
FULL OUTER JOIN approved ap ON c.month=ap.month AND c.department_id=ap.department_id
FULL OUTER JOIN paid pa ON COALESCE(c.month,ap.month)=pa.month AND COALESCE(c.department_id,ap.department_id)=pa.department_id
ORDER BY month, department_id;