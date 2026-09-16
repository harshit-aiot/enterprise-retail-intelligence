-- =============================================================================
-- 05_business_queries.sql
-- Enterprise Retail Intelligence & Decision Engine
-- Phase 7: SQL Analytics — Business Queries
--
-- Covers: customer analytics, product analytics, department analytics,
--         time analytics, reorder analysis, basic reporting.
-- =============================================================================

USE enterprise_bi;

-- ═══════════════════════════════════════════════════════════════════════════════
-- SECTION 1: CUSTOMER ANALYTICS
-- ═══════════════════════════════════════════════════════════════════════════════

-- Q1: How many unique customers exist?
SELECT
    COUNT(DISTINCT user_id)  AS unique_customers
FROM stg_orders;

-- Q2: Distribution of total orders per customer
SELECT
    total_orders,
    COUNT(*)           AS customer_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_of_customers
FROM (
    SELECT user_id, COUNT(*) AS total_orders
    FROM stg_orders
    GROUP BY user_id
) t
GROUP BY total_orders
ORDER BY total_orders;

-- Q3: Average, median-like, and max orders per customer
SELECT
    ROUND(AVG(total_orders), 2)  AS avg_orders_per_customer,
    MIN(total_orders)            AS min_orders,
    MAX(total_orders)            AS max_orders,
    -- approximate median via percentile logic
    ROUND(
        (SELECT total_orders FROM (
            SELECT user_id, COUNT(*) AS total_orders,
                   ROW_NUMBER() OVER (ORDER BY COUNT(*)) AS rn,
                   COUNT(*) OVER () AS total_users
            FROM stg_orders GROUP BY user_id
        ) sub
        WHERE rn = CEIL(total_users / 2)
        LIMIT 1
    ), 0) AS approx_median_orders
FROM (
    SELECT user_id, COUNT(*) AS total_orders
    FROM stg_orders GROUP BY user_id
) t;

-- Q4: Top 20 most frequent customers (by order count)
SELECT
    user_id,
    COUNT(*)                         AS total_orders,
    ROUND(AVG(days_since_prior_order), 1) AS avg_days_between_orders
FROM stg_orders
GROUP BY user_id
ORDER BY total_orders DESC
LIMIT 20;

-- Q5: Average number of products per order (prior orders)
SELECT
    ROUND(AVG(products_per_order), 2) AS avg_basket_size,
    MIN(products_per_order)           AS min_basket,
    MAX(products_per_order)           AS max_basket
FROM (
    SELECT order_id, COUNT(*) AS products_per_order
    FROM stg_order_products_prior
    GROUP BY order_id
) t;

