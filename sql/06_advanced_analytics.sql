-- =============================================================================
-- 06_advanced_analytics.sql
-- Enterprise Retail Intelligence & Decision Engine
-- Phase 7: SQL Analytics — Advanced Analytics
--
-- Covers: window functions, CTEs, cohort logic, running totals,
--         time analysis, LAG/LEAD, ranking, segmentation.
-- =============================================================================

USE enterprise_bi;

-- ═══════════════════════════════════════════════════════════════════════════════
-- SECTION 4: TIME ANALYTICS
-- ═══════════════════════════════════════════════════════════════════════════════

-- Q18: Order volume by day of week
--      (0=Saturday, 1=Sunday, 2=Monday, ... 6=Friday per Instacart convention)
SELECT
    order_dow,
    CASE order_dow
        WHEN 0 THEN 'Saturday'
        WHEN 1 THEN 'Sunday'
        WHEN 2 THEN 'Monday'
        WHEN 3 THEN 'Tuesday'
        WHEN 4 THEN 'Wednesday'
        WHEN 5 THEN 'Thursday'
        WHEN 6 THEN 'Friday'
    END                            AS day_name,
    COUNT(*)                       AS total_orders,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_of_orders
FROM stg_orders
GROUP BY order_dow
ORDER BY order_dow;

-- Q19: Order volume by hour of day
SELECT
    order_hour_of_day,
    COUNT(*)                       AS total_orders,
    ROUND(AVG(products_per_order), 2) AS avg_basket_size,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_of_orders
FROM stg_orders o
LEFT JOIN (
    SELECT order_id, COUNT(*) AS products_per_order
    FROM stg_order_products_prior GROUP BY order_id
) basket ON o.order_id = basket.order_id
GROUP BY order_hour_of_day
ORDER BY order_hour_of_day;

-- Q20: Demand heatmap — orders by day and hour
SELECT
    CASE order_dow
        WHEN 0 THEN 'Saturday' WHEN 1 THEN 'Sunday'
        WHEN 2 THEN 'Monday'   WHEN 3 THEN 'Tuesday'
        WHEN 4 THEN 'Wednesday' WHEN 5 THEN 'Thursday'
        WHEN 6 THEN 'Friday'
    END                            AS day_name,
    order_hour_of_day,
    COUNT(*)                       AS order_count
FROM stg_orders
GROUP BY order_dow, order_hour_of_day
ORDER BY order_dow, order_hour_of_day;

-- Q21: Peak operating windows (top 10 day+hour combinations)
SELECT
    CASE order_dow
        WHEN 0 THEN 'Saturday' WHEN 1 THEN 'Sunday'
        WHEN 2 THEN 'Monday'   WHEN 3 THEN 'Tuesday'
        WHEN 4 THEN 'Wednesday' WHEN 5 THEN 'Thursday'
        WHEN 6 THEN 'Friday'
    END                            AS day_name,
    order_hour_of_day,
    COUNT(*)                       AS order_count,
    RANK() OVER (ORDER BY COUNT(*) DESC) AS peak_rank
FROM stg_orders
GROUP BY order_dow, order_hour_of_day
ORDER BY order_count DESC
LIMIT 10;

-- Q22: Reorder rate by day of week
SELECT
    CASE o.order_dow
        WHEN 0 THEN 'Saturday' WHEN 1 THEN 'Sunday'
        WHEN 2 THEN 'Monday'   WHEN 3 THEN 'Tuesday'
        WHEN 4 THEN 'Wednesday' WHEN 5 THEN 'Thursday'
        WHEN 6 THEN 'Friday'
    END                                   AS day_name,
    COUNT(*)                              AS total_items,
    ROUND(AVG(op.reordered) * 100, 2)     AS reorder_rate_pct
FROM stg_orders o
JOIN stg_order_products_prior op ON o.order_id = op.order_id
GROUP BY o.order_dow
ORDER BY o.order_dow;

-- Q23: Reorder rate by hour of day
SELECT
    o.order_hour_of_day,
    COUNT(*)                              AS total_items,
    ROUND(AVG(op.reordered) * 100, 2)    AS reorder_rate_pct
FROM stg_orders o
JOIN stg_order_products_prior op ON o.order_id = op.order_id
GROUP BY o.order_hour_of_day
ORDER BY o.order_hour_of_day;

