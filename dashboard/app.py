"""Interactive Streamlit dashboard for the Supply Chain & Delivery Risk project.

Run with: streamlit run dashboard/app.py
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"

st.set_page_config(page_title="Supply Chain & Delivery Risk Analytics", layout="wide",
                    page_icon="🚚")


@st.cache_data
def load_data():
    return pd.read_csv(DATA / "orders_clean.csv", parse_dates=["order_date", "shipping_date"])


df = load_data()

st.title("🚚 Supply Chain & Delivery Risk Analytics")
st.caption("DataCo Global — 180,519 order line items across 65,752 orders, "
           "Jan 2015 - Jan 2018, 5 markets")

# ------------------------------------------------------------- Sidebar ----
st.sidebar.header("Filters")
markets = ["All"] + sorted(df["market"].unique().tolist())
market_sel = st.sidebar.selectbox("Market", markets)
modes = ["All"] + sorted(df["shipping_mode"].unique().tolist())
mode_sel = st.sidebar.selectbox("Shipping mode", modes)

view = df.copy()
if market_sel != "All":
    view = view[view["market"] == market_sel]
if mode_sel != "All":
    view = view[view["shipping_mode"] == mode_sel]

# --------------------------------------------------------------- KPIs -----
c1, c2, c3, c4 = st.columns(4)
c1.metric("Orders", f"{view['order_id'].nunique():,}")
c2.metric("Late delivery rate", f"{(view['late_delivery_risk'] == 1).mean():.1%}")
c3.metric("Avg. shipping gap", f"{(view['shipping_days_actual'] - view['shipping_days_scheduled']).mean():+.1f} days")
c4.metric("Loss-making line items", f"{(view['profit_per_order'] < 0).mean():.1%}")

st.divider()

# --------------------------------------------------- Delivery risk view ---
left, right = st.columns(2)
with left:
    st.subheader("Late Delivery Rate by Shipping Mode")
    by_mode = (view.groupby("shipping_mode")["late_delivery_risk"].mean() * 100).sort_values()
    fig = px.bar(by_mode, orientation="h", color=by_mode.values, color_continuous_scale="Reds")
    fig.update_layout(height=350, showlegend=False, coloraxis_showscale=False,
                       xaxis_title="Late delivery rate (%)", yaxis_title=None,
                       margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Delivery Status Breakdown")
    status = view["delivery_status"].value_counts()
    fig2 = px.pie(status, values=status.values, names=status.index, hole=0.4)
    fig2.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ------------------------------------------------------------- Trend -----
st.subheader("Monthly Late-Delivery Rate Trend")
monthly = view.groupby("order_year_month").agg(
    late_rate=("late_delivery_risk", "mean"), orders=("order_id", "nunique")).reset_index()
monthly = monthly[(monthly["order_year_month"] > monthly["order_year_month"].min()) &
                   (monthly["order_year_month"] < monthly["order_year_month"].max())]
fig3 = go.Figure()
fig3.add_trace(go.Scatter(x=monthly["order_year_month"], y=monthly["late_rate"] * 100,
                           mode="lines+markers", line=dict(color="#dc2626")))
fig3.update_layout(height=380, yaxis_title="Late delivery rate (%)", xaxis_title=None,
                    margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ------------------------------------------------- Profitability view ----
st.subheader("Profitability by Category")
by_cat = view.groupby("category_name").agg(
    revenue=("sales", "sum"), profit=("profit_per_order", "sum")).reset_index()
by_cat = by_cat.sort_values("profit")
show_n = st.slider("Show N least/most profitable categories (each side)", 3, 15, 5)
combined = pd.concat([by_cat.head(show_n), by_cat.tail(show_n)])
fig4 = px.bar(combined, x="profit", y="category_name", orientation="h",
              color=combined["profit"] > 0, color_discrete_map={True: "#059669", False: "#dc2626"})
fig4.update_layout(height=500, showlegend=False, xaxis_title="Total profit ($)",
                    yaxis_title=None, margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig4, use_container_width=True)

st.caption("Data: Kaggle DataCo Smart Supply Chain. Built by Nahid Hasan Lipu — "
           "[GitHub](https://github.com/nahid-hasan-lipu) · "
           "[LinkedIn](https://www.linkedin.com/in/nahid-hasan-lipu-922447355/)")