-- Q6: Customer reorder rate distribution
--     (what % of each customer's prior purchases were reorders)
SELECT
    CASE
        WHEN reorder_rate < 0.2  THEN '0–20% (Low reorders)'
        WHEN reorder_rate < 0.4  THEN '20–40%'
        WHEN reorder_rate < 0.6  THEN '40–60%'
        WHEN reorder_rate < 0.8  THEN '60–80%'
        ELSE '80–100% (High reorders)'
    END                             AS reorder_rate_bucket,
    COUNT(*)                        AS customer_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct
FROM (
    SELECT
        o.user_id,
        AVG(op.reordered) AS reorder_rate
    FROM stg_orders o
    JOIN stg_order_products_prior op ON o.order_id = op.order_id
    WHERE o.eval_set = 'prior'
    GROUP BY o.user_id
) t
GROUP BY reorder_rate_bucket
ORDER BY MIN(reorder_rate);

-- Q7: Average days between orders by order frequency segment
SELECT
    CASE
        WHEN total_orders BETWEEN 1  AND 5   THEN 'Infrequent (1-5 orders)'
        WHEN total_orders BETWEEN 6  AND 15  THEN 'Moderate (6-15 orders)'
        WHEN total_orders BETWEEN 16 AND 30  THEN 'Regular (16-30 orders)'
        ELSE 'Heavy (31+ orders)'
    END                                     AS frequency_segment,
    COUNT(DISTINCT user_id)                 AS customer_count,
    ROUND(AVG(avg_days), 1)                 AS avg_days_between_orders
FROM (
    SELECT
        user_id,
        COUNT(*)                              AS total_orders,
        AVG(days_since_prior_order)           AS avg_days
    FROM stg_orders
    GROUP BY user_id
) t
GROUP BY frequency_segment
ORDER BY MIN(total_orders);

-- Q8: Customers who order most frequently (weekly-ish pattern: avg ≤ 8 days)
SELECT
    user_id,
    COUNT(*)                                 AS total_orders,
    ROUND(AVG(days_since_prior_order), 1)    AS avg_days_between_orders
FROM stg_orders
GROUP BY user_id
HAVING AVG(days_since_prior_order) <= 8
   AND COUNT(*) >= 5
ORDER BY avg_days_between_orders, total_orders DESC
LIMIT 50;


-- ═══════════════════════════════════════════════════════════════════════════════
-- SECTION 2: PRODUCT ANALYTICS
-- ═══════════════════════════════════════════════════════════════════════════════

-- Q9: Top 25 most purchased products (prior orders)
SELECT
    p.product_id,
    p.product_name,
    d.department,
    a.aisle,
    COUNT(*)                  AS purchase_count,
    ROUND(AVG(op.reordered) * 100, 1) AS reorder_rate_pct
FROM stg_order_products_prior op
JOIN stg_products p ON op.product_id = p.product_id
JOIN stg_aisles a    ON p.aisle_id = a.aisle_id
JOIN stg_departments d ON p.department_id = d.department_id
GROUP BY p.product_id, p.product_name, d.department, a.aisle
ORDER BY purchase_count DESC
LIMIT 25;

-- Q10: Top 25 most reordered products (min 100 purchases for statistical reliability)
SELECT
    p.product_id,
    p.product_name,
    d.department,
    COUNT(*)                            AS total_purchases,
    SUM(op.reordered)                   AS times_reordered,
    ROUND(AVG(op.reordered) * 100, 2)   AS reorder_rate_pct
FROM stg_order_products_prior op
JOIN stg_products p    ON op.product_id = p.product_id
JOIN stg_departments d ON p.department_id = d.department_id
GROUP BY p.product_id, p.product_name, d.department
HAVING COUNT(*) >= 100
ORDER BY reorder_rate_pct DESC
LIMIT 25;

-- Q11: Products with high first purchase but low reorder rate
--      (popular initially but customers don't come back)
SELECT
    p.product_name,
    d.department,
    total_purchases,
    ROUND(reorder_rate * 100, 2) AS reorder_rate_pct,
    'Low repeat purchase' AS insight
FROM (
    SELECT
        product_id,
        COUNT(*)       AS total_purchases,
        AVG(reordered) AS reorder_rate
    FROM stg_order_products_prior
    GROUP BY product_id
    HAVING COUNT(*) >= 200
) t
JOIN stg_products p    ON t.product_id = p.product_id
JOIN stg_departments d ON p.department_id = d.department_id
WHERE reorder_rate < 0.3
ORDER BY total_purchases DESC
LIMIT 25;

-- Q12: Likely staple products — high purchase volume AND high reorder rate
SELECT
    p.product_name,
    d.department,
    a.aisle,
    COUNT(*)                          AS total_purchases,
    ROUND(AVG(op.reordered)*100, 1)   AS reorder_rate_pct,
    RANK() OVER (ORDER BY COUNT(*) DESC) AS purchase_rank,
    RANK() OVER (ORDER BY AVG(op.reordered) DESC) AS reorder_rank
FROM stg_order_products_prior op
JOIN stg_products p    ON op.product_id = p.product_id
JOIN stg_aisles a      ON p.aisle_id = a.aisle_id
JOIN stg_departments d ON p.department_id = d.department_id
GROUP BY p.product_id, p.product_name, d.department, a.aisle
HAVING COUNT(*) >= 500 AND AVG(op.reordered) >= 0.70
ORDER BY total_purchases DESC
LIMIT 30;

-- Q13: Product ranking within each department by purchase count
SELECT
    department,
    product_name,
    purchase_count,
    RANK() OVER (PARTITION BY department ORDER BY purchase_count DESC) AS dept_rank
FROM (
    SELECT
        d.department,
        p.product_name,
        COUNT(*) AS purchase_count
    FROM stg_order_products_prior op
    JOIN stg_products p    ON op.product_id = p.product_id
    JOIN stg_departments d ON p.department_id = d.department_id
    GROUP BY d.department, p.product_name
) t
QUALIFY RANK() OVER (PARTITION BY department ORDER BY purchase_count DESC) <= 5
ORDER BY department, dept_rank;


-- ═══════════════════════════════════════════════════════════════════════════════
-- SECTION 3: DEPARTMENT ANALYTICS
-- ═══════════════════════════════════════════════════════════════════════════════

-- Q14: Department ranking by total items purchased
SELECT
    d.department_id,
    d.department,
    COUNT(*)                              AS total_items_purchased,
    COUNT(DISTINCT op.order_id)           AS orders_containing_dept,
    COUNT(DISTINCT p.product_id)          AS unique_products,
    ROUND(AVG(op.reordered) * 100, 2)     AS reorder_rate_pct,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_of_all_purchases,
    RANK() OVER (ORDER BY COUNT(*) DESC)  AS purchase_rank
FROM stg_order_products_prior op
JOIN stg_products p    ON op.product_id = p.product_id
JOIN stg_departments d ON p.department_id = d.department_id
GROUP BY d.department_id, d.department
ORDER BY total_items_purchased DESC;

-- Q15: Department reorder rate ranking
SELECT
    d.department,
    COUNT(*)                              AS total_purchases,
    ROUND(AVG(op.reordered) * 100, 2)     AS reorder_rate_pct,
    RANK() OVER (ORDER BY AVG(op.reordered) DESC) AS reorder_rank
FROM stg_order_products_prior op
JOIN stg_products p    ON op.product_id = p.product_id
JOIN stg_departments d ON p.department_id = d.department_id
GROUP BY d.department
ORDER BY reorder_rate_pct DESC;

-- Q16: Top 20 aisles by purchase volume with reorder rates
SELECT
    a.aisle,
    d.department,
    COUNT(*)                           AS total_purchases,
    ROUND(AVG(op.reordered)*100, 2)    AS reorder_rate_pct,
    RANK() OVER (ORDER BY COUNT(*) DESC) AS aisle_rank
FROM stg_order_products_prior op
JOIN stg_products p    ON op.product_id = p.product_id
JOIN stg_aisles a      ON p.aisle_id = a.aisle_id
JOIN stg_departments d ON p.department_id = d.department_id
GROUP BY a.aisle, d.department
ORDER BY total_purchases DESC
LIMIT 20;

-- Q17: Departments with above-average reorder rate
WITH dept_stats AS (
    SELECT
        d.department,
        AVG(op.reordered) AS dept_reorder_rate
    FROM stg_order_products_prior op
    JOIN stg_products p    ON op.product_id = p.product_id
    JOIN stg_departments d ON p.department_id = d.department_id
    GROUP BY d.department
),
overall AS (
    SELECT AVG(reordered) AS overall_reorder_rate
    FROM stg_order_products_prior
)
SELECT
    ds.department,
    ROUND(ds.dept_reorder_rate * 100, 2)       AS dept_reorder_pct,
    ROUND(o.overall_reorder_rate * 100, 2)     AS overall_reorder_pct,
    ROUND((ds.dept_reorder_rate - o.overall_reorder_rate) * 100, 2) AS diff_from_avg
FROM dept_stats ds
CROSS JOIN overall o
WHERE ds.dept_reorder_rate > o.overall_reorder_rate
ORDER BY diff_from_avg DESC;

