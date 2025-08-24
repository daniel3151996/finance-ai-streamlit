import streamlit as st
import pandas as pd
import numpy as np
from io import StringIO

st.set_page_config(page_title="Finance AI (Free)", page_icon="💸", layout="wide")
st.title("💬 Personal Finance AI")
st.caption("Upload CSVs, see spending insights, detect subscriptions, and chat using simple heuristics (no API key needed).")

COMMON_DATE_COLS = ["date","Date","posted","Posted Date","Transaction Date"]
COMMON_DESC_COLS = ["description","Description","name","Payee","Merchant"]
COMMON_AMT_COLS  = ["amount","Amount","Transaction Amount","Debit","Credit"]

def load_csv(file) -> pd.DataFrame:
    raw = file.read()
    try:
        txt = raw.decode("utf-8")
    except:
        txt = raw.decode("latin-1")
    return pd.read_csv(StringIO(txt))

def normalize(df: pd.DataFrame) -> pd.DataFrame:
    cols = {c.lower(): c for c in df.columns}
    date_col = next((cols[c] for c in cols if "date" in c), None)
    desc_col = next((cols[c] for c in cols if "desc" in c or "merchant" in c or "payee" in c), None)
    amt_col = None
    for c in df.columns:
        cl = c.lower()
        if cl in [a.lower() for a in COMMON_AMT_COLS] or "amount" in cl or "debit" in cl or "credit" in cl:
            amt_col = c
            break
    out = pd.DataFrame()
    out["date"] = pd.to_datetime(df[date_col], errors="coerce") if date_col else pd.NaT
    out["description"] = df[desc_col].astype(str) if desc_col else ""
    if "debit" in [c.lower() for c in df.columns] and "credit" in [c.lower() for c in df.columns]:
        debit = df[[c for c in df.columns if c.lower()=="debit"][0]].fillna(0).astype(float)
        credit = df[[c for c in df.columns if c.lower()=="credit"][0]].fillna(0).astype(float)
        out["amount"] = credit - debit
    else:
        out["amount"] = pd.to_numeric(df[amt_col], errors="coerce")
    out["amount"] = out["amount"].fillna(0.0)
    out["month"] = out["date"].dt.to_period("M").astype(str)
    out["type"] = np.where(out["amount"]>=0, "income", "expense")
    out["vendor"] = out["description"].str.replace(
        r"(?i)pos|card|debit|credit|purchase|auth|online|transaction", "", regex=True
    ).str.strip()
    return out

st.write("✅ Finance AI app loaded")
