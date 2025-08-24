import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import StringIO

st.set_page_config(page_title="Finance AI", page_icon="💸", layout="wide")
st.title("💬 Personal Finance AI")
st.caption("Upload CSVs, analyze spending, detect subscriptions, and chat using simple heuristics (no API key needed).")

# --- Helpers ---
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
        if "amount" in cl or "debit" in cl or "credit" in cl:
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

# --- File upload ---
uploaded = st.file_uploader("📂 Upload a CSV file with your transactions", type=["csv"])
if uploaded:
    df_raw = load_csv(uploaded)
    df = normalize(df_raw)

    st.subheader("📊 Data Preview")
    st.dataframe(df.head())

    # --- Summary stats ---
    st.subheader("📈 Monthly Summary")
    monthly = df.groupby(["month","type"])["amount"].sum().reset_index().pivot(index="month", columns="type", values="amount").fillna(0)
    st.dataframe(monthly)

    fig, ax = plt.subplots(figsize=(8,4))
    monthly.plot(kind="bar", stacked=True, ax=ax)
    plt.title("Income vs Expenses by Month")
    st.pyplot(fig)

    # --- Subscriptions ---
    st.subheader("🔍 Possible Subscriptions")
    subs = df.groupby("vendor")["amount"].count().reset_index()
    subs = subs[subs["amount"]>=3].sort_values("amount", ascending=False)
    if not subs.empty:
        st.write("Vendors you pay frequently (possible subscriptions):")
        st.dataframe(subs)
    else:
        st.write("No recurring vendors found.")

    # --- Simple Chatbot ---
    st.subheader("💬 Ask a Question")
    user_q = st.text_input("Type a finance question, e.g. 'How much did I spend last month?'")
    if user_q and len(df)>0:
        q = user_q.lower()
        answer = "Sorry, I don’t know that yet."
        if "spend" in q and "last month" in q:
            last_month = df["month"].max()
            spend = df[(df["month"]==last_month) & (df["type"]=="expense")]["amount"].sum()
            answer = f"You spent ${spend:,.2f} in {last_month}."
        elif "income" in q:
            income = df[df["type"]=="income"]["amount"].sum()
            answer = f"Total income so far: ${income:,.2f}."
        elif "biggest expense" in q:
            biggest = df[df["type"]=="expense"].sort_values("amount").head(1)
            if not biggest.empty:
                row = biggest.iloc[0]
                answer = f"Your biggest expense was ${-row['amount']:.2f} at {row['vendor']} on {row['date'].date()}."
        st.success(answer)

else:
    st.info("👆 Upload a CSV file to begin.")
