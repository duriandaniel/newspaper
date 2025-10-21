import pandas as pd
import streamlit as st

st.set_page_config(page_title="ASX News Table", layout="wide")

@st.cache_data(ttl=600)
def load_csv(local_path: str | None, remote_url: str | None) -> pd.DataFrame:
    if remote_url:
        return pd.read_csv(remote_url)
    return pd.read_csv(local_path)

st.title("ASX News Table")

# Config: choose one source
CSV_LOCAL_PATH = "smh_business.csv"  # file in your repo
CSV_REMOTE_URL = st.secrets.get("CSV_REMOTE_URL", None)  # optional URL via Secrets

df = load_csv(CSV_LOCAL_PATH if not CSV_REMOTE_URL else None, CSV_REMOTE_URL)

# Basic validation
expected_cols = ["time", "headline", "sector", "stock", "article link"]
missing = [c for c in expected_cols if c not in df.columns]
if missing:
    st.error(f"Missing columns: {missing}. Got {list(df.columns)}")
    st.stop()

# Filters
with st.sidebar:
    st.header("Filters")
    q = st.text_input("Search headline or link").strip().lower()
    sectors = [""] + sorted([s for s in df["sector"].dropna().unique()])
    sector = st.selectbox("Sector", sectors, format_func=lambda x: "All" if x == "" else x)
    stock = st.text_input("Stock filter (e.g. REX)").strip()

# Apply filters
mask = pd.Series([True] * len(df))
if q:
    mask &= df["headline"].str.lower().str.contains(q, na=False) | df["article link"].str.lower().str.contains(q, na=False)
if sector:
    mask &= df["sector"] == sector
if stock:
    mask &= df["stock"].astype(str).str.contains(stock, case=False, na=False)

# Sort by time desc if present
if "time" in df.columns:
    with pd.option_context("future.no_silent_downcasting", True):
        df["time_sort"] = pd.to_datetime(df["time"], errors="coerce")
    out = df.loc[mask].sort_values("time_sort", ascending=False, na_position="last").drop(columns=["time_sort"])
else:
    out = df.loc[mask]

st.caption(f"Showing {len(out)} of {len(df)} rows")
st.dataframe(out, use_container_width=True)

# Small download button
csv_bytes = out.to_csv(index=False).encode("utf-8")
st.download_button("Download filtered CSV", data=csv_bytes, file_name="filtered_news.csv", mime="text/csv")
