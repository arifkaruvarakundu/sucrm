from sqlalchemy.orm import Session
from typing import Dict, List, Any
from collections import defaultdict
import pandas as pd
from app.customer.db_helper import fetch_file_rows, upsert_customers_placeholder
from app.dashboard.llm_helper import infer_customer_fields_with_llm

def normalize_dataframe_column_names(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df

def sample_values_for_llm(df: pd.DataFrame, max_rows: int = 5) -> Dict[str, List[str]]:
    samples: Dict[str, List[str]] = {}
    head = df.head(max_rows)
    for col in df.columns:
        vals = head[col].astype(str).fillna("").tolist()
        samples[col] = vals
    return samples

def extract_customer_table_from_orders(df: pd.DataFrame) -> List[Dict[str, Any]]:
    if df.empty:
        return []

    df = normalize_dataframe_column_names(df)
    column_names = list(df.columns)
    samples = sample_values_for_llm(df)

    mapping = infer_customer_fields_with_llm(column_names, samples)

    # Build a canonical customers view using only mapped columns
    selected_cols = [c for c in mapping.values() if c]
    if not selected_cols:
        return []

    projected = df[selected_cols].copy()
    rename_map = {v: k for k, v in mapping.items() if v}
    projected = projected.rename(columns=rename_map)

    # Deduplicate by the strongest identifier available
    dedupe_keys = [k for k in ["civil_id", "email", "phone"] if k in projected.columns]
    if dedupe_keys:
        projected = projected.drop_duplicates(subset=dedupe_keys)
    else:
        projected = projected.drop_duplicates()

    # Convert to dicts
    records: List[Dict[str, Any]] = projected.where(pd.notnull(projected), None).to_dict(orient="records")
    return records

def get_customers_table(db: Session, limit_rows_scanned: int | None = 5000) -> Dict[str, Any]:
    # Gather uploaded file rows and assemble into a DataFrame
    rows = fetch_file_rows(db)
    data_records: List[Dict[str, Any]] = [r.data for r in rows]
    if limit_rows_scanned is not None and len(data_records) > limit_rows_scanned:
        data_records = data_records[:limit_rows_scanned]

    if not data_records:
        return {"customers": [], "columns": ["name", "civil_id", "phone", "city", "address", "email"]}

    df = pd.DataFrame(data_records)
    customers = extract_customer_table_from_orders(df)

    # Optionally persist to a customers table in the future
    persisted = upsert_customers_placeholder(db, customers)

    return {
        "customers": persisted,
        "columns": ["name", "civil_id", "phone", "city", "address", "email"],
        "count": len(persisted)
    }


def aggregate_customers_from_orders(db: Session, limit_rows_scanned: int | None = 50000) -> List[Dict[str, Any]]:
    """Build per-customer aggregates (name, phone, order_count, total_spending, last_order_date).
    Tries to infer common columns from uploaded orders-like data.
    """
    rows = fetch_file_rows(db)
    records: List[Dict[str, Any]] = [r.data for r in rows]
    if limit_rows_scanned is not None and len(records) > limit_rows_scanned:
        records = records[:limit_rows_scanned]

    if not records:
        return []

    df = pd.DataFrame(records)
    df = normalize_dataframe_column_names(df)

    # Try to find likely columns
    possible_name_cols = [c for c in df.columns if c in {"name", "customer", "customer_name", "user"}]
    possible_phone_cols = [c for c in df.columns if c in {"phone", "mobile", "contact"}]
    possible_amount_cols = [c for c in df.columns if c in {"amount", "price", "total", "order_total", "grand_total", "invoice_amount"}]
    possible_date_cols = [c for c in df.columns if c in {"date", "order_date", "created_at", "timestamp"}]

    name_col = possible_name_cols[0] if possible_name_cols else None
    phone_col = possible_phone_cols[0] if possible_phone_cols else None
    amount_col = possible_amount_cols[0] if possible_amount_cols else None
    date_col = possible_date_cols[0] if possible_date_cols else None

    # Minimal projection
    keep_cols: List[str] = [c for c in [name_col, phone_col, amount_col, date_col] if c]
    if not keep_cols:
        return []

    projected = df[keep_cols].copy()
    if amount_col:
        projected[amount_col] = pd.to_numeric(projected[amount_col], errors="coerce").fillna(0)
    if date_col and pd.api.types.is_string_dtype(projected[date_col]):
        projected[date_col] = pd.to_datetime(projected[date_col], errors="coerce")

    # Group by the best identifiers available
    group_keys: List[str] = [k for k in [name_col, phone_col] if k]
    if not group_keys:
        return []

    grouped = projected.groupby(group_keys, dropna=False)

    results: List[Dict[str, Any]] = []
    for keys, gdf in grouped:
        if not isinstance(keys, tuple):
            keys = (keys,)
        key_map = dict(zip(group_keys, keys))

        order_count = int(len(gdf))
        total_spending = float(gdf[amount_col].sum()) if amount_col else 0.0
        last_order_date = (
            gdf[date_col].max().isoformat() if date_col and pd.api.types.is_datetime64_any_dtype(gdf[date_col]) and not gdf[date_col].isna().all() else None
        )

        results.append({
            "customer_name": key_map.get(name_col) or None,
            "phone": key_map.get(phone_col) or None,
            "order_count": order_count,
            "total_spending": total_spending,
            "last_order_date": last_order_date
        })

    # Sort by order_count desc as a default
    results.sort(key=lambda r: (r["order_count"], r["total_spending"]), reverse=True)
    return results