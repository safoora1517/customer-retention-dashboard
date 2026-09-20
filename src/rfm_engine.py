import pandas as pd
import numpy as np
from datetime import datetime

def calculate_rfm(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates RFM metrics and assigns customer segments."""
    reference_date = df["order_date"].max() + pd.Timedelta(days=1)

    rfm = df.groupby("customer_id").agg({
        "order_date": lambda dates: (reference_date - dates.max()).days,
        "order_id": "nunique",
        "revenue": "sum"
    }).reset_index()

    rfm.columns = ["customer_id", "recency", "frequency", "monetary"]
    rfm["monetary"] = rfm["monetary"].round(2)

    # 1-5 Quantile scoring (higher recency score = bought more recently)
    rfm["R_score"] = pd.qcut(rfm["recency"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["F_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["M_score"] = pd.qcut(rfm["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)

    def classify_segment(row):
        r, f = row["R_score"], row["F_score"]
        if r >= 4 and f >= 4:
            return "Champions"
        elif r >= 3 and f >= 3:
            return "Loyal Customers"
        elif r >= 4 and f < 3:
            return "Promising / Recent"
        elif r == 3 and f < 3:
            return "Needs Attention"
        elif r < 3 and f >= 3:
            return "At Risk (High Value)"
        elif r == 2 and f < 3:
            return "Hibernating"
        else:
            return "Lost / Churned"

    rfm["segment"] = rfm.apply(classify_segment, axis=1)
    return rfm

def calculate_cohort_retention(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates monthly customer retention percentage cohorts."""
    data = df.copy()
    data["order_month"] = data["order_date"].dt.to_period("M")
    data["cohort_month"] = data.groupby("customer_id")["order_date"].transform("min").dt.to_period("M")

    cohort_group = data.groupby(["cohort_month", "order_month"])["customer_id"].nunique().reset_index()
    
    # Calculate period index (Month 0, Month 1, etc.)
    cohort_group["period_number"] = (
        (cohort_group["order_month"].dt.year - cohort_group["cohort_month"].dt.year) * 12 +
        (cohort_group["order_month"].dt.month - cohort_group["cohort_month"].dt.month)
    )

    cohort_pivot = cohort_group.pivot(index="cohort_month", columns="period_number", values="customer_id")
    cohort_size = cohort_pivot.iloc[:, 0]
    retention_matrix = cohort_pivot.divide(cohort_size, axis=0) * 100
    retention_matrix.index = retention_matrix.index.astype(str)
    
    return retention_matrix.round(1)