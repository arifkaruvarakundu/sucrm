from app import models
import pandas as pd
from sqlalchemy.orm import Session
from typing import Any, List, Dict
from app.dashboard.llm_helper import infer_columns_with_llm, infer_product_column_with_llm
from app.dashboard.operation_helper import pick_columns_heuristic, _safe_sample_values
from datetime import datetime
from app.models import UploadedFile, ColumnMapping, FileRow
from sqlalchemy import or_

ANALYSIS_FIELDS = {
    "order": ["orderId","orderDate","quantity","totalAmount","orderStatus","customerName","customerPhone"],
    "customer": ["customerId","customerName","email","phone","city"],
    "product": ["productId","productName","category","price","quantity"],
}

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

def get_top_selling_products(
    db: Session,
    identity: dict,
    limit: int = 5,
    file_id: int | None = None
) -> Dict[str, Any]:
    """
    Get top-selling products overall.
    Uses totalAmount from order mapping if available,
    otherwise computes it from product mapping (price × quantity).
    """
    user = identity.get("user")
    guest_id = identity.get("guest_id")

    if not user and not guest_id:
        return {"file_id": None, "product_column": None, "amount_column": None, "rows": []}

    user_id = getattr(user, "id", None) if user else None

    # Step 1: Determine target file
    if file_id:
        target_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if not target_file:
            return {"file_id": None, "product_column": None, "amount_column": None, "rows": []}
        if user_id and target_file.user_id != user_id:
            return {"file_id": target_file.id, "product_column": None, "amount_column": None, "rows": []}
        if guest_id and target_file.guest_id != guest_id:
            return {"file_id": target_file.id, "product_column": None, "amount_column": None, "rows": []}
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
            return {"file_id": None, "product_column": None, "amount_column": None, "rows": []}

    # Step 2: Get both product + order mappings
    product_mapping = (
        db.query(ColumnMapping)
        .filter(ColumnMapping.file_id == target_file.id, ColumnMapping.analysis_type == "product")
        .order_by(ColumnMapping.updated_at.desc())
        .first()
    )
    order_mapping = (
        db.query(ColumnMapping)
        .filter(ColumnMapping.file_id == target_file.id, ColumnMapping.analysis_type == "order")
        .order_by(ColumnMapping.updated_at.desc())
        .first()
    )

    if not product_mapping and not order_mapping:
        return {"file_id": target_file.id, "product_column": None, "amount_column": None, "rows": []}

    # Step 3: Extract column mappings
    product_col = None
    qty_col = None
    price_col = None
    total_amount_col = None

    if product_mapping:
        product_col = product_mapping.mapping.get("productName")
        qty_col = product_mapping.mapping.get("quantity")
        price_col = product_mapping.mapping.get("price")

    if order_mapping:
        total_amount_col = order_mapping.mapping.get("totalAmount")

    if not product_col:
        return {"file_id": target_file.id, "product_column": None, "amount_column": None, "rows": []}

    # Step 4: Query file rows
    query = db.query(FileRow).filter(FileRow.file_id == target_file.id)
    if user:
        query = query.join(UploadedFile).filter(UploadedFile.user_id == user.id)
    elif guest_id:
        query = query.join(UploadedFile).filter(UploadedFile.guest_id == guest_id)

    rows = query.all()
    if not rows:
        return {"file_id": target_file.id, "product_column": product_col, "amount_column": None, "rows": []}

    # Step 5: Convert rows to DataFrame
    df = pd.DataFrame([r.data for r in rows])
    if df.empty:
        return {"file_id": target_file.id, "product_column": product_col, "amount_column": None, "rows": []}

    df = df.where(pd.notnull(df), None)
    df.columns = [str(c).strip() for c in df.columns]

    # Step 6: Determine effective amount column
    effective_amount_col = None
    if total_amount_col and total_amount_col in df.columns:
        df[total_amount_col] = pd.to_numeric(df[total_amount_col], errors="coerce").fillna(0)
        effective_amount_col = total_amount_col
    elif price_col and qty_col and price_col in df.columns and qty_col in df.columns:
        df[price_col] = pd.to_numeric(df[price_col], errors="coerce").fillna(0)
        df[qty_col] = pd.to_numeric(df[qty_col], errors="coerce").fillna(1)
        df["__line_total__"] = df[price_col] * df[qty_col]
        effective_amount_col = "__line_total__"
    else:
        return {"file_id": target_file.id, "product_column": product_col, "amount_column": None, "rows": []}

    # Step 7: Aggregate sales by product
    grp = df.groupby(product_col, dropna=True)
    agg = grp.agg(
        orders=(product_col, "count"),
        total_amount=(effective_amount_col, "sum")
    ).reset_index()
    agg = agg.sort_values(by=["total_amount", "orders"], ascending=False)

    # Step 8: Build response
    records = []
    for _, row in agg.head(limit).iterrows():
        records.append({
            "product": row[product_col],
            "orders": int(row["orders"]),
            "total_amount": float(row["total_amount"]) if pd.notnull(row["total_amount"]) else None
        })

    return {
        "file_id": target_file.id,
        "product_column": product_col,
        "amount_column": effective_amount_col,
        "rows": records
    }

