"""
Regulatory verification module that uses rule-based approaches and 
structured data rather than relying primarily on LLMs.
"""
import os
import re
import json
import requests
from datetime import datetime, timedelta
from chromadb import Client
from chromadb.config import Settings

# --- Structured Regulatory Rules ---
# These are extracted from SEBI/BSE/NSE guidelines and circulars
MARKET_MANIPULATION_RULES = [
    {
        "id": "SEBI-FMR-1",
        "category": "market_manipulation",
        "description": "Spread of rumors with an intention to move the price of security",
        "indicator_patterns": [
            r"prices? (?:will|shall|going to) (?:rise|jump|increase|skyrocket)",
            r"(?:target price|price target) (?:of|is) (?:\d+)",
            r"(?:multibag+er|multi-bag+er)",
            r"(?:double|triple|quadruple) your money",
            r"(?:\d+)% (?:returns|gains|profit)",
            r"stock is (?:ready to|about to|going to|will) (?:explode|skyrocket|moon)",
            r"price (?:manipulation|rigging|gaming)",
        ],
        "source": "SEBI (Prohibition of Fraudulent and Unfair Trade Practices) Regulations, 2003"
    },
    {
        "id": "SEBI-FUTP-2",
        "category": "pump_dump",
        "description": "Pump and dump schemes where individuals artificially inflate prices",
        "indicator_patterns": [
            r"(?:buy now|act fast|don'?t miss|limited time)",
            r"(?:insider|inside) (?:information|info|tip)",
            r"(?:secret|exclusive) (?:information|tip|recommendation)",
            r"(?:before|ahead of) (?:announcement|news release)",
            r"undiscovered (?:gem|stock|company)",
            r"next (?:multibag+er|multi-bag+er)",
            r"no one (?:knows|is aware) (?:about|of) this (?:stock|company)"
        ],
        "source": "SEBI Circular No. CIR/ISD/1/2011"
    },
    {
        "id": "SEBI-IPO-1",
        "category": "ipo_fraud",
        "description": "False IPO claims or misrepresentation of IPO information",
        "indicator_patterns": [
            r"(?:guaranteed|assured) (?:IPO|initial public offering) (?:allotment|allocation)",
            r"(?:apply through|special quota|guaranteed allotment)",
            r"IPO (?:launching|opening) (?:tomorrow|soon|next week)",
            r"(?:pre-IPO|pre IPO|grey market)",
            r"IPO (?:discount|special price)",
            r"(?:buy|get) (?:shares|stock) (?:before|prior to) IPO"
        ],
        "source": "SEBI (Issue of Capital and Disclosure Requirements) Regulations, 2018"
    },
    {
        "id": "BSE-UNPUB-1",
        "category": "unpublished_info",
        "description": "Trading based on unpublished price sensitive information",
        "indicator_patterns": [
            r"(?:confidential|secret) (?:information|news|announcement)",
            r"(?:before|prior to) (?:public|official) (?:announcement|news|release)",
            r"(?:insider|management|board) (?:information|update|tip)",
            r"not (?:public|announced|published) yet",
            r"(?:about to|going to) (?:announce|release|publish)",
            r"(?:merger|acquisition|takeover|buyout) (?:news|information|tip)"
        ],
        "source": "SEBI (Prohibition of Insider Trading) Regulations, 2015"
    },
    {
        "id": "NSE-ADVICE-1", 
        "category": "unauthorized_advice",
        "description": "Unauthorized investment advice without SEBI registration",
        "indicator_patterns": [
            r"(?:not|no) (?:SEBI registered|registered with SEBI|registered advisor)",
            r"(?:guaranteed|assured) (?:returns|profits|gains)",
            r"(?:100%|completely) (?:safe|risk-free|guaranteed)",
            r"(?:unregistered|unauthorized) (?:advisor|broker)",
            r"(?:partnership|profit sharing) (?:scheme|model|plan)",
        ],
        "source": "SEBI (Investment Advisers) Regulations, 2013"
    }
]

# IPO regulations and checks
IPO_REGULATIONS = {
    "min_company_age": 3,  # 3 years operational history
    "min_net_tangible_assets": 300000000,  # ₹30 crore in preceding 3 years
    "min_avg_operating_profit": 150000000,  # ₹15 crore in 3 years
    "min_net_worth": 10000000,  # ₹1 crore in preceding 2 years
    "source": "SEBI (Issue of Capital and Disclosure Requirements) Regulations, 2018"
}

# --- Alternative Market Data Sources ---
# Use open data sources instead of direct BSE/NSE APIs

def get_public_company_data(symbol):
    """Get company data from public sources instead of direct BSE/NSE APIs"""
    try:
        # Check if company appears in NSE/BSE listing
        # Using screener.in for basic data
        url = f"https://www.screener.in/api/company/{symbol}/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "found": True,
                "name": data.get("name", ""),
                "exchange": data.get("exchange", ""),
                "sector": data.get("warehouse_set", {}).get("industry", ""),
                "market_cap": data.get("market_cap", 0),
                "current_price": data.get("current_price", 0),
                "url": f"https://www.screener.in/company/{symbol}/"
            }
        
        # If screener.in fails, try other sources
        # This is an example and would need to be expanded with more sources
        return {
            "found": False,
            "error": f"Company not found in public data sources"
        }
    except Exception as e:
        return {
            "found": False,
            "error": str(e)
        }

