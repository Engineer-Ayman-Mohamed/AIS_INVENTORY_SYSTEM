"""
Accounting Calculation Engine
Operationalizes standard Accounting Information System (AIS) logic:
- FIFO (First-In, First-Out): Issues oldest cost layers first.
- LIFO (Last-In, First-Out): Issues newest cost layers first (Academic illustration with IAS 2.1.9 notice).
- WAC (Weighted Average Cost): Dynamic moving average cost recalculated on purchases.
- Perpetual vs Periodic inventory system derivations.
- ABC Inventory Classification (Pareto 80/15/5 principle).
- Stock Variance and Shrinkage Analysis (2% tolerance rule).
"""

from typing import List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from app.models import Item, CostLayer, Transaction


def calculate_fifo_cogs_and_consume(
    db: Session,
    item_id: int,
    quantity_to_sell: float,
    commit_consumption: bool = False
) -> float:
    """
    Computes COGS using First-In, First-Out (FIFO) algorithm.
    Oldest available cost layers are consumed first.
    If commit_consumption is True, decrements remaining_quantity in database layers.
    """
    # Fetch active cost layers ordered by purchase date ascending (oldest first)
    layers = (
        db.query(CostLayer)
        .filter(CostLayer.item_id == item_id, CostLayer.remaining_quantity > 0)
        .order_by(CostLayer.purchase_date.asc(), CostLayer.id.asc())
        .all()
    )

    remaining_needed = quantity_to_sell
    total_fifo_cogs = 0.0

    for layer in layers:
        if remaining_needed <= 0:
            break

        take_qty = min(layer.remaining_quantity, remaining_needed)
        total_fifo_cogs += take_qty * layer.unit_cost
        remaining_needed -= take_qty

        if commit_consumption:
            layer.remaining_quantity -= take_qty

    return round(total_fifo_cogs, 2)


def calculate_lifo_cogs_simulated(
    db: Session,
    item_id: int,
    quantity_to_sell: float
) -> float:
    """
    Computes simulated COGS using Last-In, First-Out (LIFO) algorithm.
    Newest available cost layers are consumed first.
    Note: Standard IAS 2.1.9 prohibits LIFO; included to demonstrate accounting flexibility.
    """
    # Fetch active cost layers ordered by purchase date descending (newest first)
    layers = (
        db.query(CostLayer)
        .filter(CostLayer.item_id == item_id, CostLayer.remaining_quantity > 0)
        .order_by(CostLayer.purchase_date.desc(), CostLayer.id.desc())
        .all()
    )

    remaining_needed = quantity_to_sell
    total_lifo_cogs = 0.0

    for layer in layers:
        if remaining_needed <= 0:
            break

        take_qty = min(layer.remaining_quantity, remaining_needed)
        total_lifo_cogs += take_qty * layer.unit_cost
        remaining_needed -= take_qty

    return round(total_lifo_cogs, 2)


def compute_item_valuation_by_method(
    db: Session,
    item: Item,
    method: str = "FIFO"
) -> Dict[str, float]:
    """
    Computes the closing inventory valuation and average cost for an item
    based on the specified cost-flow assumption: FIFO, WAC, or LIFO.
    """
    method = method.upper()
    stock = item.current_stock

    if stock <= 0:
        return {"stock": 0.0, "valuation": 0.0, "avg_unit_cost": 0.0}

    if method == "WAC":
        # Weighted Average Cost: stock * moving average cost
        val = stock * item.moving_avg_cost
        return {
            "stock": stock,
            "valuation": round(val, 2),
            "avg_unit_cost": round(item.moving_avg_cost, 2)
        }

    # Query all active layers
    layers_query = (
        db.query(CostLayer)
        .filter(CostLayer.item_id == item.id, CostLayer.remaining_quantity > 0)
    )

    if method == "FIFO":
        # Under FIFO, remaining ending inventory consists of the NEWEST layers
        layers = layers_query.order_by(CostLayer.purchase_date.desc(), CostLayer.id.desc()).all()
    else:  # LIFO
        # Under LIFO, remaining ending inventory consists of the OLDEST layers
        layers = layers_query.order_by(CostLayer.purchase_date.asc(), CostLayer.id.asc()).all()

    remaining_to_value = stock
    total_val = 0.0

    for layer in layers:
        if remaining_to_value <= 0:
            break
        take_qty = min(layer.remaining_quantity, remaining_to_value)
        total_val += take_qty * layer.unit_cost
        remaining_to_value -= take_qty

    # Fallback to moving average if unlayered stock exists
    if remaining_to_value > 0 and item.moving_avg_cost > 0:
        total_val += remaining_to_value * item.moving_avg_cost

    unit_cost = (total_val / stock) if stock > 0 else 0.0

    return {
        "stock": stock,
        "valuation": round(total_val, 2),
        "avg_unit_cost": round(unit_cost, 2)
    }


