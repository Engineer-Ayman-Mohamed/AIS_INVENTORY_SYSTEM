"""
Analysis & Internal Controls Router
Implements managerial oversight and AIS internal control components:
1. Automated Reorder Alerts (SKUs <= reorder level)
2. ABC Inventory Classification (Pareto usage value ranking)
3. Physical Count Reconciliation Engine (Flags variances > 2% tolerance threshold)
4. Immutable Transaction Audit Trail
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Item, PhysicalAudit, AuditLog, Transaction
from app.schemas import (
    ReconcileRequest, PhysicalAuditResponse, ABCClassificationItem, AuditLogResponse, ItemResponse
)
from app.accounting import (
    generate_abc_analysis, calculate_reconciliation_variance, compute_item_valuation_by_method
)
from app.config import settings

router = APIRouter(prefix="/api/controls", tags=["Analysis & Internal Controls"])


@router.get("/reorder-alerts", response_model=List[ItemResponse])
def get_reorder_alerts(db: Session = Depends(get_db)):
    """
    Returns items currently at or below their designated reorder threshold.
    Enforces Internal Control: Automated replenishment warning.
    """
    low_stock_items = (
        db.query(Item)
        .filter(Item.current_stock <= Item.reorder_level)
        .order_by(Item.current_stock.asc())
        .all()
    )

    result = []
    for item in low_stock_items:
        fifo_val = compute_item_valuation_by_method(db, item, "FIFO")["valuation"]
        wac_val = compute_item_valuation_by_method(db, item, "WAC")["valuation"]
        lifo_val = compute_item_valuation_by_method(db, item, "LIFO")["valuation"]

        result.append(
            ItemResponse(
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
                is_low_stock=True,
                fifo_value=fifo_val,
                wac_value=wac_val,
                lifo_value=lifo_val
            )
        )
    return result


@router.get("/abc-analysis", response_model=List[ABCClassificationItem])
def get_abc_analysis(db: Session = Depends(get_db)):
    """
    Performs dynamic ABC Inventory Classification based on usage value:
    - Class A: Top ~75% cumulative value (Tight control, high frequency monitoring)
    - Class B: Next ~15% cumulative value (Moderate control)
    - Class C: Bottom ~10% cumulative value (Basic bulk control)
    """
    items = db.query(Item).all()
    analysis = generate_abc_analysis(items, db)
    return [ABCClassificationItem(**rec) for rec in analysis]


@router.post("/reconcile", response_model=PhysicalAuditResponse, status_code=status.HTTP_201_CREATED)
def record_reconciliation(payload: ReconcileRequest, db: Session = Depends(get_db)):
    """
    Reconciles physical count against book stock.
    Enforces Internal Control:
    - Calculates absolute variance percentage.
    - Flags investigation if variance exceeds 2.0% tolerance threshold.
    - Optionally adjusts book stock to physical count and stamps audit trail.
    """
    item = db.query(Item).filter(Item.id == payload.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item SKU not found")

    operator_name = payload.operator or settings.DEFAULT_OPERATOR
    book_stock = item.current_stock
    physical_count = payload.physical_count

    variance, variance_pct, exceeds_threshold = calculate_reconciliation_variance(
        book_stock=book_stock,
        physical_count=physical_count
    )

    # Create Physical Audit record
    audit_record = PhysicalAudit(
        item_id=item.id,
        book_stock=book_stock,
        physical_count=physical_count,
        variance=variance,
        variance_pct=variance_pct,
        exceeds_threshold=exceeds_threshold,
        adjusted=payload.adjust_book_stock,
        operator=operator_name,
        notes=payload.notes or ("Discrepancy exceeds 2% threshold" if exceeds_threshold else "Within acceptable tolerance")
    )
    db.add(audit_record)
    db.flush()

    # If adjustment requested, synchronize book stock and record transaction
    if payload.adjust_book_stock and variance != 0:
        item.current_stock = physical_count
        
        # Log adjustment transaction
        tx = Transaction(
            transaction_type="RECONCILIATION_ADJUSTMENT",
            item_id=item.id,
            quantity=abs(variance),
            unit_price=item.moving_avg_cost,
            total_amount=round(abs(variance) * item.moving_avg_cost, 2),
            reference=f"AUDIT-REC-{audit_record.id}",
            party="Physical Audit Adjustment",
            operator=operator_name
        )
        db.add(tx)

    # Stamp system-wide audit log
    audit_log = AuditLog(
        action="RECONCILE",
        entity_name="PhysicalAudit",
        entity_id=audit_record.id,
        operator=operator_name,
        details=(
            f"Physical Audit for '{item.sku}': Book={book_stock}, Physical={physical_count}, "
            f"Variance={variance:+.1f} ({variance_pct:.2f}%). Exceeds 2% limit: {exceeds_threshold}. "
            f"Book stock adjusted: {payload.adjust_book_stock}"
        )
    )
    db.add(audit_log)
    db.commit()
    db.refresh(audit_record)

    return PhysicalAuditResponse(
        id=audit_record.id,
        item_id=item.id,
        item_sku=item.sku,
        item_name=item.name,
        book_stock=audit_record.book_stock,
        physical_count=audit_record.physical_count,
        variance=audit_record.variance,
        variance_pct=audit_record.variance_pct,
        exceeds_threshold=audit_record.exceeds_threshold,
        adjusted=audit_record.adjusted,
        operator=audit_record.operator,
        notes=audit_record.notes,
        timestamp=audit_record.timestamp
    )


@router.get("/reconciliations", response_model=List[PhysicalAuditResponse])
def list_reconciliations(limit: int = 50, db: Session = Depends(get_db)):
    """
    Returns audit history of physical stock reconciliations.
    """
    audits = (
        db.query(PhysicalAudit)
        .order_by(PhysicalAudit.timestamp.desc())
        .limit(limit)
        .all()
    )

    result = []
    for a in audits:
        result.append(
            PhysicalAuditResponse(
                id=a.id,
                item_id=a.item_id,
                item_sku=a.item.sku if a.item else "N/A",
                item_name=a.item.name if a.item else "N/A",
                book_stock=a.book_stock,
                physical_count=a.physical_count,
                variance=a.variance,
                variance_pct=a.variance_pct,
                exceeds_threshold=a.exceeds_threshold,
                adjusted=a.adjusted,
                operator=a.operator,
                notes=a.notes,
                timestamp=a.timestamp
            )
        )
    return result


@router.get("/audit-trail", response_model=List[AuditLogResponse])
def get_audit_trail(limit: int = 100, db: Session = Depends(get_db)):
    """
    Returns immutable chronological audit trail.
    Enforces Internal Control: Every action is logged with user stamp and UTC timestamp.
    """
    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
        .all()
    )
    return logs
