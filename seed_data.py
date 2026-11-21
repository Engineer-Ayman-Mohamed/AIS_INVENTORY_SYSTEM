"""
Seed Data Script for AIS Inventory Management & Valuation System
Populates initial sample demonstration data:
- Catalog of 6 representative retail SKUs across categories
- Initial Goods In purchases with distinct cost layers across different dates
- Goods Out sales generating perpetual COGS under FIFO/WAC/LIFO
- One physical reconciliation record with 2% threshold evaluation
- Complete audit trail entries

Usage:
  python seed_data.py
"""

from datetime import datetime, timedelta, timezone
from app.database import SessionLocal, init_db
from app.models import Item, CostLayer, Transaction, PhysicalAudit, AuditLog
from app.config import settings
from app.accounting import (
    update_moving_average_cost_on_purchase,
    calculate_fifo_cogs_and_consume,
    calculate_lifo_cogs_simulated
)


def seed_database():
    """Seeds sample data into the database."""
    init_db()
    db = SessionLocal()

    # Check if data already exists
    existing_items = db.query(Item).count()
    if existing_items > 0:
        print("[INFO] Database already contains records. Skipping seed.")
        db.close()
        return

    print("[START] Seeding demonstration AIS inventory data...")

    now = datetime.now(timezone.utc)
    operator = settings.DEFAULT_OPERATOR

    # 1. Create Initial Items
    initial_items = [
        {
            "sku": "SKU-KEY-01",
            "name": "RGB Wireless Mechanical Keyboard",
            "category": "Electronics",
            "unit": "Unit",
            "reorder_level": 15.0,
            "selling_price": 89.99
        },
        {
            "sku": "SKU-MOU-02",
            "name": "Precision Ergonomic Optical Mouse",
            "category": "Electronics",
            "unit": "Unit",
            "reorder_level": 20.0,
            "selling_price": 45.00
        },
        {
            "sku": "SKU-HUB-03",
            "name": "7-in-1 Multiport USB-C Hub",
            "category": "Accessories",
            "unit": "Unit",
            "reorder_level": 25.0,
            "selling_price": 34.50
        },
        {
            "sku": "SKU-MON-04",
            "name": "Ultra-Wide 27-inch 4K IPS Monitor",
            "category": "Displays",
            "unit": "Unit",
            "reorder_level": 8.0,
            "selling_price": 289.00
        },
        {
            "sku": "SKU-HDS-05",
            "name": "Noise-Cancelling Wireless Headset",
            "category": "Audio",
            "unit": "Unit",
            "reorder_level": 12.0,
            "selling_price": 79.99
        },
        {
            "sku": "SKU-PAD-06",
            "name": "Extended Desk Mat Waterproof",
            "category": "Accessories",
            "unit": "Unit",
            "reorder_level": 30.0,
            "selling_price": 18.00
        }
    ]

    item_objs = {}
    for itm in initial_items:
        obj = Item(
            sku=itm["sku"],
            name=itm["name"],
            category=itm["category"],
            unit_of_measure=itm["unit"],
            reorder_level=itm["reorder_level"],
            selling_price=itm["selling_price"],
            current_stock=0.0,
            moving_avg_cost=0.0
        )
        db.add(obj)
        db.flush()
        item_objs[itm["sku"]] = obj

        audit = AuditLog(
            action="CREATE_ITEM",
            entity_name="Item",
            entity_id=obj.id,
            operator=operator,
            details=f"Master item created: {obj.sku} - {obj.name}"
        )
        db.add(audit)

    db.commit()

    # 2. Add Goods In (Purchases) with distinct Cost Layers over time
    purchases_plan = [
        # Keyboard Lot 1 (15 days ago)
        {"sku": "SKU-KEY-01", "days_ago": 15, "qty": 40.0, "cost": 42.00, "supplier": "TechSupply Co", "ref": "PO-2026-01"},
        # Keyboard Lot 2 (5 days ago - price increase to illustrate FIFO vs LIFO differences)
        {"sku": "SKU-KEY-01", "days_ago": 5, "qty": 30.0, "cost": 48.00, "supplier": "TechSupply Co", "ref": "PO-2026-08"},
        
        # Mouse Lot 1
        {"sku": "SKU-MOU-02", "days_ago": 14, "qty": 50.0, "cost": 20.00, "supplier": "Peripheral World", "ref": "PO-2026-02"},
        # Mouse Lot 2 (inflationary price)
        {"sku": "SKU-MOU-02", "days_ago": 4, "qty": 40.0, "cost": 24.00, "supplier": "Peripheral World", "ref": "PO-2026-09"},
        
        # USB-C Hub (low stock demonstration: small initial purchase)
        {"sku": "SKU-HUB-03", "days_ago": 12, "qty": 20.0, "cost": 15.00, "supplier": "ConnectFast Ltd", "ref": "PO-2026-03"},
        
        # Monitor Lot 1
        {"sku": "SKU-MON-04", "days_ago": 10, "qty": 15.0, "cost": 180.00, "supplier": "Visionary Tech", "ref": "PO-2026-04"},
        # Monitor Lot 2
        {"sku": "SKU-MON-04", "days_ago": 2, "qty": 10.0, "cost": 195.00, "supplier": "Visionary Tech", "ref": "PO-2026-10"},
        
        # Headset Lot 1
        {"sku": "SKU-HDS-05", "days_ago": 8, "qty": 30.0, "cost": 38.00, "supplier": "Acoustic Labs", "ref": "PO-2026-05"},
        
        # Desk Mat Lot 1
        {"sku": "SKU-PAD-06", "days_ago": 7, "qty": 100.0, "cost": 7.50, "supplier": "ErgoGear Inc", "ref": "PO-2026-06"}
    ]

    for p in purchases_plan:
        item = item_objs[p["sku"]]
        p_date = now - timedelta(days=p["days_ago"])
        
        # Update moving average
        new_wac = update_moving_average_cost_on_purchase(
            current_stock=item.current_stock,
            current_moving_avg=item.moving_avg_cost,
            purchased_qty=p["qty"],
            purchased_unit_cost=p["cost"]
        )
        item.moving_avg_cost = new_wac
        item.current_stock += p["qty"]

        # Create Cost Layer
        layer = CostLayer(
            item_id=item.id,
            purchase_date=p_date,
            original_quantity=p["qty"],
            remaining_quantity=p["qty"],
            unit_cost=p["cost"],
            supplier=p["supplier"],
            reference=p["ref"]
        )
        db.add(layer)

        # Create Purchase Transaction
        tx = Transaction(
            transaction_type="PURCHASE",
            item_id=item.id,
            quantity=p["qty"],
            unit_price=p["cost"],
            total_amount=round(p["qty"] * p["cost"], 2),
            reference=p["ref"],
            party=p["supplier"],
            operator=operator,
            timestamp=p_date
        )
        db.add(tx)
        db.flush()

        # Audit
        audit = AuditLog(
            action="GOODS_IN",
            entity_name="Transaction",
            entity_id=tx.id,
            operator=operator,
            details=f"Received {p['qty']} {item.unit_of_measure} for '{item.sku}' @ ${p['cost']:.2f}. Ref: {p['ref']}",
            timestamp=p_date
        )
        db.add(audit)

    db.commit()

    # 3. Add Goods Out (Sales) to showcase FIFO / WAC / LIFO divergence
    sales_plan = [
        # Keyboard sale: 25 units (takes from Lot 1 @ $42)
        {"sku": "SKU-KEY-01", "days_ago": 3, "qty": 25.0, "price": 89.99, "cust": "Global Tech Retail", "ref": "INV-2026-01"},
        # Keyboard sale: 25 units (takes remaining 15 from Lot 1 @ $42 + 10 from Lot 2 @ $48)
        {"sku": "SKU-KEY-01", "days_ago": 1, "qty": 25.0, "price": 89.99, "cust": "Prime Solutions", "ref": "INV-2026-05"},
        
        # Mouse sale: 45 units
        {"sku": "SKU-MOU-02", "days_ago": 2, "qty": 45.0, "price": 45.00, "cust": "City Electronics", "ref": "INV-2026-02"},
        
        # USB-C Hub sale: 8 units (leaving 12, which is below reorder level 25 -> low stock trigger!)
        {"sku": "SKU-HUB-03", "days_ago": 3, "qty": 8.0, "price": 34.50, "cust": "EduStore Campus", "ref": "INV-2026-03"},
        
        # Monitor sale: 12 units
        {"sku": "SKU-MON-04", "days_ago": 1, "qty": 12.0, "price": 289.00, "cust": "Alpha Tech Studio", "ref": "INV-2026-04"},
        
        # Desk Mat sale: 40 units
        {"sku": "SKU-PAD-06", "days_ago": 2, "qty": 40.0, "price": 18.00, "cust": "Retail Network", "ref": "INV-2026-06"}
    ]

    for s in sales_plan:
        item = item_objs[s["sku"]]
        s_date = now - timedelta(days=s["days_ago"])
        
        cogs_fifo = calculate_fifo_cogs_and_consume(db, item.id, s["qty"], commit_consumption=True)
        cogs_wac = round(s["qty"] * item.moving_avg_cost, 2)
        cogs_lifo = calculate_lifo_cogs_simulated(db, item.id, s["qty"])

        item.current_stock -= s["qty"]
        tot_rev = round(s["qty"] * s["price"], 2)

        tx = Transaction(
            transaction_type="SALE",
            item_id=item.id,
            quantity=s["qty"],
            unit_price=s["price"],
            total_amount=tot_rev,
            cogs_fifo=cogs_fifo,
            cogs_wac=cogs_wac,
            cogs_lifo=cogs_lifo,
            reference=s["ref"],
            party=s["cust"],
            operator=operator,
            timestamp=s_date
        )
        db.add(tx)
        db.flush()

        audit = AuditLog(
            action="GOODS_OUT",
            entity_name="Transaction",
            entity_id=tx.id,
            operator=operator,
            details=f"Sales of {s['qty']} {item.unit_of_measure} for '{item.sku}'. Rev: ${tot_rev:.2f}. FIFO COGS: ${cogs_fifo:.2f}",
            timestamp=s_date
        )
        db.add(audit)

    db.commit()

    # 4. Add Sample Physical Audit Record (Reconciliation)
    # Reconcile Headset: Book stock is 30, physical counted was 29 (3.33% variance -> exceeds 2% threshold!)
    headset = item_objs["SKU-HDS-05"]
    variance = 29.0 - headset.current_stock
    var_pct = round((abs(variance) / headset.current_stock) * 100.0, 2)
    exceeds = var_pct > 2.0

    p_audit = PhysicalAudit(
        item_id=headset.id,
        book_stock=headset.current_stock,
        physical_count=29.0,
        variance=variance,
        variance_pct=var_pct,
        exceeds_threshold=exceeds,
        adjusted=False,
        operator=operator,
        notes="Physical count identified 1 unit missing in bin B-4. Shrinkage investigation initiated.",
        timestamp=now - timedelta(hours=6)
    )
    db.add(p_audit)
    db.flush()

    audit_entry = AuditLog(
        action="RECONCILE",
        entity_name="PhysicalAudit",
        entity_id=p_audit.id,
        operator=operator,
        details=f"Audit for '{headset.sku}': Book={headset.current_stock}, Physical=29.0. Variance={variance:+.1f} ({var_pct}%). Exceeds 2% tolerance: True",
        timestamp=now - timedelta(hours=6)
    )
    db.add(audit_entry)

    db.commit()
    db.close()
    print("[SUCCESS] Demonstration database seeded successfully!")


if __name__ == "__main__":
    seed_database()
