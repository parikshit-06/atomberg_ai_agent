import streamlit as st
import pandas as pd
import altair as alt
import subprocess
import os

st.set_page_config(page_title="Share of Voice Dashboard", layout="wide")
st.title("📊 Share of Voice (SoV) Dashboard")

# Config
DETAILS_FILE = "sov_multi_details.csv"
SUMMARY_FILE = "sov_multi_summary.csv"
PLATFORM_FILE = "sov_multi_platform_summary.csv"

# Sidebar
st.sidebar.header("Actions")
run_agent = st.sidebar.button("🔄 Run Data Collection Agent")
upload_mode = st.sidebar.checkbox("📤 Upload CSVs instead of running script")

if run_agent:
    with st.spinner("Running scraping agent... this may take a few minutes"):
        subprocess.run(["python", "sov_agent_multiplatform.py"], check=True)

# Data loading
if upload_mode:
    details_file = st.file_uploader("Upload Details CSV", type=["csv"])
    summary_file = st.file_uploader("Upload Summary CSV", type=["csv"])
    platform_file = st.file_uploader("Upload Per-Platform Summary CSV", type=["csv"])
    if details_file and summary_file and platform_file:
        df_details = pd.read_csv(details_file)
        df_summary = pd.read_csv(summary_file)
        df_platform = pd.read_csv(platform_file)
    else:
        st.warning("Please upload all three CSV files.")
        st.stop()
else:
    if not (os.path.exists(DETAILS_FILE) and os.path.exists(SUMMARY_FILE) and os.path.exists(PLATFORM_FILE)):
        st.error("No CSVs found. Run the agent first or enable upload mode.")
        st.stop()
    df_details = pd.read_csv(DETAILS_FILE)
    df_summary = pd.read_csv(SUMMARY_FILE)
    df_platform = pd.read_csv(PLATFORM_FILE)

# Overall SoV
st.subheader("Overall Share of Voice")
st.dataframe(df_summary)

chart = alt.Chart(df_summary).mark_bar().encode(
    x=alt.X("sov:Q", title="Share of Voice"),
    y=alt.Y("brand:N", sort="-x"),
    color="brand:N"
)
st.altair_chart(chart, use_container_width=True)

# Per-platform SoV
st.subheader("Per-Platform Share of Voice")
platform_choice = st.selectbox("Select platform", options=df_platform["platform"].unique())
df_filtered = df_platform[df_platform["platform"] == platform_choice]
st.dataframe(df_filtered)

chart_platform = alt.Chart(df_filtered).mark_bar().encode(
    x=alt.X("sov:Q", title="Share of Voice"),
    y=alt.Y("brand:N", sort="-x"),
    color="brand:N"
).properties(title=f"SoV for {platform_choice}")
st.altair_chart(chart_platform, use_container_width=True)

# Details
st.subheader("Detailed Results")
st.dataframe(df_details)
