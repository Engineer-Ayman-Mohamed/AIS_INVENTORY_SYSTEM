"""
Goods Out (Sales) Router
Records sales transactions:
- Validates stock availability (Internal Control: prevents negative stock balances)
- Computes perpetual Cost of Goods Sold (COGS) under FIFO, WAC, and LIFO
- Consumes cost layers according to FIFO rules
- Decrements item stock
- Creates immutable audit and transaction records
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Item, Transaction, AuditLog
from app.schemas import GoodsOutCreate, TransactionResponse
from app.accounting import calculate_fifo_cogs_and_consume, calculate_lifo_cogs_simulated
from app.config import settings

router = APIRouter(prefix="/api/goods-out", tags=["Goods Out (Sales)"])


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def record_goods_out(payload: GoodsOutCreate, db: Session = Depends(get_db)):
    """
    Records a stock sale transaction.
    Enforces Internal Control:
    - No Negative Inventory: Sales strictly rejected if requested quantity > current stock.
    - Perpetual Accounting: Real-time COGS computed per transaction for FIFO, WAC, and LIFO.
    """
    item = db.query(Item).filter(Item.id == payload.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item SKU not found")

    # Internal Control: No Negative Inventory
    if payload.quantity > item.current_stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Negative Inventory Violation: Requested quantity ({payload.quantity} {item.unit_of_measure}) "
                f"exceeds current physical stock on hand ({item.current_stock} {item.unit_of_measure}). "
                f"Internal accounting controls prohibit sale execution."
            )
        )

    operator_name = payload.operator or settings.DEFAULT_OPERATOR
    selling_price = payload.selling_price if payload.selling_price is not None else item.selling_price
    total_sales_amount = round(payload.quantity * selling_price, 2)

    # 1. Compute perpetual COGS under all 3 methods
    # FIFO: actually consumes the cost layers in the database
    cogs_fifo = calculate_fifo_cogs_and_consume(
        db=db,
        item_id=item.id,
        quantity_to_sell=payload.quantity,
        commit_consumption=True
    )

    # WAC: uses current moving average cost
    cogs_wac = round(payload.quantity * item.moving_avg_cost, 2)

    # LIFO: simulated calculation for comparative analysis
    cogs_lifo = calculate_lifo_cogs_simulated(
        db=db,
        item_id=item.id,
        quantity_to_sell=payload.quantity
    )

    # 2. Decrement physical stock on hand
    item.current_stock -= payload.quantity

    # 3. Create immutable Transaction record
    tx = Transaction(
        transaction_type="SALE",
        item_id=item.id,
        quantity=payload.quantity,
        unit_price=selling_price,
        total_amount=total_sales_amount,
        cogs_fifo=cogs_fifo,
        cogs_wac=cogs_wac,
        cogs_lifo=cogs_lifo,
        reference=payload.reference.strip(),
        party=payload.customer.strip(),
        operator=operator_name
    )
    db.add(tx)
    db.flush()

    # 4. Stamp Audit Trail
    audit = AuditLog(
        action="GOODS_OUT",
        entity_name="Transaction",
        entity_id=tx.id,
        operator=operator_name,
        details=(
            f"Sold {payload.quantity} {item.unit_of_measure}(s) of SKU '{item.sku}' to '{payload.customer}' "
            f"for ${total_sales_amount:.2f}. FIFO COGS: ${cogs_fifo:.2f}, WAC COGS: ${cogs_wac:.2f}"
        )
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
        cogs_fifo=tx.cogs_fifo,
        cogs_wac=tx.cogs_wac,
        cogs_lifo=tx.cogs_lifo,
        reference=tx.reference,
        party=tx.party,
        operator=tx.operator,
        timestamp=tx.timestamp
    )


@router.get("", response_model=List[TransactionResponse])
def list_sales(limit: int = 50, db: Session = Depends(get_db)):
    """
    Lists recent Goods Out sales transactions with perpetual COGS and gross profits.
    """
    sales = (
        db.query(Transaction)
        .filter(Transaction.transaction_type == "SALE")
        .order_by(Transaction.timestamp.desc())
        .limit(limit)
        .all()
    )

    result = []
    for s in sales:
        result.append(
            TransactionResponse(
                id=s.id,
                transaction_type=s.transaction_type,
                item_id=s.item_id,
                item_sku=s.item.sku if s.item else "N/A",
                item_name=s.item.name if s.item else "N/A",
                quantity=s.quantity,
                unit_price=s.unit_price,
                total_amount=s.total_amount,
                cogs_fifo=s.cogs_fifo,
                cogs_wac=s.cogs_wac,
                cogs_lifo=s.cogs_lifo,
                reference=s.reference,
                party=s.party,
                operator=s.operator,
                timestamp=s.timestamp
            )
        )
    return result
