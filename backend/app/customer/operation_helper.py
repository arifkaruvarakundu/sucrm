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

# def sample_values_for_llm(df: pd.DataFrame, max_rows: int = 5) -> Dict[str, List[str]]:
#     samples: Dict[str, List[str]] = {}
#     head = df.head(max_rows)
#     for col in df.columns:
#         vals = head[col].astype(str).fillna("").tolist()
#         samples[col] = vals
#     return samples

# def extract_customer_table_from_orders(df: pd.DataFrame) -> List[Dict[str, Any]]:
#     if df.empty:
#         return []

#     df = normalize_dataframe_column_names(df)
#     column_names = list(df.columns)
#     samples = sample_values_for_llm(df)

#     mapping = infer_customer_fields_with_llm(column_names, samples)

#     # Build a canonical customers view using only mapped columns
#     selected_cols = [c for c in mapping.values() if c]
#     if not selected_cols:
#         return []

#     projected = df[selected_cols].copy()
#     rename_map = {v: k for k, v in mapping.items() if v}
#     projected = projected.rename(columns=rename_map)

#     # Deduplicate by the strongest identifier available
#     dedupe_keys = [k for k in ["civil_id", "email", "phone"] if k in projected.columns]
#     if dedupe_keys:
#         projected = projected.drop_duplicates(subset=dedupe_keys)
#     else:
#         projected = projected.drop_duplicates()

#     # Convert to dicts
#     records: List[Dict[str, Any]] = projected.where(pd.notnull(projected), None).to_dict(orient="records")
#     return records

# def get_customers_table(
#     db: Session,
#     user_id: int | None = None,
#     guest_id: str | None = None, 
#     limit_rows_scanned: int | None = 5000) -> Dict[str, Any]:
#     # Gather uploaded file rows and assemble into a DataFrame
#     rows = fetch_file_rows(db, user_id=user_id, guest_id=guest_id, limit=limit_rows_scanned)
#     data_records: List[Dict[str, Any]] = [r.data for r in rows]
#     if limit_rows_scanned is not None and len(data_records) > limit_rows_scanned:
#         data_records = data_records[:limit_rows_scanned]

#     if not data_records:
#         return {"customers": [], "columns": ["name", "civil_id", "phone", "city", "address", "email"]}

#     df = pd.DataFrame(data_records)
#     customers = extract_customer_table_from_orders(df)

#     # Optionally persist to a customers table in the future
#     persisted = upsert_customers_placeholder(db, customers)

#     return {
#         "customers": persisted,
#         "columns": ["name", "civil_id", "phone", "city", "address", "email"],
#         "count": len(persisted)
#     }

def aggregate_customers_from_orders(db: Session, identity: dict, file_id: int | None = None) -> dict:

    """Return per-customer aggregates from orders using column mappings."""

    user = identity.get("user")
    guest_id = identity.get("guest_id")

    if not user and not guest_id:
        return {"file_id": None, "columns": [], "rows": []}

    user_id = getattr(user, "id", None) if user else None

    # Step 1: Find the target file
    if file_id:
        target_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    else:
        filters = []
        if user_id:
            filters.append(UploadedFile.user_id == user_id)
        if guest_id:
            filters.append(UploadedFile.guest_id == guest_id)
        target_file = db.query(UploadedFile).filter(or_(*filters)).order_by(UploadedFile.uploaded_at.desc()).first()

    if not target_file:
        return {"file_id": None, "columns": [], "rows": []}

    # Step 2: Fetch both mappings (customer + order)
    customer_mapping = (
        db.query(ColumnMapping)
        .filter(ColumnMapping.file_id == target_file.id, ColumnMapping.analysis_type == "customer")
        .order_by(ColumnMapping.updated_at.desc())
        .first()
    )
    order_mapping = (
        db.query(ColumnMapping)
        .filter(ColumnMapping.file_id == target_file.id, ColumnMapping.analysis_type == "order")
        .order_by(ColumnMapping.updated_at.desc())
        .first()
    )

    if not customer_mapping and not order_mapping:
        return {"file_id": target_file.id, "columns": [], "rows": []}

    # Merge mappings, prioritizing customer fields when both exist
    mapping = {}
    if order_mapping:
        mapping.update(order_mapping.mapping)
    if customer_mapping:
        mapping.update(customer_mapping.mapping)

    # Step 3: Detect key columns safely
    name_col = mapping.get("customerName")
    # Prefer 'phone' from customer mapping, else 'customerPhone' from order mapping
    phone_col = (
        customer_mapping.mapping.get("phone")
        if customer_mapping and "phone" in customer_mapping.mapping
        else order_mapping.mapping.get("customerPhone")
        if order_mapping and "customerPhone" in order_mapping.mapping
        else None
    )
    amount_col = mapping.get("totalAmount")
    date_col = mapping.get("orderDate")

    # Step 4: Fetch rows
    rows = db.query(FileRow).filter(FileRow.file_id == target_file.id).all()
    if not rows:
        return {
            "file_id": target_file.id,
            "columns": ["customerName", "phone", "orderCount", "totalSpending", "lastOrderDate"],
            "rows": []
        }

    df = pd.DataFrame([r.data for r in rows])
    if df.empty:
        return {
            "file_id": target_file.id,
            "columns": ["customerName", "phone", "orderCount", "totalSpending", "lastOrderDate"],
            "rows": []
        }

    # Step 5: Clean + convert
    df = df.where(pd.notnull(df), None)
    df.columns = [str(c).strip() for c in df.columns]

    if amount_col and amount_col in df.columns:
        df[amount_col] = pd.to_numeric(df[amount_col], errors="coerce").fillna(0)
    if date_col and date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    # Step 6: Aggregate per customer
    grouped_customers = []
    if name_col and name_col in df.columns:
        group_keys = [k for k in [name_col, phone_col] if k and k in df.columns]
        grouped = df.groupby(group_keys, dropna=False)

        for keys, gdf in grouped:
            if not isinstance(keys, tuple):
                keys = (keys,)
            key_map = dict(zip(group_keys, keys))

            order_count = len(gdf)
            total_spending = gdf[amount_col].sum() if amount_col in gdf.columns else 0.0
            last_order_date = (
                gdf[date_col].max().isoformat()
                if date_col in gdf.columns and not gdf[date_col].isna().all()
                else None
            )

            grouped_customers.append({
                "customerName": key_map.get(name_col),
                "phone": key_map.get(phone_col),
                "orderCount": order_count,
                "totalSpending": float(total_spending),
                "lastOrderDate": last_order_date
            })

    return {
        "file_id": target_file.id,
        "columns": ["customerName", "phone", "orderCount", "totalSpending", "lastOrderDate"],
        "rows": grouped_customers
    }

