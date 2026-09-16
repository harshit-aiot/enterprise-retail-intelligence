-- =============================================================================
-- 07_views.sql
-- Enterprise Retail Intelligence & Decision Engine
-- Phase 7: SQL Analytics — Analytical Views
--
-- Creates reusable views that the Streamlit app and further SQL can query.
-- =============================================================================

USE enterprise_bi;

-- ── Drop existing views ───────────────────────────────────────────────────────
DROP VIEW IF EXISTS vw_product_summary;
DROP VIEW IF EXISTS vw_department_summary;
DROP VIEW IF EXISTS vw_customer_summary;
DROP VIEW IF EXISTS vw_time_summary;
DROP VIEW IF EXISTS vw_top_products;
DROP VIEW IF EXISTS vw_aisle_summary;

-- ── VIEW: vw_product_summary ──────────────────────────────────────────────────
-- One row per product with purchase stats, reorder rates, rankings
CREATE VIEW vw_product_summary AS
SELECT
    p.product_id,
    p.product_name,
    a.aisle_id,
    a.aisle,
    d.department_id,
    d.department,
    COUNT(op.order_id)                  AS total_purchases,
    SUM(op.reordered)                   AS total_reorders,
    ROUND(AVG(op.reordered) * 100, 2)   AS reorder_rate_pct,
    ROUND(AVG(op.add_to_cart_order), 2) AS avg_cart_position,
    RANK() OVER (ORDER BY COUNT(op.order_id) DESC) AS purchase_rank,
    RANK() OVER (PARTITION BY d.department_id ORDER BY COUNT(op.order_id) DESC) AS dept_purchase_rank
FROM stg_products p
JOIN stg_aisles a      ON p.aisle_id = a.aisle_id
JOIN stg_departments d ON p.department_id = d.department_id
LEFT JOIN stg_order_products_prior op ON p.product_id = op.product_id
GROUP BY p.product_id, p.product_name, a.aisle_id, a.aisle, d.department_id, d.department;

-- ── VIEW: vw_department_summary ───────────────────────────────────────────────
CREATE VIEW vw_department_summary AS
SELECT
    d.department_id,
    d.department,
    COUNT(DISTINCT p.product_id)         AS product_count,
    COUNT(op.order_id)                   AS total_purchases,
    ROUND(AVG(op.reordered) * 100, 2)    AS reorder_rate_pct,
    COUNT(DISTINCT op.order_id)          AS orders_containing_dept,
    ROUND(COUNT(op.order_id) * 100.0 / SUM(COUNT(op.order_id)) OVER (), 2) AS pct_of_all_purchases,
    RANK() OVER (ORDER BY COUNT(op.order_id) DESC) AS purchase_rank,
    RANK() OVER (ORDER BY AVG(op.reordered) DESC)  AS reorder_rank
FROM stg_departments d
JOIN stg_products p         ON d.department_id = p.department_id
LEFT JOIN stg_order_products_prior op ON p.product_id = op.product_id
GROUP BY d.department_id, d.department;

-- ── VIEW: vw_aisle_summary ────────────────────────────────────────────────────
CREATE VIEW vw_aisle_summary AS
SELECT
    a.aisle_id,
    a.aisle,
    d.department_id,
    d.department,
    COUNT(DISTINCT p.product_id)          AS product_count,
    COUNT(op.order_id)                    AS total_purchases,
    ROUND(AVG(op.reordered) * 100, 2)     AS reorder_rate_pct,
    RANK() OVER (ORDER BY COUNT(op.order_id) DESC) AS purchase_rank
FROM stg_aisles a
JOIN stg_products p    ON a.aisle_id = p.aisle_id
JOIN stg_departments d ON p.department_id = d.department_id
LEFT JOIN stg_order_products_prior op ON p.product_id = op.product_id
GROUP BY a.aisle_id, a.aisle, d.department_id, d.department;

-- ── VIEW: vw_customer_summary ─────────────────────────────────────────────────
CREATE VIEW vw_customer_summary AS
SELECT
    o.user_id,
    COUNT(DISTINCT o.order_id)              AS total_orders,
    MAX(o.order_number)                     AS max_order_number,
    ROUND(AVG(o.days_since_prior_order), 1) AS avg_days_between_orders,
    MIN(o.days_since_prior_order)           AS min_days,
    MAX(o.days_since_prior_order)           AS max_days,
    -- Most common order day
    (SELECT order_dow FROM stg_orders o2
     WHERE o2.user_id = o.user_id
     GROUP BY order_dow ORDER BY COUNT(*) DESC LIMIT 1) AS preferred_dow,
    -- Most common order hour
    (SELECT order_hour_of_day FROM stg_orders o3
     WHERE o3.user_id = o.user_id
     GROUP BY order_hour_of_day ORDER BY COUNT(*) DESC LIMIT 1) AS preferred_hour,
    CASE
        WHEN COUNT(DISTINCT o.order_id) = 1                   THEN 'One-time'
        WHEN COUNT(DISTINCT o.order_id) BETWEEN 2  AND 5      THEN 'Occasional'
        WHEN COUNT(DISTINCT o.order_id) BETWEEN 6  AND 15     THEN 'Regular'
        WHEN COUNT(DISTINCT o.order_id) BETWEEN 16 AND 30     THEN 'Loyal'
        ELSE 'Champion'
    END AS frequency_segment
FROM stg_orders o
GROUP BY o.user_id;

-- ── VIEW: vw_time_summary ─────────────────────────────────────────────────────
CREATE VIEW vw_time_summary AS
SELECT
    o.order_dow,
    CASE o.order_dow
        WHEN 0 THEN 'Saturday' WHEN 1 THEN 'Sunday'
        WHEN 2 THEN 'Monday'   WHEN 3 THEN 'Tuesday'
        WHEN 4 THEN 'Wednesday' WHEN 5 THEN 'Thursday'
        WHEN 6 THEN 'Friday'
    END                                       AS day_name,
    o.order_hour_of_day,
    COUNT(DISTINCT o.order_id)                AS total_orders,
    COUNT(op.product_id)                      AS total_items,
    ROUND(AVG(op.reordered) * 100, 2)         AS reorder_rate_pct,
    ROUND(COUNT(op.product_id) * 1.0 / COUNT(DISTINCT o.order_id), 2) AS avg_basket_size
FROM stg_orders o
LEFT JOIN stg_order_products_prior op ON o.order_id = op.order_id
GROUP BY o.order_dow, o.order_hour_of_day;

-- ── VIEW: vw_top_products ─────────────────────────────────────────────────────
CREATE VIEW vw_top_products AS
SELECT
    p.product_id,
    p.product_name,
    d.department,
    a.aisle,
    COUNT(op.order_id)                   AS total_purchases,
    ROUND(AVG(op.reordered) * 100, 2)    AS reorder_rate_pct,
    RANK() OVER (ORDER BY COUNT(op.order_id) DESC) AS overall_rank,
    RANK() OVER (PARTITION BY d.department ORDER BY COUNT(op.order_id) DESC) AS dept_rank
FROM stg_order_products_prior op
JOIN stg_products p    ON op.product_id = p.product_id
JOIN stg_aisles a      ON p.aisle_id = a.aisle_id
JOIN stg_departments d ON p.department_id = d.department_id
GROUP BY p.product_id, p.product_name, d.department, a.aisle;

-- Confirm views
SHOW FULL TABLES WHERE TABLE_TYPE = 'VIEW';
