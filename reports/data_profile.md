# Enterprise Retail Intelligence & Decision Engine
## Data Profile Report

**Generated:** 2026-09-17 02:49:21  
**Phase:** 2 — Dataset Profiling  

---

## Table: `aisles`

| Property          | Value |
|-------------------|-------|
| File              | `aisles.csv` |
| File Size         | 0.0 MB |
| Rows              | 134 |
| Columns           | 2 |
| Memory (in RAM)   | 0.008 MB |
| Full-row Dupes    | 0 |

### Columns & Data Types

| Column | dtype | Missing | Missing % | Unique Values |
|--------|-------|---------|-----------|---------------|
| `aisle_id` | int16 | 0 | 0.00% | 134 |
| `aisle` | category | 0 | 0.00% | 134 |

### Numeric Statistics

| Column | Min | Max | Mean | Median | Std | Q25 | Q75 |
|--------|-----|-----|------|--------|-----|-----|-----|
| `aisle_id` | 1.0 | 134.0 | 67.5 | 67.5 | 38.8265 | 34.25 | 100.75 |

### Categorical Top Values

**`aisle`:** `air fresheners candles` (1), `asian foods` (1), `baby accessories` (1), `baby bath body care` (1), `baby food formula` (1)

### Primary Key Check

| PK Column(s) | Duplicate Count | Status |
|---|---|---|
| `aisle_id` | 0 | ✅ UNIQUE |

---

## Table: `departments`

| Property          | Value |
|-------------------|-------|
| File              | `departments.csv` |
| File Size         | 0.0 MB |
| Rows              | 21 |
| Columns           | 2 |
| Memory (in RAM)   | 0.001 MB |
| Full-row Dupes    | 0 |

### Columns & Data Types

| Column | dtype | Missing | Missing % | Unique Values |
|--------|-------|---------|-----------|---------------|
| `department_id` | int8 | 0 | 0.00% | 21 |
| `department` | category | 0 | 0.00% | 21 |

### Numeric Statistics

| Column | Min | Max | Mean | Median | Std | Q25 | Q75 |
|--------|-----|-----|------|--------|-----|-----|-----|
| `department_id` | 1.0 | 21.0 | 11.0 | 11.0 | 6.2048 | 6.0 | 16.0 |

### Categorical Top Values

**`department`:** `alcohol` (1), `babies` (1), `bakery` (1), `beverages` (1), `breakfast` (1)

### Primary Key Check

| PK Column(s) | Duplicate Count | Status |
|---|---|---|
| `department_id` | 0 | ✅ UNIQUE |

---

## Table: `products`

| Property          | Value |
|-------------------|-------|
| File              | `products.csv` |
| File Size         | 2.07 MB |
| Rows              | 49,688 |
| Columns           | 4 |
| Memory (in RAM)   | 4.123 MB |
| Full-row Dupes    | 0 |

### Columns & Data Types

| Column | dtype | Missing | Missing % | Unique Values |
|--------|-------|---------|-----------|---------------|
| `product_id` | int32 | 0 | 0.00% | 49,688 |
| `product_name` | object | 0 | 0.00% | 49,688 |
| `aisle_id` | int16 | 0 | 0.00% | 134 |
| `department_id` | int8 | 0 | 0.00% | 21 |

### Numeric Statistics

| Column | Min | Max | Mean | Median | Std | Q25 | Q75 |
|--------|-----|-----|------|--------|-----|-----|-----|
| `product_id` | 1.0 | 49688.0 | 24844.5 | 24844.5 | 14343.8344 | 12422.75 | 37266.25 |
| `aisle_id` | 1.0 | 134.0 | 67.7696 | 69.0 | 38.3162 | 35.0 | 100.0 |
| `department_id` | 1.0 | 21.0 | 11.7287 | 13.0 | 5.8504 | 7.0 | 17.0 |

### Categorical Top Values

**`product_name`:** `Chocolate Sandwich Cookies` (1), `All-Seasons Salt` (1), `Robust Golden Unsweetened Oolong Tea` (1), `Smart Ones Classic Favorites Mini Rigatoni With Vodka Cream Sauce` (1), `Green Chile Anytime Sauce` (1)

### Primary Key Check

| PK Column(s) | Duplicate Count | Status |
|---|---|---|
| `product_id` | 0 | ✅ UNIQUE |

---

## Table: `orders`

| Property          | Value |
|-------------------|-------|
| File              | `orders.csv` |
| File Size         | 103.92 MB |
| Rows              | 3,421,083 |
| Columns           | 7 |
| Memory (in RAM)   | 55.464 MB |
| Full-row Dupes    | 0 |

### Columns & Data Types

| Column | dtype | Missing | Missing % | Unique Values |
|--------|-------|---------|-----------|---------------|
| `order_id` | int32 | 0 | 0.00% | 3,421,083 |
| `user_id` | int32 | 0 | 0.00% | 206,209 |
| `eval_set` | category | 0 | 0.00% | 3 |
| `order_number` | int16 | 0 | 0.00% | 100 |
| `order_dow` | int8 | 0 | 0.00% | 7 |
| `order_hour_of_day` | int8 | 0 | 0.00% | 24 |
| `days_since_prior_order` | float32 | 206,209 | 6.03% | 32 |

### Numeric Statistics

