
import streamlit as st
import requests
from bs4 import BeautifulSoup
from transformers import pipeline
import re

# Set up Streamlit page
st.set_page_config(page_title="StatsCan Chatbot", layout="wide")
st.title("📊 Ask Statistics Canada (AI-Powered Search)")

# Question input
question = st.text_input("Ask a question (e.g., What is the population of Ottawa?)")

# SerpAPI Key (set this in Streamlit Cloud secrets)
SERPAPI_KEY = st.secrets["SERPAPI_KEY"]

# QA model
qa_pipeline = pipeline("question-answering", model="distilbert-base-uncased-distilled-squad")

# Search StatsCan using SerpAPI
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

# Extract and clean text from a StatsCan page
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

# Fallback: use regex to find population-like answers
def fallback_population_answer(text, location):
    match = re.search(fr"population of {location}[^\d]*(\d[\d,]*)", text, re.I)
    if match:
        return match.group(1)
    return None

# Main logic
if question:
    st.info("🔍 Searching Statistics Canada...")
    results = search_statcan(question)
    location = question.split()[-1]  # crude extraction for fallback

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
                    # Try QA model
                    answer = qa_pipeline({
                        "context": content,
                        "question": question
                    })["answer"]

                    # Fallback if answer too vague
                    if answer.lower() in question.lower():
                        fallback = fallback_population_answer(content, location)
                        if fallback:
                            answer = fallback

                    st.subheader(f"🔎 {title}")
                    st.markdown(f"**Answer:** {answer}")
                    st.markdown(f"[🔗 Source]({link})")
                    found_answer = True
                    break
                except:
                    continue

        if not found_answer:
            st.warning("Couldn't extract an answer, but here are some pages you can check:")
            for result in results:
                st.markdown(f"[{result.get('title')}]({result.get('link')})")
