"""
Pydantic Schemas for Request & Response Validation
Enforces input validation internal controls:
- Non-negative and non-zero quantities
- Positive costs and prices
- Standardized response payloads
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


# ==========================================
# Item Schemas
# ==========================================

class ItemBase(BaseModel):
    sku: str = Field(..., min_length=1, max_length=50, description="Unique Stock Keeping Unit Code")
    name: str = Field(..., min_length=1, max_length=120, description="Product Name")
    category: str = Field("General", max_length=60, description="Product Category")
    unit_of_measure: str = Field("Unit", max_length=20, description="Unit of Measure (Unit, Box, Kg)")
    reorder_level: float = Field(10.0, ge=0.0, description="Minimum inventory threshold for alerts")
    selling_price: float = Field(0.0, ge=0.0, description="Standard selling price")


class ItemCreate(ItemBase):
    initial_stock: float = Field(0.0, ge=0.0, description="Optional opening stock quantity")
    initial_cost: float = Field(0.0, ge=0.0, description="Unit cost for initial opening stock")


class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    category: Optional[str] = Field(None, max_length=60)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    reorder_level: Optional[float] = Field(None, ge=0.0)
    selling_price: Optional[float] = Field(None, ge=0.0)


class CostLayerResponse(BaseModel):
    id: int
    purchase_date: datetime
    original_quantity: float
    remaining_quantity: float
    unit_cost: float
    supplier: str
    reference: str

    class Config:
        from_attributes = True


class ItemResponse(ItemBase):
    id: int
    current_stock: float
    moving_avg_cost: float
    created_at: datetime
    updated_at: datetime
    
    # Dynamic valuation metrics
    is_low_stock: bool = False
    fifo_value: float = 0.0
    wac_value: float = 0.0
    lifo_value: float = 0.0

    class Config:
        from_attributes = True


# ==========================================
# Goods In (Purchases) Schemas
# ==========================================

class GoodsInCreate(BaseModel):
    item_id: int = Field(..., description="Target Item Master ID")
    quantity: float = Field(..., gt=0.0, description="Acquired quantity (must be strictly > 0)")
    unit_cost: float = Field(..., gt=0.0, description="Unit purchase cost (must be strictly > 0)")
    supplier: str = Field(..., min_length=1, max_length=100, description="Supplier Name")
    reference: str = Field("PO-Auto", max_length=100, description="Purchase Order or Invoice Ref")
    operator: Optional[str] = Field(None, description="Operator stamping the transaction")


# ==========================================
# Goods Out (Sales) Schemas
# ==========================================

class GoodsOutCreate(BaseModel):
    item_id: int = Field(..., description="Target Item Master ID")
    quantity: float = Field(..., gt=0.0, description="Sold quantity (must be strictly > 0)")
    selling_price: Optional[float] = Field(None, ge=0.0, description="Unit selling price (uses item default if omitted)")
    customer: str = Field(..., min_length=1, max_length=100, description="Customer Name")
    reference: str = Field("INV-Auto", max_length=100, description="Sales Invoice Ref")
    operator: Optional[str] = Field(None, description="Operator stamping the transaction")


class TransactionResponse(BaseModel):
    id: int
    transaction_type: str
    item_id: int
    item_sku: Optional[str] = None
    item_name: Optional[str] = None
    quantity: float
    unit_price: float
    total_amount: float
    cogs_fifo: float
    cogs_wac: float
    cogs_lifo: float
    reference: str
    party: str
    operator: str
    timestamp: datetime

    class Config:
        from_attributes = True


# ==========================================
# Valuation Report Schemas
# ==========================================

class ValuationItemDetail(BaseModel):
    item_id: int
    sku: str
    name: str
    category: str
    unit: str
    current_stock: float
    moving_avg_cost: float
    total_purchases_qty: float
    total_sales_qty: float
    goods_available_qty: float
    goods_available_cost: float
    cogs: float
    ending_inventory_value: float
    revenue: float
    gross_margin: float
    gross_margin_pct: float
    inventory_turnover: float
    days_in_inventory: float


class ValuationReportResponse(BaseModel):
    method: str  # FIFO, WAC, LIFO
    system: str  # PERPETUAL, PERIODIC
    generated_at: datetime
    compliance_note: Optional[str] = None
    total_goods_available_cost: float
    total_cogs: float
    total_ending_inventory_value: float
    total_revenue: float
    total_gross_margin: float
    overall_gross_margin_pct: float
    overall_turnover_rate: float
    overall_days_in_inventory: float
    items: List[ValuationItemDetail]


# ==========================================
# Internal Controls & Analysis Schemas
# ==========================================

class ReconcileRequest(BaseModel):
    item_id: int = Field(..., description="Target Item Master ID")
    physical_count: float = Field(..., ge=0.0, description="Physical inventory count verified by audit")
    adjust_book_stock: bool = Field(False, description="Whether to synchronize book stock to physical count")
    notes: Optional[str] = Field("", max_length=255, description="Audit notes or shrinkage observations")
    operator: Optional[str] = Field(None, description="Operator stamping the audit")


class PhysicalAuditResponse(BaseModel):
    id: int
    item_id: int
    item_sku: Optional[str] = None
    item_name: Optional[str] = None
    book_stock: float
    physical_count: float
    variance: float
    variance_pct: float
    exceeds_threshold: bool
    adjusted: bool
    operator: str
    notes: str
    timestamp: datetime

    class Config:
        from_attributes = True


class ABCClassificationItem(BaseModel):
    item_id: int
    sku: str
    name: str
    category: str
    current_stock: float
    total_sold_units: float
    unit_cost: float
    usage_value: float
    value_share_pct: float
    cumulative_share_pct: float
    abc_category: str  # 'A', 'B', or 'C'
    recommended_control: str


class AuditLogResponse(BaseModel):
    id: int
    action: str
    entity_name: str
    entity_id: Optional[int]
    operator: str
    details: str
    timestamp: datetime

    class Config:
        from_attributes = True
