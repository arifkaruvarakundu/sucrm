from fastapi import Depends, Query
from app.dashboard.db_helper import get_dashboard_data_from_db, get_total_orders_count_data_from_db
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
import pandas as pd
from app import models
from app.dashboard.llm_helper import infer_columns_with_llm, infer_unique_id_column_with_llm
from app.customer.db_helper import fetch_file_rows
from app.database import get_db
from app.utils.deps import get_identity
from app.models import *
from sqlalchemy import or_

def get_dashboard_data(db, limit, user_id: int | None = None, guest_id: str | None = None):

    dashboard_data_response = get_dashboard_data_from_db(db, limit, user_id, guest_id)

    return dashboard_data_response

CUSTOMER_CANDIDATES = [
  "customer", "customer_name", "name", "full_name", "username", "user", "client", "buyer","اسم_العميل", "العميل"
]

AMOUNT_CANDIDATES = [
  "total", "amount", "price", "subtotal", "grand_total", "order_total", "total_price", "payment_amount", "إجمالي_المدفوع", "إجمالي", "المبلغ"
]

UNIQUE_ID_CANDIDATES = [
  "phone", "phone_number", "mobile", "email", "customer_id", "user_id", "client_id", 
  "customer_code", "account_number", "contact_number", "civil_id", "رقم_الهاتف", "رقم البطاقة المدنية"
]

PRODUCT_CANDIDATES = ["product","product_name","item","item_name","product_id","item_id","sku","product_code","product_title", "order_item"]

JUNK_KEYWORDS = ["total", "grand total", "subtotal", "summary", "إجمالي", "المجموع"]

def pick_columns_heuristic(df: pd.DataFrame) -> Tuple[Optional[str], Optional[str]]:
  # Lowercase map for exact/contains matches
  lower_to_raw = {c.lower(): c for c in df.columns}

  def match(cands: List[str]) -> Optional[str]:
    for key in cands:
      if key in lower_to_raw:
        return lower_to_raw[key]
    for key in cands:
      for lc, raw in lower_to_raw.items():
        if key in lc:
          return raw
    return None

  customer_col = match(CUSTOMER_CANDIDATES)
  amount_col = match(AMOUNT_CANDIDATES)
  return customer_col, amount_col

def pick_unique_id_column_heuristic(df: pd.DataFrame) -> Optional[str]:
  """Find the best unique identifier column for counting distinct customers."""
  lower_to_raw = {c.lower(): c for c in df.columns}
  
  def match(cands: List[str]) -> Optional[str]:
    for key in cands:
      if key in lower_to_raw:
        return lower_to_raw[key]
    for key in cands:
      for lc, raw in lower_to_raw.items():
        if key in lc:
          return raw
    return None
  
  return match(UNIQUE_ID_CANDIDATES)

def _safe_sample_values(df: pd.DataFrame, per_col: int = 5) -> Dict[str, List[str]]:
  """
  Return a tiny sample per column for LLM context.
  Mask likely PII like emails/phones to reduce leakage.
  """
  samples: Dict[str, List[str]] = {}
  for col in df.columns:
    vals = df[col].dropna().astype(str).unique().tolist()[: per_col]
    masked = []
    for v in vals:
      lower = v.lower()
      if "@" in lower or lower.replace("+", "").replace("-", "").replace(" ", "").isdigit():
        masked.append("[REDACTED]")
      else:
        masked.append(v[:40])  # clip long strings
    samples[col] = masked
  return samples

def _aggregate_top_customers(df: pd.DataFrame, customer_col: str, amount_col: str | None, limit: int) -> List[Dict[str, Any]]:
  # Coerce amount to numeric for summing
  if amount_col and amount_col in df.columns:
    df[amount_col] = pd.to_numeric(df[amount_col], errors="coerce")
  grp = df.groupby(customer_col, dropna=True)
  if amount_col and amount_col in df.columns:
    agg = grp.agg(orders=(customer_col, "count"), total_amount=(amount_col, "sum")).reset_index()
    agg = agg.sort_values(by=["total_amount", "orders"], ascending=False)
  else:
    agg = grp.agg(orders=(customer_col, "count")).reset_index()
    agg["total_amount"] = None
    agg = agg.sort_values(by=["orders"], ascending=False)

  return agg.head(limit).to_dict(orient="records")