from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Dict, Any
import pandas as pd
from app.models import UploadedFile, FileRow, ColumnMapping

def _extract_customer_table(df: pd.DataFrame, mapping: dict) -> list[dict]:
    """Extracts customer info using provided column mappings dynamically."""
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    df = df.where(pd.notnull(df), None)

    selected_cols = {}
    for logical_name, actual_name in mapping.items():
        if actual_name:
            normalized = str(actual_name).strip().lower().replace(" ", "_")
            if normalized in df.columns:
                selected_cols[logical_name] = normalized

    if not selected_cols:
        return []

    projected = df[list(selected_cols.values())].copy()
    projected.columns = list(selected_cols.keys())

    dedupe_keys = [k for k in ["civil_id", "email", "phone"] if k in projected.columns]
    if dedupe_keys:
        projected = projected.drop_duplicates(subset=dedupe_keys)
    else:
        projected = projected.drop_duplicates()

    return projected.to_dict(orient="records")

def get_customers_table(db: Session, identity: dict, file_id: int | None = None) -> Dict[str, Any]:
    """Return a clean customer table using 'customer' analysis first, 
    falling back to 'order' for phone if needed."""

    user = identity.get("user")
    guest_id = identity.get("guest_id")

    if not user and not guest_id:
        return {"file_id": None, "columns": [], "rows": []}

    user_id = getattr(user, "id", None) if user else None

    # Step 1: Locate the file
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

    # Step 2: Get both mappings (customer + order)
    customer_mapping_obj = (
        db.query(ColumnMapping)
        .filter(ColumnMapping.file_id == target_file.id, ColumnMapping.analysis_type == "customer")
        .order_by(ColumnMapping.updated_at.desc())
        .first()
    )

    order_mapping_obj = (
        db.query(ColumnMapping)
        .filter(ColumnMapping.file_id == target_file.id, ColumnMapping.analysis_type == "order")
        .order_by(ColumnMapping.updated_at.desc())
        .first()
    )

    if not customer_mapping_obj and not order_mapping_obj:
        return {"file_id": target_file.id, "columns": [], "rows": []}

    customer_mapping = customer_mapping_obj.mapping if customer_mapping_obj else {}
    order_mapping = order_mapping_obj.mapping if order_mapping_obj else {}

    # Step 3: Determine the final phone mapping
    # Prefer customer.phone; if missing, use order.customerPhone
    final_mapping = customer_mapping.copy()
    if "phone" not in final_mapping and "customerPhone" in order_mapping:
        final_mapping["phone"] = order_mapping["customerPhone"]

    # Step 4: Query all rows
    rows = db.query(FileRow).filter(FileRow.file_id == target_file.id).all()
    if not rows:
        return {"file_id": target_file.id, "columns": ["customerName", "customerId", "phone", "city"], "rows": []}

    df = pd.DataFrame([r.data for r in rows])
    if df.empty:
        return {"file_id": target_file.id, "columns": ["customerName", "customerId", "phone", "city"], "rows": []}

    # Step 5: Extract clean customer data
    customers = _extract_customer_table(df, final_mapping)

    # Keep only relevant fields
    desired_cols = ["customerName", "customerId", "phone", "city"]
    filtered_rows = [
        {k: v for k, v in row.items() if k in desired_cols}
        for row in customers
    ]

    # Step 6: Return clean response
    return {
        "file_id": target_file.id,
        "columns": desired_cols,
        "rows": filtered_rows
    }

