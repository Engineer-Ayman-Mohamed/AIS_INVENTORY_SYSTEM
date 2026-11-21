"""
Valuation Report Router
The primary accounting engine of the AIS system.
Features:
- Dynamic calculation toggles for cost-flow assumptions:
  * FIFO (First-In, First-Out)
  * WAC (Weighted Average Cost)
  * LIFO (Last-In, First-Out - with IAS 2.1.9 compliance warning)
- Dynamic system toggle:
  * Perpetual (continuous real-time stock/cost updates)
  * Periodic (mathematically derived at period close)
- Outputs core accounting metrics:
  * Goods Available for Sale (Quantity & Cost)
  * Cost of Goods Sold (COGS)
  * Ending Inventory Valuation
  * Revenue, Gross Margin ($ and %)
  * Inventory Turnover & Days in Inventory (DSI)
"""

from datetime import datetime, timezone
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Item, CostLayer, Transaction
from app.schemas import ValuationReportResponse, ValuationItemDetail
from app.accounting import compute_item_valuation_by_method

router = APIRouter(prefix="/api/valuation", tags=["Valuation Report"])


@router.get("/report", response_model=ValuationReportResponse)
def get_valuation_report(
    method: str = Query("FIFO", pattern="^(FIFO|WAC|LIFO)$", description="Cost flow method"),
    system: str = Query("PERPETUAL", pattern="^(PERPETUAL|PERIODIC)$", description="Inventory accounting system"),
    db: Session = Depends(get_db)
):
    """
    Generates dynamic financial valuation reports reflecting selected accounting toggles.
    """
    method = method.upper()
    system = system.upper()

    compliance_note = None
    if method == "LIFO":
        compliance_note = (
            "Academic Demonstration Only: International Accounting Standard IAS 2.1.9 prohibits "
            "the use of LIFO (Last-In, First-Out) for general-purpose financial reporting due to "
            "potential mismatch with physical inventory flow and profit distortion."
        )

    items = db.query(Item).order_by(Item.sku.asc()).all()

    item_details: List[ValuationItemDetail] = []
    
    total_goods_available_cost = 0.0
    total_cogs = 0.0
    total_ending_val = 0.0
    total_revenue = 0.0

    for item in items:
        # Fetch purchases
        purchases = (
            db.query(Transaction)
            .filter(Transaction.item_id == item.id, Transaction.transaction_type == "PURCHASE")
            .all()
        )
        total_purchases_qty = sum(p.quantity for p in purchases)
        purchases_cost = sum(p.total_amount for p in purchases)

        # Fetch sales
        sales = (
            db.query(Transaction)
            .filter(Transaction.item_id == item.id, Transaction.transaction_type == "SALE")
            .all()
        )
        total_sales_qty = sum(s.quantity for s in sales)
        revenue = sum(s.total_amount for s in sales)

        # Goods Available for Sale
        goods_available_qty = total_purchases_qty
        goods_available_cost = purchases_cost

        # Determine Ending Inventory Valuation
        val_result = compute_item_valuation_by_method(db, item, method)
        ending_val = val_result["valuation"]

        # Determine COGS based on system toggle
        if system == "PERPETUAL":
            # Perpetual: sum transaction-level COGS
            if method == "FIFO":
                cogs = sum(s.cogs_fifo for s in sales)
            elif method == "LIFO":
                cogs = sum(s.cogs_lifo for s in sales)
            else:  # WAC
                cogs = sum(s.cogs_wac for s in sales)
        else:
            # Periodic: COGS = Goods Available for Sale - Ending Inventory
            cogs = max(0.0, goods_available_cost - ending_val)

        cogs = round(cogs, 2)
        gross_margin = round(revenue - cogs, 2)
        gross_margin_pct = round((gross_margin / revenue * 100), 2) if revenue > 0 else 0.0

        # Turnover and Days in Inventory
        turnover = round(cogs / ending_val, 2) if ending_val > 0 else 0.0
        days_in_inv = round(365 / turnover, 1) if turnover > 0 else 0.0

        item_detail = ValuationItemDetail(
            item_id=item.id,
            sku=item.sku,
            name=item.name,
            category=item.category,
            unit=item.unit_of_measure,
            current_stock=item.current_stock,
            moving_avg_cost=item.moving_avg_cost,
            total_purchases_qty=total_purchases_qty,
            total_sales_qty=total_sales_qty,
            goods_available_qty=goods_available_qty,
            goods_available_cost=round(goods_available_cost, 2),
            cogs=cogs,
            ending_inventory_value=ending_val,
            revenue=round(revenue, 2),
            gross_margin=gross_margin,
            gross_margin_pct=gross_margin_pct,
            inventory_turnover=turnover,
            days_in_inventory=days_in_inv
        )
        item_details.append(item_detail)

        total_goods_available_cost += goods_available_cost
        total_cogs += cogs
        total_ending_val += ending_val
        total_revenue += revenue

    total_gross_margin = round(total_revenue - total_cogs, 2)
    overall_gross_margin_pct = round((total_gross_margin / total_revenue * 100), 2) if total_revenue > 0 else 0.0
    overall_turnover = round(total_cogs / total_ending_val, 2) if total_ending_val > 0 else 0.0
    overall_days = round(365 / overall_turnover, 1) if overall_turnover > 0 else 0.0

    return ValuationReportResponse(
        method=method,
        system=system,
        generated_at=datetime.now(timezone.utc),
        compliance_note=compliance_note,
        total_goods_available_cost=round(total_goods_available_cost, 2),
        total_cogs=round(total_cogs, 2),
        total_ending_inventory_value=round(total_ending_val, 2),
        total_revenue=round(total_revenue, 2),
        total_gross_margin=total_gross_margin,
        overall_gross_margin_pct=overall_gross_margin_pct,
        overall_turnover_rate=overall_turnover,
        overall_days_in_inventory=overall_days,
        items=item_details
    )


@router.get("/comparison", response_model=Dict[str, Any])
def get_valuation_comparison(db: Session = Depends(get_db)):
    """
    Directly compares the financial impact of FIFO vs WAC vs LIFO side-by-side.
    Ideal for presentation to academic reviewers and college professors.
    """
    items = db.query(Item).all()
    sales = db.query(Transaction).filter(Transaction.transaction_type == "SALE").all()
    revenue = sum(s.total_amount for s in sales)

    methods = ["FIFO", "WAC", "LIFO"]
    results = {}

    for m in methods:
        ending_val = sum(compute_item_valuation_by_method(db, itm, m)["valuation"] for itm in items)
        if m == "FIFO":
            cogs = sum(s.cogs_fifo for s in sales)
        elif m == "LIFO":
            cogs = sum(s.cogs_lifo for s in sales)
        else:
            cogs = sum(s.cogs_wac for s in sales)

        gross_profit = revenue - cogs
        margin_pct = (gross_profit / revenue * 100) if revenue > 0 else 0.0

        results[m] = {
            "ending_inventory_value": round(ending_val, 2),
            "cogs": round(cogs, 2),
            "revenue": round(revenue, 2),
            "gross_profit": round(gross_profit, 2),
            "gross_margin_pct": round(margin_pct, 2),
            "turnover_rate": round(cogs / ending_val, 2) if ending_val > 0 else 0.0
        }

    return {
        "revenue": round(revenue, 2),
        "comparison": results,
        "ias_notice": "IAS 2.1.9 explicitly restricts LIFO; FIFO or Weighted Average are the sanctioned frameworks."
    }
