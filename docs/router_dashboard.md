# Module Documentation: `app/routers/dashboard.py`

## 1. Executive Summary & Purpose
The [dashboard.py](file:///E:/Enexabit/AIS_Inventory_system/app/routers/dashboard.py) router provides aggregated high-level business intelligence, operational metrics, and Chart.js visualization datasets. It condenses the real-time financial and physical state of inventory into actionable Key Performance Indicators (KPIs) for executive review.

---

## 2. AIS Cycle Phase: **Output & Managerial Reporting**
In the AIS cycle, the executive dashboard operationalizes the **Output** phase:
- Computes aggregate valuations across all three cost-flow methods simultaneously.
- Derives efficiency and activity ratios (Turnover Rate, Days Sales in Inventory).
- Feeds data visualization engines for category distributions and comparative valuation analyses.

---

## 3. Endpoints & Operations

### 1. `GET /api/dashboard/summary`
Returns comprehensive executive summary KPIs in real-time.

| KPI Field | Type | Description / Formula |
| :--- | :--- | :--- |
| `active_skus` | `int` | Total count of unique catalog items registered in the Item Master. |
| `total_units_in_stock` | `float` | Cumulative sum of all units currently on hand across all SKUs. |
| `low_stock_count` | `int` | Count of SKUs whose `current_stock <= reorder_level`. |
| `total_valuation_wac` | `float` | Cumulative balance sheet valuation under Weighted Average Cost. |
| `total_valuation_fifo` | `float` | Cumulative balance sheet valuation under First-In, First-Out. |
| `total_valuation_lifo` | `float` | Cumulative balance sheet valuation under Last-In, First-Out (simulated). |
| `total_revenue` | `float` | Cumulative sales revenue earned from all sales transactions. |
| `total_cogs` | `float` | Cumulative Cost of Goods Sold under WAC. |
| `gross_profit` | `float` | $\text{Total Revenue} - \text{Total COGS (WAC)}$ |
| `gross_margin_pct` | `float` | $(\text{Gross Profit} / \text{Total Revenue}) \times 100$ |
| `turnover_rate` | `float` | $\text{Total COGS} / \text{Ending Inventory (WAC)}$ |
| `days_in_inventory` | `float` | $365 / \text{Turnover Rate}$ (Average days to sell current inventory). |
| `total_purchases_val` | `float` | Cumulative acquisition expenditures for Goods In. |
| `total_transactions_count`| `int` | Total count of sales and purchase transactions processed. |

### 2. `GET /api/dashboard/charts`
Delivers structured payload ready for client-side Chart.js rendering:
- **`categories`**: Array of category names and their corresponding total inventory value ($\sum \text{Stock} \times \text{WAC}$).
- **`methods_comparison`**: Direct value comparison array between FIFO, WAC, and LIFO totals.
- **`recent_feed`**: Chronological stream of the latest 6 transactions (`PURCHASE` and `SALE`) showing SKU, product name, quantities, amounts, and formatted timestamps.

---

## 4. Key Accounting & Internal Controls Enforced
- **Real-Time Synthesis:** Unlike batch-processed legacy accounting systems, dashboard figures reflect instant ledger state upon every committed transaction.
- **Multi-Method Comparison:** Exposes valuation differences side-by-side, enabling managers to understand the balance sheet impact of cost-flow assumptions.
- **Division-by-Zero Safety:** Ratios (e.g., turnover rate, gross margin %) employ defensive guards against zero revenue or zero ending inventory.

---

## 5. Module Dependencies & Interconnections
- **Upstream:**
  - [database.py](file:///E:/Enexabit/AIS_Inventory_system/app/database.py): Injects database session via `Depends(get_db)`.
  - [models.py](file:///E:/Enexabit/AIS_Inventory_system/app/models.py): Queries `Item` and `Transaction` tables.
  - [accounting.py](file:///E:/Enexabit/AIS_Inventory_system/app/accounting.py): Invokes `compute_item_valuation_by_method()`.
- **Downstream:**
  - Mounted onto the root application in [main.py](file:///E:/Enexabit/AIS_Inventory_system/app/main.py).
  - Consumed by front-end dashboard cards and charting libraries.
