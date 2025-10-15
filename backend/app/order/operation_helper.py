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

from typing import Dict, List, Any, Optional
import pandas as pd
from app.dashboard.llm_helper import infer_order_fields_with_llm  # new LLM helper for orders
from sqlalchemy.orm import Session
from datetime import datetime
from app.customer.db_helper import fetch_file_rows
from app.models import UploadedFile, ColumnMapping, FileRow, FileColumn
from sqlalchemy import or_

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

    selected_cols = [c for c in mapping.values() if c]
    if not selected_cols:
        return []

    projected = df[selected_cols].copy()
    rename_map = {v: k for k, v in mapping.items() if v}
    projected = projected.rename(columns=rename_map)

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
    identity: dict,
    file_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Return all orders in the given date range.
    Uses stored column mappings (not LLM extraction).
    """

    # --- Step 1: Identify user or guest ---
    user = identity.get("user")
    user_id = getattr(user, "id", None) if user else None
    guest_id = identity.get("guest_id")

    # --- Step 2: Find file mappings ---
    q = db.query(ColumnMapping).filter(ColumnMapping.analysis_type == "order")
    if user_id:
        q = q.filter(ColumnMapping.user_id == user_id)
    elif guest_id:
        q = q.filter(ColumnMapping.guest_id == guest_id)

    if file_id:
        q = q.filter(ColumnMapping.file_id == file_id)

    mapping_obj = q.first()
    if not mapping_obj or not mapping_obj.mapping:
        return []

    mapping = mapping_obj.mapping  # e.g. {"orderId": "م", "orderDate": "التاريخ", ...}

  
    # --- Step 3: Fetch all rows for this file ---
    rows_q = db.query(FileRow).filter(FileRow.file_id == mapping_obj.file_id)
    rows = rows_q.all()
    if not rows:
        return []

    records = [r.data for r in rows]
    df = pd.DataFrame(records)

    # --- Step 4: Apply field mapping safely ---
    order_date_col = mapping.get("orderDate")
    amount_col = mapping.get("totalAmount")
    order_id_col = mapping.get("orderId")
    customer_col = mapping.get("customerName")

    if not order_date_col or order_date_col not in df.columns:
        return []

    # --- Step 5: Normalize dataframe ---
    df_orders = pd.DataFrame({
        "order_id": df.get(order_id_col),
        "customer_name": df.get(customer_col),
        "date": df.get(order_date_col),
        "amount": df.get(amount_col),
    })

    # --- Step 6: Convert and filter dates ---
    df_orders["date"] = pd.to_datetime(df_orders["date"], errors="coerce")
    df_orders = df_orders.dropna(subset=["date"])

    try:
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
    except Exception:
        raise ValueError("Invalid date format. Use YYYY-MM-DD.")

    df_filtered = df_orders.loc[(df_orders["date"] >= start_dt) & (df_orders["date"] <= end_dt)]

    if df_filtered.empty:
        return []

    # --- Step 7: Clean and prepare for JSON ---
    df_filtered["date"] = df_filtered["date"].dt.strftime("%Y-%m-%d")
    df_filtered = df_filtered.where(pd.notnull(df_filtered), None)

    # Optional: reorder columns for readability
    ordered_cols = ["order_id", "customer_name", "date", "amount"]
    df_filtered = df_filtered[[c for c in ordered_cols if c in df_filtered.columns]]

    return df_filtered.to_dict(orient="records")

def get_orders_aggregated(
    db: Session,
    start_date: str,
    end_date: str,
    identity: dict,
    granularity: str = "daily",
    file_id: int | None = None
) -> dict:
    """
    Return aggregated orders (daily/monthly/yearly) using file_columns + column_mappings.
    """

    user = identity.get("user")
    guest_id = identity.get("guest_id")
    user_id = getattr(user, "id", None) if user else None

    if not user_id and not guest_id:
        return {"file_id": None, "columns": [], "rows": []}

    # Step 1: Resolve target file
    if file_id:
        target_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    else:
        filters = []
        if user_id:
            filters.append(UploadedFile.user_id == user_id)
        if guest_id:
            filters.append(UploadedFile.guest_id == guest_id)
        target_file = (
            db.query(UploadedFile)
            .filter(or_(*filters))
            .order_by(UploadedFile.uploaded_at.desc())
            .first()
        )

    if not target_file:
        return {"file_id": None, "columns": [], "rows": []}

    # Step 2: Fetch file columns + mapping
    file_columns = db.query(FileColumn).filter(FileColumn.file_id == target_file.id).all()
    order_mapping = (
        db.query(ColumnMapping)
        .filter(ColumnMapping.file_id == target_file.id, ColumnMapping.analysis_type == "order")
        .order_by(ColumnMapping.updated_at.desc())
        .first()
    )

    if not file_columns or not order_mapping:
        return {"file_id": target_file.id, "columns": ["period", "orderCount", "totalAmount"], "rows": []}

    # Step 3: Build reverse mapping: actual column name → logical name
    # Example: "التاريخ" -> "orderDate"
    reverse_mapping = {}
    mapping = order_mapping.mapping or {}
    print ("mappings or product sample", mapping)

    for logical_name, mapped_col in mapping.items():
        for col in file_columns:
            # Normalize both for comparison
            col_name = str(col.name).strip()
            if col_name == mapped_col.strip():
                reverse_mapping[col_name] = logical_name
                break

    # Step 4: Load file rows
    rows = db.query(FileRow).filter(FileRow.file_id == target_file.id).all()

    print ("rows from file",rows)

    if not rows:
        return {"file_id": target_file.id, "columns": ["period", "orderCount", "totalAmount"], "rows": []}

    df = pd.DataFrame([r.data for r in rows])

    print("df data frame", df)

    if df.empty:
        return {"file_id": target_file.id, "columns": ["period", "orderCount", "totalAmount"], "rows": []}

    df = df.where(pd.notnull(df), None)
    print("second df", df)
    df.columns = [str(c).strip() for c in df.columns]

    # Step 5: Rename columns using reverse mapping
    df = df.rename(columns=reverse_mapping)

    print("third df", df)

    # Step 6: Identify columns
    date_col = "orderDate" if "orderDate" in df.columns else None
    # If totalAmount is missing, try computing it
    lower_cols = [c.lower() for c in df.columns]

    if "totalamount" not in lower_cols and "price" in lower_cols and "quantity" in lower_cols:
        df["totalAmount"] = (
            pd.to_numeric(df.loc[:, [c for c in df.columns if c.lower() == "price"][0]], errors="coerce").fillna(0)
            * pd.to_numeric(df.loc[:, [c for c in df.columns if c.lower() == "quantity"][0]], errors="coerce").fillna(0)
        )

    amount_col = "totalAmount" if "totalAmount" in df.columns else None
    order_id_col = "orderId" if "orderId" in df.columns else None
    print("amount",amount_col)
    print("date",date_col)
    print("orde id",order_id_col)

    if not all([date_col, amount_col]):
        return {"file_id": target_file.id, "columns": ["period", "orderCount", "totalAmount"], "rows": []}

    # Step 7: Convert + clean
    df[amount_col] = pd.to_numeric(df[amount_col], errors="coerce").fillna(0)
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.tz_localize(None)
    df = df.dropna(subset=[date_col])

    print("fourth df:", df)

    # Step 8: Filter by date range
    try:
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
    except Exception:
        raise ValueError("Invalid date format. Use YYYY-MM-DD.")

    df = df.loc[(df[date_col] >= start_dt) & (df[date_col] <= end_dt)]

    print("fifth df:", df)
    if df.empty:
        return {"file_id": target_file.id, "columns": ["period", "orderCount", "totalAmount"], "rows": []}

    # Step 9: Aggregate
    if granularity == "daily":
        df["period"] = df[date_col].dt.strftime("%Y-%m-%d")
    elif granularity == "monthly":
        df["period"] = df[date_col].dt.strftime("%Y-%m")
    elif granularity == "yearly":
        df["period"] = df[date_col].dt.strftime("%Y")
    else:
        raise ValueError("Granularity must be 'daily', 'monthly', or 'yearly'.")

    df_agg = (
        df.groupby("period")
        .agg(orderCount=(order_id_col or amount_col, "count"), totalAmount=(amount_col, "sum"))
        .reset_index()
    )

    # Step 10: Final output
    df_agg["totalAmount"] = df_agg["totalAmount"].astype(float)

    return {

        "file_id": target_file.id,
        "columns": ["period", "orderCount", "totalAmount"],
        "rows": df_agg.to_dict(orient="records"),

    }

