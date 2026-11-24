-- Q01: Month-end headcount by plant & department
SELECT 
    EOMONTH(a.attendance_date) AS month_end,
    d.plant,
    d.department_name,
    COUNT(DISTINCT a.employee_id) AS headcount
FROM warehouse.fact_attendance_daily a
JOIN warehouse.dim_employee e ON a.employee_id = e.employee_id 
    AND a.attendance_date BETWEEN e.valid_from AND e.valid_to
JOIN warehouse.dim_department d ON e.department_id = d.department_id
GROUP BY EOMONTH(a.attendance_date), d.plant, d.department_name
ORDER BY month_end, d.plant, d.department_name;