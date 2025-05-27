
import streamlit as st
import requests
from bs4 import BeautifulSoup
from transformers import pipeline
import openai
import re

st.set_page_config(page_title="StatsCan Hybrid Chatbot", layout="wide")
st.title("📊 StatsCan Chatbot with GPT Fallback")

question = st.text_input("Ask anything (e.g., What is CPI today? or Why does inflation matter?)")

SERPAPI_KEY = st.secrets["SERPAPI_KEY"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
openai.api_key = OPENAI_API_KEY

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

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
        paragraph_text = " ".join(p.get_text() for p in paragraphs[:10])
        table_text = " ".join(t.get_text() for t in tables[:10])
        return paragraph_text + " " + table_text, soup, html
    except:
        return "", None, ""

def extract_population(soup):
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

def extract_numeric_statements(text):
    lines = text.split(". ")
    numeric_lines = [line for line in lines if re.search(r"\d[\d,.%]*", line)]
    return ". ".join(numeric_lines[:5])

def fallback_gpt(question):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": question}],
            max_tokens=300,
            temperature=0.7
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return "GPT fallback failed."

if question:
    st.info("🔍 Searching Statistics Canada...")
    results = search_statcan(question)

    if not results:
        st.warning("No StatsCan result, using GPT fallback.")
        gpt_reply = fallback_gpt(question)
        st.markdown(f"**GPT Answer:** {gpt_reply}")
    else:
        found_answer = False
        for result in results:
            title = result.get("title")
            link = result.get("link")
            content, soup, html = extract_text_and_soup(link)

            if "population" in question.lower():
                pop = extract_population(soup)
                if pop:
                    st.subheader(f"🔎 {title}")
                    st.markdown(f"**Population Answer:** {pop}")
                    st.markdown(f"[🔗 Source]({link})")
                    found_answer = True
                    break

            if content:
                try:
                    summary = summarizer(content[:1024], max_length=160, min_length=50, do_sample=False)[0]["summary_text"]
                    numeric_facts = extract_numeric_statements(content)
                    st.subheader(f"🔎 {title}")
                    st.markdown("**Detailed Answer:**")
                    st.markdown(f"{summary}")
                    if numeric_facts:
                        st.markdown(f"**Key Numbers:**\n{numeric_facts}")
                    st.markdown(f"[🔗 Source]({link})")
                    found_answer = True
                    break
                except:
                    continue

        if not found_answer:
            st.warning("StatsCan found no answer. Using GPT fallback.")
            gpt_reply = fallback_gpt(question)
            st.markdown(f"**GPT Answer:** {gpt_reply}")
