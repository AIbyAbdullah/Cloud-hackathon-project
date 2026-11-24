-- Q03: Absenteeism rate (Absent ÷ Total Working Days, excluding leave)
SELECT 
    FORMAT(a.attendance_date,'yyyy-MM') AS month,
    d.plant,
    SUM(CASE WHEN a.status='Absent' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS absenteeism_rate_pct,
    SUM(CASE WHEN a.status='Absent' THEN 1 ELSE 0 END) AS absent_days,
    COUNT(*) AS total_days
FROM warehouse.fact_attendance_daily a
JOIN warehouse.dim_employee e ON a.employee_id=e.employee_id AND a.attendance_date BETWEEN e.valid_from AND e.valid_to
JOIN warehouse.dim_department d ON e.department_id=d.department_id
LEFT JOIN warehouse.fact_leave_day l ON a.employee_id=l.employee_id AND a.attendance_date=l.leave_date
WHERE l.employee_id IS NULL -- exclude approved leave
GROUP BY FORMAT(a.attendance_date,'yyyy-MM'), d.plant
ORDER BY month, plant;