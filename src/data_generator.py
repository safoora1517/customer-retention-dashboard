import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_mock_transactions(filepath: str, n_customers: int = 400, n_orders: int = 3500) -> pd.DataFrame:
    """Generates synthetic transactional data with realistic re-order behavior."""
    # Check that the file exists AND is not empty
    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
        return pd.read_csv(filepath, parse_dates=["order_date"])

    np.random.seed(42)
    customer_ids = [f"CUST-{1000 + i}" for i in range(n_customers)]
    categories = ["Electronics", "Apparel", "Home & Kitchen", "Beauty & Care", "Sports"]

    # Customer acquisition dates spread across the last 18 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=540)
    
    records = []
    for _ in range(n_orders):
        cust = np.random.choice(customer_ids)
        random_days = np.random.randint(0, 540)
        order_date = start_date + timedelta(days=int(random_days))
        
        category = np.random.choice(categories, p=[0.25, 0.3, 0.2, 0.15, 0.1])
        quantity = np.random.choice([1, 2, 3, 4], p=[0.6, 0.25, 0.1, 0.05])
        unit_price = {
            "Electronics": 120.0,
            "Apparel": 45.0,
            "Home & Kitchen": 65.0,
            "Beauty & Care": 30.0,
            "Sports": 55.0
        }[category] * np.random.uniform(0.85, 1.25)
        
        revenue = round(quantity * unit_price, 2)
        records.append({
            "order_id": f"ORD-{np.random.randint(100000, 999999)}",
            "customer_id": cust,
            "order_date": order_date,
            "category": category,
            "revenue": revenue
        })

    df = pd.DataFrame(records).sort_values("order_date").reset_index(drop=True)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False)
    return df