-- Q24: Days between orders distribution
SELECT
    days_since_prior_order,
    COUNT(*) AS frequency
FROM stg_orders
WHERE days_since_prior_order IS NOT NULL
GROUP BY days_since_prior_order
ORDER BY days_since_prior_order;


-- ═══════════════════════════════════════════════════════════════════════════════
-- SECTION 5: REORDER ANALYSIS (Window Functions, LAG/LEAD)
-- ═══════════════════════════════════════════════════════════════════════════════

-- Q25: Customer purchase sequence — LAG to show gap from previous order
SELECT
    user_id,
    order_id,
    order_number,
    order_dow,
    order_hour_of_day,
    days_since_prior_order,
    LAG(days_since_prior_order)  OVER (PARTITION BY user_id ORDER BY order_number) AS prev_gap,
    LEAD(days_since_prior_order) OVER (PARTITION BY user_id ORDER BY order_number) AS next_gap
FROM stg_orders
WHERE user_id <= 10   -- sample first 10 users for illustration
ORDER BY user_id, order_number;

-- Q26: How reorder rate evolves with order sequence
--      (Do customers reorder more as they become loyal?)
SELECT
    order_number_bucket,
    total_items,
    ROUND(AVG(reorder_rate) * 100, 2) AS avg_reorder_rate_pct
FROM (
    SELECT
        CASE
            WHEN o.order_number = 1        THEN '01 - First Order'
            WHEN o.order_number BETWEEN 2 AND 3  THEN '02-03'
            WHEN o.order_number BETWEEN 4 AND 6  THEN '04-06'
            WHEN o.order_number BETWEEN 7 AND 10 THEN '07-10'
            WHEN o.order_number BETWEEN 11 AND 20 THEN '11-20'
            ELSE '21+'
        END                          AS order_number_bucket,
        COUNT(*)                     AS total_items,
        AVG(op.reordered)            AS reorder_rate
    FROM stg_orders o
    JOIN stg_order_products_prior op ON o.order_id = op.order_id
    GROUP BY order_number_bucket, o.order_id
) t
GROUP BY order_number_bucket
ORDER BY order_number_bucket;