def get_top_customers(db: Session, identity: dict, file_id: int | None = None, limit: int = 5) -> dict:
    user = identity.get("user")
    guest_id = identity.get("guest_id")

    if not user and not guest_id:
        return {"file_id": None, "customer_column": None, "amount_column": None, "rows": []}

    user_id = getattr(user, "id", None) if user else None

    # Step 1: Determine target file
    if file_id:
        target_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if not target_file:
            return {"file_id": None, "customer_column": None, "amount_column": None, "rows": []}
        if user_id and target_file.user_id != user_id:
            return {"file_id": target_file.id, "customer_column": None, "amount_column": None, "rows": []}
        if guest_id and target_file.guest_id != guest_id:
            return {"file_id": target_file.id, "customer_column": None, "amount_column": None, "rows": []}
    else:
        filters = []
        if user_id:
            filters.append(UploadedFile.user_id == user_id)
        if guest_id:
            filters.append(UploadedFile.guest_id == guest_id)
        if not filters:
            return {"file_id": None, "customer_column": None, "amount_column": None, "rows": []}

        target_file = (
            db.query(UploadedFile)
            .filter(or_(*filters))
            .order_by(UploadedFile.uploaded_at.desc())
            .first()
        )
        if not target_file:
            return {"file_id": None, "customer_column": None, "amount_column": None, "rows": []}

    # Step 2: Get column mapping for "order" analysis
    mapping_obj = (
        db.query(ColumnMapping)
        .filter(ColumnMapping.file_id == target_file.id, ColumnMapping.analysis_type == "order")
        .order_by(ColumnMapping.updated_at.desc())
        .first()
    )

    customer_col = mapping_obj.mapping.get("customerName") if mapping_obj else None
    amount_col = mapping_obj.mapping.get("amount") if mapping_obj else None

    # Step 3: Query FileRows for this file and user/guest
    query = db.query(FileRow).filter(FileRow.file_id == target_file.id)
    if user:
        query = query.join(UploadedFile).filter(UploadedFile.user_id == user.id)
    elif guest_id:
        query = query.join(UploadedFile).filter(UploadedFile.guest_id == guest_id)

    rows = query.all()
    if not rows:
        return {"file_id": target_file.id, "customer_column": customer_col, "amount_column": amount_col, "rows": []}

    # Step 4: Convert rows to DataFrame
    df = pd.DataFrame([r.data for r in rows])
    if df.empty:
        return {"file_id": target_file.id, "customer_column": customer_col, "amount_column": amount_col, "rows": []}

    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    df = df.where(pd.notnull(df), None)

    # Step 5: Detect customer + amount columns if mapping missing
    if not customer_col or not amount_col:
        detected_cust, detected_amt = pick_columns_heuristic(df)
        if not customer_col:
            customer_col = detected_cust
        if not amount_col:
            amount_col = detected_amt

    # Step 6: Aggregate top customers
    if not customer_col:
        return {"file_id": target_file.id, "customer_column": None, "amount_column": amount_col, "rows": []}

    result = _aggregate_top_customers(df, customer_col, amount_col, limit)

    return {
        "file_id": target_file.id,
        "customer_column": customer_col,
        "amount_column": amount_col,
        "rows": result,
    }

JUNK_KEYWORDS = [
    "total", "grand total", "subtotal", "summary",
    "إجمالي", "المجموع", "المجموع الكلي", "الاجمالي", "page"
]

POSSIBLE_ORDER_KEYS = {
    "رقم الفاتورة": "order_id",
    "invoice_no": "order_id",
    "invoice number": "order_id",
    "orderid": "order_id",
    "order_id": "order_id",
    "order_no": "order_id",
    "order number": "order_id",
    "رقم الطلب": "order_id"
}

def normalize_key(key: str) -> str:
    return str(key).strip().lower().replace(" ", "_")

def detect_order_column(df: pd.DataFrame) -> str | None:
    cols = list(df.columns)
    normalized_cols = {normalize_key(c): c for c in cols}
    for key in POSSIBLE_ORDER_KEYS.keys():
        nk = normalize_key(key)
        if nk in normalized_cols:
            return normalized_cols[nk]
    return None

