# from sqlalchemy.orm import Session
# from typing import Dict, List, Any
# import pandas as pd
# from datetime import datetime
# from app.customer.db_helper import fetch_file_rows

# def normalize_dataframe_column_names(df: pd.DataFrame) -> pd.DataFrame:
#     df = df.copy()
#     df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
#     return df

# def get_orders_in_range(
#     db: Session,
#     start_date: str,
#     end_date: str,
#     # limit_rows_scanned: int | None = 50000
# ) -> List[Dict[str, Any]]:
#     """
#     Return all orders between start_date and end_date with details.
#     Tries to infer common columns from uploaded orders-like data.
#     """
#     rows = fetch_file_rows(db)
#     records: List[Dict[str, Any]] = [r.data for r in rows]

#     # if limit_rows_scanned is not None and len(records) > limit_rows_scanned:
#     #     records = records[:limit_rows_scanned]

#     if not records:
#         return []

#     df = pd.DataFrame(records)
#     df = normalize_dataframe_column_names(df)

#     # Candidate columns
#     possible_id_cols = [c for c in df.columns if c in {"order_id", "invoice_id", "id", "OrderID", "orderid"}]
#     possible_customer_cols = [c for c in df.columns if c in {"customer", "customer_name", "name", "user"}]
#     possible_amount_cols = [c for c in df.columns if c in {"amount", "price", "total", "order_total", "grand_total", "invoice_amount"}]
#     possible_date_cols = [c for c in df.columns if c in {"date", "order_date", "created_at", "timestamp"}]
#     possible_status_cols = [c for c in df.columns if c in {"status", "order_status", "state"}]

#     id_col = possible_id_cols[0] if possible_id_cols else None
#     customer_col = possible_customer_cols[0] if possible_customer_cols else None
#     amount_col = possible_amount_cols[0] if possible_amount_cols else None
#     date_col = possible_date_cols[0] if possible_date_cols else None
#     status_col = possible_status_cols[0] if possible_status_cols else None

#     # Required for filtering
#     if not date_col:
#         return []

#     # Parse dates
#     df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
#     df = df.dropna(subset=[date_col])  # remove rows with invalid dates

#     try:
#         start_dt = pd.to_datetime(start_date)
#         end_dt = pd.to_datetime(end_date)
#     except Exception:
#         raise ValueError("Invalid date format. Use YYYY-MM-DD.")

#     # Filter range
#     mask = (df[date_col] >= start_dt) & (df[date_col] <= end_dt)
#     df = df.loc[mask]

#     if df.empty:
#         return []

#     # Clean amount column
#     if amount_col:
#         df[amount_col] = pd.to_numeric(df[amount_col], errors="coerce").fillna(0)

#     # Project useful fields
#     keep_cols = [c for c in [id_col, customer_col, amount_col, date_col, status_col] if c]
#     projected = df[keep_cols].copy()

#     # Convert for JSON safe return
#     projected[date_col] = projected[date_col].dt.strftime("%Y-%m-%d %H:%M:%S")
#     records_out: List[Dict[str, Any]] = projected.where(pd.notnull(projected), None).to_dict(orient="records")

#     return records_out

from typing import Dict, List, Any
import pandas as pd
from app.dashboard.llm_helper import infer_order_fields_with_llm  # new LLM helper for orders
from sqlalchemy.orm import Session
from datetime import datetime
from app.customer.db_helper import fetch_file_rows

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

def extract_orders_table_from_raw(df: pd.DataFrame) -> List[Dict[str, Any]]:
    if df.empty:
        return []

    df = normalize_dataframe_column_names(df)
    column_names = list(df.columns)
    samples = sample_values_for_llm(df)

    # 🔑 Ask LLM which columns map to canonical order fields
    mapping = infer_order_fields_with_llm(column_names, samples)
    print("LLM Mapping:", mapping)

    # --- Fallbacks if LLM fails or chooses useless columns ---
    # --- Fallbacks if LLM fails ---
    fallback_map = {
        "order_id": ["order_id", "invoice_id", "id", "orderid", "OrderID"],
        "customer_name": ["customer", "customer_name", "name", "user"],
        "amount": ["amount", "price", "total", "order_total", "grand_total", "invoice_amount"],
        "date": ["orderdate", "date", "order_date", "created_at", "timestamp"],  # 👈 put orderdate first
        "status": ["status", "order_status", "state", "payment"]
    }

    for field, candidates in fallback_map.items():
        chosen = mapping.get(field)

        if not chosen or (chosen in df.columns and df[chosen].dropna().empty):
            for cand in candidates:
                cand_norm = cand.strip().lower()
                if cand_norm in df.columns and not df[cand_norm].dropna().empty:
                    mapping[field] = cand_norm
                    break

    print("FINAL mapping:", mapping)

    selected_cols = [c for c in mapping.values() if c]
    if not selected_cols:
        return []

    projected = df[selected_cols].copy()
    rename_map = {v: k for k, v in mapping.items() if v}
    projected = projected.rename(columns=rename_map)

    print("COLUMNS:", df.columns.tolist())
    print("SAMPLES:", samples)
    print("PROJECTED DF:", projected.head())

    # Type conversions
    if "amount" in projected.columns:
        projected["amount"] = pd.to_numeric(projected["amount"], errors="coerce").fillna(0)
    if "date" in projected.columns:
        projected["date"] = pd.to_datetime(projected["date"], errors="coerce")

    return projected.where(pd.notnull(projected), None).to_dict(orient="records")


