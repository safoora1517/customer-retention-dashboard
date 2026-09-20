import os
import streamlit as st
import plotly.express as px
import plotly.figure_factory as ff
from src.data_generator import generate_mock_transactions
from src.rfm_engine import calculate_rfm, calculate_cohort_retention

# Page configuration
st.set_page_config(
    page_title="Retention & Revenue Health Dashboard",
    page_icon="📈",
    layout="wide"
)

# Load data
DATA_PATH = os.path.join("data", "transactions.csv")
raw_df = generate_mock_transactions(DATA_PATH)

# Sidebar Controls
st.sidebar.title("Dashboard Controls")
st.sidebar.markdown("Filter customer purchase behavior across business timelines.")

min_date = raw_df["order_date"].min().date()
max_date = raw_df["order_date"].max().date()

date_range = st.sidebar.date_input(
    "Select Transaction Window",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_d, end_d = date_range
    df = raw_df[(raw_df["order_date"].dt.date >= start_d) & (raw_df["order_date"].dt.date <= end_d)]
else:
    df = raw_df

# Engine processing
rfm_df = calculate_rfm(df)
cohort_retention = calculate_cohort_retention(df)

# Header
st.title("📊 Customer Retention & Revenue Health Dashboard")
st.caption("Commercial KPI tracking, RFM customer segmentation, and cohort retention diagnostics.")

# Top-level KPI Metrics
total_revenue = df["revenue"].sum()
total_orders = df["order_id"].nunique()
active_customers = df["customer_id"].nunique()
avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
at_risk_count = rfm_df[rfm_df["segment"].isin(["At Risk (High Value)", "Lost / Churned"])]["customer_id"].count()
churn_risk_rate = (at_risk_count / active_customers * 100) if active_customers > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"${total_revenue:,.2f}")
col2.metric("Active Customers", f"{active_customers:,}")
col3.metric("Avg Order Value (AOV)", f"${avg_order_value:,.2f}")
col4.metric("Churn Risk Rate", f"{churn_risk_rate:.1f}%", delta=f"-{at_risk_count} critical accounts", delta_color="inverse")

st.markdown("---")

# Section 1: Customer Segmentation Breakdown
col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("Customer Health Segments (RFM)")
    seg_summary = rfm_df.groupby("segment").agg(
        customers=("customer_id", "count"),
        total_value=("monetary", "sum"),
        avg_recency=("recency", "mean")
    ).reset_index().sort_values("customers", ascending=False)

    fig_bar = px.bar(
        seg_summary,
        x="segment",
        y="customers",
        color="segment",
        text="customers",
        hover_data={"total_value": ":$,.2f", "avg_recency": ":.0f days"},
        labels={"segment": "Segment", "customers": "Customer Count"},
        title="Distribution of Customers Across RFM Tiers"
    )
    fig_bar.update_layout(showlegend=False, xaxis_tickangle=-30)
    st.plotly_chart(fig_bar, use_container_width=True)

with col_right:
    st.subheader("Revenue Contribution by Tier")
    fig_donut = px.pie(
        seg_summary,
        names="segment",
        values="total_value",
        hole=0.45,
        title="Share of Total Revenue ($)"
    )
    st.plotly_chart(fig_donut, use_container_width=True)

# Section 2: Cohort Retention Matrix
st.subheader("📅 Monthly Cohort Retention Heatmap (%)")
st.markdown("Tracks the percentage of new customer cohorts that return to purchase in subsequent months.")

# Plotly Heatmap for Cohort Analysis
cohort_vals = cohort_retention.values
y_labels = list(cohort_retention.index)
x_labels = [f"M+{col}" for col in cohort_retention.columns]

fig_heatmap = px.imshow(
    cohort_vals,
    labels=dict(x="Months Since First Purchase", y="Cohort Month", color="Retention %"),
    x=x_labels,
    y=y_labels,
    color_continuous_scale="Blues",
    text_auto=".1f",
    aspect="auto"
)
fig_heatmap.update_layout(height=450)
st.plotly_chart(fig_heatmap, use_container_width=True)

# Section 3: Actionable Customer Intelligence Table
st.subheader("🎯 Customer Risk & Retargeting Explorer")
st.markdown("Filter and export high-priority customer cohorts for targeted re-engagement campaigns.")

selected_segment = st.selectbox(
    "Filter by Customer Segment:",
    options=["All"] + list(rfm_df["segment"].unique()),
    index=0
)

filtered_table = rfm_df if selected_segment == "All" else rfm_df[rfm_df["segment"] == selected_segment]

st.dataframe(
    filtered_table[["customer_id", "segment", "recency", "frequency", "monetary"]].rename(columns={
        "customer_id": "Customer ID",
        "segment": "Segment Tier",
        "recency": "Days Since Last Order",
        "frequency": "Total Purchases",
        "monetary": "Lifetime Value ($)"
    }),
    use_container_width=True
)

csv_data = filtered_table.to_csv(index=False).encode("utf-8")
st.download_button(
    label=f"⬇️ Download Filtered Data ({len(filtered_table)} Customers)",
    data=csv_data,
    file_name=f"customer_retention_report_{selected_segment.lower().replace(' ', '_')}.csv",
    mime="text/csv"
)