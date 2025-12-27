import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import date

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
st.markdown("Track *public sentiment* across Indian political parties using news data.")

# ------------------ PARTY FULL NAMES ------------------
PARTY_FULL_NAMES = {
    "BJP": "Bharatiya Janata Party",
    "INC": "Indian National Congress",
    "AAP": "Aam Aadmi Party",
    "BSP": "Bahujan Samaj Party",
    "CPI(M)": "Communist Party of India (Marxist)",
    "SP": "Samajwadi Party",
    "AITC": "All India Trinamool Congress",
    "BJD": "Biju Janata Dal",
    "Shiv Sena": "Shiv Sena",
    "NCP": "Nationalist Congress Party",
    "DMK": "Dravida Munnetra Kazhagam",
    "AIADMK": "All India Anna Dravida Munnetra Kazhagam",
    "TDP": "Telugu Desam Party",
    "YSRCP": "YSR Congress Party"
}

ALL_PARTIES = list(PARTY_FULL_NAMES.keys())

# ------------------ PARTY SYMBOL IMAGE URLS (OFFICIAL) ------------------
PARTY_SYMBOLS = {
    "BJP": "https://upload.wikimedia.org/wikipedia/en/1/1e/Bharatiya_Janata_Party_logo.svg",
    "INC": "https://upload.wikimedia.org/wikipedia/commons/5/5b/Indian_National_Congress_hand_logo.svg",
    "AAP": "https://upload.wikimedia.org/wikipedia/commons/8/8b/Aam_Aadmi_Party_logo.svg",
    "BSP": "https://upload.wikimedia.org/wikipedia/commons/3/3b/Bahujan_Samaj_Party_Elephant.svg",
    "CPI(M)": "https://upload.wikimedia.org/wikipedia/commons/5/55/Hammer_and_sickle.svg",
    "SP": "https://upload.wikimedia.org/wikipedia/commons/3/3c/Samajwadi_Party_bicycle.svg",
    "AITC": "https://upload.wikimedia.org/wikipedia/commons/6/6e/All_India_Trinamool_Congress_symbol.svg",
    "BJD": "https://upload.wikimedia.org/wikipedia/commons/8/8d/Biju_Janata_Dal_symbol.svg",
    "Shiv Sena": "https://upload.wikimedia.org/wikipedia/commons/4/4d/Shiv_Sena_bow_and_arrow.svg",
    "NCP": "https://upload.wikimedia.org/wikipedia/commons/7/73/Nationalist_Congress_Party_clock.svg",
    "DMK": "https://upload.wikimedia.org/wikipedia/commons/d/d4/DMK_Sun_Rising.svg",
    "AIADMK": "https://upload.wikimedia.org/wikipedia/commons/4/45/AIADMK_two_leaves.svg",
    "TDP": "https://upload.wikimedia.org/wikipedia/commons/2/2c/Telugu_Desam_Party_cycle.svg",
    "YSRCP": "https://upload.wikimedia.org/wikipedia/commons/0/02/YSR_Congress_Party_symbol.svg",
}

# ------------------ SIDEBAR FILTERS ------------------
st.sidebar.header("📅 Filters")
start_date = st.sidebar.date_input("Start Date", value=date.today())
end_date = st.sidebar.date_input("End Date", value=date.today())

selected_party = st.sidebar.selectbox(
    "Select Political Party",
    ALL_PARTIES,
    format_func=lambda p: f"{p} — {PARTY_FULL_NAMES[p]}"
)

st.sidebar.image(
    PARTY_SYMBOLS[selected_party],
    width=80,
    caption=PARTY_FULL_NAMES[selected_party]
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

sentiments = ["Positive", "Negative", "Neutral"]
base_df = pd.DataFrame({"sentiment": sentiments, "total": [0, 0, 0]})

if not summary_df.empty:
    summary_df = base_df.merge(summary_df, on="sentiment", how="left").fillna(0)

summary_df.insert(0, "party", selected_party)
summary_df.index = range(1, len(summary_df) + 1)

# ------------------ MAIN DISPLAY ------------------
st.subheader(f"📌 Sentiment Summary — {selected_party} ({PARTY_FULL_NAMES[selected_party]})")
st.image(PARTY_SYMBOLS[selected_party], width=120)

st.dataframe(summary_df, use_container_width=True)

st.subheader("📊 Sentiment Distribution")
st.bar_chart(summary_df.set_index("sentiment")["total"])

# ------------------ HEADLINES ------------------
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
            {row['source']} | {row['published_at']}  
            *Sentiment:* {row['sentiment']}  
            ---
            """
        )
else:
    st.info("No articles found for the selected filters.")
