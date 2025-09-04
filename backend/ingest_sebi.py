import os
import requests
from bs4 import BeautifulSoup
from chromadb import Client
from chromadb.config import Settings
from dotenv import load_dotenv

# Load Gemini API key from .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ChromaDB setup
chroma_client = Client(Settings(persist_directory="chroma_db"))
collection = chroma_client.get_or_create_collection("sebi_docs")

# 1. Scrape SEBI circulars (example: https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&smid=0&ssid=0)
def fetch_sebi_circulars():
    url = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&smid=0&ssid=0"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    links = [a['href'] for a in soup.select('a') if a.get('href', '').startswith('https://www.sebi.gov.in/enforcement/circulars')]
    return links[:5]  # Limit for demo

def fetch_circular_text(url):
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    paras = [p.get_text(strip=True) for p in soup.find_all('p')]
    return '\n'.join(paras)

# 2. Gemini embedding API (textembedding-gecko)
def gemini_embed(text):
    endpoint = "https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent?key=" + GEMINI_API_KEY
    data = {"content": {"parts": [{"text": text}]}}
    r = requests.post(endpoint, json=data)
    r.raise_for_status()
    return r.json()['embedding']['values']

# 3. Ingest and embed
if __name__ == "__main__":
    links = fetch_sebi_circulars()
    for i, link in enumerate(links):
        print(f"Fetching: {link}")
        text = fetch_circular_text(link)
        if not text.strip():
            continue
        # Chunk text (simple split for demo)
        chunks = [text[i:i+512] for i in range(0, len(text), 512)]
        for j, chunk in enumerate(chunks):
            emb = gemini_embed(chunk)
            collection.add(
                documents=[chunk],
                embeddings=[emb],
                ids=[f"doc_{i}_chunk_{j}"]
            )
        print(f"Ingested {len(chunks)} chunks from {link}")
    print("Ingestion complete.")