def update_moving_average_cost_on_purchase(
    current_stock: float,
    current_moving_avg: float,
    purchased_qty: float,
    purchased_unit_cost: float
) -> float:
    """
    Recalculates Weighted Average Cost (WAC) dynamically upon purchase:
    New Average Cost = ((Current Stock * Current Cost) + (New Qty * New Cost)) / (Current Stock + New Qty)
    """
    total_existing_val = max(0.0, current_stock) * max(0.0, current_moving_avg)
    new_purchase_val = purchased_qty * purchased_unit_cost
    new_total_qty = current_stock + purchased_qty

    if new_total_qty <= 0:
        return round(purchased_unit_cost, 2)

    new_avg = (total_existing_val + new_purchase_val) / new_total_qty
    return round(new_avg, 2)


def generate_abc_analysis(items: List[Item], db: Session) -> List[Dict[str, Any]]:
    """
    Performs ABC Inventory Classification based on annual/total usage value.
    Logic:
    - Usage Value = Total Units Sold * Moving Average Cost (or Selling Price)
    - Cumulative value threshold:
        - A Items: 0% to 75% of cumulative value (Highest priority, strict controls)
        - B Items: 75% to 90% of cumulative value (Moderate priority)
        - C Items: 90% to 100% of cumulative value (Bulk/Low priority)
    """
    analysis_records = []
    total_inventory_usage_value = 0.0

    for item in items:
        # Sum total quantity sold from transactions
        sales = (
            db.query(Transaction)
            .filter(Transaction.item_id == item.id, Transaction.transaction_type == "SALE")
            .all()
        )
        total_sold_units = sum(t.quantity for t in sales)
        
        # Calculate usage value (units sold * moving average cost; or stock * cost if no sales yet)
        base_cost = item.moving_avg_cost if item.moving_avg_cost > 0 else item.selling_price
        usage_value = (total_sold_units * base_cost) if total_sold_units > 0 else (item.current_stock * base_cost)
        total_inventory_usage_value += usage_value

        analysis_records.append({
            "item_id": item.id,
            "sku": item.sku,
            "name": item.name,
            "category": item.category,
            "current_stock": item.current_stock,
            "total_sold_units": total_sold_units,
            "unit_cost": base_cost,
            "usage_value": usage_value
        })

    # Sort descending by usage value
    analysis_records.sort(key=lambda x: x["usage_value"], reverse=True)

    # Calculate cumulative percentages and assign A / B / C
    cumulative_value = 0.0
    total_val = total_inventory_usage_value if total_inventory_usage_value > 0 else 1.0

    for record in analysis_records:
        val = record["usage_value"]
        cumulative_value += val
        
        value_share_pct = round((val / total_val) * 100, 2)
        cum_share_pct = round((cumulative_value / total_val) * 100, 2)
        
        record["value_share_pct"] = value_share_pct
        record["cumulative_share_pct"] = cum_share_pct

        if cum_share_pct <= 75.0:
            record["abc_category"] = "A"
            record["recommended_control"] = "Tight Control: Weekly physical count, rigorous reorder monitoring"
        elif cum_share_pct <= 90.0:
            record["abc_category"] = "B"
            record["recommended_control"] = "Moderate Control: Bi-weekly review, standard safety buffer"
        else:
            record["abc_category"] = "C"
            record["recommended_control"] = "Basic Control: Periodic review, bulk order policy"

    return analysis_records


def calculate_reconciliation_variance(book_stock: float, physical_count: float) -> Tuple[float, float, bool]:
    """
    Computes physical count reconciliation variance.
    Internal Control: Flags if absolute variance percentage exceeds 2.0% tolerance.
    Returns: (variance, variance_pct, exceeds_threshold)
    """
    variance = physical_count - book_stock
    if book_stock > 0:
        variance_pct = round((abs(variance) / book_stock) * 100.0, 2)
    elif physical_count > 0:
        variance_pct = 100.0
    else:
        variance_pct = 0.0

    exceeds_threshold = variance_pct > 2.0
    return round(variance, 2), variance_pct, exceeds_threshold
