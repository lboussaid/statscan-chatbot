import streamlit as st
from duckduckgo_search import ddg
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="StatsCan Search Bot", layout="wide")
st.title("📊 Real-Time Search Bot for Statistics Canada")

query = st.text_input("Ask anything about Canadian stats (e.g. population of Ottawa):")

def search_statcan_links(query):
    results = ddg(f"site:statcan.gc.ca {query}", max_results=5)
    return results

def quick_preview(url):
    try:
        html = requests.get(url, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        paragraphs = soup.find_all("p")
        snippet = " ".join(p.get_text() for p in paragraphs[:3])
        return snippet.strip()
    except:
        return "⚠️ Could not preview content."

if query:
    st.info("🔍 Searching live...")
    results = search_statcan_links(query)

    if not results:
        st.warning("No relevant results found.")
    else:
        for res in results:
            st.subheader(res["title"])
            st.markdown(f"[🔗 Open Source]({res['href']})")
            st.markdown(f"📄 URL: `{res['href']}`")
            preview = quick_preview(res["href"])
            st.markdown(f"📝 **Preview:** {preview}")
            st.markdown("---")
