"""
Executive Dashboard Router
Provides aggregated Key Performance Indicators (KPIs):
- Total Stock Valuation across all 3 cost-flow methods (FIFO, WAC, LIFO)
- Active SKU Count
- Items below Reorder Level (Low Stock Alert count)
- Inventory Turnover Rate & Days Sales of Inventory (DSI)
- Visual Chart metrics (Stock by Category, Cost-Flow Valuation Comparison)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.models import Item, Transaction
from app.accounting import compute_item_valuation_by_method

router = APIRouter(prefix="/api/dashboard", tags=["Executive Dashboard"])


@router.get("/summary", response_model=Dict[str, Any])
def get_dashboard_summary(db: Session = Depends(get_db)):
    """
    Returns executive summary KPIs for real-time managerial decision making.
    """
    items = db.query(Item).all()
    active_skus = len(items)
    
    total_fifo_val = 0.0
    total_wac_val = 0.0
    total_lifo_val = 0.0
    low_stock_count = 0
    total_units_in_stock = 0.0

    for itm in items:
        total_units_in_stock += itm.current_stock
        if itm.current_stock <= itm.reorder_level:
            low_stock_count += 1
            
        fifo = compute_item_valuation_by_method(db, itm, "FIFO")
        wac = compute_item_valuation_by_method(db, itm, "WAC")
        lifo = compute_item_valuation_by_method(db, itm, "LIFO")
        
        total_fifo_val += fifo["valuation"]
        total_wac_val += wac["valuation"]
        total_lifo_val += lifo["valuation"]

    # Compute Total Revenue and COGS from historical sales
    sales_transactions = (
        db.query(Transaction)
        .filter(Transaction.transaction_type == "SALE")
        .all()
    )
    total_revenue = sum(t.total_amount for t in sales_transactions)
    total_cogs_fifo = sum(t.cogs_fifo for t in sales_transactions)
    total_cogs_wac = sum(t.cogs_wac for t in sales_transactions)
    total_cogs_lifo = sum(t.cogs_lifo for t in sales_transactions)

    # Inventory Turnover Rate = COGS / Ending Inventory (Annualized approximation)
    turnover_rate = round(total_cogs_wac / total_wac_val, 2) if total_wac_val > 0 else 0.0
    days_in_inventory = round(365 / turnover_rate, 1) if turnover_rate > 0 else 0.0

    # Total Purchases
    purchases = (
        db.query(Transaction)
        .filter(Transaction.transaction_type == "PURCHASE")
        .all()
    )
    total_purchases_val = sum(t.total_amount for t in purchases)

    return {
        "active_skus": active_skus,
        "total_units_in_stock": round(total_units_in_stock, 1),
        "low_stock_count": low_stock_count,
        "total_valuation_wac": round(total_wac_val, 2),
        "total_valuation_fifo": round(total_fifo_val, 2),
        "total_valuation_lifo": round(total_lifo_val, 2),
        "total_revenue": round(total_revenue, 2),
        "total_cogs": round(total_cogs_wac, 2),
        "gross_profit": round(total_revenue - total_cogs_wac, 2),
        "gross_margin_pct": round(((total_revenue - total_cogs_wac) / total_revenue * 100), 2) if total_revenue > 0 else 0.0,
        "turnover_rate": turnover_rate,
        "days_in_inventory": days_in_inventory,
        "total_purchases_val": round(total_purchases_val, 2),
        "total_transactions_count": len(sales_transactions) + len(purchases)
    }


@router.get("/charts", response_model=Dict[str, Any])
def get_dashboard_charts(db: Session = Depends(get_db)):
    """
    Returns structured datasets for Chart.js rendering on the Executive Dashboard:
    - Stock Valuation Breakdown by Category
    - Comparative Valuation (FIFO vs WAC vs LIFO)
    - Monthly/Transaction Activity Stream
    """
    items = db.query(Item).all()
    
    # Category Breakdown
    category_map: Dict[str, float] = {}
    for itm in items:
        val = itm.current_stock * itm.moving_avg_cost
        category_map[itm.category] = category_map.get(itm.category, 0.0) + val

    category_labels = list(category_map.keys())
    category_values = [round(v, 2) for v in category_map.values()]

    # Method Comparison
    total_fifo = sum(compute_item_valuation_by_method(db, itm, "FIFO")["valuation"] for itm in items)
    total_wac = sum(compute_item_valuation_by_method(db, itm, "WAC")["valuation"] for itm in items)
    total_lifo = sum(compute_item_valuation_by_method(db, itm, "LIFO")["valuation"] for itm in items)

    # Recent Transactions for mini feed
    recent_txs = (
        db.query(Transaction)
        .order_by(Transaction.timestamp.desc())
        .limit(6)
        .all()
    )
    
    tx_feed = []
    for tx in recent_txs:
        tx_feed.append({
            "id": tx.id,
            "type": tx.transaction_type,
            "sku": tx.item.sku if tx.item else "N/A",
            "name": tx.item.name if tx.item else "N/A",
            "quantity": tx.quantity,
            "amount": tx.total_amount,
            "timestamp": tx.timestamp.strftime("%Y-%m-%d %H:%M")
        })

    return {
        "categories": {
            "labels": category_labels if category_labels else ["No Items"],
            "values": category_values if category_values else [0]
        },
        "methods_comparison": {
            "labels": ["FIFO (First-In, First-Out)", "WAC (Weighted Average)", "LIFO (Last-In, First-Out)"],
            "values": [round(total_fifo, 2), round(total_wac, 2), round(total_lifo, 2)]
        },
        "recent_feed": tx_feed
    }