| Column | Min | Max | Mean | Median | Std | Q25 | Q75 |
|--------|-----|-----|------|--------|-----|-----|-----|
| `order_id` | 1.0 | 3421083.0 | 1710542.0 | 1710542.0 | 987581.7398 | 855271.5 | 2565812.5 |
| `user_id` | 1.0 | 206209.0 | 102978.2081 | 102689.0 | 59533.7178 | 51394.0 | 154385.0 |
| `order_number` | 1.0 | 100.0 | 17.1549 | 11.0 | 17.7332 | 5.0 | 23.0 |
| `order_dow` | 0.0 | 6.0 | 2.7762 | 3.0 | 2.0468 | 1.0 | 5.0 |
| `order_hour_of_day` | 0.0 | 23.0 | 13.452 | 13.0 | 4.2261 | 10.0 | 16.0 |
| `days_since_prior_order` | 0.0 | 30.0 | 11.1148 | 7.0 | 9.2067 | 4.0 | 15.0 |

### Categorical Top Values

**`eval_set`:** `prior` (3,214,874), `train` (131,209), `test` (75,000)

### Primary Key Check

| PK Column(s) | Duplicate Count | Status |
|---|---|---|
| `order_id` | 0 | ✅ UNIQUE |

---

## Table: `order_products__prior`

| Property          | Value |
|-------------------|-------|
| File              | `order_products__prior.csv` |
| File Size         | 550.8 MB |
| Rows              | 32,434,489 |
| Columns           | 4 |
| Memory (in RAM)   | 340.251 MB |
| Full-row Dupes    | 0 |

### Columns & Data Types

| Column | dtype | Missing | Missing % | Unique Values |
|--------|-------|---------|-----------|---------------|
| `order_id` | int32 | 0 | 0.00% | 3,214,874 |
| `product_id` | int32 | 0 | 0.00% | 49,677 |
| `add_to_cart_order` | int16 | 0 | 0.00% | 145 |
| `reordered` | int8 | 0 | 0.00% | 2 |

### Numeric Statistics

| Column | Min | Max | Mean | Median | Std | Q25 | Q75 |
|--------|-----|-----|------|--------|-----|-----|-----|
| `order_id` | 2.0 | 3421083.0 | 1710748.5189 | 1711048.0 | 987300.6965 | 855943.0 | 2565514.0 |
| `product_id` | 1.0 | 49688.0 | 25576.3375 | 25256.0 | 14096.6891 | 13530.0 | 37935.0 |
| `add_to_cart_order` | 1.0 | 145.0 | 8.3511 | 6.0 | 7.1267 | 3.0 | 11.0 |
| `reordered` | 0.0 | 1.0 | 0.5897 | 1.0 | 0.4919 | 0.0 | 1.0 |
### Primary Key Check

| PK Column(s) | Duplicate Count | Status |
|---|---|---|
| `order_id`, `product_id` | 0 | ✅ UNIQUE |

---

## Table: `order_products__train`

| Property          | Value |
|-------------------|-------|
| File              | `order_products__train.csv` |
| File Size         | 23.54 MB |
| Rows              | 1,384,617 |
| Columns           | 4 |
| Memory (in RAM)   | 14.525 MB |
| Full-row Dupes    | 0 |

### Columns & Data Types

| Column | dtype | Missing | Missing % | Unique Values |
|--------|-------|---------|-----------|---------------|
| `order_id` | int32 | 0 | 0.00% | 131,209 |
| `product_id` | int32 | 0 | 0.00% | 39,123 |
| `add_to_cart_order` | int16 | 0 | 0.00% | 80 |
| `reordered` | int8 | 0 | 0.00% | 2 |

### Numeric Statistics

| Column | Min | Max | Mean | Median | Std | Q25 | Q75 |
|--------|-----|-----|------|--------|-----|-----|-----|
| `order_id` | 1.0 | 3421070.0 | 1706297.6211 | 1701880.0 | 989732.6489 | 843370.0 | 2568023.0 |
| `product_id` | 1.0 | 49688.0 | 25556.2357 | 25298.0 | 14121.2724 | 13380.0 | 37940.0 |
| `add_to_cart_order` | 1.0 | 80.0 | 8.758 | 7.0 | 7.4239 | 3.0 | 12.0 |
| `reordered` | 0.0 | 1.0 | 0.5986 | 1.0 | 0.4902 | 0.0 | 1.0 |
### Primary Key Check

| PK Column(s) | Duplicate Count | Status |
|---|---|---|
| `order_id`, `product_id` | 0 | ✅ UNIQUE |

---

## Referential Integrity Checks

| Child Table | FK Column | Parent Table | Parent Column | Orphan Values | Status |
|-------------|-----------|--------------|---------------|---------------|--------|
| `products` | `aisle_id` | `aisles` | `aisle_id` | 0 | PASS |
| `products` | `department_id` | `departments` | `department_id` | 0 | PASS |
| `order_products__prior` | `order_id` | `orders` | `order_id` | 0 | PASS |
| `order_products__prior` | `product_id` | `products` | `product_id` | 0 | PASS |
| `order_products__train` | `order_id` | `orders` | `order_id` | 0 | PASS |
| `order_products__train` | `product_id` | `products` | `product_id` | 0 | PASS |

---

*Report generated by python/profile_dataset.py — Phase 2*