def get_top_selling_products_by_date(
    db: Session,
    identity: dict,
    start_date: str,
    end_date: str,
    limit: int = 5,
    file_id: int | None = None
) -> Dict[str, Any]:
    """
    Get top selling products within a date range.
    Uses order mapping's totalAmount for total calculation.
    """
    user = identity.get("user")
    guest_id = identity.get("guest_id")
    if not user and not guest_id:
        return {"file_id": None, "product_column": None, "amount_column": None, "rows": []}

    user_id = getattr(user, "id", None) if user else None

    # Step 1: Determine target file
    if file_id:
        target_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if not target_file:
            return {"file_id": None, "product_column": None, "amount_column": None, "rows": []}
        if user_id and target_file.user_id != user_id:
            return {"file_id": target_file.id, "product_column": None, "amount_column": None, "rows": []}
        if guest_id and target_file.guest_id != guest_id:
            return {"file_id": target_file.id, "product_column": None, "amount_column": None, "rows": []}
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
            return {"file_id": None, "product_column": None, "amount_column": None, "rows": []}

    # Step 2: Get column mappings
    product_mapping = (
        db.query(ColumnMapping)
        .filter(ColumnMapping.file_id == target_file.id, ColumnMapping.analysis_type == "product")
        .order_by(ColumnMapping.updated_at.desc())
        .first()
    )
    order_mapping = (
        db.query(ColumnMapping)
        .filter(ColumnMapping.file_id == target_file.id, ColumnMapping.analysis_type == "order")
        .order_by(ColumnMapping.updated_at.desc())
        .first()
    )

    if not product_mapping or not order_mapping:
        return {"file_id": target_file.id, "product_column": None, "amount_column": None, "rows": []}

     # Step 3: Extract mapping info
    product_col = None
    qty_col = None
    price_col = None
    total_amount_col = None
    order_date_col = None

    if product_mapping:
        product_col = product_mapping.mapping.get("productName")
        qty_col = product_mapping.mapping.get("quantity")
        price_col = product_mapping.mapping.get("price")

    if order_mapping:
        total_amount_col = order_mapping.mapping.get("totalAmount")
        order_date_col = order_mapping.mapping.get("orderDate")

    # Step 4: Validate we have necessary columns
    if not product_col:
        return {"file_id": target_file.id, "product_column": None, "amount_column": None, "rows": []}

    # Step 5: Query rows
    query = db.query(FileRow).filter(FileRow.file_id == target_file.id)
    if user:
        query = query.join(UploadedFile).filter(UploadedFile.user_id == user.id)
    elif guest_id:
        query = query.join(UploadedFile).filter(UploadedFile.guest_id == guest_id)

    rows = query.all()
    if not rows:
        return {"file_id": target_file.id, "product_column": product_col, "amount_column": None, "rows": []}

    # Step 6: Convert to DataFrame
    df = pd.DataFrame([r.data for r in rows])
    df = df.where(pd.notnull(df), None)
    df.columns = [str(c).strip() for c in df.columns]

    # Identify orderDate column case-insensitively if missing in mapping
    if not order_date_col:
        for col in df.columns:
            if col.lower() == "orderdate":
                order_date_col = col
                break

    if not order_date_col or order_date_col not in df.columns:
        return {"file_id": target_file.id, "product_column": product_col, "amount_column": None, "rows": []}

    # Step 7: Filter by date range
    df[order_date_col] = pd.to_datetime(df[order_date_col], errors="coerce").dt.tz_localize(None)
    start = pd.to_datetime(start_date, errors="coerce").tz_localize(None)
    end = pd.to_datetime(end_date, errors="coerce").tz_localize(None)
    df = df[(df[order_date_col] >= start) & (df[order_date_col] <= end)]
    if df.empty:
        return {"file_id": target_file.id, "product_column": product_col, "amount_column": None, "rows": []}

    # Step 8: Determine amount source (totalAmount or price×quantity)
    effective_amount_col = None
    if total_amount_col and total_amount_col in df.columns:
        df[total_amount_col] = pd.to_numeric(df[total_amount_col], errors="coerce").fillna(0)
        effective_amount_col = total_amount_col
    elif price_col and qty_col and price_col in df.columns and qty_col in df.columns:
        df[price_col] = pd.to_numeric(df[price_col], errors="coerce").fillna(0)
        df[qty_col] = pd.to_numeric(df[qty_col], errors="coerce").fillna(1)
        df["__line_total__"] = df[price_col] * df[qty_col]
        effective_amount_col = "__line_total__"
    else:
        return {"file_id": target_file.id, "product_column": product_col, "amount_column": None, "rows": []}

    # Step 9: Group and aggregate
    grp = df.groupby(product_col, dropna=True)
    agg = grp.agg(
        orders=(product_col, "count"),
        total_amount=(effective_amount_col, "sum")
    ).reset_index()
    agg = agg.sort_values(by=["total_amount", "orders"], ascending=False)

    # Step 10: Prepare final response
    records = []
    for _, row in agg.head(limit).iterrows():
        records.append({
            "product": row[product_col],
            "orders": int(row["orders"]),
            "total_amount": float(row["total_amount"]) if pd.notnull(row["total_amount"]) else None
        })

    return {
        "file_id": target_file.id,
        "product_column": product_col,
        "amount_column": effective_amount_col,
        "rows": records
    }

