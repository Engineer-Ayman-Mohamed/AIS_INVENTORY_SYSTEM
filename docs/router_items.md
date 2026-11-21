# Module Documentation: `app/routers/items.py`

## 1. Executive Summary & Purpose
The [items.py](file:///E:/Enexabit/AIS_Inventory_system/app/routers/items.py) router manages the Item Master catalog (Stock Keeping Units - SKUs). It exposes full lifecycle operations (List, Create, Retrieve Layers, Update, and Delete) while enforcing data integrity rules and audit accountability.

---

## 2. AIS Cycle Phase: **Input & Master File Maintenance**
In the AIS cycle, the Item Master represents the central repository for product metadata, replenishment triggers, and current stock balances:
- **Catalog Standardization:** Standardizes SKU naming, product category grouping, and measurement units.
- **Stock Tracking:** Holds the live aggregate stock on hand and moving average unit cost.
- **Audit Logging:** Every modification or deletion is stamped into the immutable audit trail.

---

## 3. Endpoints & Operations

### 1. `GET /api/items`
- **Output:** List of `ItemResponse` objects sorted alphabetically by SKU.
- **Enrichment:** Calculates real-time valuations per item under FIFO, WAC, and LIFO, alongside the `is_low_stock` boolean flag (`current_stock <= reorder_level`).

### 2. `POST /api/items` (Status 201 Created)
- **Input:** `ItemCreate` payload.
- **Integrity Validation:** Enforces SKU uniqueness (case-insensitive check). Throws `400 Bad Request` if SKU already exists.
- **Opening Balance Handling:** If `initial_stock > 0` and `initial_cost > 0`:
  - Automatically initializes an opening `CostLayer` lot.
  - Automatically posts an opening `PURCHASE` transaction.
  - Sets initial `moving_avg_cost`.
- **Audit Stamping:** Writes a `CREATE_ITEM` event to `AuditLog`.

### 3. `GET /api/items/{item_id}/layers`
- **Output:** List of active `CostLayerResponse` objects for the specified SKU.
- **Purpose:** Exposes granular unconsumed purchase lots, displaying original quantities, remaining quantities, and distinct unit costs for FIFO/LIFO transparency.

### 4. `PUT /api/items/{item_id}`
- **Input:** `ItemUpdate` partial payload.
- **Function:** Selectively updates editable product metadata (name, category, unit of measure, reorder level, and selling price).
- **Audit Stamping:** Records an `UPDATE_ITEM` event detailing modified fields.

### 5. `DELETE /api/items/{item_id}`
- **Enforces Internal Control:** Strict historical integrity protection.
- **Rule:** If the SKU has any associated records in `Transaction`, deletion is **strictly blocked** with `400 Bad Request` ("Data Integrity Violation: SKU cannot be deleted because it possesses historical transactions").
- **Audit Stamping:** If eligible, removes item and records a `DELETE_ITEM` event.

---

## 4. Key Accounting & Internal Controls Enforced
- **SKU Uniqueness:** Prohibits duplicate stock codes to eliminate ambiguous ledger entries.
- **Referential & Audit Trail Integrity:** Hard block against deleting active or past inventory records preserves accounting ledger continuity.
- **Opening Balance Symmetry:** Synchronizes stock balance, moving average cost, cost layer creation, and audit trails simultaneously when creating items with initial inventory.

---

## 5. Module Dependencies & Interconnections
- **Upstream:**
  - [database.py](file:///E:/Enexabit/AIS_Inventory_system/app/database.py): Session provider `Depends(get_db)`.
  - [models.py](file:///E:/Enexabit/AIS_Inventory_system/app/models.py): Reads and mutates `Item`, `CostLayer`, `Transaction`, `AuditLog`.
  - [schemas.py](file:///E:/Enexabit/AIS_Inventory_system/app/schemas.py): Validates inputs (`ItemCreate`, `ItemUpdate`) and formats outputs (`ItemResponse`, `CostLayerResponse`).
  - [accounting.py](file:///E:/Enexabit/AIS_Inventory_system/app/accounting.py): Calls `compute_item_valuation_by_method()`.
  - [config.py](file:///E:/Enexabit/AIS_Inventory_system/app/config.py): Sources operator name for audit stamping.
- **Downstream:**
  - Mounted onto the FastAPI application in [main.py](file:///E:/Enexabit/AIS_Inventory_system/app/main.py).
