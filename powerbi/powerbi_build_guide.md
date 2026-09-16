# Power BI Desktop Dashboard Build Guide
**Enterprise Retail Intelligence & Decision Engine**

This build guide outlines the exact layout, visuals, configurations, and DAX measures required to assemble the 7-page executive portfolio report in Power BI Desktop.

---

## 1. Connecting Data to Power BI Desktop

### Option A: Direct MySQL 8.4 Connection (Full 37M Rows)
1. Open **Power BI Desktop**.
2. Click **Get Data** → **MySQL database**.
3. Server: `localhost:3306` | Database: `enterprise_bi`.
4. Select Data Connectivity mode: **Import** or **DirectQuery**.
5. Select the 6 tables: `dim_departments`, `dim_aisles`, `dim_products`, `fact_orders`, `fact_order_items_train`, `fact_order_items_prior` (or the views in `07_views.sql`).

### Option B: Optimized CSV Import (Fast & Lightweight)
Run the automated exporter script from your terminal:
```bash
python powerbi/export_powerbi_data.py
```
This writes star-schema CSV tables directly into `powerbi/data/`. In Power BI Desktop:
1. Click **Get Data** → **Text/CSV** or **Folder** (`powerbi/data/`).
2. Load all CSVs into the model.

---

## 2. Setting Relationships (Model View)

Navigate to the **Model View** tab in Power BI Desktop and create the following single-direction relationships:

| From Table | Column | To Table | Column | Cardinality | Cross Filter |
|------------|--------|----------|--------|-------------|--------------|
| `fact_order_items` | `order_id` | `fact_orders` | `order_id` | Many-to-One (`* : 1`) | Single |
| `fact_order_items` | `product_id` | `dim_products` | `product_id` | Many-to-One (`* : 1`) | Single |
| `dim_products` | `department_id` | `dim_departments` | `department_id` | Many-to-One (`* : 1`) | Single |
| `dim_products` | `aisle_id` | `dim_aisles` | `aisle_id` | Many-to-One (`* : 1`) | Single |
| `fact_orders` | `user_id` | `dim_customers` | `user_id` | Many-to-One (`* : 1`) | Single |

---

## 3. Page-by-Page Visual Construction

### PAGE 1 — EXECUTIVE OVERVIEW
*Objective: High-level business health summary and top-line operational metrics.*

#### KPI Cards (Header Row):
- **Card 1**: `[Total Orders]` (Format: 3.42M)
- **Card 2**: `[Total Items Purchased]` (Format: 33.8M)
- **Card 3**: `[Unique Customers]` (Format: 206K)
- **Card 4**: `[Reorder Rate]` (Format: 59.9%)
- **Card 5**: `[Average Basket Size]` (Format: 10.1 items)
- **Card 6**: `[Average Orders per Customer]` (Format: 16.6)

#### Visuals:
1. **Area / Line Chart — Order Velocity by Hour**:
   - X-Axis: `fact_orders[order_hour_of_day]` (0 to 23)
   - Y-Axis: `[Total Orders]`
   - Visual Cue: Peak bell-curve between 10:00 AM and 4:00 PM.
2. **Bar Chart — Top 10 Departments by Order Volume**:
   - Y-Axis: `dim_departments[department]`
   - X-Axis: `[Total Items Purchased]`
   - Data labels enabled (Produce & Dairy account for >50% of items).
3. **Donut Chart — Reorder vs First-Time Split**:
   - Legend: `Reorder Status` (Reordered vs First Purchase)
   - Values: `[Total Items Purchased]`
4. **Table / Bar Chart — Top 10 Products Overall**:
   - Columns: `dim_products[product_name]`, `[Total Items Purchased]`, `[Reorder Rate]`
   - Top items: Banana, Bag of Organic Bananas, Organic Strawberries.

---

### PAGE 2 — CUSTOMER INTELLIGENCE
*Objective: Customer order frequencies, repurchase cadence, and customer segmentation.*

#### Visuals:
1. **Histogram / Column Chart — Customer Order Frequency**:
   - X-Axis: `dim_customers[total_orders]` (binned 4-100)
   - Y-Axis: `[Unique Customers]`
2. **Donut / Pie Chart — Customer Segment Distribution**:
   - Legend: `dim_customers[cluster_name]` (Occasional Buyers: 57.7%, Loyal Regulars: 42.3%)
   - Values: `[Unique Customers]`
3. **Scatter Plot — Basket Size vs Reorder Rate**:
   - X-Axis: `dim_customers[avg_basket_size]`
   - Y-Axis: `dim_customers[user_reorder_rate]`
   - Legend: `dim_customers[cluster_name]`
