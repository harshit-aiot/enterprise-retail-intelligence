# Enterprise Retail Intelligence & Decision Engine
## Data Dictionary

**Generated:** 2026-09-17  
**Phase:** 3 — Data Understanding  
**Source Dataset:** Instacart Market Basket Analysis (Kaggle, 2017)

---

## Entity Relationship Overview

```
departments (1)
    └──< products (M)
            └──< order_products__prior (M)
            └──< order_products__train (M)

aisles (1)
    └──< products (M)

orders (1)
    └──< order_products__prior (M)
    └──< order_products__train (M)

users (implicit — via orders.user_id)
    └──< orders (M)
```

**Relationship Summary:**

| Relationship | Type | FK Column | Notes |
|---|---|---|---|
| departments → products | One-to-Many | products.department_id | Each product belongs to one department |
| aisles → products | One-to-Many | products.aisle_id | Each product belongs to one aisle |
| orders → order_products__prior | One-to-Many | order_id | Prior basket transactions |
| orders → order_products__train | One-to-Many | order_id | Train basket transactions |
| products → order_products__prior | One-to-Many | product_id | Products in prior orders |
| products → order_products__train | One-to-Many | product_id | Products in train orders |

**Note on eval_set:** orders.eval_set ∈ {prior, train, test}  
- `prior` orders → joined to order_products__prior  
- `train` orders → joined to order_products__train  
- `test` orders → no product detail available (held out by Instacart)

---

## Table 1: `aisles`

**Purpose:** Reference table of store aisles. Each aisle belongs to a department (inferred via products).  
**Rows:** 134  
**Primary Key:** `aisle_id`

| Column | dtype | PK | FK | Nullable | Business Meaning | Example |
|--------|-------|----|----|----------|-----------------|---------|
| `aisle_id` | int16 | ✅ | — | No | Unique integer identifier for the aisle | `1` |
| `aisle` | category | — | — | No | Human-readable aisle name | `"prepared soups salads"` |

**Notes:**
- 134 unique aisles confirmed
- No missing values
- No duplicates
- No direct department_id column — department is inferred via products table

---

## Table 2: `departments`

**Purpose:** Reference table of store departments. Top-level category hierarchy.  
**Rows:** 21  
**Primary Key:** `department_id`

| Column | dtype | PK | FK | Nullable | Business Meaning | Example |
|--------|-------|----|----|----------|-----------------|---------|
| `department_id` | int8 | ✅ | — | No | Unique integer identifier for the department | `1` |
| `department` | category | — | — | No | Human-readable department name | `"frozen"` |

**Notes:**
- 21 unique departments confirmed
- No missing values
- No duplicates

---

## Table 3: `products`

**Purpose:** Reference/dimension table of all products sold. Links to aisles and departments.  
**Rows:** 49,688  
**Primary Key:** `product_id`  
**Foreign Keys:** `aisle_id` → aisles.aisle_id | `department_id` → departments.department_id

| Column | dtype | PK | FK | Nullable | Business Meaning | Example |
|--------|-------|----|----|----------|-----------------|---------|
| `product_id` | int32 | ✅ | — | No | Unique integer identifier for the product | `1` |
| `product_name` | object | — | — | No | Full product name string | `"Chocolate Sandwich Cookies"` |
| `aisle_id` | int16 | — | ✅ aisles | No | The aisle this product belongs to | `61` |
| `department_id` | int8 | — | ✅ departments | No | The department this product belongs to | `19` |

**Notes:**
- 49,688 unique products confirmed
- No missing values in any column
- No duplicate product_ids
- product_name is free text — may contain special characters, varying capitalization
- No product price, cost, or SKU information available in the dataset
- FK integrity to aisles and departments: 100% valid (0 orphans)

---

## Table 4: `orders`

**Purpose:** Fact table of customer orders. One row per order. Links customers to their order history.  
**Rows:** 3,421,083  
**Primary Key:** `order_id`

| Column | dtype | PK | FK | Nullable | Business Meaning | Example |
|--------|-------|----|----|----------|-----------------|---------|
| `order_id` | int32 | ✅ | — | No | Unique integer identifier for the order | `2539329` |
| `user_id` | int32 | — | — | No | Unique customer identifier (implicit FK to user dimension) | `1` |
| `eval_set` | category | — | — | No | Dataset partition: `prior`, `train`, or `test` | `"prior"` |
| `order_number` | int16 | — | — | No | Sequence number of this order for this customer (1 = first) | `1` |
| `order_dow` | int8 | — | — | No | Day of week the order was placed (0=Saturday, 1=Sunday, per Instacart convention) | `2` |
| `order_hour_of_day` | int8 | — | — | No | Hour of day (0–23) the order was placed | `8` |
| `days_since_prior_order` | float32 | — | — | **Yes** | Number of days since the customer's immediately preceding order. NULL for the customer's first-ever order | `15.0` |

