import time
import re
import json
import os
from pathlib import Path
from yfinance_verifier import verify_company_yfinance  # Changed from relative to absolute import
from social_media_fraud_detector import analyze_social_message_enhanced  # Changed from relative to absolute import
from llm_utils import gemini_llm  # Changed from relative to absolute import
from pump_and_dump_detector import record_mention, analyze_pump_and_dump  # Changed from relative to absolute import
from sentiment_analyzer import record_sentiment, detect_sentiment_patterns, detect_coordinated_campaigns  # Changed from relative to absolute import
from wikipedia_verifier import verify_entity_wikipedia, is_legitimate_entity  # Import Wikipedia verification
from financial_institutions_db import is_legitimate_financial_entity, get_financial_entity_info  # Import for financial institution verification
from offline_company_database import is_legitimate_company, get_company_info  # Import for company verification

# Data directory for additional entities
DATA_DIR = Path(__file__).parent / "data"
ADDITIONAL_FINANCIAL_ENTITIES_FILE = DATA_DIR / "additional_financial_entities.json"

# Load additional financial entities if available
def load_additional_financial_entities():
    if ADDITIONAL_FINANCIAL_ENTITIES_FILE.exists():
        try:
            with open(ADDITIONAL_FINANCIAL_ENTITIES_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading additional financial entities: {e}")
    return {}

# Example: live API for advisor/company/IPO, RAG for rules/news

def hybrid_verify_message(message):
    start = time.time()
    # Use LLM to classify and extract entities
    prompt = (
        "You are an expert financial fraud and news detection agent. "
        "Given the following message, do ALL of the following:\n"
        "1. Classify the message as one of: SCAM, NEWS, NEUTRAL, or UNKNOWN.\n"
        "2. Extract all company names or symbols mentioned (ignore financial terms like NIM, YoY, Cr, etc).\n"
        "3. If any company/entity is mentioned, say if it is a real/legit company (if you know).\n"
        "4. Give a 1-2 sentence justification for your classification.\n"
        "5. If you think it's a SCAM, explain why.\n"
        f"\nMessage: {message}\n"
        "Respond in JSON with keys: classification, companies, justification, scam_reason (if any)."
    )

    import json
    try:
        llm_response = gemini_llm(prompt)
        # Remove markdown formatting if present
        if llm_response.strip().startswith('```'):
            llm_response = llm_response.strip()
            # Remove triple backticks and optional 'json' label
            llm_response = llm_response.lstrip('`').lstrip('json').lstrip().rstrip('`').strip()
        parsed = json.loads(llm_response)
    except Exception as e:
        # Fallback: try to extract classification from text, else show raw output
        llm_response = llm_response.strip() if 'llm_response' in locals() else ''
        classification = "UNKNOWN"
        if "scam" in llm_response.lower():
            classification = "SCAM"
        elif "news" in llm_response.lower():
            classification = "NEWS"
        elif "neutral" in llm_response.lower():
            classification = "NEUTRAL"
        parsed = {
            "classification": classification,
            "companies": [],
            "justification": f"LLM error: {e}. Raw output: {llm_response}",
            "scam_reason": None
        }

    # Company verification (use yfinance for all extracted companies)
    verified_companies = []
    suspicious_companies = []
    
    # List of well-known companies to auto-verify
    well_known_companies = [
        'NVIDIA', 'NVDA', 'APPLE', 'MICROSOFT', 'GOOGLE', 'ALPHABET', 'AMAZON', 
        'META', 'FACEBOOK', 'TESLA', 'AMD', 'INTEL', 'GOLDMAN SACHS', 'MORGAN STANLEY',
        'SMH', 'SPDR', 'ETF', 'IBM', 'CISCO', 'ORACLE', 'QUALCOMM', 'BROADCOM',
        'S&P 500', 'S&P500', 'DOW', 'DOW JONES', 'NASDAQ'
    ]
    
    # Mapping for company names to symbols
    name_to_symbol = {
        # US companies
        'NVIDIA': 'NVDA',
        'NVDA': 'NVDA',
        'APPLE': 'AAPL',
        'MICROSOFT': 'MSFT',
        'GOOGLE': 'GOOGL',
        'ALPHABET': 'GOOGL',
        'AMAZON': 'AMZN',
        'META': 'META',
        'FACEBOOK': 'META',
        'TESLA': 'TSLA',
        'AMD': 'AMD',
        'GOLDMAN SACHS': 'GS',
        'MORGAN STANLEY': 'MS',
        'SMH': 'SMH',  # VanEck Semiconductor ETF
        # Indian companies
        'SBI': 'SBIN',
        'STATE BANK OF INDIA': 'SBIN',
        'TCS': 'TCS',
        'TATA CONSULTANCY SERVICES': 'TCS',
        'HDFC': 'HDFCBANK',
        'HDFC BANK': 'HDFCBANK',
        'ICICI': 'ICICIBANK',
        'ICICI BANK': 'ICICIBANK',
        # Add more as needed
    }
    for comp in parsed.get("companies", []):
        key = comp.strip().upper()
        
        # STEP 1: Check if it's a financial institution (broker, media, etc.) 
        # Financial institutions shouldn't be treated as companies to trade
        if is_legitimate_financial_entity(comp):
            # Don't include financial institutions in either list - they're not stocks to trade
            # But log it so we know it was recognized properly
            print(f"[INFO] Identified legitimate financial entity: {comp}")
            continue
            
        # STEP 2: Check additional financial entities loaded at runtime
        additional_entities = load_additional_financial_entities()
        if key in additional_entities or any(key in entity.get('full_name', '').upper() for entity in additional_entities.values()):
            print(f"[INFO] Identified additional financial entity: {comp}")
            continue
        
        # STEP 3: Use Wikipedia verification for entities not in our databases
        # This helps identify legitimate financial institutions, brokerages, etc.
        wiki_result = verify_entity_wikipedia(comp)
        if wiki_result["exists"]:
            entity_type = wiki_result.get("entity_type")
            if entity_type == "financial_institution" or entity_type == "media":
                # It's a financial institution or media outlet, not a company to trade
                print(f"[INFO] Wikipedia verified financial entity: {comp} ({entity_type})")
                continue
            elif entity_type == "public_company" or entity_type == "company":
                # It's a legitimate company according to Wikipedia
                print(f"[INFO] Wikipedia verified company: {comp}")
                verified_companies.append(comp)
                continue
            else:
                # It exists but we're not sure what it is, so verify further
                print(f"[INFO] Wikipedia verified entity of unknown type: {comp}")
                # Continue to next checks
        
        # STEP 4: Check if company is in our offline database
        if is_legitimate_company(comp):
            verified_companies.append(comp)
            continue
            
        # STEP 5: Check if company is in well-known list for quick verification
        if any(known.upper() in key for known in well_known_companies):
            verified_companies.append(comp)
            continue
            
        # STEP 6: Try to verify using stock market data
        symbol = name_to_symbol.get(key, key)
        # Check both the name and the symbol (if different)
        results = []
        # 1. Check as-is (name)
        results.append(verify_company_yfinance(comp))
        # 2. Check as symbol (if different)
        if symbol != key:
            results.append(verify_company_yfinance(symbol))
        # 3. Try alternative exchanges for US companies and ETFs
        for alt_symbol in [f"{symbol}.NS", f"{symbol}.BO", f"{symbol}:US", f"{symbol}-US"]:
            results.append(verify_company_yfinance(alt_symbol))
            
        # If any result is valid, treat as legitimate
        is_legit = False
        for result in results:
            us_valid = result.get('us', {}).get('found', False)
            nse_valid = result.get('nse', {}).get('found', False)
            bse_valid = result.get('bse', {}).get('found', False)
            etf_valid = 'etf' in result
            trusted = result.get('trusted_mapping', False)
            if us_valid or nse_valid or bse_valid or etf_valid or trusted:
                is_legit = True
                break
                
        if is_legit:
            verified_companies.append(comp)
        else:
            # FINAL CHECK: One more attempt with Wikipedia as a general entity verifier
            # This can help with entities that aren't in our databases but are legitimate
            if not wiki_result["exists"]:  # If we haven't already checked Wikipedia
                wiki_result = verify_entity_wikipedia(comp, categories_check=False)
                
            if wiki_result["exists"]:
                # It exists on Wikipedia, so it's likely a legitimate entity of some kind
                # But we're not sure what kind of entity it is, so we'll put it in verified_companies
                print(f"[INFO] Final Wikipedia verification passed for: {comp}")
                verified_companies.append(comp)
            else:
                # Not found in any database or on Wikipedia - mark as suspicious
                suspicious_companies.append(comp)

    # --- Rule-based regulatory verification ---
    try:
        from regulatory_verification import verify_regulatory_compliance
        # Use rules-based verification instead of RAG+LLM
        sebi_rag_result = verify_regulatory_compliance(message)
    except Exception as e:
        print(f"Error in regulatory verification: {e}")
        # Fallback if the new module fails
        sebi_rag_result = {
            "source": "SEBI Rules Analysis",
            "is_valid": True,  # Default fallback
            "reason": "Could not perform regulatory verification",
            "error": str(e)
        }
    # ---
    
    # --- Sentiment Analysis and Market Manipulation Detection ---
    # First, analyze message sentiment and detect coordinated campaigns
    sentiment_result = record_sentiment(message)
    
    # --- Price and Volume Analysis for Pump & Dump Schemes ---
    pump_dump_results = {}
    sentiment_patterns = {}
    
    # Record mentions for all detected companies (for tracking social media activity)
    for comp in verified_companies + suspicious_companies:
        # Record this mention with sentiment from our analysis
        sentiment_score = sentiment_result.get("score", 0)
        record_mention(comp, sentiment_score=sentiment_score)
        
        # Record sentiment specifically for this company
        record_sentiment(message, entity=comp)
        
        # Look for sentiment patterns for this company
        sentiment_patterns[comp] = detect_sentiment_patterns(comp)
        
        # Run pump & dump analysis for each company
        if comp in verified_companies:  # Only analyze verified companies
            try:
                pump_dump_results[comp] = analyze_pump_and_dump(comp)
            except Exception as e:
                print(f"Error analyzing pump & dump for {comp}: {e}")
                pump_dump_results[comp] = {
                    "risk_score": 0,
                    "risk_factors": [],
                    "price_spike": False,
                    "volume_spike": False,
                    "unusual_pattern": False
                }
    
    # Check for coordinated campaigns across all messages
    coordinated_campaigns = detect_coordinated_campaigns()
    # ---

    # Compose a summary of all findings for the LLM to generate a concise reason
    findings = {
        "classification": parsed.get("classification"),
        "scam_reason": parsed.get("scam_reason"),
        "justification": parsed.get("justification"),
        "verified_companies": verified_companies,
        "suspicious_companies": suspicious_companies,
        "sebi_rag_message": sebi_rag_result.get("message") if sebi_rag_result else None,
        "sebi_rag_context": sebi_rag_result.get("context") if sebi_rag_result else None,
        "pump_dump_analysis": pump_dump_results,
        "sentiment_analysis": sentiment_result,
        "sentiment_patterns": sentiment_patterns,
        "coordinated_campaigns": coordinated_campaigns
    }
    # Already imported at the top
    summary_prompt = (
        "You are an expert financial compliance assistant. Given the following analysis results, "
        "write a single, short reason (1-2 sentences, max 50 words) explaining why the message is genuine or fraudulent. "
        "Do not mention 'RAG', 'LLM', or internal process. Just give a clear, user-friendly explanation for a dashboard.\n"
        f"Analysis Results: {findings}"
    )
    try:
        concise_reason = gemini_llm(summary_prompt)
    except Exception as e:
        concise_reason = "Unable to generate concise reason."

    # Set summary and is_valid based on the concise reason (to avoid contradiction)
    reason_lower = concise_reason.lower() if concise_reason else ""
    message_lower = message.lower() if message else ""
    
    # Check for specific high-risk patterns regardless of LLM classification
    penny_stock_pattern = re.search(r"(multibagger|penny stock|\d{3}%\s*returns?\s*(in|within)?\s*\d+\s*day)", message_lower)
    
    if penny_stock_pattern or any(word in reason_lower for word in ["fraud", "scam", "red flag", "not legitimate", "not real", "suspicious", "violation"]):
        summary = "Fraudulent/Scam"
        is_valid = False
        
        # Enhance the reason if it's a penny stock scam but not detected by LLM
        if penny_stock_pattern and not any(word in reason_lower for word in ["fraud", "scam"]):
            concise_reason = f"The message promotes a {penny_stock_pattern.group(0)}, which is a classic sign of a pump-and-dump scheme designed to artificially inflate the stock price."
    elif any(word in reason_lower for word in ["legitimate", "real", "genuine", "valid", "compliant"]):
        summary = "Legitimate/Real"
        is_valid = True
    else:
        summary = "Inconclusive"
        is_valid = False

    elapsed = time.time() - start
    # Check for high-risk pump & dump alerts
    pump_dump_alerts = []
    for company, analysis in pump_dump_results.items():
        if analysis.get("flagged", False):
            pump_dump_alerts.append({
                "company": company, 
                "risk_score": analysis.get("risk_score", 0),
                "risk_factors": analysis.get("risk_factors", [])
            })
    
    # Check for sentiment manipulation patterns
    sentiment_alerts = []
    for company, pattern in sentiment_patterns.items():
        if pattern and pattern.get("confidence", 0) > 0.6:
            sentiment_alerts.append({
                "company": company,
                "pattern": pattern.get("pattern"),
                "confidence": pattern.get("confidence"),
                "description": pattern.get("description")
            })
    
    # Check for coordinated campaigns
    campaign_alerts = []
    for campaign in coordinated_campaigns:
        if campaign.get("confidence", 0) > 0.7:
            campaign_alerts.append({
                "id": campaign.get("id"),
                "message_count": campaign.get("message_count"),
                "common_phrases": campaign.get("common_phrases"),
                "confidence": campaign.get("confidence"),
                "description": f"Potential coordinated messaging campaign detected"
            })
    
    # If we have any high-risk alerts, override the summary only if not clearly news
    # Give more weight to the LLM classification for well-known companies
    has_well_known = any(any(known.upper() in comp.upper() for known in well_known_companies) 
                         for comp in verified_companies)
                         
    if parsed.get("classification") != "NEWS" and not (has_well_known and "news" in reason_lower) and (
        (pump_dump_alerts and any(alert["risk_score"] > 70 for alert in pump_dump_alerts)) or
        (sentiment_alerts and any(alert["confidence"] > 0.7 for alert in sentiment_alerts)) or
        (campaign_alerts and any(alert["confidence"] > 0.7 for alert in campaign_alerts))
    ):
        summary = "Fraudulent/Scam"
        is_valid = False
        
    return {
        "summary": summary,
        "is_valid": is_valid,
        "reason": concise_reason,
        "elapsed_seconds": elapsed,
        "classification": parsed.get("classification"),
        "verified_companies": verified_companies,
        "suspicious_companies": suspicious_companies,
        "sebi_rag": sebi_rag_result,
        "pump_dump_alerts": pump_dump_alerts if pump_dump_alerts else None,
        "sentiment_alerts": sentiment_alerts if sentiment_alerts else None,
        "campaign_alerts": campaign_alerts if campaign_alerts else None,
    }

if __name__ == "__main__":
    sample = "TCS IPO is open now! Get guaranteed returns. Is this allowed as per SEBI?"
    print(hybrid_verify_message(sample))
