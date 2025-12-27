import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import date
import matplotlib.pyplot as plt

# ------------------ SUPABASE CONFIG ------------------
SUPABASE_URL = "https://qvtfopfumqjkztyhizpf.supabase.co"
SUPABASE_KEY = "sb_publishable_uuEDfCh-X11vUa7o29qTTg_KFPNFCWM"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------ PAGE CONFIG ------------------
st.set_page_config(
    page_title="Political Social Listening Dashboard",
    layout="wide"
)

st.title("📊 Political Social Listening Dashboard")
st.markdown(
    "Track **public sentiment** across Indian political parties using news data."
)

# ------------------ PARTY FULL NAMES ------------------
PARTY_FULL_NAMES = {
    "BJP": "Bharatiya Janata Party",
    "INC": "Indian National Congress",
    "AAP": "Aam Aadmi Party",
    "BSP": "Bahujan Samaj Party",
    "CPI(M)": "Communist Party of India (Marxist)",
    "NPP": "National People's Party",
    "SP": "Samajwadi Party",
    "RJD": "Rashtriya Janata Dal",
    "JD(U)": "Janata Dal (United)",
    "SAD": "Shiromani Akali Dal",
    "INLD": "Indian National Lok Dal",
    "DMK": "Dravida Munnetra Kazhagam",
    "AIADMK": "All India Anna Dravida Munnetra Kazhagam",
    "TDP": "Telugu Desam Party",
    "YSRCP": "YSR Congress Party",
    "BRS": "Bharat Rashtra Samithi",
    "JD(S)": "Janata Dal (Secular)",
    "AITC": "All India Trinamool Congress",
    "BJD": "Biju Janata Dal",
    "Shiv Sena": "Shiv Sena",
    "NCP": "Nationalist Congress Party",
    "JMM": "Jharkhand Mukti Morcha",
    "MNF": "Mizo National Front",
    "SKM": "Sikkim Krantikari Morcha",
    "AGP": "Asom Gana Parishad",
    "Tipra Motha": "Tipra Motha Party"
}

ALL_PARTIES = list(PARTY_FULL_NAMES.keys())

# ------------------ DATE FILTER ------------------
st.sidebar.header("📅 Filters")
start_date = st.sidebar.date_input("Start Date", value=date.today())
end_date = st.sidebar.date_input("End Date", value=date.today())

# ------------------ PARTY SELECT ------------------
selected_party = st.sidebar.selectbox(
    "Select Political Party",
    ALL_PARTIES,
    format_func=lambda p: f"{p} — {PARTY_FULL_NAMES[p]}"
)

# ------------------ FETCH SENTIMENT SUMMARY ------------------
summary_response = (
    supabase
    .table("party_sentiment_summary")
    .select("*")
    .eq("party", selected_party)
    .execute()
)

summary_df = pd.DataFrame(summary_response.data)

# ------------------ ENSURE ALL 3 SENTIMENTS (BULLETPROOF) ------------------
sentiments = ["Positive", "Negative", "Neutral"]

# Always start with base structure
summary_df = pd.DataFrame({
    "sentiment": sentiments,
    "total": [0, 0, 0]
})

if summary_response.data:
    temp_df = pd.DataFrame(summary_response.data)

    # Normalize column name
    if "count" in temp_df.columns and "total" not in temp_df.columns:
        temp_df = temp_df.rename(columns={"count": "total"})

    if "sentiment" in temp_df.columns and "total" in temp_df.columns:
        summary_df = summary_df.merge(
            temp_df[["sentiment", "total"]],
            on="sentiment",
            how="left"
        )
        summary_df["total"] = summary_df["total_y"].fillna(summary_df["total_x"])
        summary_df = summary_df[["sentiment", "total"]]

# Add party column
summary_df.insert(0, "party", selected_party)

# ------------------ SERIAL NUMBER FROM 1 ------------------
summary_df.index = range(1, len(summary_df) + 1)


# ------------------ SENTIMENT SUMMARY TABLE ------------------
st.subheader(
    f"📌 Sentiment Summary — {selected_party} ({PARTY_FULL_NAMES[selected_party]})"
)
st.dataframe(summary_df, use_container_width=True)

# ------------------ FILTER ZERO VALUES FOR CHARTS ONLY ------------------
chart_df = summary_df[summary_df["total"] > 0]

# ------------------ BAR CHART ------------------
st.subheader("📊 Sentiment Distribution")

if not chart_df.empty:
    st.bar_chart(chart_df.set_index("sentiment")["total"])
else:
    st.info("No sentiment data available to display.")

# ------------------ PIE CHART ------------------
st.subheader("🌗 Sentiment Share")

if not chart_df.empty:
    fig, ax = plt.subplots()
    ax.pie(
        chart_df["total"],
        labels=chart_df["sentiment"],
        autopct="%1.1f%%",
        startangle=90
    )
    ax.axis("equal")
    st.pyplot(fig)
else:
    st.info("No sentiment data available to display.")

# ------------------ FETCH LATEST HEADLINES ------------------
st.subheader("📰 Latest Headlines")

news_response = (
    supabase
    .table("news")
    .select("title, source, published_at, sentiment")
    .eq("party", selected_party)
    .gte("published_at", str(start_date))
    .lte("published_at", str(end_date))
    .order("published_at", desc=True)
    .limit(10)
    .execute()
)

news_df = pd.DataFrame(news_response.data)

if not news_df.empty:
    for _, row in news_df.iterrows():
        st.markdown(
            f"""
            **{row['title']}**  
            *{row['source']} | {row['published_at']}*  
            **Sentiment:** `{row['sentiment']}`  
            ---
            """
        )
else:
    st.info("No articles found for the selected filters.")
