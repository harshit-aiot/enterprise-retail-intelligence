-- =============================================================================
-- 08_business_questions.sql
-- Enterprise Retail Intelligence & Decision Engine
-- Phase 7: SQL Analytics — Business Questions (Final Set)
--
-- Direct answers to the 35 business questions from the master prompt.
-- Each query is labelled with its business question number.
-- =============================================================================

USE enterprise_bi;

-- BQ1: How many unique customers/users exist?
SELECT COUNT(DISTINCT user_id) AS unique_customers FROM stg_orders;

-- BQ2: How frequently do customers order? (avg days between orders)
SELECT
    ROUND(AVG(days_since_prior_order), 1) AS avg_days_between_orders,
    MIN(days_since_prior_order)           AS min_days,
    MAX(days_since_prior_order)           AS max_days
FROM stg_orders
WHERE days_since_prior_order IS NOT NULL;

-- BQ3: What is the average number of products per order?
SELECT
    ROUND(AVG(items_per_order), 2) AS avg_products_per_order
FROM (
    SELECT order_id, COUNT(*) AS items_per_order
    FROM stg_order_products_prior
    GROUP BY order_id
) t;

-- BQ4: Which customers demonstrate high purchase frequency?
SELECT
    user_id,
    total_orders,
    ROUND(avg_days, 1) AS avg_days_between_orders,
    'High Frequency' AS label
FROM (
    SELECT user_id, COUNT(*) AS total_orders,
           AVG(days_since_prior_order) AS avg_days
    FROM stg_orders
    GROUP BY user_id
) t
WHERE total_orders >= 20 AND avg_days <= 10
ORDER BY total_orders DESC, avg_days
LIMIT 30;

-- BQ5: What percentage of products are reordered? (overall reorder rate)
SELECT
    ROUND(AVG(reordered) * 100, 2) AS overall_reorder_rate_pct
FROM stg_order_products_prior;

-- BQ6: Which customers have the highest reorder behavior?
SELECT
    o.user_id,
    COUNT(*) AS total_items,
    ROUND(AVG(op.reordered) * 100, 2) AS reorder_rate_pct,
    COUNT(DISTINCT o.order_id) AS total_orders
FROM stg_orders o
JOIN stg_order_products_prior op ON o.order_id = op.order_id
GROUP BY o.user_id
HAVING COUNT(*) >= 50
ORDER BY reorder_rate_pct DESC
LIMIT 25;

-- BQ7: Distribution of order frequency
SELECT
    order_count_bucket,
    COUNT(*) AS customers,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct
FROM (
    SELECT user_id,
           CASE
               WHEN COUNT(*) = 1          THEN '1 order'
               WHEN COUNT(*) BETWEEN 2 AND 5  THEN '2–5 orders'
               WHEN COUNT(*) BETWEEN 6 AND 15 THEN '6–15 orders'
               WHEN COUNT(*) BETWEEN 16 AND 30 THEN '16–30 orders'
               ELSE '31+ orders'
           END AS order_count_bucket
    FROM stg_orders GROUP BY user_id
) t
GROUP BY order_count_bucket
ORDER BY MIN(CASE order_count_bucket
    WHEN '1 order' THEN 1 WHEN '2–5 orders' THEN 2
    WHEN '6–15 orders' THEN 3 WHEN '16–30 orders' THEN 4 ELSE 5 END);

-- BQ9: Most frequently purchased products (Top 10)
SELECT
    p.product_name, d.department, COUNT(*) AS purchases
FROM stg_order_products_prior op
JOIN stg_products p    ON op.product_id = p.product_id
JOIN stg_departments d ON p.department_id = d.department_id
GROUP BY p.product_name, d.department
ORDER BY purchases DESC LIMIT 10;

-- BQ10: Most reordered products (min 200 purchases)
SELECT
    p.product_name, d.department,
    COUNT(*)                          AS purchases,
    ROUND(AVG(op.reordered)*100, 2)   AS reorder_rate_pct
FROM stg_order_products_prior op
JOIN stg_products p    ON op.product_id = p.product_id
JOIN stg_departments d ON p.department_id = d.department_id
GROUP BY p.product_name, d.department
HAVING COUNT(*) >= 200
ORDER BY reorder_rate_pct DESC LIMIT 15;

