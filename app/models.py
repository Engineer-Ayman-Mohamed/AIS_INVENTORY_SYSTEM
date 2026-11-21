"""
Database Entities (Data Models)
Summary of Entities:
1. Item: Master catalog of inventory SKUs with stock levels and moving average cost.
2. CostLayer: Tracks distinct purchase lots for FIFO / LIFO accounting algorithms.
3. Transaction: Immutable records of Goods In (Purchases), Goods Out (Sales), and adjustments.
4. PhysicalAudit: Stock reconciliation records enforcing the 2% tolerance threshold.
5. AuditLog: System-wide audit trail recording user actions with timestamps.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
)
from sqlalchemy.orm import relationship
from app.database import Base


def utcnow():
    """Returns current UTC timestamp."""
    return datetime.now(timezone.utc)


class Item(Base):
    """
    Item Master Entity
    Represents inventory stock keeping units (SKUs).
    Maintains current stock balance, reorder trigger levels, and real-time moving average cost.
    """
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(120), nullable=False)
    category = Column(String(60), default="General", nullable=False)
    unit_of_measure = Column(String(20), default="Unit", nullable=False)
    reorder_level = Column(Float, default=10.0, nullable=False)
    selling_price = Column(Float, default=0.0, nullable=False)
    current_stock = Column(Float, default=0.0, nullable=False)
    moving_avg_cost = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    cost_layers = relationship("CostLayer", back_populates="item", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="item")
    audits = relationship("PhysicalAudit", back_populates="item")


class CostLayer(Base):
    """
    Cost Layer Entity
    Tracks individual acquisition lots for FIFO and LIFO cost-flow accounting.
    Created automatically when Goods In (Purchases) are received.
    """
    __tablename__ = "cost_layers"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False, index=True)
    purchase_date = Column(DateTime, default=utcnow, nullable=False)
    original_quantity = Column(Float, nullable=False)
    remaining_quantity = Column(Float, nullable=False)
    unit_cost = Column(Float, nullable=False)
    supplier = Column(String(100), default="Standard Supplier", nullable=False)
    reference = Column(String(100), default="PO-Auto", nullable=False)

    # Relationship back to Item
    item = relationship("Item", back_populates="cost_layers")


class Transaction(Base):
    """
    Transaction Entity
    Records all inventory movements:
    - PURCHASE (Goods In)
    - SALE (Goods Out)
    - RECONCILIATION_ADJUSTMENT (Stock variance correction)
    Stores pre-calculated COGS per cost-flow assumption (FIFO, WAC, LIFO) for perpetual reporting.
    """
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_type = Column(String(30), nullable=False)  # PURCHASE, SALE, RECONCILIATION_ADJUSTMENT
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)  # Cost for purchases, Price for sales
    total_amount = Column(Float, nullable=False)
    
    # Pre-calculated COGS per transaction under perpetual accounting rules
    cogs_fifo = Column(Float, default=0.0, nullable=False)
    cogs_wac = Column(Float, default=0.0, nullable=False)
    cogs_lifo = Column(Float, default=0.0, nullable=False)
    
    reference = Column(String(100), default="REF-NONE", nullable=False)
    party = Column(String(100), default="Direct", nullable=False)  # Supplier or Customer name
    operator = Column(String(80), default="System Operator", nullable=False)
    timestamp = Column(DateTime, default=utcnow, nullable=False)

    # Relationship back to Item
    item = relationship("Item", back_populates="transactions")


class PhysicalAudit(Base):
    """
    Physical Stock Audit / Reconciliation Entity
    Stores results of physical inventory counts vs book stock.
    Enforces Internal Control: flags variances exceeding the 2.0% tolerance threshold.
    """
    __tablename__ = "physical_audits"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False, index=True)
    book_stock = Column(Float, nullable=False)
    physical_count = Column(Float, nullable=False)
    variance = Column(Float, nullable=False)          # physical_count - book_stock
    variance_pct = Column(Float, nullable=False)      # (|variance| / book_stock) * 100
    exceeds_threshold = Column(Boolean, default=False, nullable=False)  # True if > 2%
    adjusted = Column(Boolean, default=False, nullable=False)
    operator = Column(String(80), default="System Operator", nullable=False)
    notes = Column(String(255), default="", nullable=False)
    timestamp = Column(DateTime, default=utcnow, nullable=False)

    item = relationship("Item", back_populates="audits")


class AuditLog(Base):
    """
    Immutable Audit Trail Entity
    Enforces Internal Control: every action (item creation, edit, purchase, sale, reconciliation)
    is permanently recorded with operator identity and timestamp.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(50), nullable=False)  # CREATE_ITEM, UPDATE_ITEM, GOODS_IN, GOODS_OUT, RECONCILE
    entity_name = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=True)
    operator = Column(String(80), default="System Operator", nullable=False)
    details = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=utcnow, nullable=False)
