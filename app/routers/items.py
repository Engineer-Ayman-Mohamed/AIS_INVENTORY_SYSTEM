"""
Item Master Router
Manages core product catalog (SKUs):
- List, Create, Read, Update, Delete items
- Enforces Internal Controls:
  * Unique SKU constraint
  * Prevents deletion of items with transaction history (Data Integrity)
  * Real-time stock status and low-stock threshold triggers
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Item, CostLayer, Transaction, AuditLog
from app.schemas import ItemCreate, ItemUpdate, ItemResponse, CostLayerResponse
from app.accounting import compute_item_valuation_by_method
from app.config import settings

router = APIRouter(prefix="/api/items", tags=["Item Master"])


@router.get("", response_model=List[ItemResponse])
def list_items(db: Session = Depends(get_db)):
    """
    Retrieves all inventory items with their current stock and dynamic valuations.
    """
    items = db.query(Item).order_by(Item.sku.asc()).all()
    result = []
    for item in items:
        fifo_val = compute_item_valuation_by_method(db, item, "FIFO")["valuation"]
        wac_val = compute_item_valuation_by_method(db, item, "WAC")["valuation"]
        lifo_val = compute_item_valuation_by_method(db, item, "LIFO")["valuation"]
        
        item_dict = {
            "id": item.id,
            "sku": item.sku,
            "name": item.name,
            "category": item.category,
            "unit_of_measure": item.unit_of_measure,
            "reorder_level": item.reorder_level,
            "selling_price": item.selling_price,
            "current_stock": item.current_stock,
            "moving_avg_cost": item.moving_avg_cost,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
            "is_low_stock": item.current_stock <= item.reorder_level,
            "fifo_value": fifo_val,
            "wac_value": wac_val,
            "lifo_value": lifo_val
        }
        result.append(ItemResponse(**item_dict))
    return result


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(payload: ItemCreate, db: Session = Depends(get_db)):
    """
    Creates a new inventory SKU.
    Enforces Internal Control: SKU uniqueness validation.
    If initial stock is specified (>0), automatically initializes a cost layer and opening transaction.
    """
    # Check SKU uniqueness
    existing = db.query(Item).filter(Item.sku.ilike(payload.sku.strip())).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Item code '{payload.sku}' already exists. Internal control enforces unique SKUs."
        )

    # Create new Item
    item = Item(
        sku=payload.sku.strip().upper(),
        name=payload.name.strip(),
        category=payload.category.strip() or "General",
        unit_of_measure=payload.unit_of_measure.strip() or "Unit",
        reorder_level=payload.reorder_level,
        selling_price=payload.selling_price,
        current_stock=payload.initial_stock,
        moving_avg_cost=payload.initial_cost if payload.initial_stock > 0 else 0.0
    )
    db.add(item)
    db.flush()

    # If opening stock provided, create initial cost layer and transaction
    if payload.initial_stock > 0 and payload.initial_cost > 0:
        layer = CostLayer(
            item_id=item.id,
            original_quantity=payload.initial_stock,
            remaining_quantity=payload.initial_stock,
            unit_cost=payload.initial_cost,
            supplier="Initial Opening Balance",
            reference="INIT-STOCK"
        )
        db.add(layer)

        tx = Transaction(
            transaction_type="PURCHASE",
            item_id=item.id,
            quantity=payload.initial_stock,
            unit_price=payload.initial_cost,
            total_amount=round(payload.initial_stock * payload.initial_cost, 2),
            reference="OPENING-BALANCE",
            party="Opening Balance",
            operator=settings.DEFAULT_OPERATOR
        )
        db.add(tx)

    # Record Audit Log
    audit = AuditLog(
        action="CREATE_ITEM",
        entity_name="Item",
        entity_id=item.id,
        operator=settings.DEFAULT_OPERATOR,
        details=f"Created SKU '{item.sku}' - {item.name}. Initial Stock: {payload.initial_stock}"
    )
    db.add(audit)
    db.commit()
    db.refresh(item)

    fifo_val = compute_item_valuation_by_method(db, item, "FIFO")["valuation"]
    wac_val = compute_item_valuation_by_method(db, item, "WAC")["valuation"]
    lifo_val = compute_item_valuation_by_method(db, item, "LIFO")["valuation"]

    return ItemResponse(
        id=item.id,
        sku=item.sku,
        name=item.name,
        category=item.category,
        unit_of_measure=item.unit_of_measure,
        reorder_level=item.reorder_level,
        selling_price=item.selling_price,
        current_stock=item.current_stock,
        moving_avg_cost=item.moving_avg_cost,
        created_at=item.created_at,
        updated_at=item.updated_at,
        is_low_stock=item.current_stock <= item.reorder_level,
        fifo_value=fifo_val,
        wac_value=wac_val,
        lifo_value=lifo_val
    )


@router.get("/{item_id}/layers", response_model=List[CostLayerResponse])
def get_item_cost_layers(item_id: int, db: Session = Depends(get_db)):
    """
    Fetches active acquisition cost layers for a given SKU (used for FIFO/LIFO transparency).
    """
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    layers = (
        db.query(CostLayer)
        .filter(CostLayer.item_id == item_id, CostLayer.remaining_quantity > 0)
        .order_by(CostLayer.purchase_date.asc())
        .all()
    )
    return layers


@router.put("/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, payload: ItemUpdate, db: Session = Depends(get_db)):
    """
    Updates editable item metadata (Name, Category, Unit, Reorder Level, Selling Price).
    """
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    updates = []
    if payload.name is not None:
        item.name = payload.name.strip()
        updates.append("name")
    if payload.category is not None:
        item.category = payload.category.strip()
        updates.append("category")
    if payload.unit_of_measure is not None:
        item.unit_of_measure = payload.unit_of_measure.strip()
        updates.append("unit_of_measure")
    if payload.reorder_level is not None:
        item.reorder_level = payload.reorder_level
        updates.append("reorder_level")
    if payload.selling_price is not None:
        item.selling_price = payload.selling_price
        updates.append("selling_price")

    audit = AuditLog(
        action="UPDATE_ITEM",
        entity_name="Item",
        entity_id=item.id,
        operator=settings.DEFAULT_OPERATOR,
        details=f"Updated SKU '{item.sku}' fields: {', '.join(updates)}"
    )
    db.add(audit)
    db.commit()
    db.refresh(item)

    fifo_val = compute_item_valuation_by_method(db, item, "FIFO")["valuation"]
    wac_val = compute_item_valuation_by_method(db, item, "WAC")["valuation"]
    lifo_val = compute_item_valuation_by_method(db, item, "LIFO")["valuation"]

    return ItemResponse(
        id=item.id,
        sku=item.sku,
        name=item.name,
        category=item.category,
        unit_of_measure=item.unit_of_measure,
        reorder_level=item.reorder_level,
        selling_price=item.selling_price,
        current_stock=item.current_stock,
        moving_avg_cost=item.moving_avg_cost,
        created_at=item.created_at,
        updated_at=item.updated_at,
        is_low_stock=item.current_stock <= item.reorder_level,
        fifo_value=fifo_val,
        wac_value=wac_val,
        lifo_value=lifo_val
    )


@router.delete("/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    """
    Deletes an item master.
    Enforces Internal Control: Data Integrity rule strictly blocks deletion
    if the item possesses any transaction history.
    """
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    has_transactions = db.query(Transaction).filter(Transaction.item_id == item.id).first()
    if has_transactions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Data Integrity Violation: SKU '{item.sku}' cannot be deleted because it possesses historical transactions. Accounting audit rules restrict deletion."
        )

    db.delete(item)
    audit = AuditLog(
        action="DELETE_ITEM",
        entity_name="Item",
        entity_id=item_id,
        operator=settings.DEFAULT_OPERATOR,
        details=f"Deleted SKU '{item.sku}'"
    )
    db.add(audit)
    db.commit()
    return {"message": f"Item '{item.sku}' successfully removed."}
