"""
queries.py — Centralized SQL query definitions for the Streamlit app.
"""

KPI_SUMMARY = """
SELECT
    (SELECT COUNT(DISTINCT user_id)         FROM stg_orders)                      AS unique_customers,
    (SELECT COUNT(DISTINCT order_id)        FROM stg_orders)                      AS total_orders,
    (SELECT COUNT(*)                        FROM stg_order_products_prior)         AS total_items_purchased,
    (SELECT COUNT(DISTINCT product_id)      FROM stg_products)                    AS unique_products,
    (SELECT ROUND(AVG(reordered)*100,2)     FROM stg_order_products_prior)        AS reorder_rate_pct,
    (SELECT ROUND(COUNT(*)*1.0/COUNT(DISTINCT order_id),2)
     FROM stg_order_products_prior)                                               AS avg_basket_size
"""

DEPT_RANKING = """
SELECT
    d.department,
    COUNT(op.order_id)                 AS total_purchases,
    ROUND(AVG(op.reordered)*100,2)     AS reorder_rate_pct,
    ROUND(COUNT(op.order_id)*100.0/SUM(COUNT(op.order_id)) OVER(),2) AS pct_share
FROM stg_order_products_prior op
JOIN stg_products p    ON op.product_id = p.product_id
JOIN stg_departments d ON p.department_id = d.department_id
GROUP BY d.department
ORDER BY total_purchases DESC
"""

TOP_PRODUCTS = """
SELECT
    p.product_name, d.department,
    COUNT(*)                          AS purchases,
    ROUND(AVG(op.reordered)*100,2)    AS reorder_rate_pct
FROM stg_order_products_prior op
JOIN stg_products p    ON op.product_id = p.product_id
JOIN stg_departments d ON p.department_id = d.department_id
GROUP BY p.product_name, d.department
ORDER BY purchases DESC
LIMIT :n
"""

ORDERS_BY_DOW = """
SELECT
    order_dow,
    CASE order_dow
        WHEN 0 THEN 'Saturday' WHEN 1 THEN 'Sunday' WHEN 2 THEN 'Monday'
        WHEN 3 THEN 'Tuesday'  WHEN 4 THEN 'Wednesday' WHEN 5 THEN 'Thursday'
        WHEN 6 THEN 'Friday'
    END AS day_name,
    COUNT(*) AS orders
FROM stg_orders GROUP BY order_dow ORDER BY order_dow
"""

ORDERS_BY_HOUR = """
SELECT order_hour_of_day, COUNT(*) AS orders
FROM stg_orders GROUP BY order_hour_of_day ORDER BY order_hour_of_day
"""

PRODUCT_SEARCH = """
SELECT
    p.product_name, d.department, a.aisle,
    COUNT(op.order_id)               AS total_purchases,
    ROUND(AVG(op.reordered)*100,2)   AS reorder_rate_pct
FROM stg_products p
JOIN stg_aisles a      ON p.aisle_id = a.aisle_id
JOIN stg_departments d ON p.department_id = d.department_id
LEFT JOIN stg_order_products_prior op ON p.product_id = op.product_id
WHERE p.product_name LIKE :search
GROUP BY p.product_name, d.department, a.aisle
ORDER BY total_purchases DESC
LIMIT 20
"""

CUSTOMER_STATS = """
SELECT
    user_id,
    COUNT(DISTINCT order_id)               AS total_orders,
    ROUND(AVG(days_since_prior_order),1)   AS avg_days_between,
    MAX(order_number)                      AS last_order_number
FROM stg_orders
WHERE user_id = :user_id
GROUP BY user_id
"""

MARKET_BASKET_LOOKUP = """
SELECT antecedent_name, consequent_name, support, confidence, lift, co_occurrence
FROM market_basket_cache
WHERE antecedent_name LIKE :product
ORDER BY lift DESC
LIMIT 20
"""
