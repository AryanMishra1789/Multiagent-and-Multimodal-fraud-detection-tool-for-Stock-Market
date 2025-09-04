import re
from yfinance_verifier import verify_company_yfinance  # Changed from relative to absolute import
import pandas as pd
import tldextract
from llm_utils import gemini_llm  # Changed from relative to absolute import
import os

# Load advisor data - use absolute path
ADVISOR_CSV = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sebi_advisors_clean.csv")
advisor_df = pd.read_csv(ADVISOR_CSV) if os.path.exists(ADVISOR_CSV) else pd.DataFrame()

# Scammy language patterns
SCAM_PATTERNS = [
    r"guaranteed returns?",
    r"multibagger",
    r"100% safe",
    r"insider tip|insider news|exclusive insider",
    r"sure shot",
    r"double your money",
    r"no risk",
    r"secret stock",
    r"get rich quick",
    r"limited time offer",
    r"join our telegram",
    r"DM for tips",
    r"exclusive IPO|exclusive offer|exclusive news",
    r"breaking news",
    r"top broker|broker source|confirmed by broker",
    r"buy now",
    r"200% returns?|100% returns?|profit|huge profit|big profit",
    r"tip|stock tip|hot tip",
    r"pre-ipo",
    r"bonus shares",
    r"register now",
    r"unbelievable returns?",
    r"act fast",
    r"don't miss",
    r"sure profit",
    r"whatsapp|telegram group",
]

# Additional suspicious keywords and URL patterns
PHISHING_KEYWORDS = [
    r"free demat",
    r"zero brokerage",
    r"exclusive offer",
    r"click here",
    r"limited seats",
    r"register now",
    r"bonus shares",
    r"pre-ipo",
    r"guaranteed listing",
]
FAKE_DOMAINS = [".xyz", ".top", ".club", "binance", "wazirx", "olatrade", "angelbroking-offer", "zerodha-bonus"]

# Helper: Check for scammy language
def detect_scam_language(text):
    found = []
    for pat in SCAM_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            found.append(pat)
    return found

# Helper: Check for advisor impersonation
def detect_advisor_impersonation(text):
    matches = []
    for _, row in advisor_df.iterrows():
        name = str(row.get("Name", "")).strip()
        reg = str(row.get("Registration No.", "")).strip()
        if name and name.lower() in text.lower():
            matches.append({"type": "name", "value": name, "reg": reg})
        if reg and reg in text:
            matches.append({"type": "reg", "value": reg, "name": name})
    return matches


# Helper: Check for company/IPO mentions (try to extract all uppercase words and any 'Ltd.' or 'Limited' patterns)
import re
def detect_company_mentions(text):
    found = []
    # Extract all uppercase words (likely symbols)
    symbols = re.findall(r'\b[A-Z]{2,}\b', text)
    # Extract 'XYZ Ltd.' or 'XYZ Limited' patterns
    ltds = re.findall(r'([A-Za-z0-9 .,&-]+)\s+(?:Ltd\.|Limited)', text)
    candidates = set(symbols + [l.strip().upper() for l in ltds])
    for symbol in candidates:
        result = verify_company_yfinance(symbol)
        # If not found or invalid, flag as suspicious
        if not result.get('nse', {}).get('valid', False) and not result.get('bse', {}).get('valid', False):
            found.append({"symbol": symbol, "verification": result, "suspicious": True})
        else:
            found.append({"symbol": symbol, "verification": result, "suspicious": False})
    return found

# Helper: Detect suspicious URLs/domains
def detect_suspicious_urls(text):
    urls = re.findall(r"https?://\S+", text)
    flagged = []
    for url in urls:
        ext = tldextract.extract(url)
        domain = f"{ext.domain}.{ext.suffix}" if ext.suffix else ext.domain
        for bad in FAKE_DOMAINS:
            if bad in domain:
                flagged.append(url)
        for kw in PHISHING_KEYWORDS:
            if re.search(kw, url, re.IGNORECASE):
                flagged.append(url)
    return list(set(flagged))

# Helper: Cross-check IPO/news claims (stub, to be replaced with real agent/RAG)
def cross_check_ipo_news(text):
    # In production, use your BSE/NSE/SEBI/news agent or RAG pipeline
    # Here, call gemini_llm with a prompt and return the answer
    prompt = f"Is the following claim about IPO or news true and supported by official sources?\nClaim: {text}"
    try:
        answer = gemini_llm(prompt)
        return answer
    except Exception as e:
        return f"RAG pipeline error: {e}"

# Main fraud detection function

def analyze_social_message(text):
    scam_lang = detect_scam_language(text)
    advisor_imp = detect_advisor_impersonation(text)
    company_mentions = detect_company_mentions(text)
    return {
        "scam_language": scam_lang,
        "advisor_impersonation": advisor_imp,
        "company_mentions": company_mentions,
    }

# Main enhanced fraud detection function
def analyze_social_message_enhanced(text):
    scam_lang = detect_scam_language(text)
    advisor_imp = detect_advisor_impersonation(text)
    company_mentions = detect_company_mentions(text)
    suspicious_urls = detect_suspicious_urls(text)
    rag_claim_check = cross_check_ipo_news(text) if ("ipo" in text.lower() or "news" in text.lower()) else None
    return {
        "scam_language": scam_lang,
        "advisor_impersonation": advisor_imp,
        "company_mentions": company_mentions,
        "suspicious_urls": suspicious_urls,
        "rag_claim_check": rag_claim_check,
    }

if __name__ == "__main__":
    sample = "Get guaranteed returns from TCS IPO! Register now at http://fakeipo.xyz. Contact SEBI registered advisor Mr. Mukesh Ambani INH000000001."
    print(analyze_social_message_enhanced(sample))