def verify_ipo_status(company_name):
    """Check if a company has a legitimate ongoing or upcoming IPO"""
    try:
        # Public sources for IPO data
        url = "https://www.chittorgarh.com/api/ipo/mainboard_ipo_list/?year=2023"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            ipo_data = response.json()
            
            # Check if company is in the list
            company_ipos = [ipo for ipo in ipo_data if company_name.lower() in ipo.get("company_name", "").lower()]
            
            if company_ipos:
                ipo = company_ipos[0]
                return {
                    "has_ipo": True,
                    "details": {
                        "company_name": ipo.get("company_name"),
                        "open_date": ipo.get("open_date"),
                        "close_date": ipo.get("close_date"),
                        "lot_size": ipo.get("lot_size"),
                        "issue_price": ipo.get("issue_price"),
                        "issue_size": ipo.get("issue_size")
                    }
                }
            
            return {
                "has_ipo": False,
                "message": "No ongoing or upcoming IPO found for this company"
            }
    except Exception as e:
        return {
            "has_ipo": False,
            "error": str(e)
        }

# --- Rule-based Regulatory Checks ---

def check_regulatory_compliance(message):
    """
    Check if message complies with regulatory rules
    Returns violations with specific regulations rather than LLM guesses
    """
    message_lower = message.lower()
    violations = []
    
    for rule in MARKET_MANIPULATION_RULES:
        for pattern in rule["indicator_patterns"]:
            if re.search(pattern, message_lower, re.IGNORECASE):
                violations.append({
                    "rule_id": rule["id"],
                    "category": rule["category"],
                    "description": rule["description"],
                    "source": rule["source"],
                    "matched_pattern": pattern
                })
                break  # Only report each rule once
    
    return {
        "compliant": len(violations) == 0,
        "violations_count": len(violations),
        "violations": violations
    }

def get_ipo_regulatory_requirements():
    """Return the regulatory requirements for IPOs"""
    return IPO_REGULATIONS

# --- RAG-based SEBI Regulation Retrieval ---
# This uses vector DB but without relying primarily on LLM reasoning

def get_relevant_regulations(query, use_gemini_embed=False):
    """
    Get relevant regulations using vector search
    This is RAG but focused on retrieval without heavy LLM reasoning
    """
    try:
        # Initialize ChromaDB
        chroma_db_path = os.path.join(os.path.dirname(__file__), "chroma_db")
        chroma_client = Client(Settings(persist_directory=chroma_db_path))
        sebi_collection = chroma_client.get_or_create_collection("sebi_docs")
        
        # Use embeddings if available, otherwise use keyword search
        if use_gemini_embed:
            # Import only if needed
            from llm_utils import gemini_embed
            query_emb = gemini_embed(query)
            results = sebi_collection.query(query_embeddings=[query_emb], n_results=3)
        else:
            # Use keyword search as fallback
            results = sebi_collection.query(query_texts=[query], n_results=3)
            
        regulations = []
        if results and 'documents' in results and results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                regulations.append({
                    "text": doc,
                    "relevance": results.get('distances', [[]])[0][i] if 'distances' in results else None,
                    "id": results.get('ids', [[]])[0][i] if 'ids' in results else f"doc_{i}"
                })
        
        return {
            "success": True,
            "count": len(regulations),
            "regulations": regulations
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "regulations": []
        }

# --- Main Verification Function ---

def verify_regulatory_compliance(message, company_name=None):
    """
    Main function to verify regulatory compliance
    Uses rule-based approach instead of relying on LLM
    """
    # 1. Check for rule violations in the message
    compliance_check = check_regulatory_compliance(message)
    
    # 2. Get relevant SEBI regulations
    relevant_regs = get_relevant_regulations(message)
    
    # 3. Company verification
    company_data = None
    ipo_data = None
    if company_name:
        company_data = get_public_company_data(company_name)
        if not company_data.get("found", False):
            # Try to check for IPO
            ipo_data = verify_ipo_status(company_name)
    
    # Determine if the message is compliant
    is_compliant = compliance_check.get("compliant", False)
    
    # Generate a reason based on rule matches, not LLM
    reason = "The message appears to comply with regulatory guidelines."
    if not is_compliant:
        violations = compliance_check.get("violations", [])
        categories = set(v.get("category") for v in violations)
        categories_str = ", ".join(categories)
        reason = f"The message may violate regulations related to: {categories_str}"
    
    return {
        "is_valid": is_compliant,
        "reason": reason,
        "compliance_check": compliance_check,
        "relevant_regulations": relevant_regs.get("regulations", []),
        "company_data": company_data,
        "ipo_data": ipo_data
    }

# For testing
if __name__ == "__main__":
    test_message = "Buy ABC stocks NOW before the big announcement tomorrow! Guaranteed to double your money in a week!"
    print(json.dumps(verify_regulatory_compliance(test_message), indent=2))
