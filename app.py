# app.py

import os

# Fix for PermissionError
os.environ["STREAMLIT_CONFIG_DIR"] = os.path.expanduser("~/.streamlit")

# Now import Streamlit
import streamlit as st

# Your Streamlit code starts here
st.title("My Streamlit App")
st.write("Hello, world!")

import os
import json
import time
from datetime import datetime
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt

# ------------------------------
# Config
# ------------------------------
st.set_page_config(page_title="Google Play Analytics", page_icon="📱", layout="wide")

st.title("📱 Google Play Store — Real-time Analytics Dashboard")
st.caption("Interactive dashboard built from your Colab exports (apps.json, reviews.json, meta.json).")

# ------------------------------
# Data Loading
# ------------------------------
@st.cache_data(show_spinner=True)
def load_json(path_or_url):
    try:
        if path_or_url.startswith("http"):
            return pd.read_json(path_or_url)
        with open(path_or_url, "r", encoding="utf-8") as f:
            data = json.load(f)
        return pd.json_normalize(data)
    except Exception as e:
        st.warning(f"Could not load {path_or_url}: {e}")
        return pd.DataFrame()

@st.cache_data(show_spinner=True)
def load_data(base: str):
    # Try JSON first (Colab web exports), then CSV fallbacks if present
    apps = load_json(os.path.join(base, "apps_clean.json"))
    if apps.empty:
        apps = load_json(os.path.join(base, "apps.json"))
    if apps.empty and os.path.exists("apps.csv"):
        apps = pd.read_csv("apps.csv")
    reviews = load_json(os.path.join(base, "reviews.json"))
    if reviews.empty and os.path.exists("reviews.csv"):
        reviews = pd.read_csv("reviews.csv")
    meta_path = os.path.join(base, "meta.json")
    meta = {}
    try:
        if meta_path.startswith("http"):
            meta = json.loads(pd.read_json(meta_path).to_json(orient="records"))
        else:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
    except Exception:
        meta = {}
    return apps, reviews, meta

st.sidebar.header("Data Source")
default_base = "web/data" if os.path.exists("web/data") else "data"
data_base = st.sidebar.text_input("Path or URL to data folder", value=default_base, help="e.g., web/data or https://raw.githubusercontent.com/<user>/<repo>/main/web/data")
apps_df, reviews_df, meta = load_data(data_base)

if apps_df.empty:
    st.error("No apps data found. Ensure apps.json/apps_clean.json (or apps.csv) exist in the provided path/URL.")
    st.stop()

# Normalize columns expected from google-play-scraper
def clean_installs(x):
    try:
        return int(str(x).replace("+","").replace(",","").strip())
    except:
        return np.nan

if "installs_num" not in apps_df.columns and "installs" in apps_df.columns:
    apps_df["installs_num"] = apps_df["installs"].apply(clean_installs)

if "score" in apps_df.columns:
    apps_df["score"] = pd.to_numeric(apps_df["score"], errors="coerce")

if "ratings" in apps_df.columns:
    # ratings can be count, sometimes string
    apps_df["ratings_count"] = pd.to_numeric(apps_df["ratings"], errors="coerce")

# ------------------------------
# Sidebar Filters
# ------------------------------
st.sidebar.header("Filters")

# Search
search_q = st.sidebar.text_input("Search app title")

# Category
genre_col = "genre" if "genre" in apps_df.columns else ("genreId" if "genreId" in apps_df.columns else None)
genres = sorted([g for g in apps_df.get(genre_col, pd.Series([])).dropna().unique()]) if genre_col else []
chosen_genre = st.sidebar.selectbox("Category", options=["All"] + genres, index=0)

# Rating range
min_rate, max_rate = float(np.nanmin(apps_df["score"])) if "score" in apps_df else 0.0, float(np.nanmax(apps_df["score"])) if "score" in apps_df else 5.0
rate_range = st.sidebar.slider("Rating range", 0.0, 5.0, (max(0.0, min_rate), min(5.0, max_rate)))

# Installs range
min_inst = int(np.nanmin(apps_df["installs_num"])) if "installs_num" in apps_df and apps_df["installs_num"].notna().any() else 0
max_inst = int(np.nanmax(apps_df["installs_num"])) if "installs_num" in apps_df and apps_df["installs_num"].notna().any() else 10**9
inst_range = st.sidebar.slider("Installs range", 0, max(10_000, max_inst), (min_inst, max_inst))

