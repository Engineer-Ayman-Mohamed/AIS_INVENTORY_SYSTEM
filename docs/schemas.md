# Module Documentation: `app/schemas.py`

## 1. Executive Summary & Purpose
The [schemas.py](file:///E:/Enexabit/AIS_Inventory_system/app/schemas.py) module defines the Pydantic data schemas governing input validation, data integrity enforcement, and serialization for all API request payloads and responses. It acts as the boundary gateway protecting the core database from malformed accounting entries.

---

## 2. AIS Cycle Phase: **Input Validation & Data Integrity**
A cardinal principle of an Accounting Information System (AIS) is "Garbage In, Garbage Out" prevention. [schemas.py](file:///E:/Enexabit/AIS_Inventory_system/app/schemas.py) operationalizes strict field-level boundary rules:
- **Strictly Positive Quantities:** Blocks zero or negative acquisition and sales transactions at the schema layer before reaching database transactions.
- **Price & Cost Positivity:** Enforces non-negative sales prices and acquisition costs ($>0.0$ for purchases, $\ge 0.0$ for sales).
- **String Boundary Constraints:** Enforces min/max lengths on SKUs, product names, vendor identities, and audit notes.

---

## 3. Schema Structure & Key Classes

### 1. Item Master Schemas
- **`ItemBase(BaseModel)`**: Shared fields (`sku`, `name`, `category`, `unit_of_measure`, `reorder_level >= 0.0`, `selling_price >= 0.0`).
- **`ItemCreate(ItemBase)`**: Adds optional opening balance parameters:
  - `initial_stock: float` ($\ge 0.0$)
  - `initial_cost: float` ($\ge 0.0$)
- **`ItemUpdate(BaseModel)`**: Partial update fields (all fields optional for atomic updates).
- **`ItemResponse(ItemBase)`**: Complete item representation with database timestamps and calculated metrics:
  - `current_stock`, `moving_avg_cost`, `created_at`, `updated_at`
  - Dynamic indicators: `is_low_stock: bool`, `fifo_value: float`, `wac_value: float`, `lifo_value: float`
- **`CostLayerResponse(BaseModel)`**: Serialization schema for individual cost lots.

### 2. Transaction Schemas
- **`GoodsInCreate(BaseModel)`**:
  - `item_id: int`
  - `quantity: float` (Field constraint: `gt=0.0`)
  - `unit_cost: float` (Field constraint: `gt=0.0`)
  - `supplier: str` (1 to 100 characters)
  - `reference: str` (PO voucher)
  - `operator: Optional[str]`
- **`GoodsOutCreate(BaseModel)`**:
  - `item_id: int`
  - `quantity: float` (Field constraint: `gt=0.0`)
  - `selling_price: Optional[float]` ($\ge 0.0$; defaults to Item catalog price if omitted)
  - `customer: str` (1 to 100 characters)
  - `reference: str` (Invoice voucher)
  - `operator: Optional[str]`
- **`TransactionResponse(BaseModel)`**: Complete transaction payload including perpetual COGS derivations (`cogs_fifo`, `cogs_wac`, `cogs_lifo`) and item SKU/Name annotations.

### 3. Valuation & Financial Reporting Schemas
- **`ValuationItemDetail(BaseModel)`**: Per-SKU breakdown including:
  - Inventory volumes: `total_purchases_qty`, `total_sales_qty`, `goods_available_qty`
  - Accounting figures: `goods_available_cost`, `cogs`, `ending_inventory_value`
  - Performance KPIs: `revenue`, `gross_margin`, `gross_margin_pct`, `inventory_turnover`, `days_in_inventory`
- **`ValuationReportResponse(BaseModel)`**: Aggregate financial report for a chosen methodology (`FIFO`, `WAC`, `LIFO`) and system (`PERPETUAL`, `PERIODIC`), including aggregate metrics and compliance advisories (e.g. IAS 2 notice for LIFO).

### 4. Internal Controls & Audit Schemas
- **`ReconcileRequest(BaseModel)`**: Captures `item_id`, `physical_count >= 0.0`, `adjust_book_stock: bool`, and audit `notes`.
- **`PhysicalAuditResponse(BaseModel)`**: Reconciled record with `book_stock`, `physical_count`, `variance`, `variance_pct`, and `exceeds_threshold: bool`.
- **`ABCClassificationItem(BaseModel)`**: Pareto classification record detailing `usage_value`, `value_share_pct`, `cumulative_share_pct`, `abc_category` (A, B, or C), and `recommended_control`.
- **`AuditLogResponse(BaseModel)`**: Immutable audit trail event representation.

---

## 4. Key Accounting & Internal Controls Enforced
- **Input Validation Control:** Pydantic validators reject negative purchase costs or zero-quantity movements with automatic HTTP 422 Unprocessable Entity responses.
- **ORM Mode Compatibility:** Models use `from_attributes = True` (`ConfigDict` / `Config`) to serialize directly from SQLAlchemy model instances without manual dictionary translation.

---

## 5. Module Dependencies & Interconnections
- **Upstream:** Powered by `pydantic`.
- **Downstream Consumers:**
  - Injected as request bodies and response models across all router modules:
    - [routers/items.py](file:///E:/Enexabit/AIS_Inventory_system/app/routers/items.py)
    - [routers/goods_in.py](file:///E:/Enexabit/AIS_Inventory_system/app/routers/goods_in.py)
    - [routers/goods_out.py](file:///E:/Enexabit/AIS_Inventory_system/app/routers/goods_out.py)
    - [routers/valuation.py](file:///E:/Enexabit/AIS_Inventory_system/app/routers/valuation.py)
    - [routers/controls.py](file:///E:/Enexabit/AIS_Inventory_system/app/routers/controls.py)
