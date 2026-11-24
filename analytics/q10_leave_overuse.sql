-- Q10: Employees whose approved Annual leave in 6 months exceeds full-year entitlement
WITH annual_leave AS (
    SELECT employee_id, COUNT(*) AS annual_days_used
    FROM warehouse.fact_leave_day
    WHERE leave_type='Annual'
    GROUP BY employee_id
),
entitlement AS (
    SELECT employee_id, 20 AS full_year_entitlement -- data_dictionary.md me dekho, usually 20 days
    FROM warehouse.dim_employee
    GROUP BY employee_id
)
SELECT 
    a.employee_id,
    a.annual_days_used,
    e.full_year_entitlement,
    a.annual_days_used - e.full_year_entitlement AS excess_days
FROM annual_leave a
JOIN entitlement e ON a.employee_id=e.employee_id
WHERE a.annual_days_used > e.full_year_entitlement
ORDER BY excess_days DESC;