# Apply filters
def apply_filters(df):
    out = df.copy()
    if search_q:
        out = out[out["title"].fillna("").str.contains(search_q, case=False, na=False)]
    if chosen_genre != "All" and genre_col:
        out = out[out[genre_col] == chosen_genre]
    if "score" in out.columns:
        out = out[(out["score"] >= rate_range[0]) & (out["score"] <= rate_range[1])]
    if "installs_num" in out.columns:
        out = out[(out["installs_num"] >= inst_range[0]) & (out["installs_num"] <= inst_range[1])]
    return out

apps_f = apply_filters(apps_df)

# ------------------------------
# KPIs
# ------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Apps", f"{len(apps_f):,}")
col2.metric("Avg Rating", f"{apps_f['score'].mean():.2f}" if "score" in apps_f.columns and not apps_f["score"].empty else "—")
col3.metric("Median Installs", f"{int(apps_f['installs_num'].median()):,}" if "installs_num" in apps_f.columns and apps_f["installs_num"].notna().any() else "—")
col4.metric("Updated (IST)", meta.get("generatedAtIST", "—") if isinstance(meta, dict) else "—")

st.divider()

# ------------------------------
# Charts
# ------------------------------
st.subheader("Rating Distribution")
if "score" in apps_f.columns:
    fig = px.histogram(apps_f, x="score", nbins=30, title="Distribution of App Ratings")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Rating column ('score') not available.")

st.subheader("Installs vs Rating")
if "installs_num" in apps_f.columns and "score" in apps_f.columns:
    fig = px.scatter(
        apps_f.dropna(subset=["installs_num","score"]),
        x="installs_num", y="score", hover_name="title",
        size="ratings_count" if "ratings_count" in apps_f.columns else None,
        size_max=40, log_x=True, title="Installs vs Rating"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Need 'installs_num' and 'score' for this chart.")

st.subheader("Average Rating by Category")
if genre_col and "score" in apps_f.columns:
    avg_rating = apps_f.groupby(genre_col)["score"].mean().sort_values(ascending=False).reset_index()
    fig = px.bar(avg_rating, x=genre_col, y="score", title="Average Rating by Category")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Category column not available.")

st.subheader("Top 15 Apps by Reviews")
reviews_col = "reviews" if "reviews" in apps_f.columns else ("ratings_count" if "ratings_count" in apps_f.columns else None)
if reviews_col:
    top_reviewed = apps_f.sort_values(by=reviews_col, ascending=False).head(15)
    fig = px.bar(top_reviewed, y="title", x=reviews_col, orientation="h", title="Top 15 Most Reviewed Apps")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No review count column found.")

# Sentiment Pie (optional)
st.subheader("Review Sentiment Distribution (if available)")
if not reviews_df.empty and "sentiment" in reviews_df.columns and not reviews_df["sentiment"].isnull().all():
    sent_counts = reviews_df["sentiment"].value_counts().reset_index()
    sent_counts.columns = ["sentiment", "count"]
    fig = px.pie(sent_counts, values="count", names="sentiment", title="Review Sentiment Distribution")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.caption("No 'sentiment' column in reviews data.")

# Choropleth (optional)
st.subheader("Review Count by Country (if available)")
if not reviews_df.empty and "country" in reviews_df.columns and not reviews_df["country"].isnull().all():
    country_count = reviews_df["country"].value_counts().reset_index()
    country_count.columns = ["country", "count"]
    fig = px.choropleth(
        country_count, locations="country", locationmode="country names", color="count",
        hover_name="country", title="App Review Count by Country"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.caption("No 'country' column in reviews data.")

st.divider()

# ------------------------------
# Data Table
# ------------------------------
st.subheader("Apps Table (filtered)")
show_cols = [c for c in ["title", genre_col or "genre", "score", "installs_num", "priceText", "free", "appId"] if c in apps_f.columns]
st.dataframe(apps_f[show_cols].sort_values(by="score", ascending=False).head(300), use_container_width=True)

# Download filtered data
csv = apps_f.to_csv(index=False).encode("utf-8")
st.download_button("Download filtered apps as CSV", csv, "filtered_apps.csv", "text/csv")

st.caption("Tip: Update data by rerunning your Colab export to JSON and point the data path/URL here.")