def get_total_sales(db: Session = Depends(get_db), identity: dict = Depends(get_identity), file_id: int | None = Query(None, description="Optional file ID")):
    user = identity.get("user")
    guest_id = identity.get("guest_id")

    if not user and not guest_id:
        return {"file_id": None, "total_sales": 0.0, "row_count": 0}

    user_id = getattr(user, "id", None) if user else None

    # Step 1: Determine target file
    if file_id:
        target_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if not target_file:
            return {"file_id": None, "total_sales": 0.0, "row_count": 0}
        if user_id and target_file.user_id != user_id:
            return {"file_id": target_file.id, "total_sales": 0.0, "row_count": 0}
        if guest_id and target_file.guest_id != guest_id:
            return {"file_id": target_file.id, "total_sales": 0.0, "row_count": 0}
    else:
        target_file = (
            db.query(UploadedFile)
            .filter(
                (UploadedFile.user_id == user_id if user_id else False) |
                (UploadedFile.guest_id == guest_id if guest_id else False)
            )
            .order_by(UploadedFile.uploaded_at.desc())
            .first()
        )
        if not target_file:
            return {"file_id": None, "total_sales": 0.0, "row_count": 0}

    # Step 2: Get column mapping for "order" analysis
    mapping_obj = (
        db.query(ColumnMapping)
        .filter(ColumnMapping.file_id == target_file.id, ColumnMapping.analysis_type == "order")
        .order_by(ColumnMapping.updated_at.desc())
        .first()
    )
    if not mapping_obj or "orderId" not in mapping_obj.mapping:
        return {"file_id": target_file.id, "total_sales": 0.0, "row_count": 0}

    order_col = mapping_obj.mapping["orderId"]
    amount_col = mapping_obj.mapping.get("totalAmount")
    if not amount_col:
        return {"file_id": target_file.id, "total_sales": 0.0, "row_count": 0}

    # Step 3: Query FileRows for this file and user/guest
    query = db.query(FileRow).join(UploadedFile, FileRow.file_id == UploadedFile.id).filter(FileRow.file_id == target_file.id)

    if user:
        query = query.filter(UploadedFile.user_id == user.id)
    elif guest_id:
        query = query.filter(UploadedFile.guest_id == guest_id)

    # Filter rows with valid orderId and non-empty amount
    query = query.filter(FileRow.data[order_col].astext.isnot(None))
    query = query.filter(FileRow.data[order_col].astext != "")
    query = query.filter(FileRow.data[amount_col].astext.isnot(None))
    query = query.filter(FileRow.data[amount_col].astext != "")

    rows = query.all()
    row_count = len(rows)
    if row_count == 0:
        return {"file_id": target_file.id, "total_sales": 0.0, "row_count": 0}

    # Step 4: Sum only the rows that have valid order IDs
    total_sales = sum(float(r.data.get(amount_col) or 0.0) for r in rows)

    return {
        "file_id": target_file.id,
        "total_sales": round(total_sales, 3),
        "row_count": row_count
    }

def get_total_customers(db: Session, identity: dict, file_id: int | None = None) -> dict:

    user = identity.get("user")
    guest_id = identity.get("guest_id")

    if not user and not guest_id:
        return {"file_id": None, "total_customers": 0, "row_count": 0}

    user_id = getattr(user, "id", None) if user else None

    # Step 1: Determine target file
    if file_id:
        target_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if not target_file:
            return {"file_id": None, "total_customers": 0, "row_count": 0}
        if user_id and target_file.user_id != user_id:
            return {"file_id": target_file.id, "total_customers": 0, "row_count": 0}
        if guest_id and target_file.guest_id != guest_id:
            return {"file_id": target_file.id, "total_customers": 0, "row_count": 0}
    else:
        filters = []
        if user_id:
            filters.append(UploadedFile.user_id == user_id)
        if guest_id:
            filters.append(UploadedFile.guest_id == guest_id)
        if not filters:
            return {"file_id": None, "total_customers": 0, "row_count": 0}

        target_file = (
            db.query(UploadedFile)
            .filter(or_(*filters))
            .order_by(UploadedFile.uploaded_at.desc())
            .first()
        )
        if not target_file:
            return {"file_id": None, "total_customers": 0, "row_count": 0}

    # Step 2: Get column mapping for "order" analysis
    mapping_obj = (
        db.query(ColumnMapping)
        .filter(ColumnMapping.file_id == target_file.id, ColumnMapping.analysis_type == "order")
        .order_by(ColumnMapping.updated_at.desc())
        .first()
    )
    if not mapping_obj:
        return {"file_id": target_file.id, "total_customers": 0, "row_count": 0}

    customer_name_col = mapping_obj.mapping.get("customerName")
    customer_phone_col = mapping_obj.mapping.get("customerPhone")

    if not customer_name_col and not customer_phone_col:
        return {"file_id": target_file.id, "total_customers": 0, "row_count": 0}

    # Step 3: Query FileRows for this file and user/guest
    query = db.query(FileRow).join(UploadedFile, FileRow.file_id == UploadedFile.id).filter(FileRow.file_id == target_file.id)
    if user:
        query = query.filter(UploadedFile.user_id == user.id)
    elif guest_id:
        query = query.filter(UploadedFile.guest_id == guest_id)

    # Step 4: Filter rows with valid orderId if exists
    if "orderId" in mapping_obj.mapping:
        order_col = mapping_obj.mapping["orderId"]
        query = query.filter(FileRow.data[order_col].astext.isnot(None), FileRow.data[order_col].astext != "")

    # Filter valid name/phone
    if customer_name_col:
        query = query.filter(FileRow.data[customer_name_col].astext.isnot(None), FileRow.data[customer_name_col].astext != "")
    if customer_phone_col:
        query = query.filter(FileRow.data[customer_phone_col].astext.isnot(None), FileRow.data[customer_phone_col].astext != "")

    rows = query.all()
    row_count = len(rows)
    if row_count == 0:
        return {"file_id": target_file.id, "total_customers": 0, "row_count": 0}

    # Step 5: Count unique customers based on available keys
    if customer_name_col and customer_phone_col:
        # Use composite key
        unique_customers = len(set(
            (r.data.get(customer_name_col), r.data.get(customer_phone_col)) 
            for r in rows
            if r.data.get(customer_name_col) or r.data.get(customer_phone_col)
        ))
    elif customer_phone_col:
        # Use phone only
        unique_customers = len(set(
            r.data.get(customer_phone_col) for r in rows if r.data.get(customer_phone_col)
        ))
    else:
        # Use name only
        unique_customers = len(set(
            r.data.get(customer_name_col) for r in rows if r.data.get(customer_name_col)
        ))

    return {
        "file_id": target_file.id,
        "total_customers": unique_customers,
        "row_count": row_count
    }