-- Q27: Running total of orders per customer (window function)
SELECT
    user_id,
    order_number,
    order_id,
    days_since_prior_order,
    SUM(1) OVER (PARTITION BY user_id ORDER BY order_number
                 ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_orders
FROM stg_orders
WHERE user_id IN (1, 2, 3, 4, 5)
ORDER BY user_id, order_number;

-- Q28: Products most commonly added first to cart (add_to_cart_order = 1)
SELECT
    p.product_name,
    d.department,
    COUNT(*) AS times_added_first,
    RANK() OVER (ORDER BY COUNT(*) DESC) AS first_add_rank
FROM stg_order_products_prior op
JOIN stg_products p    ON op.product_id = p.product_id
JOIN stg_departments d ON p.department_id = d.department_id
WHERE op.add_to_cart_order = 1
GROUP BY p.product_name, d.department
ORDER BY times_added_first DESC
LIMIT 25;

-- Q29: Products with improving reorder rate in train vs prior
--      Compare reorder rate in train set vs prior set
WITH prior_rates AS (
    SELECT
        product_id,
        AVG(reordered) AS prior_reorder_rate,
        COUNT(*)       AS prior_purchases
    FROM stg_order_products_prior
    GROUP BY product_id
    HAVING COUNT(*) >= 100
),
train_rates AS (
    SELECT
        product_id,
        AVG(reordered) AS train_reorder_rate,
        COUNT(*)       AS train_purchases
    FROM stg_order_products_train
    GROUP BY product_id
    HAVING COUNT(*) >= 20
)
SELECT
    p.product_name,
    d.department,
    ROUND(pr.prior_reorder_rate * 100, 2)  AS prior_reorder_pct,
    ROUND(tr.train_reorder_rate * 100, 2)  AS train_reorder_pct,
    ROUND((tr.train_reorder_rate - pr.prior_reorder_rate) * 100, 2) AS delta_pct
FROM prior_rates pr
JOIN train_rates tr    ON pr.product_id = tr.product_id
JOIN stg_products p    ON pr.product_id = p.product_id
JOIN stg_departments d ON p.department_id = d.department_id
ORDER BY delta_pct DESC
LIMIT 20;


-- ═══════════════════════════════════════════════════════════════════════════════
-- SECTION 6: COHORT & SEGMENTATION QUERIES
-- ═══════════════════════════════════════════════════════════════════════════════

-- Q30: Customer segmentation by order frequency
WITH customer_stats AS (
    SELECT
        user_id,
        COUNT(*)                          AS total_orders,
        AVG(days_since_prior_order)       AS avg_days_between,
        MAX(order_number)                 AS max_order_number
    FROM stg_orders
    GROUP BY user_id
)
SELECT
    CASE
        WHEN total_orders = 1                   THEN 'One-time buyer'
        WHEN total_orders BETWEEN 2  AND 5      THEN 'Occasional (2-5)'
        WHEN total_orders BETWEEN 6  AND 15     THEN 'Regular (6-15)'
        WHEN total_orders BETWEEN 16 AND 30     THEN 'Loyal (16-30)'
        ELSE 'Champion (30+)'
    END                                         AS segment,
    COUNT(*)                                    AS customer_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_customers,
    ROUND(AVG(avg_days_between), 1)             AS avg_days_between_orders
FROM customer_stats
GROUP BY segment
ORDER BY MIN(total_orders);

-- Q31: High-value behavior segment: frequent + high reorder
--      (using prior orders data joined to orders)
WITH user_behavior AS (
    SELECT
        o.user_id,
        COUNT(DISTINCT o.order_id)   AS total_orders,
        AVG(op.reordered)            AS reorder_rate,
        COUNT(*) / COUNT(DISTINCT o.order_id) AS avg_basket_size
    FROM stg_orders o
    JOIN stg_order_products_prior op ON o.order_id = op.order_id
    WHERE o.eval_set = 'prior'
    GROUP BY o.user_id
)
SELECT
    CASE
        WHEN total_orders >= 10 AND reorder_rate >= 0.6 THEN 'High-Frequency High-Loyalty'
        WHEN total_orders >= 10 AND reorder_rate <  0.6 THEN 'High-Frequency Explorer'
        WHEN total_orders <  10 AND reorder_rate >= 0.6 THEN 'Low-Frequency Loyal'
        ELSE 'Low-Frequency Explorer'
    END                                             AS behavior_segment,
    COUNT(*)                                        AS customer_count,
    ROUND(AVG(total_orders), 1)                     AS avg_orders,
    ROUND(AVG(reorder_rate) * 100, 1)               AS avg_reorder_rate_pct,
    ROUND(AVG(avg_basket_size), 1)                  AS avg_basket_size
FROM user_behavior
GROUP BY behavior_segment
ORDER BY customer_count DESC;

-- Q32: Order frequency percentiles using window functions
WITH user_order_counts AS (
    SELECT
        user_id,
        COUNT(*) AS total_orders
    FROM stg_orders
    GROUP BY user_id
)
SELECT
    ROUND(PERCENTILE_CONT(0.10) WITHIN GROUP (ORDER BY total_orders), 0) AS p10,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY total_orders), 0) AS p25,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY total_orders), 0) AS p50_median,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total_orders), 0) AS p75,
    ROUND(PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY total_orders), 0) AS p90,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_orders), 0) AS p95,
    ROUND(PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY total_orders), 0) AS p99
FROM user_order_counts;

-- Q33: Running cumulative % of orders by day of week (window function)
SELECT
    day_name,
    total_orders,
    SUM(total_orders) OVER (ORDER BY total_orders DESC
                            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_orders,
    ROUND(SUM(total_orders) OVER (ORDER BY total_orders DESC
                                  ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
          * 100.0 / SUM(total_orders) OVER (), 2) AS cumulative_pct
FROM (
    SELECT
        CASE order_dow
            WHEN 0 THEN 'Saturday' WHEN 1 THEN 'Sunday'
            WHEN 2 THEN 'Monday'   WHEN 3 THEN 'Tuesday'
            WHEN 4 THEN 'Wednesday' WHEN 5 THEN 'Thursday'
            WHEN 6 THEN 'Friday'
        END AS day_name,
        COUNT(*) AS total_orders
    FROM stg_orders
    GROUP BY order_dow
) t
ORDER BY total_orders DESC;

