
import streamlit as st
import requests
from bs4 import BeautifulSoup
from transformers import pipeline
import re

st.set_page_config(page_title="StatsCan Chatbot", layout="wide")
st.title("📊 Ask Statistics Canada (Smart Extractor + AI Chatbot)")

question = st.text_input("Ask a question (e.g., What is the population of Ottawa?)")
SERPAPI_KEY = st.secrets["SERPAPI_KEY"]
qa_pipeline = pipeline("question-answering", model="distilbert-base-uncased-distilled-squad")

def search_statcan(query):
    params = {
        "q": f"site:statcan.gc.ca {query}",
        "api_key": SERPAPI_KEY,
        "engine": "google",
        "num": "3"
    }
    res = requests.get("https://serpapi.com/search", params=params)
    data = res.json()
    return data.get("organic_results", [])

def extract_text_and_soup(url):
    try:
        html = requests.get(url, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        main = soup.find("main") or soup.body
        paragraphs = main.find_all("p") if main else []
        tables = main.find_all(["td", "th"]) if main else []
        paragraph_text = " ".join(p.get_text() for p in paragraphs)
        table_text = " ".join(t.get_text() for t in tables)
        return paragraph_text + " " + table_text, soup, html
    except:
        return "", None, ""

def extract_population_from_any_table(soup):
    try:
        for row in soup.find_all("tr"):
            cells = row.find_all(["th", "td"])
            for i, cell in enumerate(cells):
                text = cell.get_text(strip=True).lower()
                if "population" in text and i + 1 < len(cells):
                    value = re.search(r"(\d[\d,]*)", cells[i + 1].get_text(strip=True))
                    if value:
                        return value.group(1)
    except:
        pass
    return None

def fallback_answer(question, text):
    patterns = [
        r"Population\s*[:\-]?\s*(\d[\d,]*)",
        r"Total population\s*[:\-]?\s*(\d[\d,]*)",
        r"Population in \d{4}\s*[:\-]?\s*(\d[\d,]*)"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            return match.group(1)
    return None

def extract_the_daily_summary(html):
    try:
        soup = BeautifulSoup(html, "html.parser")
        main = soup.find("main") or soup.body
        paragraphs = main.find_all("p")
        top_paragraphs = paragraphs[:3]
        return " ".join(p.get_text(strip=True) for p in top_paragraphs)
    except:
        return None

if question:
    st.info("🔍 Searching Statistics Canada...")
    results = search_statcan(question)

    if not results:
        st.warning("No results found.")
    else:
        found_answer = False

        for result in results:
            title = result.get("title")
            link = result.get("link")
            content, soup, html = extract_text_and_soup(link)

            if "daily" in link.lower():
                summary = extract_the_daily_summary(html)
                if summary:
                    st.subheader(f"🔎 {title}")
                    st.markdown(f"**Summary:** {summary}")
                    st.markdown(f"[🔗 Source]({link})")
                    found_answer = True
                    break

            if "population" in question.lower():
                direct = extract_population_from_any_table(soup)
                if direct:
                    st.subheader(f"🔎 {title}")
                    st.markdown(f"**Answer:** {direct}")
                    st.markdown(f"[🔗 Source]({link})")
                    found_answer = True
                    break

            if content:
                try:
                    answer = qa_pipeline({
                        "context": content,
                        "question": question
                    })["answer"]

                    if answer.lower() in question.lower() or len(answer.split()) <= 2:
                        fallback = fallback_answer(question, content)
                        if fallback:
                            answer = fallback

                    st.subheader(f"🔎 {title}")
                    st.markdown(f"**Answer:** {answer}")
                    st.markdown(f"[🔗 Source]({link})")
                    found_answer = True
                    break
                except Exception as e:
                    continue

        if not found_answer:
            st.warning("Couldn't extract a direct answer, but here are some relevant pages:")
            for result in results:
                st.markdown(f"[{result.get('title')}]({result.get('link')})")
