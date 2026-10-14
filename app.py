import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Retail KPI Dashboard", page_icon="📊", layout="wide")
st.title("📊 Retail Performance & Customer Insights")
st.caption("RABTECH Academy · Task 05 · Interactive KPI dashboard")

@st.cache_data
def load_data():
    candidates = ["clean_dataset.csv", "retail_ab_test_10000.csv"]
    for path in candidates:
        if os.path.exists(path):
            return pd.read_csv(path), path
    return None, None

import os
df, source = load_data()
if df is None:
    st.error("CSV not found. Place clean_dataset.csv or retail_ab_test_10000.csv in the same folder as app.py.")
    st.stop()

st.sidebar.header("Filters")
filtered = df.copy()

if "experiment_group" in filtered.columns:
    options = sorted(filtered["experiment_group"].dropna().astype(str).unique())
    chosen = st.sidebar.multiselect("Experiment group", options, default=options)
    if chosen:
        filtered = filtered[filtered["experiment_group"].astype(str).isin(chosen)]

if "region" in filtered.columns:
    options = sorted(filtered["region"].dropna().astype(str).unique())
    chosen = st.sidebar.multiselect("Region", options, default=options)
    if chosen:
        filtered = filtered[filtered["region"].astype(str).isin(chosen)]

if "device" in filtered.columns:
    options = sorted(filtered["device"].dropna().astype(str).unique())
    chosen = st.sidebar.multiselect("Device", options, default=options)
    if chosen:
        filtered = filtered[filtered["device"].astype(str).isin(chosen)]

if filtered.empty:
    st.warning("No records match the selected filters.")
    st.stop()

# Determine conversion metric from available columns
conversion_col = "conversion_flag" if "conversion_flag" in filtered.columns else ("purchased" if "purchased" in filtered.columns else None)
purchase_mask = filtered["purchased"].eq(1) if "purchased" in filtered.columns else pd.Series(False, index=filtered.index)

revenue = filtered.loc[purchase_mask, "order_value"].fillna(0).sum() if "order_value" in filtered.columns and "purchased" in filtered.columns else (filtered["order_value"].fillna(0).sum() if "order_value" in filtered.columns else 0)
orders = int(purchase_mask.sum()) if "purchased" in filtered.columns else (int((filtered["order_value"].fillna(0) > 0).sum()) if "order_value" in filtered.columns else 0)
customers = filtered["customer_id"].nunique() if "customer_id" in filtered.columns else len(filtered)
conversion = filtered[conversion_col].mean() if conversion_col else 0
aov = revenue / orders if orders else 0
return_rate = filtered["returned"].mean() if "returned" in filtered.columns else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Revenue", f"{revenue:,.2f}")
c2.metric("Conversion Rate", f"{conversion:.1%}")
c3.metric("Average Order Value", f"{aov:,.2f}")
c4.metric("Return Rate", f"{return_rate:.1%}")

st.caption(f"Data source: {source} · Records after filters: {len(filtered):,} · Unique customers: {customers:,}")

left, right = st.columns(2)
if "week" in filtered.columns and conversion_col:
    trend = filtered.groupby("week", as_index=False)[conversion_col].mean()
    with left:
        st.subheader("Conversion trend by week")
        st.plotly_chart(px.area(trend, x="week", y=conversion_col, markers=True, title="Weekly conversion rate"), use_container_width=True)
if "experiment_group" in filtered.columns and conversion_col:
    group = filtered.groupby("experiment_group", as_index=False).agg(
        conversion_rate=(conversion_col, "mean"),
        records=(conversion_col, "size")
    )
    with right:
        st.subheader("Conversion by experiment group")
        st.plotly_chart(px.bar(group, x="experiment_group", y="conversion_rate", color="experiment_group",
                               hover_data=["records"], title="Conversion rate by group"), use_container_width=True)

left, right = st.columns(2)
if "region" in filtered.columns and "order_value" in filtered.columns:
    reg = filtered.groupby("region", as_index=False).agg(revenue=("order_value", "sum"))
    with left:
        st.subheader("Revenue by region")
        st.plotly_chart(px.bar(reg, x="region", y="revenue", title="Revenue by region"), use_container_width=True)
if "traffic_source" in filtered.columns and conversion_col:
    traffic = filtered.groupby("traffic_source", as_index=False).agg(conversion_rate=(conversion_col, "mean"))
    with right:
        st.subheader("Conversion by traffic source")
        st.plotly_chart(px.bar(traffic, x="traffic_source", y="conversion_rate", title="Conversion by traffic source"), use_container_width=True)

if "order_value" in filtered.columns:
    st.subheader("Order value distribution")
    st.plotly_chart(px.histogram(filtered, x="order_value", nbins=30, title="Order value distribution"), use_container_width=True)

with st.expander("View filtered data"):
    st.dataframe(filtered, use_container_width=True)

st.download_button("Download filtered data as CSV", filtered.to_csv(index=False).encode("utf-8"),
                   file_name="filtered_retail_data.csv", mime="text/csv")
