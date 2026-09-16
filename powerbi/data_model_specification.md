# Power BI Star Schema Data Model Specification
**Enterprise Retail Intelligence & Decision Engine**

---

## 1. Overview
The analytical data model in Power BI follows a **Star Schema** architecture optimized for fast in-memory DAX queries, cross-filtering, and executive reporting.

```
                    ┌─────────────────┐
                    │ dim_departments │
                    └────────┬────────┘
                             │ 1
                             │
                             │ *
                    ┌────────┴────────┐
                    │  dim_aisles     │
                    └────────┬────────┘
                             │ 1
                             │
                             │ *
┌───────────────┐   ┌────────┴────────┐
│ dim_customers │   │  dim_products   │
└───────┬───────┘   └────────┬────────┘
        │ 1                  │ 1
        │                    │
        │ *                  │ *
┌───────┴────────────────────┴────────┐
│        fact_order_items             │
└────────────────┬────────────────────┘
                 │ *
                 │
                 │ 1
        ┌────────┴────────┐
        │   fact_orders   │
        └────────┬────────┘
                 │ *
                 │
                 │ 1
        ┌────────┴────────┐
        │    dim_time     │
        └─────────────────┘
```

---

## 2. Table Specifications

### Fact Tables
1. **`fact_order_items`**:
   - **Grain**: One row per product per customer order.
   - **Columns**: `order_id` (FK), `product_id` (FK), `add_to_cart_order` (Integer), `reordered` (0/1 Flag).
   - **Relationships**:
     - `fact_order_items[order_id]` Many-to-One (`* : 1`) `fact_orders[order_id]`
     - `fact_order_items[product_id]` Many-to-One (`* : 1`) `dim_products[product_id]`

2. **`fact_orders`**:
   - **Grain**: One row per customer order header.
   - **Columns**: `order_id` (PK), `user_id` (FK), `eval_set` (String), `order_number` (Integer), `order_dow` (0..6), `order_hour_of_day` (0..23), `days_since_prior_order` (Float/Int).
   - **Relationships**:
     - `fact_orders[user_id]` Many-to-One (`* : 1`) `dim_customers[user_id]`
     - `fact_orders[order_hour_of_day]` Many-to-One (`* : 1`) `dim_time[hour_of_day]`

3. **`fact_market_basket`**:
   - **Grain**: One row per frequent itemset association rule.
   - **Columns**: `product_a` (String), `product_b` (String), `support` (Float), `confidence_a_to_b` (Float), `confidence_b_to_a` (Float), `lift` (Float).

---

### Dimension Tables
1. **`dim_products`**:
   - **Columns**: `product_id` (PK), `product_name` (String), `aisle_id` (FK), `department_id` (FK).
   - **Role**: Conformed product dimension providing SKU descriptions and hierarchy.

2. **`dim_departments`**:
   - **Columns**: `department_id` (PK), `department` (String).
   - **Role**: Top-level retail merchandise classification (21 categories).

3. **`dim_aisles`**:
   - **Columns**: `aisle_id` (PK), `aisle` (String).
   - **Role**: Category sub-tier location (134 aisles).

4. **`dim_customers`**:
   - **Columns**: `user_id` (PK), `total_orders`, `total_items`, `avg_basket_size`, `user_reorder_rate`, `cluster_name` ('Loyal Regulars' vs 'Occasional Buyers').
   - **Role**: Customer behavioral attributes and ML segmentation segments.

5. **`dim_time`**:
   - **Columns**: `hour_of_day` (0..23), `time_bucket` ('Morning', 'Afternoon', 'Evening', 'Night'), `peak_flag` (Yes/No).

---

## 3. Storage Mode Recommendations
- **Recommended**: **Import Mode** with aggregated dataset or pre-filtered fact items (via Power Query or Python export script) to ensure sub-second report interactivity and offline portability.
- **DirectQuery Mode**: Supported when pointing Power BI Desktop directly to the local MySQL 8.4 server `enterprise_bi` via ODBC or MySQL Connector/NET.
