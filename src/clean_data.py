"""Clean the raw DataCo Supply Chain dataset into an analysis-ready orders file.

Source: Kaggle shashwatwork/dataco-smart-supply-chain-for-big-data-analysis
180,519 line items across 65,752 orders, Jan 2015 - Jan 2018.

Deliberate column drops (see data/README.md for the full rationale):
- Customer Fname/Lname/Email/Password/Street: no analytical value, and
  Fname/Lname/Street can't be confirmed synthetic vs real, so excluded
  entirely regardless (Email/Password are already masked by the publisher).
- Product Description: 100% null in the source file.
- Product Status: constant (always 0) - zero information value.
- Order Profit Per Order: exact duplicate of Benefit per order.
- Order Zipcode: 86% missing, redundant with Order City/State/Country.
"""
import pandas as pd
from pathlib import Path

RAW_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "DataCoSupplyChainDataset.csv"
OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "orders_clean.csv"

DROP_COLUMNS = [
    "Customer Fname", "Customer Lname", "Customer Email", "Customer Password",
    "Customer Street", "Product Description", "Product Status",
    "Order Profit Per Order", "Order Zipcode", "Product Image",
]

RENAME_MAP = {
    "Type": "payment_type",
    "Days for shipping (real)": "shipping_days_actual",
    "Days for shipment (scheduled)": "shipping_days_scheduled",
    "Benefit per order": "profit_per_order",
    "Sales per customer": "sales_per_customer",
    "Delivery Status": "delivery_status",
    "Late_delivery_risk": "late_delivery_risk",
    "Category Id": "category_id",
    "Category Name": "category_name",
    "Customer City": "customer_city",
    "Customer Country": "customer_country",
    "Customer Id": "customer_id",
    "Customer Segment": "customer_segment",
    "Customer State": "customer_state",
    "Customer Zipcode": "customer_zipcode",
    "Department Id": "department_id",
    "Department Name": "department_name",
    "Latitude": "latitude",
    "Longitude": "longitude",
    "Market": "market",
    "Order City": "order_city",
    "Order Country": "order_country",
    "Order Customer Id": "order_customer_id",
    "order date (DateOrders)": "order_date",
    "Order Id": "order_id",
    "Order Item Cardprod Id": "order_item_cardprod_id",
    "Order Item Discount": "order_item_discount",
    "Order Item Discount Rate": "order_item_discount_rate",
    "Order Item Id": "order_item_id",
    "Order Item Product Price": "order_item_product_price",
    "Order Item Profit Ratio": "order_item_profit_ratio",
    "Order Item Quantity": "order_item_quantity",
    "Sales": "sales",
    "Order Item Total": "order_item_total",
    "Order Region": "order_region",
    "Order State": "order_state",
    "Order Status": "order_status",
    "Product Card Id": "product_card_id",
    "Product Category Id": "product_category_id",
    "Product Name": "product_name",
    "Product Price": "product_price",
    "shipping date (DateOrders)": "shipping_date",
    "Shipping Mode": "shipping_mode",
}


def load_raw() -> pd.DataFrame:
    # Source file is Latin-1 encoded, not UTF-8 (confirmed by inspection).
    return pd.read_csv(RAW_PATH, encoding="latin1")


def clean(df: pd.DataFrame) -> pd.DataFrame:
    n_start = len(df)

    df = df.drop(columns=DROP_COLUMNS)
    df = df.rename(columns=RENAME_MAP)

    df["order_date"] = pd.to_datetime(df["order_date"])
    df["shipping_date"] = pd.to_datetime(df["shipping_date"])
    df["order_year_month"] = df["order_date"].dt.to_period("M").astype(str)

    df = df.drop_duplicates()

    print(f"Rows: {n_start:,} raw -> {len(df):,} clean (columns: {n_start and df.shape[1]})")
    return df


def main():
    df = clean(load_raw())
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    print(f"Saved: {OUT_PATH} ({len(df):,} rows, {df.shape[1]} columns)")
    print(f"Date range: {df['order_date'].min()} -> {df['order_date'].max()}")
    print(f"Orders: {df['order_id'].nunique():,} | Customers: {df['customer_id'].nunique():,}")
    print(f"Late delivery rate: {(df['late_delivery_risk'] == 1).mean():.1%}")


if __name__ == "__main__":
    main()
