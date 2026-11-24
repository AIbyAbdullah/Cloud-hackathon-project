-- Q02: Monthly attrition rate (separations ÷ avg headcount)
WITH separations AS (
    SELECT FORMAT(e.valid_to,'yyyy-MM') AS month, e.department_id, COUNT(*) AS sep_count
    FROM warehouse.dim_employee e
    WHERE e.is_current = 0
    GROUP BY FORMAT(e.valid_to,'yyyy-MM'), e.department_id
),
avg_headcount AS (
    SELECT FORMAT(attendance_date,'yyyy-MM') AS month, e.department_id, COUNT(DISTINCT a.employee_id) AS avg_hc
    FROM warehouse.fact_attendance_daily a
    JOIN warehouse.dim_employee e ON a.employee_id=e.employee_id AND a.attendance_date BETWEEN e.valid_from AND e.valid_to
    GROUP BY FORMAT(attendance_date,'yyyy-MM'), e.department_id
)
SELECT s.month, s.department_id, s.sep_count, h.avg_hc,
       CAST(s.sep_count * 1.0 / NULLIF(h.avg_hc,0) * 100 AS DECIMAL(5,2)) AS attrition_rate_pct
FROM separations s
JOIN avg_headcount h ON s.month=h.month AND s.department_id=h.department_id
ORDER BY s.month;