def pick_product_column_heuristic(df):
  lower_to_raw = {c.lower(): c for c in df.columns}
  for k in PRODUCT_CANDIDATES:
    if k in lower_to_raw: return lower_to_raw[k]
  for k in PRODUCT_CANDIDATES:
    for lc, raw in lower_to_raw.items():
      if k in lc: return raw
  return None

def get_total_products(db: Session, identity: dict, file_id: int | None = None) -> dict:
    user = identity.get("user")
    guest_id = identity.get("guest_id")

    if not user and not guest_id:
        return {"file_id": None, "total_products": 0, "row_count": 0}

    user_id = getattr(user, "id", None) if user else None

    # Step 1: Determine target file
    if file_id:
        target_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if not target_file:
            return {"file_id": None, "total_products": 0, "row_count": 0}
        if user_id and target_file.user_id != user_id:
            return {"file_id": target_file.id, "total_products": 0, "row_count": 0}
        if guest_id and target_file.guest_id != guest_id:
            return {"file_id": target_file.id, "total_products": 0, "row_count": 0}
    else:
        filters = []
        if user_id:
            filters.append(UploadedFile.user_id == user_id)
        if guest_id:
            filters.append(UploadedFile.guest_id == guest_id)

        if not filters:
            return {"file_id": None, "total_products": 0, "row_count": 0}

        target_file = (
            db.query(UploadedFile)
            .filter(or_(*filters))
            .order_by(UploadedFile.uploaded_at.desc())
            .first()
        )
        if not target_file:
            return {"file_id": None, "total_products": 0, "row_count": 0}

    # Step 2: Get column mapping for "product" analysis
    mapping_obj = (
        db.query(ColumnMapping)
        .filter(ColumnMapping.file_id == target_file.id, ColumnMapping.analysis_type == "product")
        .order_by(ColumnMapping.updated_at.desc())
        .first()
    )
    if not mapping_obj or not mapping_obj.mapping:
        return {"file_id": target_file.id, "total_products": 0, "row_count": 0}

    product_col = mapping_obj.mapping.get("productName")
    if not product_col:
        # fallback: pick first column in mapping
        product_col = list(mapping_obj.mapping.values())[0]

    # Step 3: Query FileRows for this file and user/guest
    query = db.query(FileRow).join(UploadedFile, FileRow.file_id == UploadedFile.id).filter(FileRow.file_id == target_file.id)
    if user:
        query = query.filter(UploadedFile.user_id == user.id)
    elif guest_id:
        query = query.filter(UploadedFile.guest_id == guest_id)

    # Step 4: Only consider rows with valid product value
    query = query.filter(FileRow.data[product_col].astext.isnot(None))
    query = query.filter(FileRow.data[product_col].astext != "")

    rows = query.all()
    row_count = len(rows)
    if row_count == 0:
        return {"file_id": target_file.id, "total_products": 0, "row_count": 0}

    # Step 5: Count unique products
    unique_products = len(set(r.data.get(product_col) for r in rows if r.data.get(product_col)))

    return {
        "file_id": target_file.id,
        "total_products": unique_products,
        "row_count": row_count
    }

def get_total_orders_count(db: Session, identity: dict, file_id: Optional[int] = None) -> Dict[str, Any]:

  total_orders_count_data = get_total_orders_count_data_from_db(db, identity, file_id)

  return total_orders_count_data