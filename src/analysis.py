"""Core analysis: delivery risk, fulfillment performance, product profitability.

Writes result tables to data/processed/ and chart PNGs to figures/, so both
the Streamlit dashboard and the README can reuse the same numbers.
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
FIGS = ROOT / "figures"
FIGS.mkdir(exist_ok=True)

plt.rcParams.update({"figure.dpi": 120, "font.size": 10, "axes.spines.top": False,
                      "axes.spines.right": False})


def load_orders() -> pd.DataFrame:
    return pd.read_csv(DATA / "orders_clean.csv", parse_dates=["order_date", "shipping_date"])


# ------------------------------------------------------- Delivery risk ----
def delivery_risk_by_dimension(df: pd.DataFrame, dim: str) -> pd.Series:
    return (df.groupby(dim)["late_delivery_risk"].mean().sort_values(ascending=False))


def delivery_risk_analysis(df: pd.DataFrame):
    overall_rate = (df["late_delivery_risk"] == 1).mean()

    status_counts = df["delivery_status"].value_counts()
    status_counts.to_csv(DATA / "delivery_status_counts.csv")

    by_shipping_mode = delivery_risk_by_dimension(df, "shipping_mode")
    by_market = delivery_risk_by_dimension(df, "market")
    by_segment = delivery_risk_by_dimension(df, "customer_segment")
    by_department = delivery_risk_by_dimension(df, "department_name")

    by_shipping_mode.to_csv(DATA / "late_risk_by_shipping_mode.csv")
    by_market.to_csv(DATA / "late_risk_by_market.csv")
    by_segment.to_csv(DATA / "late_risk_by_segment.csv")
    by_department.to_csv(DATA / "late_risk_by_department.csv")

    # Delivery status breakdown (donut)
    fig, ax = plt.subplots(figsize=(6, 6))
    colors = ["#dc2626", "#2563eb", "#059669", "#d97706"]
    status_counts.plot(kind="pie", ax=ax, autopct="%1.1f%%", startangle=90,
                        colors=colors, wedgeprops=dict(width=0.4))
    ax.set_ylabel("")
    ax.set_title("Delivery Status Breakdown (180,519 line items)")
    plt.tight_layout()
    plt.savefig(FIGS / "delivery_status_breakdown.png")
    plt.close()

    # Late delivery rate by shipping mode
    fig, ax = plt.subplots(figsize=(7, 4))
    (by_shipping_mode * 100).plot(kind="barh", ax=ax, color="#dc2626")
    ax.set_xlabel("Late delivery rate (%)")
    ax.set_title("Late Delivery Rate by Shipping Mode")
    ax.axvline(overall_rate * 100, color="black", linestyle="--", linewidth=1,
               label=f"Overall avg ({overall_rate:.1%})")
    ax.legend()
    plt.tight_layout()
    plt.savefig(FIGS / "late_risk_by_shipping_mode.png")
    plt.close()

    # Late delivery rate by market
    fig, ax = plt.subplots(figsize=(7, 4))
    (by_market * 100).plot(kind="barh", ax=ax, color="#2563eb")
    ax.set_xlabel("Late delivery rate (%)")
    ax.set_title("Late Delivery Rate by Market")
    ax.axvline(overall_rate * 100, color="black", linestyle="--", linewidth=1)
    plt.tight_layout()
    plt.savefig(FIGS / "late_risk_by_market.png")
    plt.close()

    return overall_rate, by_shipping_mode, by_market, by_segment, by_department


# --------------------------------------------------- Fulfillment gap ------
def fulfillment_gap_analysis(df: pd.DataFrame):
    df = df.copy()
    df["shipping_gap_days"] = df["shipping_days_actual"] - df["shipping_days_scheduled"]

    gap_by_mode = df.groupby("shipping_mode")["shipping_gap_days"].mean().sort_values(ascending=False)
    gap_by_mode.to_csv(DATA / "shipping_gap_by_mode.csv")

    monthly = df.groupby("order_year_month").agg(
        orders=("order_id", "nunique"),
        late_rate=("late_delivery_risk", "mean"),
        avg_gap=("shipping_gap_days", "mean"),
    ).reset_index()
    monthly = monthly.iloc[1:-1].reset_index(drop=True)  # drop partial edge months
    monthly.to_csv(DATA / "monthly_fulfillment_trend.csv", index=False)

    fig, ax1 = plt.subplots(figsize=(9, 4))
    ax1.plot(monthly["order_year_month"], monthly["late_rate"] * 100, color="#dc2626",
             marker="o", ms=3)
    ax1.set_ylabel("Late delivery rate (%)", color="#dc2626")
    ax1.set_title("Monthly Late-Delivery Rate Trend")
    plt.xticks(rotation=60, ha="right", fontsize=7)
    plt.tight_layout()
    plt.savefig(FIGS / "monthly_late_rate_trend.png")
    plt.close()

    order_status = df["order_status"].value_counts()
    order_status.to_csv(DATA / "order_status_counts.csv")
    fig, ax = plt.subplots(figsize=(7, 4))
    order_status.sort_values().plot(kind="barh", ax=ax, color="#7c3aed")
    ax.set_xlabel("Number of line items")
    ax.set_title("Order Status Breakdown")
    plt.tight_layout()
    plt.savefig(FIGS / "order_status_breakdown.png")
    plt.close()

    return gap_by_mode, monthly, order_status


# ------------------------------------------------- Product profitability --
def profitability_analysis(df: pd.DataFrame):
    by_category = df.groupby("category_name").agg(
        revenue=("sales", "sum"),
        profit=("profit_per_order", "sum"),
        orders=("order_id", "nunique"),
    ).sort_values("profit")
    by_category["margin"] = by_category["profit"] / by_category["revenue"]
    by_category.to_csv(DATA / "profitability_by_category.csv")

    loss_making = df[df["profit_per_order"] < 0]
    loss_rate = len(loss_making) / len(df)

    top_loss_products = (df.groupby("product_name")["profit_per_order"].sum()
                          .sort_values().head(10))
    top_loss_products.to_csv(DATA / "top_loss_making_products.csv")

    top_profit_products = (df.groupby("product_name")["profit_per_order"].sum()
                            .sort_values(ascending=False).head(10))
    top_profit_products.to_csv(DATA / "top_profit_products.csv")

    # Two subplots with independent x-axis scales: the most-profitable
    # categories are ~1000x the least-profitable ones in absolute dollars,
    # so a single shared scale visually flattens the "least profitable"
    # side to nothing. Also: none of these are actual losses (see
    # loss_making check below), so amber (not red) avoids implying losses
    # that aren't there.
    worst5 = by_category.head(5)
    best5 = by_category.tail(5).sort_values("profit")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    ax1.barh(worst5.index, worst5["profit"], color="#d97706")
    ax1.set_xlabel("Total profit ($)")
    ax1.set_title("5 Least Profitable Categories")

    ax2.barh(best5.index, best5["profit"], color="#059669")
    ax2.set_xlabel("Total profit ($)")
    ax2.set_title("5 Most Profitable Categories")

    fig.suptitle("Category Profitability — note the two panels use different x-axis scales", y=1.02)
    plt.tight_layout()
    plt.savefig(FIGS / "profitability_by_category.png", bbox_inches="tight")
    plt.close()

    return by_category, loss_rate, top_loss_products, top_profit_products


def main():
    df = load_orders()

    overall_rate, by_mode, by_market, by_segment, by_dept = delivery_risk_analysis(df)
    gap_by_mode, monthly, order_status = fulfillment_gap_analysis(df)
    by_category, loss_rate, top_loss, top_profit = profitability_analysis(df)

    print(f"=== Overall late delivery rate: {overall_rate:.1%} ===")
    print("\n--- Late risk by shipping mode ---")
    print(by_mode)
    print("\n--- Late risk by market ---")
    print(by_market)
    print(f"\n--- Loss-making line items: {loss_rate:.1%} ---")
    print("\n--- Worst 3 categories by total profit ---")
    print(by_category.head(3))
    print("\nAll outputs written to data/processed/ and figures/")


if __name__ == "__main__":
    main()
