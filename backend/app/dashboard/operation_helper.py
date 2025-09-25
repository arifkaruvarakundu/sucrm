from app.dashboard.db_helper import get_dashboard_data_from_db, get_total_orders_count_data_from_db
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
import pandas as pd
from app import models
from app.dashboard.llm_helper import infer_columns_with_llm, infer_unique_id_column_with_llm

def get_dashboard_data(db, limit):

    dashboard_data_response = get_dashboard_data_from_db(db, limit)

    return dashboard_data_response

CUSTOMER_CANDIDATES = [
  "customer", "customer_name", "name", "full_name", "username", "user", "client", "buyer"
]
AMOUNT_CANDIDATES = [
  "total", "amount", "price", "subtotal", "grand_total", "order_total", "total_price", "payment_amount"
]
UNIQUE_ID_CANDIDATES = [
  "phone", "phone_number", "mobile", "email", "customer_id", "user_id", "client_id", 
  "customer_code", "account_number", "contact_number"
]

PRODUCT_CANDIDATES = ["product","product_name","item","item_name","product_id","item_id","sku","product_code","product_title", "order_item"]


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

def get_top_customers(db: Session, limit: int = 5) -> Dict[str, Any]:
  # Pull a recent sample to analyze (adjust limit as needed)
  rows: List[models.FileRow] = (
    db.query(models.FileRow)
      .order_by(models.FileRow.id.desc())
      # .limit(1000)
      .all()
  )
  data_rows = [r.data for r in rows]
  if not data_rows:
    return {"customer_column": None, "amount_column": None, "rows": []}

  df = pd.DataFrame(data_rows)
  df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
  df = df.where(pd.notnull(df), None)

  # Heuristic first
  cust_col, amt_col = pick_columns_heuristic(df)
  # If missing, try LLM
  if not cust_col:
    cols = list(df.columns)
    samples = _safe_sample_values(df)
    llm_cust, llm_amt = infer_columns_with_llm(cols, samples)
    cust_col = cust_col or llm_cust
    amt_col = amt_col or llm_amt

  if not cust_col:
    return {"customer_column": None, "amount_column": amt_col, "rows": []}

  result = _aggregate_top_customers(df, cust_col, amt_col, limit)
  return {"customer_column": cust_col, "amount_column": amt_col, "rows": result}

def get_total_sales(db: Session) -> Dict[str, Any]:
  """
  Find amount column using heuristics + LLM fallback, then sum all values.
  Returns: { amount_column: str, total_sales: float, row_count: int }
  """
  # Pull recent rows to analyze
  rows: List[models.FileRow] = (
    db.query(models.FileRow)
      .order_by(models.FileRow.id.desc())
      # .limit(1000)
      .all()
  )
  data_rows = [r.data for r in rows]
  if not data_rows:
    return {"amount_column": None, "total_sales": 0.0, "row_count": 0}

  df = pd.DataFrame(data_rows)
  df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
  df = df.where(pd.notnull(df), None)

  # Heuristic first - only need amount column
  _, amt_col = pick_columns_heuristic(df)
  
  # If missing, try LLM
  if not amt_col:
    cols = list(df.columns)
    samples = _safe_sample_values(df)
    _, llm_amt = infer_columns_with_llm(cols, samples)
    amt_col = amt_col or llm_amt

  if not amt_col:
    return {"amount_column": None, "total_sales": 0.0, "row_count": len(df)}

  # Convert to numeric and sum
  numeric_values = pd.to_numeric(df[amt_col], errors="coerce")
  total_sales = float(numeric_values.sum()) if not numeric_values.isna().all() else 0.0
  
  return {
    "amount_column": amt_col,
    "total_sales": round(total_sales, 3),
    "row_count": len(df)
  }

def get_total_customers(db: Session) -> Dict[str, Any]:
  """
  Find unique identifier column using heuristics + LLM fallback, then count distinct customers.
  Returns: { unique_id_column: str, total_customers: int, row_count: int }
  """
  # Pull recent rows to analyze
  rows: List[models.FileRow] = (
    db.query(models.FileRow)
      .order_by(models.FileRow.id.desc())
      # .limit(1000)
      .all()
  )
  data_rows = [r.data for r in rows]
  if not data_rows:
    return {"unique_id_column": None, "total_customers": 0, "row_count": 0}

  df = pd.DataFrame(data_rows)
  df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
  df = df.where(pd.notnull(df), None)

  # Heuristic first
  unique_id_col = pick_unique_id_column_heuristic(df)
  
  # If missing, try LLM
  if not unique_id_col:
    cols = list(df.columns)
    samples = _safe_sample_values(df)
    # Ask LLM to identify unique identifier column
    llm_unique_id = infer_unique_id_column_with_llm(cols, samples)
    unique_id_col = unique_id_col or llm_unique_id

  if not unique_id_col:
    return {"unique_id_column": None, "total_customers": 0, "row_count": len(df)}

  # Count distinct values in the unique identifier column
  distinct_count = df[unique_id_col].nunique()
  
  return {
    "unique_id_column": unique_id_col,
    "total_customers": int(distinct_count),
    "row_count": len(df)
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

def get_total_orders_count(db: Session):

  total_orders_count_data = get_total_orders_count_data_from_db(db)

  return total_orders_count_data