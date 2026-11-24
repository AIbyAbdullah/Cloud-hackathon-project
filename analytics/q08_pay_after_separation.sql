-- Q08: Employees still receiving pay after separation date
SELECT 
    p.employee_id,
    e.valid_to AS separation_date,
    p.pay_month,
    p.amount
FROM warehouse.fact_payroll_line p
JOIN warehouse.dim_employee e ON p.employee_id=e.employee_id
WHERE e.is_current=0 AND p.pay_month > e.valid_to
ORDER BY p.pay_month DESC;