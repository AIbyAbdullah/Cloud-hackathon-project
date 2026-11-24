-- Q04: 10 employees with most late arrivals
SELECT TOP 10
    a.employee_id,
    e.department_id,
    d.department_name,
    COUNT(*) AS late_count,
    SUM(a.late_minutes) AS total_late_minutes
FROM warehouse.fact_attendance_daily a
JOIN warehouse.dim_employee e ON a.employee_id=e.employee_id AND a.attendance_date BETWEEN e.valid_from AND e.valid_to
JOIN warehouse.dim_department d ON e.department_id=d.department_id
WHERE a.status='Present' AND a.late_minutes > 10 -- PDF Rule: >10 min late
GROUP BY a.employee_id, e.department_id, d.department_name
ORDER BY late_count DESC;