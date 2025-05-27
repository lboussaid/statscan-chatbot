import streamlit as st
import requests
from bs4 import BeautifulSoup
import os

st.set_page_config(page_title="StatsCan Search Bot", layout="wide")
st.title("📊 Real-Time Search Bot for Statistics Canada")

SERPAPI_KEY = st.secrets["SERPAPI_KEY"]

query = st.text_input("Ask about Canadian statistics (e.g. 'labour force in Ontario'):")

def search_statcan(query):
    params = {
        "q": f"site:statcan.gc.ca {query}",
        "api_key": SERPAPI_KEY,
        "engine": "google",
        "num": "5"
    }
    res = requests.get("https://serpapi.com/search", params=params)
    data = res.json()
    return data.get("organic_results", [])

def preview(url):
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        paragraphs = soup.find_all("p")
        return " ".join(p.text for p in paragraphs[:3])
    except:
        return "Preview not available."

if query:
    st.info("🔎 Searching StatsCan...")
    results = search_statcan(query)

    if not results:
        st.warning("No results found.")
    else:
        for result in results:
            title = result.get("title")
            link = result.get("link")
            st.subheader(title)
            st.markdown(f"[🔗 Source]({link})")
            st.markdown(f"📄 URL: `{link}`")
            st.markdown(f"📝 **Preview:** {preview(link)}")
            st.markdown("---")