-- BQ13: Likely staple products (high volume + high reorder)
SELECT
    p.product_name, d.department, a.aisle,
    COUNT(*) AS purchases,
    ROUND(AVG(op.reordered)*100,1) AS reorder_rate_pct
FROM stg_order_products_prior op
JOIN stg_products p    ON op.product_id = p.product_id
JOIN stg_aisles a      ON p.aisle_id = a.aisle_id
JOIN stg_departments d ON p.department_id = d.department_id
GROUP BY p.product_name, d.department, a.aisle
HAVING COUNT(*) >= 1000 AND AVG(op.reordered) >= 0.65
ORDER BY purchases DESC LIMIT 15;

-- BQ15: Departments with highest order volume
SELECT
    d.department,
    COUNT(*) AS items_purchased,
    ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER (),2) AS pct_share
FROM stg_order_products_prior op
JOIN stg_products p    ON op.product_id = p.product_id
JOIN stg_departments d ON p.department_id = d.department_id
GROUP BY d.department ORDER BY items_purchased DESC;

-- BQ19: Which days have highest order volume?
SELECT
    CASE order_dow
        WHEN 0 THEN 'Saturday' WHEN 1 THEN 'Sunday'
        WHEN 2 THEN 'Monday'   WHEN 3 THEN 'Tuesday'
        WHEN 4 THEN 'Wednesday' WHEN 5 THEN 'Thursday'
        WHEN 6 THEN 'Friday'
    END AS day,
    COUNT(*) AS orders
FROM stg_orders GROUP BY order_dow ORDER BY orders DESC;

-- BQ20: Which hours have highest order volume?
SELECT order_hour_of_day, COUNT(*) AS orders
FROM stg_orders
GROUP BY order_hour_of_day ORDER BY orders DESC LIMIT 5;

-- BQ25: How does reorder behavior change with order sequence?
SELECT
    CASE
        WHEN o.order_number = 1       THEN 'Order 1'
        WHEN o.order_number <= 5      THEN 'Orders 2-5'
        WHEN o.order_number <= 10     THEN 'Orders 6-10'
        WHEN o.order_number <= 20     THEN 'Orders 11-20'
        ELSE 'Orders 21+'
    END AS order_stage,
    COUNT(*) AS items,
    ROUND(AVG(op.reordered)*100, 2) AS reorder_rate_pct
FROM stg_orders o
JOIN stg_order_products_prior op ON o.order_id = op.order_id
GROUP BY order_stage ORDER BY order_stage;

-- BQ28: Average days between orders
SELECT
    ROUND(AVG(days_since_prior_order), 1) AS avg_days,
    ROUND(STDDEV(days_since_prior_order), 1) AS stddev_days
FROM stg_orders WHERE days_since_prior_order IS NOT NULL;

-- BQ33: Busiest operating periods
SELECT
    CASE order_dow
        WHEN 0 THEN 'Saturday' WHEN 1 THEN 'Sunday'
        WHEN 2 THEN 'Monday'   WHEN 3 THEN 'Tuesday'
        WHEN 4 THEN 'Wednesday' WHEN 5 THEN 'Thursday'
        WHEN 6 THEN 'Friday'
    END AS day,
    order_hour_of_day AS hour,
    COUNT(*) AS orders
FROM stg_orders
GROUP BY order_dow, order_hour_of_day
ORDER BY orders DESC LIMIT 5;

-- BQ34: Departments with unusual reorder behavior vs overall average
WITH dept_reorder AS (
    SELECT d.department, AVG(op.reordered) AS dept_rate, COUNT(*) AS vol
    FROM stg_order_products_prior op
    JOIN stg_products p    ON op.product_id = p.product_id
    JOIN stg_departments d ON p.department_id = d.department_id
    GROUP BY d.department
),
overall AS (SELECT AVG(reordered) AS overall_rate FROM stg_order_products_prior)
SELECT
    department,
    ROUND(dept_rate * 100, 2)     AS dept_reorder_pct,
    ROUND(overall_rate * 100, 2)  AS overall_reorder_pct,
    ROUND(ABS(dept_rate - overall_rate) * 100, 2) AS abs_deviation_pct,
    CASE WHEN dept_rate > overall_rate THEN 'Above Average' ELSE 'Below Average' END AS direction
FROM dept_reorder CROSS JOIN overall
WHERE ABS(dept_rate - overall_rate) > 0.05
ORDER BY abs_deviation_pct DESC;

