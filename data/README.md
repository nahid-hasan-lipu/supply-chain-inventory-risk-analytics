# Data

**Source**: [DataCo Smart Supply Chain for Big Data Analysis](https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis) (Kaggle, published by shashwatwork). 180,519 order line items across 65,752 orders, Jan 2015 – Jan 2018, 5 global markets.

Not committed to this repo (see `.gitignore`) — download `DataCoSupplyChainDataset.csv` from the link above into `data/raw/`, then run `python src/clean_data.py`.

**Encoding note**: the raw CSV is Latin-1, not UTF-8 — reading it with the default encoding raises a `UnicodeDecodeError`.

## Columns dropped during cleaning, and why

| Column(s) | Reason |
|---|---|
| `Customer Fname`, `Customer Lname`, `Customer Street` | Realistic-looking names/addresses that can't be confirmed synthetic vs. real from inspection alone. Dropped as a precaution — no legitimate analytical need for individual customer names in aggregate delivery/profitability analysis. |
| `Customer Email`, `Customer Password` | Already masked by the dataset publisher (`XXXXXXXXX`), dropped anyway since they carry no information. |
| `Product Description` | 100% null in the source file. |
| `Product Status` | Constant (always 0) across all 180,519 rows — zero information value. |
| `Order Profit Per Order` | Exact duplicate of `Benefit per order` (verified: identical for every row). |
| `Order Zipcode` | 86% missing (155,679 / 180,519 nulls); geographic detail already available via `Order City`/`Order State`/`Order Country`/`Order Region`. |
| `Product Image` | A hotlinked URL, not analytically relevant. |

## Known data-quality quirks (not "corrected", just documented)

- **`Category Name` "Electronics" maps to two different `Category Id` values** (13 under Department "Footwear", 37 under "Outdoors") — a genuine inconsistency in the source data. Left as-is rather than guessing which mapping is "correct."
- **Grain is line-item level, not order level**: 180,519 rows across 65,752 distinct orders (~2.75 line items per order on average). `late_delivery_risk` and `delivery_status` are recorded per line item but logically describe the whole order's shipment — this dataset doesn't distinguish partial-order shipments, so line-item-level aggregation is treated as equivalent to order-level for this analysis.
- **No inventory/stock-level data**: this is an order and shipment transaction log, not a warehouse inventory system — there's no stock-on-hand, reorder point, or COGS data. A literal "inventory turnover" metric can't be honestly computed from this dataset; the analysis instead focuses on delivery risk, fulfillment performance, and product/category profitability, which the data does support.
