-- =============================================================================
-- 02_create_tables.sql
-- Enterprise Retail Intelligence & Decision Engine
-- Phase 6: MySQL Database
--
-- Creates staging tables (stg_*) for raw data loads.
-- Tables mirror the cleaned CSV/Parquet structure exactly.
-- =============================================================================

USE enterprise_bi;

-- Drop in reverse FK dependency order
DROP TABLE IF EXISTS stg_order_products_train;
DROP TABLE IF EXISTS stg_order_products_prior;
DROP TABLE IF EXISTS stg_orders;
DROP TABLE IF EXISTS stg_products;
DROP TABLE IF EXISTS stg_aisles;
DROP TABLE IF EXISTS stg_departments;

-- ─────────────────────────────────────────────────────────────
-- STAGING: stg_departments
-- ─────────────────────────────────────────────────────────────
CREATE TABLE stg_departments (
    department_id   TINYINT UNSIGNED NOT NULL,
    department      VARCHAR(100)     NOT NULL,
    CONSTRAINT pk_stg_departments PRIMARY KEY (department_id)
) ENGINE=InnoDB
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci
  COMMENT='Staging: store departments (21 departments)';

-- ─────────────────────────────────────────────────────────────
-- STAGING: stg_aisles
-- ─────────────────────────────────────────────────────────────
CREATE TABLE stg_aisles (
    aisle_id        SMALLINT UNSIGNED NOT NULL,
    aisle           VARCHAR(200)      NOT NULL,
    CONSTRAINT pk_stg_aisles PRIMARY KEY (aisle_id)
) ENGINE=InnoDB
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci
  COMMENT='Staging: store aisles (134 aisles)';

-- ─────────────────────────────────────────────────────────────
-- STAGING: stg_products
-- ─────────────────────────────────────────────────────────────
CREATE TABLE stg_products (
    product_id      INT UNSIGNED      NOT NULL,
    product_name    VARCHAR(500)      NOT NULL,
    aisle_id        SMALLINT UNSIGNED NOT NULL,
    department_id   TINYINT UNSIGNED  NOT NULL,
    CONSTRAINT pk_stg_products PRIMARY KEY (product_id),
    CONSTRAINT fk_products_aisle      FOREIGN KEY (aisle_id)      REFERENCES stg_aisles(aisle_id),
    CONSTRAINT fk_products_department FOREIGN KEY (department_id) REFERENCES stg_departments(department_id)
) ENGINE=InnoDB
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci
  COMMENT='Staging: products (49,688 products)';

-- ─────────────────────────────────────────────────────────────
-- STAGING: stg_orders
-- ─────────────────────────────────────────────────────────────
CREATE TABLE stg_orders (
    order_id                INT UNSIGNED      NOT NULL,
    user_id                 INT UNSIGNED      NOT NULL,
    eval_set                ENUM('prior','train','test') NOT NULL,
    order_number            SMALLINT UNSIGNED NOT NULL,
    order_dow               TINYINT UNSIGNED  NOT NULL  COMMENT '0=Saturday, 1=Sunday, ..., 6=Friday',
    order_hour_of_day       TINYINT UNSIGNED  NOT NULL  COMMENT '0-23',
    days_since_prior_order  DECIMAL(5,1)      NULL       COMMENT 'NULL for first order per user',
    is_first_order          TINYINT(1)        NOT NULL   DEFAULT 0,
    CONSTRAINT pk_stg_orders PRIMARY KEY (order_id),
    CONSTRAINT chk_order_dow  CHECK (order_dow  BETWEEN 0 AND 6),
    CONSTRAINT chk_order_hour CHECK (order_hour_of_day BETWEEN 0 AND 23),
    CONSTRAINT chk_days_prior CHECK (days_since_prior_order IS NULL OR days_since_prior_order BETWEEN 0 AND 30)
) ENGINE=InnoDB
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci
  COMMENT='Staging: orders (3.4M orders)';

-- ─────────────────────────────────────────────────────────────
-- STAGING: stg_order_products_prior
-- ─────────────────────────────────────────────────────────────
CREATE TABLE stg_order_products_prior (
    order_id          INT UNSIGNED      NOT NULL,
    product_id        INT UNSIGNED      NOT NULL,
    add_to_cart_order SMALLINT UNSIGNED NOT NULL,
    reordered         TINYINT(1)        NOT NULL,
    CONSTRAINT pk_stg_opp PRIMARY KEY (order_id, product_id),
    CONSTRAINT chk_opp_reordered CHECK (reordered IN (0,1))
) ENGINE=InnoDB
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci
  COMMENT='Staging: prior order-product lines (32.4M rows)';

-- ─────────────────────────────────────────────────────────────
-- STAGING: stg_order_products_train
-- ─────────────────────────────────────────────────────────────
CREATE TABLE stg_order_products_train (
    order_id          INT UNSIGNED      NOT NULL,
    product_id        INT UNSIGNED      NOT NULL,
    add_to_cart_order SMALLINT UNSIGNED NOT NULL,
    reordered         TINYINT(1)        NOT NULL,
    CONSTRAINT pk_stg_opt PRIMARY KEY (order_id, product_id),
    CONSTRAINT chk_opt_reordered CHECK (reordered IN (0,1))
) ENGINE=InnoDB
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci
  COMMENT='Staging: train order-product lines (1.38M rows)';

-- Confirm tables created
SHOW TABLES;
