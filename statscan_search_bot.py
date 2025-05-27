
import streamlit as st
import requests
from bs4 import BeautifulSoup
from transformers import pipeline
import re

# Streamlit UI setup
st.set_page_config(page_title="StatsCan Chatbot", layout="wide")
st.title("📊 Ask Statistics Canada (AI-Powered Search)")

question = st.text_input("Ask a question (e.g., What is the population of Ottawa?)")
SERPAPI_KEY = st.secrets["SERPAPI_KEY"]

# QA model
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

def extract_text_from_url(url):
    try:
        html = requests.get(url, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        main = soup.find("main") or soup.body
        paragraphs = main.find_all("p") if main else []
        text = " ".join(p.get_text() for p in paragraphs)
        return text.strip()
    except:
        return ""

# Fallback logic with more patterns for population-style data
def fallback_answer(question, text):
    location = question.split()[-1].lower()

    patterns = [
        fr"population of {location}[^\d]*(\d[\d,]*)",
        r"Population\s*[:\-]?\s*(\d[\d,]*)",
        r"Total population\s*[:\-]?\s*(\d[\d,]*)",
        r"Population in \d{4}\s*[:\-]?\s*(\d[\d,]*)"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            return match.group(1)
    return None

# Main logic
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
            content = extract_text_from_url(link)

            if content:
                try:
                    # Try QA first
                    answer = qa_pipeline({
                        "context": content,
                        "question": question
                    })["answer"]

                    # Check if answer is vague or same as question
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
