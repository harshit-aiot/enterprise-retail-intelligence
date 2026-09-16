-- =============================================================================
-- 03_indexes.sql
-- Enterprise Retail Intelligence & Decision Engine
-- Phase 6: MySQL Database
--
-- Creates analytical indexes on staging tables.
--
-- Index strategy:
--   - PK indexes are already created with table definitions
--   - Additional indexes target the most common query patterns:
--       * Filter by user (customer analytics)
--       * Filter by eval_set (train/prior splits)
--       * Filter by product (product analytics)
--       * Filter by department/aisle (category analytics)
--       * Filter by time (order_dow, order_hour)
--       * Reorder analysis
-- =============================================================================

USE enterprise_bi;

-- ─────────────────────────────────────────────────────────────
-- stg_orders indexes
-- ─────────────────────────────────────────────────────────────

-- Most critical: user_id (all customer queries filter on this)
CREATE INDEX idx_orders_user_id
    ON stg_orders (user_id);

-- eval_set: frequent filter for prior vs train vs test splits
CREATE INDEX idx_orders_eval_set
    ON stg_orders (eval_set);

-- Time-based analysis: day of week and hour
CREATE INDEX idx_orders_dow
    ON stg_orders (order_dow);

CREATE INDEX idx_orders_hour
    ON stg_orders (order_hour_of_day);

-- Composite: user_id + order_number — for per-customer sequence queries
CREATE INDEX idx_orders_user_ordernum
    ON stg_orders (user_id, order_number);

-- ─────────────────────────────────────────────────────────────
-- stg_products indexes
-- ─────────────────────────────────────────────────────────────

-- department_id: category drill-downs
CREATE INDEX idx_products_department_id
    ON stg_products (department_id);

-- aisle_id: aisle-level queries
CREATE INDEX idx_products_aisle_id
    ON stg_products (aisle_id);

-- ─────────────────────────────────────────────────────────────
-- stg_order_products_prior indexes
-- ─────────────────────────────────────────────────────────────

-- product_id: product ranking, reorder analysis
CREATE INDEX idx_opp_product_id
    ON stg_order_products_prior (product_id);

-- reordered: filter for reorder analysis
CREATE INDEX idx_opp_reordered
    ON stg_order_products_prior (reordered);

-- Composite: product_id + reordered — reorder rate by product
CREATE INDEX idx_opp_product_reordered
    ON stg_order_products_prior (product_id, reordered);

-- ─────────────────────────────────────────────────────────────
-- stg_order_products_train indexes
-- ─────────────────────────────────────────────────────────────

CREATE INDEX idx_opt_product_id
    ON stg_order_products_train (product_id);

CREATE INDEX idx_opt_reordered
    ON stg_order_products_train (reordered);

-- Confirm indexes created
SELECT
    TABLE_NAME,
    INDEX_NAME,
    COLUMN_NAME,
    NON_UNIQUE
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = 'enterprise_bi'
ORDER BY TABLE_NAME, INDEX_NAME;
