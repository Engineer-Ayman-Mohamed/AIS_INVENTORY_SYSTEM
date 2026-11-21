"""
Goods In (Purchases) Router
Captures stock acquisitions:
- Creates a distinct "Cost Layer" in the database (FIFO/LIFO tracking)
- Recalculates moving average cost (WAC) immediately
- Updates Item Master current stock balance
- Creates an immutable audit & transaction record
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Item, CostLayer, Transaction, AuditLog
from app.schemas import GoodsInCreate, TransactionResponse
from app.accounting import update_moving_average_cost_on_purchase
from app.config import settings

router = APIRouter(prefix="/api/goods-in", tags=["Goods In (Purchases)"])


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def record_goods_in(payload: GoodsInCreate, db: Session = Depends(get_db)):
    """
    Records a stock purchase acquisition.
    Enforces AIS Processing Cycle:
    1. Input Validation: Quantity and unit cost strictly positive.
    2. Processing:
       - Generates a distinct FIFO/LIFO Cost Layer.
       - Recalculates Weighted Average Cost dynamically.
       - Increments current stock.
    3. Output & Control:
       - Logs transaction permanently.
       - Records audit trail stamped with operator.
    """
    item = db.query(Item).filter(Item.id == payload.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item SKU not found")

    operator_name = payload.operator or settings.DEFAULT_OPERATOR

    # 1. Update moving average cost before updating stock
    new_wac = update_moving_average_cost_on_purchase(
        current_stock=item.current_stock,
        current_moving_avg=item.moving_avg_cost,
        purchased_qty=payload.quantity,
        purchased_unit_cost=payload.unit_cost
    )
    item.moving_avg_cost = new_wac
    item.current_stock += payload.quantity

    # 2. Create distinct Cost Layer
    cost_layer = CostLayer(
        item_id=item.id,
        original_quantity=payload.quantity,
        remaining_quantity=payload.quantity,
        unit_cost=payload.unit_cost,
        supplier=payload.supplier.strip(),
        reference=payload.reference.strip()
    )
    db.add(cost_layer)

    # 3. Create immutable Transaction Record
    total_amount = round(payload.quantity * payload.unit_cost, 2)
    tx = Transaction(
        transaction_type="PURCHASE",
        item_id=item.id,
        quantity=payload.quantity,
        unit_price=payload.unit_cost,
        total_amount=total_amount,
        reference=payload.reference.strip(),
        party=payload.supplier.strip(),
        operator=operator_name
    )
    db.add(tx)
    db.flush()

    # 4. Stamp Audit Trail
    audit = AuditLog(
        action="GOODS_IN",
        entity_name="Transaction",
        entity_id=tx.id,
        operator=operator_name,
        details=f"Received {payload.quantity} {item.unit_of_measure}(s) of SKU '{item.sku}' @ ${payload.unit_cost:.2f} from '{payload.supplier}'. New WAC: ${new_wac:.2f}"
    )
    db.add(audit)
    db.commit()
    db.refresh(tx)

    return TransactionResponse(
        id=tx.id,
        transaction_type=tx.transaction_type,
        item_id=item.id,
        item_sku=item.sku,
        item_name=item.name,
        quantity=tx.quantity,
        unit_price=tx.unit_price,
        total_amount=tx.total_amount,
        cogs_fifo=0.0,
        cogs_wac=0.0,
        cogs_lifo=0.0,
        reference=tx.reference,
        party=tx.party,
        operator=tx.operator,
        timestamp=tx.timestamp
    )


@router.get("", response_model=List[TransactionResponse])
def list_purchases(limit: int = 50, db: Session = Depends(get_db)):
    """
    Lists recent Goods In purchase transactions with item metadata.
    """
    purchases = (
        db.query(Transaction)
        .filter(Transaction.transaction_type == "PURCHASE")
        .order_by(Transaction.timestamp.desc())
        .limit(limit)
        .all()
    )

    result = []
    for p in purchases:
        result.append(
            TransactionResponse(
                id=p.id,
                transaction_type=p.transaction_type,
                item_id=p.item_id,
                item_sku=p.item.sku if p.item else "N/A",
                item_name=p.item.name if p.item else "N/A",
                quantity=p.quantity,
                unit_price=p.unit_price,
                total_amount=p.total_amount,
                cogs_fifo=p.cogs_fifo,
                cogs_wac=p.cogs_wac,
                cogs_lifo=p.cogs_lifo,
                reference=p.reference,
                party=p.party,
                operator=p.operator,
                timestamp=p.timestamp
            )
        )
    return result
