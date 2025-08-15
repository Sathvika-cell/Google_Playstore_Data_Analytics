
# Google Play Analytics — Streamlit App

An interactive Streamlit dashboard for your Google Play Store analytics, built to read the JSON exports from your Colab pipeline.

## 📂 Project Structure
```
gplay_streamlit_app/
├─ app.py
├─ requirements.txt
└─ README.md
```

## ▶️ Run Locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
Then open the URL shown in the terminal.

## 📡 Pointing to Your Data
In the sidebar, set **Path or URL to data folder** to where your JSON lives:
- Local: `web/data` (if you cloned your site folder locally)
- Remote (GitHub raw): `https://raw.githubusercontent.com/<your-username>/<your-repo>/main/web/data`

The app tries to load:
- `apps_clean.json` (or `apps.json`)
- `reviews.json`
- `meta.json`

It also falls back to `apps.csv` and `reviews.csv` if present.

## 🚀 Deploy (fastest): Streamlit Community Cloud
1. Push this folder to a GitHub repo.
2. Go to **https://share.streamlit.io** and deploy the repo.
3. In the app’s sidebar, point to your JSON URL (GitHub raw links).

## 🔁 Alternative: Keep Netlify/Vercel for Static Site
- Use the static `/web` folder we generated earlier for Netlify/Vercel (ideal for static hosting).
- Use this Streamlit app for dynamic exploration (Streamlit Cloud/Render).

## ✅ Features
- Sidebar filters: search, category, rating, installs
- KPIs: apps count, average rating, median installs
- Charts: rating histogram, installs vs rating scatter, avg rating by category, top reviewed apps
- Optional: sentiment pie & review country choropleth (if columns exist)
- Data table + CSV download
