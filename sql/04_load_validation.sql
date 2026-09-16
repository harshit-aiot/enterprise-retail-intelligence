-- =============================================================================
-- 04_load_validation.sql
-- Enterprise Retail Intelligence & Decision Engine
-- Phase 6: MySQL Database — Load Validation
--
-- Run after data load to verify counts and basic integrity.
-- =============================================================================

USE enterprise_bi;

-- ── Row count verification ────────────────────────────────────────────────────
SELECT 'ROW COUNT VALIDATION' AS section;

SELECT
    'stg_departments'           AS table_name, COUNT(*) AS row_count, 21          AS expected, IF(COUNT(*)=21,         'PASS','FAIL') AS status FROM stg_departments
UNION ALL SELECT
    'stg_aisles',                COUNT(*),                              134,         IF(COUNT(*)=134,        'PASS','FAIL')             FROM stg_aisles
UNION ALL SELECT
    'stg_products',              COUNT(*),                              49688,       IF(COUNT(*)=49688,      'PASS','FAIL')             FROM stg_products
UNION ALL SELECT
    'stg_orders',                COUNT(*),                              3421083,     IF(COUNT(*)=3421083,    'PASS','FAIL')             FROM stg_orders
UNION ALL SELECT
    'stg_order_products_prior',  COUNT(*),                              32434489,    IF(COUNT(*)=32434489,   'PASS','FAIL')             FROM stg_order_products_prior
UNION ALL SELECT
    'stg_order_products_train',  COUNT(*),                              1384617,     IF(COUNT(*)=1384617,    'PASS','FAIL')             FROM stg_order_products_train;

-- ── Null checks ───────────────────────────────────────────────────────────────
SELECT 'NULL VALUE CHECKS' AS section;

SELECT
    'orders.days_since_prior NULL count' AS check_name,
    COUNT(*) AS value,
    'Expected ~206209 (first orders)' AS note
FROM stg_orders
WHERE days_since_prior_order IS NULL;

SELECT
    'orders.days_since_prior non-NULL in order_number=1' AS check_name,
    COUNT(*) AS should_be_zero
FROM stg_orders
WHERE order_number = 1 AND days_since_prior_order IS NOT NULL;

-- ── Basic sanity queries ──────────────────────────────────────────────────────
SELECT 'BASIC SANITY CHECKS' AS section;

-- Unique users
SELECT
    'Unique users' AS metric,
    COUNT(DISTINCT user_id) AS value
FROM stg_orders;

-- eval_set distribution
SELECT
    eval_set,
    COUNT(*) AS order_count
FROM stg_orders
GROUP BY eval_set
ORDER BY order_count DESC;

-- Average basket size (prior)
SELECT
    'Average basket size (prior)' AS metric,
    ROUND(COUNT(*) / COUNT(DISTINCT order_id), 2) AS avg_products_per_order
FROM stg_order_products_prior;

-- Overall reorder rate (prior)
SELECT
    'Overall reorder rate (prior)' AS metric,
    ROUND(AVG(reordered) * 100, 2) AS reorder_rate_pct
FROM stg_order_products_prior;
