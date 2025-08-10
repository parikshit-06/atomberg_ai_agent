import streamlit as st
import pandas as pd
import altair as alt
import ast

# ---- CONFIG ----
st.set_page_config(page_title="Atomberg AI Agent", layout="wide")
SUMMARY_FILE = "sov_multi_summary.csv"
PLATFORM_FILE = "sov_multi_platform_summary.csv"
DETAILS_FILE = "sov_multi_details.csv"

# ---- SIDEBAR ----
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Tech Stack & Tools", "Findings & Recommendations"])

# ---- PAGE 1 ----
if page == "Tech Stack & Tools":
    st.title("Tech Stack & Tools")
    st.markdown("""
    ### 🛠 Tech Stack
    - **Python 3.10+** — Core programming language
    - **Streamlit** — Dashboard UI
    - **HuggingFace Transformers (DistilBERT)** — Sentiment analysis
    - **SerpAPI** — Google Search results scraping
    - **YouTube Data API v3** — Fetch video titles, descriptions, stats
    - **BeautifulSoup4** — Fallback web scraping
    - **pandas** — Data cleaning & aggregation
    - **dotenv** — Securely load API keys
    - **tqdm** — Progress bars during scraping

    ### 📂 Links
    - [GitHub Repository](https://github.com/parikshit-06/atomberg_ai_agent)
    - [SerpAPI Documentation](https://serpapi.com/)
    - [YouTube API Docs](https://developers.google.com/youtube/v3)
    """)

# ---- PAGE 2 ----
elif page == "Findings & Recommendations":
    st.title("Findings & Recommendations")

    # Load CSV data
    try:
        df_summary = pd.read_csv(SUMMARY_FILE)
        df_platform = pd.read_csv(PLATFORM_FILE)
        df_details = pd.read_csv(DETAILS_FILE)
    except FileNotFoundError:
        st.error("CSV files not found. Please run the data collection script first.")
        st.stop()

    # ---- Overall SOV ----
    st.subheader("📊 Overall Share of Voice")
    st.dataframe(df_summary)

    chart_sov = alt.Chart(df_summary).mark_bar().encode(
        x=alt.X('brand:N', title="Brand"),
        y=alt.Y('sov:Q', title="Share of Voice"),
        tooltip=['brand', 'total_mentions', 'sov']
    ).properties(width=600)
    st.altair_chart(chart_sov)

    # ---- Platform-wise SOV ----
    st.subheader("📈 Platform-wise Share of Voice")
    st.dataframe(df_platform)

    chart_platform = alt.Chart(df_platform).mark_bar().encode(
        x=alt.X('platform:N', title="Platform"),
        y=alt.Y('sov:Q', title="Share of Voice"),
        color='brand:N',
        tooltip=['platform', 'brand', 'total_mentions', 'sov']
    ).properties(width=800)
    st.altair_chart(chart_platform)

    # ---- Sentiment Breakdown ----
    st.subheader("🗣 Sentiment Breakdown by Brand")

    sentiment_counts = []
    for _, row in df_details.iterrows():
        brand_sentiments = ast.literal_eval(row['sentiment_by_brand'])
        for brand, sent in brand_sentiments.items():
            sentiment_counts.append({
                "brand": brand,
                "sentiment": sent["label"],
                "count": 1
            })

    df_sentiment = pd.DataFrame(sentiment_counts)
    if not df_sentiment.empty:
        chart_sentiment = alt.Chart(df_sentiment.groupby(["brand", "sentiment"]).size().reset_index(name="count")).mark_bar().encode(
            x=alt.X('brand:N', title="Brand"),
            y=alt.Y('count:Q', title="Mentions"),
            color='sentiment:N',
            tooltip=['brand', 'sentiment', 'count']
        ).properties(width=800)
        st.altair_chart(chart_sentiment)
    else:
        st.info("No sentiment data available.")

    # ---- Recommendations ----
    st.subheader("💡 Recommendations")
    st.markdown("""
    1. **Double down on SEO** — Atomberg already dominates Google Search, but there’s room for more product comparison content.
    2. **Expand YouTube presence** — High engagement on fan review videos.
    3. **Leverage social listening** — Integrating Twitter data could give more real-time market feedback.
    4. **Monitor competitors** — Competitors’ online visibility is weak — an opportunity to own the narrative.
    """)
