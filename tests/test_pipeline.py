"""Sanity checks for the cleaning and analysis pipeline.

Run with: pytest tests/
"""
import pandas as pd
import pytest
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data" / "processed"


@pytest.fixture(scope="module")
def orders():
    path = DATA / "orders_clean.csv"
    if not path.exists():
        pytest.skip("Run src/clean_data.py first to generate processed data.")
    return pd.read_csv(path, parse_dates=["order_date", "shipping_date"])


def test_no_pii_columns_present(orders):
    pii_columns = {"Customer Fname", "Customer Lname", "Customer Email",
                    "Customer Password", "Customer Street"}
    assert pii_columns.isdisjoint(orders.columns)


def test_late_delivery_risk_is_binary(orders):
    assert set(orders["late_delivery_risk"].unique()) <= {0, 1}


def test_late_delivery_risk_matches_delivery_status(orders):
    late_status = orders.loc[orders["delivery_status"] == "Late delivery", "late_delivery_risk"]
    not_late_status = orders.loc[orders["delivery_status"] != "Late delivery", "late_delivery_risk"]
    assert (late_status == 1).all()
    assert (not_late_status == 0).all()


def test_no_negative_quantities_or_prices(orders):
    assert (orders["order_item_quantity"] > 0).all()
    assert (orders["order_item_product_price"] > 0).all()


def test_shipping_date_not_before_order_date(orders):
    assert (orders["shipping_date"] >= orders["order_date"]).all()


def test_sales_equals_price_times_quantity(orders):
    expected = orders["order_item_product_price"] * orders["order_item_quantity"]
    assert (orders["sales"] - expected).abs().max() < 1e-2
