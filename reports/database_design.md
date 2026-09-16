# Enterprise Retail Intelligence & Decision Engine
## Database Design Report

**Generated:** 2026-09-17  
**Phase:** 6 — MySQL Database  
**MySQL Version:** 8.4.11

---

## 1. Database: enterprise_bi

| Property       | Value           |
|----------------|-----------------|
| Database Name  | enterprise_bi   |
| Character Set  | utf8mb4         |
| Collation      | utf8mb4_unicode_ci |
| Engine         | InnoDB          |
| MySQL Version  | 8.4.11 (Homebrew, arm64) |

---

## 2. Tables Created

| Table | Type | Rows | Description |
|-------|------|------|-------------|
| stg_departments | Staging/Dimension | 21 | Store departments reference |
| stg_aisles | Staging/Dimension | 134 | Store aisles reference |
| stg_products | Staging/Dimension | 49,688 | Product catalog |
| stg_orders | Staging/Fact | 3,421,083 | Customer orders |
| stg_order_products_prior | Staging/Fact | 32,434,489 | Prior basket transactions |
| stg_order_products_train | Staging/Fact | 1,384,617 | Train basket transactions |

---

## 3. Schema Design

### Staging Layer (stg_*)
All tables are prefixed `stg_` to denote they are staging tables — direct
mirrors of the cleaned source data. They serve dual purpose: staging for ETL
and primary analytical tables for this portfolio project.

### Why not separate DIM/FACT layers?
For this dataset, the stg_ tables already serve as clean analytical tables.
Creating a separate DIM/FACT copy would double storage with no analytical
benefit for this use case. Analytics views (vw_*) provide the dimensional
abstraction on top of the staging tables.

---

## 4. Primary Keys

| Table | Primary Key | Type | Notes |
|-------|-------------|------|-------|
| stg_departments | department_id | TINYINT UNSIGNED | 21 values (fits in 1 byte) |
| stg_aisles | aisle_id | SMALLINT UNSIGNED | 134 values |
| stg_products | product_id | INT UNSIGNED | 49,688 products |
| stg_orders | order_id | INT UNSIGNED | 3.4M orders |
| stg_order_products_prior | (order_id, product_id) | Composite | 32.4M rows |
| stg_order_products_train | (order_id, product_id) | Composite | 1.38M rows |

---

## 5. Foreign Keys

| Child Table | FK Column | Parent Table | Parent Column | Purpose |
|-------------|-----------|--------------|---------------|---------|
| stg_products | aisle_id | stg_aisles | aisle_id | Product → Aisle |
| stg_products | department_id | stg_departments | department_id | Product → Dept |

> **Note:** FK constraints to stg_orders from the order_products tables are
> not enforced at DB level (performance on 32M+ rows), but validated via
> Python validation script (validate_data.py) — all pass.

---

## 6. Indexes

### stg_orders Indexes

| Index Name | Column(s) | Rationale |
|-----------|-----------|-----------|
| PRIMARY | order_id | PK — clustered index |
| idx_orders_user_id | user_id | **Critical**: all customer queries filter on user_id |
| idx_orders_eval_set | eval_set | Frequent filter: prior vs train vs test |
| idx_orders_dow | order_dow | Time analysis queries |
| idx_orders_hour | order_hour_of_day | Hourly demand queries |
| idx_orders_user_ordernum | (user_id, order_number) | Customer order sequence queries |

### stg_products Indexes

| Index Name | Column(s) | Rationale |
|-----------|-----------|-----------|
| PRIMARY | product_id | PK |
| idx_products_department_id | department_id | Department drill-down joins |
| idx_products_aisle_id | aisle_id | Aisle-level queries |
| FK indexes | aisle_id, department_id | Auto-created by InnoDB for FK constraints |

### stg_order_products_prior Indexes

| Index Name | Column(s) | Rationale |
|-----------|-----------|-----------|
| PRIMARY | (order_id, product_id) | Composite PK |
| idx_opp_product_id | product_id | Product analytics — most critical query |
| idx_opp_reordered | reordered | Reorder analysis filter |
| idx_opp_product_reordered | (product_id, reordered) | Composite: reorder rate by product |

### stg_order_products_train Indexes

| Index Name | Column(s) | Rationale |
|-----------|-----------|-----------|
| PRIMARY | (order_id, product_id) | Composite PK |
| idx_opt_product_id | product_id | Product-level train analysis |
| idx_opt_reordered | reordered | Reorder analysis |

### Columns NOT indexed (and why)

| Column | Reason Not Indexed |
|--------|--------------------|
| stg_orders.order_number | Low cardinality benefit; accessed via user_id composite |
| stg_orders.days_since_prior_order | Range queries; full scans acceptable on this column |
| stg_products.product_name | VARCHAR; not used as join/filter key; full-text if needed |
| stg_order_products_prior.add_to_cart_order | Rarely filtered on directly |

---

## 7. Analytical Views

| View | Purpose |
|------|---------|
| vw_product_summary | Pre-aggregated product stats with rankings |
| vw_department_summary | Department-level aggregates and rankings |
| vw_aisle_summary | Aisle-level aggregates |
| vw_customer_summary | Per-customer behavioral summary |
| vw_time_summary | Orders by day×hour with basket stats |
| vw_top_products | Top products with department rankings |

---

## 8. Data Type Decisions

| Column | MySQL Type | Rationale |
|--------|-----------|-----------|
| department_id | TINYINT UNSIGNED | 21 values; saves 3 bytes vs INT |
| aisle_id | SMALLINT UNSIGNED | 134 values; saves 2 bytes vs INT |
| order_dow | TINYINT UNSIGNED | Values 0–6; 1 byte sufficient |
| order_hour_of_day | TINYINT UNSIGNED | Values 0–23; 1 byte |
| days_since_prior_order | DECIMAL(5,1) | NULL-able; preserves precision |
| eval_set | ENUM('prior','train','test') | Only 3 known values; saves space + enforces validity |
| reordered | TINYINT(1) | Boolean 0/1; minimum storage |
| is_first_order | TINYINT(1) DEFAULT 0 | Derived flag; fast boolean filter |

---

## 9. Constraints

### CHECK Constraints (MySQL 8.0.16+)
```sql
-- stg_orders
CHECK (order_dow BETWEEN 0 AND 6)
CHECK (order_hour_of_day BETWEEN 0 AND 23)
CHECK (days_since_prior_order IS NULL OR days_since_prior_order BETWEEN 0 AND 30)

-- stg_order_products_prior / train
CHECK (reordered IN (0, 1))
```

---

*Report generated during Phase 6 — Database Design*