**Notes:**
- 3,421,083 unique order_ids confirmed (PK is unique)
- 206,209 NULL values in `days_since_prior_order` (6.03%) — these are all first orders per user; this is EXPECTED and MEANINGFUL. Do not impute or drop.
- `order_dow` convention: 0 = Saturday, 1 = Sunday, 2 = Monday ... 6 = Friday (Instacart convention — confirmed from data patterns)
- `eval_set = test` orders have no corresponding rows in order_products tables — product details are withheld for competition
- 206,209 users have at least 1 order (equal to NULL count in days_since_prior_order)

**eval_set Distribution (from profiling):**
- `prior` — the vast majority of orders (historical basket data for training)
- `train` — one order per user designated for supervised learning target
- `test` — one order per user with no product details (competition holdout)

---

## Table 5: `order_products__prior`

**Purpose:** Transaction fact table. One row per product per order, for all `prior` orders. This is the primary analytical table.  
**Rows:** 32,434,489  
**Primary Key:** Composite (`order_id`, `product_id`)  
**Foreign Keys:** `order_id` → orders.order_id | `product_id` → products.product_id

| Column | dtype | PK | FK | Nullable | Business Meaning | Example |
|--------|-------|----|----|----------|-----------------|---------|
| `order_id` | int32 | ✅ (composite) | ✅ orders | No | The order this line item belongs to | `2` |
| `product_id` | int32 | ✅ (composite) | ✅ products | No | The product purchased in this line item | `33120` |
| `add_to_cart_order` | int16 | — | — | No | Position in which this product was added to the cart (1 = first added) | `1` |
| `reordered` | int8 | — | — | No | Binary flag: 1 = customer had ordered this product before, 0 = first time | `1` |

**Notes:**
- 32,434,489 rows — the largest file (551 MB)
- Composite PK (order_id + product_id) is unique — confirmed (0 duplicates)
- 0 missing values in any column
- FK to orders: 100% valid
- FK to products: 100% valid
- `reordered` values are 0 or 1 only
- `add_to_cart_order` starts at 1 for each order

---

## Table 6: `order_products__train`

**Purpose:** Transaction fact table for `train` set orders. One row per product per order. Used as supervised learning target alongside prior order history.  
**Rows:** 1,384,617  
**Primary Key:** Composite (`order_id`, `product_id`)  
**Foreign Keys:** `order_id` → orders.order_id | `product_id` → products.product_id

| Column | dtype | PK | FK | Nullable | Business Meaning | Example |
|--------|-------|----|----|----------|-----------------|---------|
| `order_id` | int32 | ✅ (composite) | ✅ orders | No | The order this line item belongs to | `1` |
| `product_id` | int32 | ✅ (composite) | ✅ products | No | The product purchased | `49302` |
| `add_to_cart_order` | int16 | — | — | No | Cart add sequence position | `1` |
| `reordered` | int8 | — | — | No | 1 = previously ordered, 0 = new product for this customer | `1` |

**Notes:**
- 1,384,617 rows — the train basket for supervised ML
- Composite PK is unique — confirmed
- 0 missing values
- FK to orders: 100% valid
- FK to products: 100% valid
- Structure is identical to order_products__prior

---

## Data Model Diagram (Conceptual)

```
┌─────────────┐         ┌───────────────┐
│ departments │◄────────│   products    │
│─────────────│  dept   │───────────────│
│department_id│  FK     │product_id  PK │
│department   │         │product_name   │
└─────────────┘         │aisle_id    FK │
                        │department_id  │
┌─────────────┐         └───────┬───────┘
│   aisles    │◄────────────────┘
│─────────────│  aisle FK
│aisle_id  PK │
│aisle        │
└─────────────┘

┌─────────────┐         ┌────────────────────────────┐
│   orders    │◄────────│   order_products__prior     │
│─────────────│  ord    │────────────────────────────│
│order_id  PK │  FK     │order_id    FK (composite PK)│
│user_id      │         │product_id  FK (composite PK)│
│eval_set     │         │add_to_cart_order            │
│order_number │         │reordered                    │
│order_dow    │         └────────────────────────────┘
│order_hour...|
│days_since.. │         ┌────────────────────────────┐
└─────────────┘◄────────│   order_products__train    │
                        │────────────────────────────│
                        │order_id    FK (composite PK)│
                        │product_id  FK (composite PK)│
                        │add_to_cart_order            │
                        │reordered                    │
                        └────────────────────────────┘
```

---

## Data Confirmed NOT Available

The following are **not present** in the source data and must never be fabricated:

| Field | Status |
|-------|--------|
| Product price / cost | ❌ Not available |
| Revenue / sales value | ❌ Not available |
| Customer age / gender | ❌ Not available |
| Customer location | ❌ Not available |
| Store location | ❌ Not available |
| Inventory quantities | ❌ Not available |
| Actual timestamps | ❌ Only DOW + hour available |
| Payment method | ❌ Not available |
| Discounts / promotions | ❌ Not available |

---

*Report generated during Phase 3 — Data Understanding*  
*All facts verified against actual CSV files — no assumptions made.*
