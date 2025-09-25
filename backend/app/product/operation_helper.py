from app import models
import pandas as pd
from sqlalchemy.orm import Session
from typing import Any, List, Dict
from app.dashboard.llm_helper import infer_columns_with_llm, infer_product_column_with_llm
from app.dashboard.operation_helper import pick_columns_heuristic, _safe_sample_values
from datetime import datetime

PRODUCT_CANDIDATES = ["product","product_name","item","item_name","product_id","item_id","sku","product_code","product_title", "order_item"]

def pick_product_column_heuristic(df):
  lower_to_raw = {c.lower(): c for c in df.columns}
  for k in PRODUCT_CANDIDATES:
    if k in lower_to_raw: return lower_to_raw[k]
  for k in PRODUCT_CANDIDATES:
    for lc, raw in lower_to_raw.items():
      if k in lc: return raw
  return None

def get_total_products(db):
  rows = (db.query(models.FileRow).order_by(models.FileRow.id.desc()).all())
  data_rows = [r.data for r in rows]
  if not data_rows:
    return {"product_column": None, "total_products": 0, "row_count": 0}
  df = pd.DataFrame(data_rows)
  df.columns = [str(c).strip().lower().replace(" ","_") for c in df.columns]
  df = df.where(pd.notnull(df), None)

  product_col = pick_product_column_heuristic(df)
  if not product_col:
    from app.dashboard.llm_helper import infer_product_column_with_llm
    cols = list(df.columns)
    samples = {c: df[c].dropna().astype(str).unique().tolist()[:5] for c in df.columns}
    product_col = infer_product_column_with_llm(cols, samples)

  if not product_col:
    return {"product_column": None, "total_products": 0, "row_count": len(df)}

  return {
    "product_column": product_col,
    "total_products": int(df[product_col].nunique()),
    "row_count": len(df),
  }

def get_top_selling_products(db: Session, limit: int = 5) -> Dict[str, Any]:
    rows: List[models.FileRow] = (
        db.query(models.FileRow)
          .order_by(models.FileRow.id.desc())
          .all()
    )
    data_rows = [r.data for r in rows]
    if not data_rows:
        return {"product_column": None, "amount_column": None, "rows": None}

    df = pd.DataFrame(data_rows)
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    df = df.where(pd.notnull(df), None)

    # --- product column ---
    product_col = pick_product_column_heuristic(df)
    if not product_col:
        cols = list(df.columns)
        samples = _safe_sample_values(df)
        product_col = infer_product_column_with_llm(cols, samples)
    if not product_col:
        return {"product_column": None, "amount_column": None, "rows": None}

    # --- amount column ---
    qty_col = next((c for c in ["quantity", "qty", "count", "units"] if c in df.columns), None)
    price_col = next((c for c in ["price", "unit_price", "rate", "unitcost", "unit_cost"] if c in df.columns), None)

    effective_amount_col = None
    if qty_col and price_col:
        df[qty_col] = pd.to_numeric(df[qty_col], errors="coerce").fillna(0)
        df[price_col] = pd.to_numeric(df[price_col], errors="coerce").fillna(0)
        df["__line_total__"] = df[qty_col] * df[price_col]
        effective_amount_col = "__line_total__"

    # --- group by product ---
    grp = df.groupby(product_col, dropna=True)
    if effective_amount_col:
        agg = grp.agg(orders=(product_col, "count"), total_amount=(effective_amount_col, "sum")).reset_index()
        agg = agg.sort_values(by=["total_amount", "orders"], ascending=False)
    else:
        agg = grp.agg(orders=(product_col, "count")).reset_index()
        agg["total_amount"] = None
        agg = agg.sort_values(by=["orders"], ascending=False)

    # --- format response ---
    records = []
    for _, row in agg.head(limit).iterrows():
        records.append({
            "product": row[product_col],
            "orders": int(row["orders"]),
            "total_amount": (float(row["total_amount"]) if effective_amount_col and pd.notnull(row["total_amount"]) else None)
        })

    return {"product_column": product_col, "amount_column": effective_amount_col, "rows": records}


