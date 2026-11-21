# Module Documentation: `seed_data.py`

## 1. Executive Summary & Purpose
The [seed_data.py](file:///E:/Enexabit/AIS_Inventory_system/seed_data.py) script serves as the database initialization and demonstration seeder for the AIS Inventory Management & Valuation System. It constructs a complete, realistic accounting history featuring retail electronic SKUs, staggered purchases with inflationary cost layers, sales transactions with perpetual COGS derivation, a physical stock reconciliation that triggers the 2% tolerance threshold, and an audit trail.

---

## 2. AIS Cycle Phase: **Demonstration & Verification Baseline**
In the AIS cycle, the seed script establishes a verifiable dataset to audit system logic:
- Verifies cost-layer depletion order under FIFO vs LIFO.
- Validates the dynamic Weighted Average Cost calculation across multiple acquisition batches.
- Provides sample transactions across categories for Chart.js and executive KPI visualization.
- Exercises internal controls (reorder triggers, reconciliation tolerance breaches).

---

## 3. Seed Execution & Data Composition

### Execution
```powershell
python seed_data.py
```
*Idempotency Guard:* The script first counts existing `Item` records; if records exist, it skips execution to avoid corrupting existing ledgers.

### 1. Catalog Master Items (6 SKUs)
| SKU | Name | Category | Unit | Reorder Level | Selling Price |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `SKU-KEY-01` | RGB Wireless Mechanical Keyboard | Electronics | Unit | 15.0 | $89.99 |
| `SKU-MOU-02` | Precision Ergonomic Optical Mouse | Electronics | Unit | 20.0 | $45.00 |
| `SKU-HUB-03` | 7-in-1 Multiport USB-C Hub | Accessories | Unit | 25.0 | $34.50 |
| `SKU-MON-04` | Ultra-Wide 27-inch 4K IPS Monitor | Displays | Unit | 8.0 | $289.00 |
| `SKU-HDS-05` | Noise-Cancelling Wireless Headset | Audio | Unit | 12.0 | $79.99 |
| `SKU-PAD-06` | Extended Desk Mat Waterproof | Accessories | Unit | 30.0 | $18.00 |

### 2. Purchase Plan & Inflationary Cost Layers
Staggers purchases across past dates with varying unit costs to highlight valuation divergences between FIFO and LIFO:
- `SKU-KEY-01`: Lot 1 (40 units @ $42.00) $\to$ Lot 2 (30 units @ $48.00)
- `SKU-MOU-02`: Lot 1 (50 units @ $20.00) $\to$ Lot 2 (40 units @ $24.00)
- `SKU-HUB-03`: Lot 1 (20 units @ $15.00) [Intentionally below reorder level of 25.0 to demonstrate low-stock alert]
- `SKU-MON-04`: Lot 1 (15 units @ $180.00) $\to$ Lot 2 (10 units @ $195.00)
- `SKU-HDS-05`: Lot 1 (30 units @ $38.00)
- `SKU-PAD-06`: Lot 1 (100 units @ $7.50)

### 3. Sales Transactions & Perpetual COGS
Executes representative sales against the inventory:
- `SKU-KEY-01`: 45 units sold. Depletes Lot 1 (40 units @ $42.00) and takes 5 units from Lot 2 (@ $48.00). FIFO COGS = $1,920.00.
- `SKU-MOU-02`: 35 units sold. Depletes 35 units from Lot 1 (@ $20.00). FIFO COGS = $700.00.
- `SKU-MON-04`: 8 units sold. Depletes 8 units from Lot 1 (@ $180.00). FIFO COGS = $1,440.00.

### 4. Physical Count Reconciliation Audit
- Audits `SKU-KEY-01`:
  - **Book Stock:** 25.0 units.
  - **Physical Count:** 23.0 units (Discrepancy: -2.0 units shrinkage).
  - **Variance Percentage:** $\frac{2.0}{25.0} \times 100 = 8.0\%$.
  - **Threshold Evaluation:** $8.0\% > 2.0\%$ tolerance limit $\implies$ `exceeds_threshold = True`.
  - Stamped into `PhysicalAudit` and adjusted in book stock.

---

## 4. Key Accounting & Internal Controls Enforced
- **Algorithmic Integrity:** Uses the production functions `update_moving_average_cost_on_purchase()`, `calculate_fifo_cogs_and_consume()`, and `calculate_lifo_cogs_simulated()` to ensure sample data precisely matches runtime API transactions.
- **Audit Logging Synchronization:** Stamps every creation, purchase, sale, and reconciliation into `AuditLog` using the default executive operator profile.

---

## 5. Module Dependencies & Interconnections
- **Upstream:**
  - [database.py](file:///E:/Enexabit/AIS_Inventory_system/app/database.py): Imports `SessionLocal` and `init_db`.
  - [models.py](file:///E:/Enexabit/AIS_Inventory_system/app/models.py): Instantiates `Item`, `CostLayer`, `Transaction`, `PhysicalAudit`, `AuditLog`.
  - [accounting.py](file:///E:/Enexabit/AIS_Inventory_system/app/accounting.py): Invokes core cost allocation engines.
  - [config.py](file:///E:/Enexabit/AIS_Inventory_system/app/config.py): Sources `settings.DEFAULT_OPERATOR`.