def get_products_sales_table(
    db: Session,
    identity: dict,
    start_date: str,
    end_date: str,
    file_id: int | None = None
) -> Dict[str, Any]:

    """
    Returns product sales between start_date and end_date.
    Uses column mappings (product/order) for correct column detection.
    """

    # --- Step 1: Identify user or guest ---
    user = identity.get("user")
    guest_id = identity.get("guest_id")
    if not user and not guest_id:
        return {"columns": {}, "rows": []}

    user_id = getattr(user, "id", None) if user else None

    # --- Step 2: Find target file ---
    if file_id:
        target_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if not target_file:
            return {"columns": {}, "rows": []}
        if user_id and target_file.user_id != user_id:
            return {"columns": {}, "rows": []}
        if guest_id and target_file.guest_id != guest_id:
            return {"columns": {}, "rows": []}
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
            return {"columns": {}, "rows": []}

    # --- Step 3: Get column mappings ---
    product_mapping = (
        db.query(ColumnMapping)
        .filter(ColumnMapping.file_id == target_file.id, ColumnMapping.analysis_type == "product")
        .order_by(ColumnMapping.updated_at.desc())
        .first()
    )
    order_mapping = (
        db.query(ColumnMapping)
        .filter(ColumnMapping.file_id == target_file.id, ColumnMapping.analysis_type == "order")
        .order_by(ColumnMapping.updated_at.desc())
        .first()
    )

    # Defaults
    product_col = None
    category_col = None
    qty_col = None
    price_col = None
    order_date_col = None

    # --- Extract mapped columns if available ---
    if product_mapping:
        product_col = product_mapping.mapping.get("productName")
        category_col = product_mapping.mapping.get("category")
        qty_col = product_mapping.mapping.get("quantity")

    if order_mapping:
        price_col = order_mapping.mapping.get("totalAmount")  # e.g. "Price"
        order_date_col = order_mapping.mapping.get("orderDate")

    # --- Step 4: Load file rows ---
    query = db.query(FileRow).filter(FileRow.file_id == target_file.id)
    if user:
        query = query.join(UploadedFile).filter(UploadedFile.user_id == user.id)
    elif guest_id:
        query = query.join(UploadedFile).filter(UploadedFile.guest_id == guest_id)

    rows = query.all()
    if not rows:
        return {"columns": {}, "rows": []}

    # --- Step 5: Convert to DataFrame ---
    df = pd.DataFrame([r.data for r in rows])
    if df.empty:
        return {"columns": {}, "rows": []}

    df.columns = [str(c).strip() for c in df.columns]
    df = df.where(pd.notnull(df), None)

    # --- Find date column case-insensitively ---
    if not order_date_col:
        for col in df.columns:
            if col.lower() == "orderdate":
                order_date_col = col
                break

    if not order_date_col or order_date_col not in df.columns:
        return {"columns": {}, "rows": []}

    df[order_date_col] = pd.to_datetime(df[order_date_col], errors="coerce").dt.tz_localize(None)
    start = pd.to_datetime(start_date, errors="coerce").tz_localize(None)
    end = pd.to_datetime(end_date, errors="coerce").tz_localize(None)

    df = df[(df[order_date_col] >= start) & (df[order_date_col] <= end)]
    if df.empty:
        return {"columns": {}, "rows": []}

    # --- Step 6: Detect missing columns if mappings not found ---
    if not product_col:
        product_col = next((c for c in df.columns if "product" in c.lower()), None)
    if not category_col:
        category_col = next((c for c in df.columns if "category" in c.lower()), None)
    if not qty_col:
        qty_col = next((c for c in df.columns if c.lower() in ["quantity", "qty", "count", "units"]), None)
    if not price_col:
        price_col = next((c for c in df.columns if c.lower() in ["price", "unit_price", "rate"]), None)

    # --- Step 7: Clean numeric data ---
    if qty_col and qty_col in df.columns:
        df[qty_col] = pd.to_numeric(df[qty_col], errors="coerce").fillna(1)
    else:
        qty_col = "__dummy_qty__"
        df[qty_col] = 1

    if price_col and price_col in df.columns:
        df[price_col] = pd.to_numeric(df[price_col], errors="coerce").fillna(0.0)
    else:
        price_col = "__dummy_price__"
        df[price_col] = 0.0

    # --- Step 8: Build response ---
    results = []
    for idx, row in df.iterrows():
        results.append({
            "id": idx + 1,
            "name": row.get(product_col, None),
            "category": row.get(category_col, None),
            "price": float(row.get(price_col, 0.0)),
            "quantity": float(row.get(qty_col, 0.0)),
            "date": row.get(order_date_col).strftime("%Y-%m-%d") if pd.notnull(row.get(order_date_col)) else None
        })

    return {
        "file_id": target_file.id,
        "columns": {
            "product_column": product_col,
            "category_column": category_col,
            "price_column": price_col,
            "quantity_column": qty_col,
            "date_column": order_date_col,
        },
        "rows": results,
    }