4. **KPI Cards**:
   - `[Average Days Between Orders]`: 15.4 Days
   - `[Loyal Customer Share]`: 42.3%

---

### PAGE 3 — PRODUCT INTELLIGENCE
*Objective: SKU-level performance, velocity, and add-to-cart prioritization.*

#### Slicers:
- Dropdown Slicer: `dim_departments[department]`
- Dropdown Slicer: `dim_aisles[aisle]`
- Search bar: `dim_products[product_name]`

#### Visuals:
1. **Matrix Grid — Product Scorecard**:
   - Rows: `dim_products[product_name]`
   - Values: `[Total Items Purchased]`, `[Reorder Rate]`, `[Product Rank by Volume]`
2. **Horizontal Bar Chart — Highest Reorder Rate Products**:
   - Y-Axis: `dim_products[product_name]` (Filtered to min 500 orders)
   - X-Axis: `[Reorder Rate]`
   - Highlights: Organic Milk, Sparkling Waters, Fresh Produce (>75% reorders).
3. **Line Chart — Reorder Rate by Add-to-Cart Position**:
   - X-Axis: `fact_order_items[add_to_cart_order]` (1 to 20)
   - Y-Axis: `[Reorder Rate]`
   - Insight: Position 1-3 items show ~70% reorder rate vs ~40% for position 20+.

---

### PAGE 4 — DEPARTMENT & AISLE ANALYTICS
*Objective: Merchandising mix, category contribution, and aisle cross-shopping.*

#### Visuals:
1. **Treemap — Department Volume Share**:
   - Group: `dim_departments[department]`
   - Values: `[Total Items Purchased]`
2. **Clustered Bar Chart — Aisle Volume vs Reorder Rate**:
   - Y-Axis: `dim_aisles[aisle]` (Top 25 Aisles)
   - X-Axis: `[Total Items Purchased]`
   - Color Saturation: `[Reorder Rate]`
3. **Decomposition Tree / Hierarchy**:
   - Analyze: `[Total Items Purchased]`
   - Explain by: `dim_departments[department]` → `dim_aisles[aisle]` → `dim_products[product_name]`

---

### PAGE 5 — TIME & OPERATIONS
*Objective: Warehouse logistics, delivery fleet staffing, and intraday demand.*

#### Visuals:
1. **Matrix / Heatmap — Orders by Day of Week & Hour**:
   - Rows: `Day Name` (Sunday to Saturday)
   - Columns: `Hour of Day` (0 to 23)
   - Values: `[Total Orders]`
   - Conditional Formatting: Background color scale (White to Deep Navy).
2. **Column Chart — Orders by Day of Week**:
   - X-Axis: `Day of Week`
   - Y-Axis: `[Total Orders]`
   - Insight: Sunday (Day 0) and Monday (Day 1) represent 35% of weekly volume.
3. **Gauge / KPI Card — Weekend Order Share**:
   - Value: `[Weekend vs Weekday Ratio]`

---

### PAGE 6 — MARKET BASKET & CROSS-SELLING
*Objective: Association rule mining for bundle merchandising and cart recommendations.*

#### Slicers:
- Slider: `Min Lift` (1.0 to 6.0)
- Slider: `Min Confidence` (0.05 to 0.50)

#### Visuals:
1. **Table / Matrix — Top Association Rules**:
   - Columns: `Product A (Antecedent)`, `Product B (Consequent)`, `Support`, `Confidence`, `Lift`
   - Key Insight: Limes → Large Cilantro (Lift = 5.78, Confidence = 24.3%).
2. **Scatter Chart — Support vs Confidence**:
   - X-Axis: `Support`
   - Y-Axis: `Confidence`
   - Size: `Lift`
   - Tooltips: `Product Pair`

---

### PAGE 7 — ML & DECISION SUPPORT
*Objective: Executive model performance, feature importance, and revenue impact.*

#### KPI Cards (Model Health):
- **ROC-AUC**: `0.792`
- **Model F1-Score**: `0.784`
- **Model Accuracy**: `72.7%`
- **Precision / Recall**: `73.0% / 84.6%`

#### Visuals:
1. **Bar Chart — Feature Importance (Random Forest)**:
   - Features ranked by impact: `product_reorder_rate`, `user_reorder_rate`, `user_total_orders`, `add_to_cart_order`, `user_avg_basket_size`.
2. **Waterfall / Scenario Simulator — Strategic Revenue Levers**:
   - Base Revenue → Loyalty Uplift (+5%) → Cross-Sell Basket Uplift (+1 item) → Projected Revenue.
3. **Executive Action Matrix**:
   - Table outlining prioritized merchandising decisions based on model findings.