def get_orders_in_range(
    db: Session,
    start_date: str,
    end_date: str,
) -> List[Dict[str, Any]]:

    """Return all orders in date range using LLM-based field extraction."""
    rows = fetch_file_rows(db)
    records: List[Dict[str, Any]] = [r.data for r in rows]
    if not records:
        return []

    df = pd.DataFrame(records)
    orders = extract_orders_table_from_raw(df)
    if not orders:
        return []

    df_orders = pd.DataFrame(orders)

    if "date" not in df_orders.columns:
        return []
    
    # Parse dates
    df_orders["date"] = pd.to_datetime(df_orders["date"], errors="coerce")
    df_orders = df_orders.dropna(subset=["date"])
    print("Orders DF:", df_orders.head())
    try:
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
    except Exception:
        raise ValueError("Invalid date format. Use YYYY-MM-DD.")

    # print("=== BEFORE FILTERING ===")
    # print(df.head(20))  # show some rows
    # print(df.dtypes)
    # print("min date:", df['date'].min(), "max date:", df['date'].max())

    # Filter range
    mask = (df_orders["date"] >= start_dt) & (df_orders["date"] <= end_dt)
    df_filtered = df_orders.loc[mask]

    if df_filtered.empty:
        return []

    # Format for JSON
    df_filtered["date"] = df_filtered["date"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return df_filtered.where(pd.notnull(df_filtered), None).to_dict(orient="records")

def get_orders_aggregated(
    db: Session,
    start_date: str,
    end_date: str,
    granularity: str = "daily"
) -> List[Dict[str, Any]]:
    """
    Return aggregated orders for charts, grouped by daily, monthly, or yearly.
    Uses the same LLM-based extraction as `get_orders_in_range`.
    """

    # Step 1: Fetch and normalize raw data
    rows = fetch_file_rows(db)
    records: List[Dict[str, Any]] = [r.data for r in rows]
    if not records:
        return []

    df = pd.DataFrame(records)
    orders = extract_orders_table_from_raw(df)
    if not orders:
        return []

    df_orders = pd.DataFrame(orders)
    if "date" not in df_orders.columns or "amount" not in df_orders.columns:
        return []

    df_orders["date"] = pd.to_datetime(df_orders["date"], errors="coerce")
    df_orders = df_orders.dropna(subset=["date"])

    # Step 2: Filter by date range
    try:
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
    except Exception:
        raise ValueError("Invalid date format. Use YYYY-MM-DD.")

    df_orders = df_orders.loc[(df_orders["date"] >= start_dt) & (df_orders["date"] <= end_dt)]
    if df_orders.empty:
        return []

    # Step 3: Aggregate based on granularity
    if granularity == "daily":
        df_orders["period"] = df_orders["date"].dt.strftime("%Y-%m-%d")
    elif granularity == "monthly":
        df_orders["period"] = df_orders["date"].dt.strftime("%Y-%m")
    elif granularity == "yearly":
        df_orders["period"] = df_orders["date"].dt.strftime("%Y")
    else:
        raise ValueError("Granularity must be 'daily', 'monthly', or 'yearly'.")

    df_agg = df_orders.groupby("period").agg(
        order_count=pd.NamedAgg(column="order_id", aggfunc="count"),
        total_amount=pd.NamedAgg(column="amount", aggfunc="sum")
    ).reset_index()

    # Step 4: Convert to JSON-friendly format
    df_agg["total_amount"] = df_agg["total_amount"].astype(float)
    result = df_agg.to_dict(orient="records")
    return result