def get_top_selling_products_by_date(
    db: Session,
    start_date: str,
    end_date: str,
    limit: int = 5
) -> Dict[str, Any]:
    """
    Get top selling products within a date range.
    start_date and end_date should be ISO format: 'YYYY-MM-DD'
    """
    rows: List[models.FileRow] = (
        db.query(models.FileRow)
          .order_by(models.FileRow.id.desc())
          .all()
    )
    data_rows = [r.data for r in rows]
    if not data_rows:
        return {"product_column": None, "amount_column": None, "rows": None}

    df = pd.DataFrame(data_rows)
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    df = df.where(pd.notnull(df), None)

    # --- parse orderdate ---
    if "orderdate" not in df.columns:
        return {"product_column": None, "amount_column": None, "rows": None}
    df["orderdate"] = pd.to_datetime(df["orderdate"], errors="coerce").dt.tz_localize(None)

    # --- filter by range ---
    start = pd.to_datetime(start_date, errors="coerce").tz_localize(None)
    end = pd.to_datetime(end_date, errors="coerce").tz_localize(None)

    df = df[(df["orderdate"] >= start) & (df["orderdate"] <= end)]
    if df.empty:
        return {"product_column": "product", "amount_column": "__line_total__", "rows": []}

    # --- product column ---
    product_col = pick_product_column_heuristic(df)
    if not product_col:
        cols = list(df.columns)
        samples = _safe_sample_values(df)
        product_col = infer_product_column_with_llm(cols, samples)
    if not product_col:
        return {"product_column": None, "amount_column": None, "rows": None}

    # --- derive amount column ---
    qty_col = next((c for c in ["quantity", "qty", "count", "units"] if c in df.columns), None)
    price_col = next((c for c in ["price", "unit_price", "rate", "unitcost", "unit_cost"] if c in df.columns), None)

    effective_amount_col = None
    if qty_col and price_col:
        df[qty_col] = pd.to_numeric(df[qty_col], errors="coerce").fillna(0)
        df[price_col] = pd.to_numeric(df[price_col], errors="coerce").fillna(0)
        df["__line_total__"] = df[qty_col] * df[price_col]
        effective_amount_col = "__line_total__"

    # --- aggregate ---
    grp = df.groupby(product_col, dropna=True)
    if effective_amount_col:
        agg = grp.agg(
            orders=(product_col, "count"),
            total_amount=(effective_amount_col, "sum")
        ).reset_index()
        agg = agg.sort_values(by=["total_amount", "orders"], ascending=False)
    else:
        agg = grp.agg(orders=(product_col, "count")).reset_index()
        agg["total_amount"] = None
        agg = agg.sort_values(by=["orders"], ascending=False)

    # --- response ---
    records = []
    for _, row in agg.head(limit).iterrows():
        records.append({
            "product": row[product_col],
            "orders": int(row["orders"]),
            "total_amount": (float(row["total_amount"]) if effective_amount_col and pd.notnull(row["total_amount"]) else None)
        })

    return {"product_column": product_col, "amount_column": effective_amount_col, "rows": records}

def get_products_sales_table(
    db: Session,
    start_date: str,
    end_date: str,
) -> Dict[str, Any]:
    """
    Returns product sales between start_date and end_date.
    Response includes both detected column mappings and row data.
    """
    rows = db.query(models.FileRow).order_by(models.FileRow.id).all()
    data_rows = [r.data for r in rows]
    if not data_rows:
        return {"columns": {}, "rows": []}

    # Convert to DataFrame
    df = pd.DataFrame(data_rows)
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    df = df.where(pd.notnull(df), None)

    # --- orderdate ---
    if "orderdate" not in df.columns:
        return {"columns": {}, "rows": []}

    df["orderdate"] = pd.to_datetime(df["orderdate"], errors="coerce").dt.tz_localize(None)
    start = pd.to_datetime(start_date, errors="coerce").tz_localize(None)
    end = pd.to_datetime(end_date, errors="coerce").tz_localize(None)

    df = df[(df["orderdate"] >= start) & (df["orderdate"] <= end)]
    if df.empty:
        return {"columns": {}, "rows": []}

    # --- detect product column ---
    product_col = pick_product_column_heuristic(df)
    if not product_col:
        cols = list(df.columns)
        samples = _safe_sample_values(df)
        product_col = infer_product_column_with_llm(cols, samples)

    # --- detect category column ---
    category_candidates = ["category", "cat", "dept", "department", "class", "segment"]
    category_col = next((c for c in df.columns if any(k in c for k in category_candidates)), None)

    # --- detect price column ---
    price_candidates = ["price", "unit_price", "rate", "unitcost", "unit_cost"]
    price_col = next((c for c in df.columns if c in price_candidates), None)

    # --- detect quantity column ---
    qty_candidates = ["quantity", "qty", "count", "units", "amount"]
    qty_col = next((c for c in df.columns if c in qty_candidates), None)

    # --- safe defaults ---
    if qty_col:
        df[qty_col] = pd.to_numeric(df[qty_col], errors="coerce").fillna(0)
    else:
        qty_col = "__dummy_qty__"
        df[qty_col] = 1  # assume 1 if no column

    if price_col:
        df[price_col] = pd.to_numeric(df[price_col], errors="coerce").fillna(0)
    else:
        price_col = "__dummy_price__"
        df[price_col] = 0.0  # assume 0 if no column

    # --- group by product ---
    group_cols = [c for c in [product_col, category_col, price_col] if c and c in df.columns]
    agg = (
        df.groupby(group_cols, dropna=True)
          .agg(total_sales=(qty_col, "sum"))
          .reset_index()
    )

    # --- format rows ---
    results = []
    for idx, row in agg.iterrows():
        results.append({
            "id": idx + 1,
            "name": row.get(product_col, None),
            "category": row.get(category_col, None),
            "price": float(row.get(price_col, 0)),
            "total_sales": int(row.get("total_sales", 0)),
        })

    # --- return metadata + rows ---
    return {
        "columns": {
            "product_column": product_col,
            "category_column": category_col,
            "price_column": price_col,
            "quantity_column": qty_col,
        },
        "rows": results,
    }
