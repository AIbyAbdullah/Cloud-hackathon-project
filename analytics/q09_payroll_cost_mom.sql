-- Q09: Payroll cost per employee by department, with MoM change
WITH monthly_cost AS (
    SELECT 
        FORMAT(p.pay_month,'yyyy-MM') AS month,
        e.department_id,
        d.department_name,
        SUM(p.amount) AS total_cost,
        COUNT(DISTINCT p.employee_id) AS emp_count,
        SUM(p.amount)/NULLIF(COUNT(DISTINCT p.employee_id),0) AS cost_per_emp
    FROM warehouse.fact_payroll_line p
    JOIN warehouse.dim_employee e ON p.employee_id=e.employee_id
    JOIN warehouse.dim_department d ON e.department_id=d.department_id
    GROUP BY FORMAT(p.pay_month,'yyyy-MM'), e.department_id, d.department_name
)
SELECT 
    month, department_id, department_name, total_cost, emp_count, cost_per_emp,
    cost_per_emp - LAG(cost_per_emp) OVER (PARTITION BY department_id ORDER BY month) AS mom_change,
    (cost_per_emp - LAG(cost_per_emp) OVER (PARTITION BY department_id ORDER BY month)) / NULLIF(LAG(cost_per_emp) OVER (PARTITION BY department_id ORDER BY month),0) * 100 AS mom_pct_change
FROM monthly_cost
ORDER BY department_id, month;