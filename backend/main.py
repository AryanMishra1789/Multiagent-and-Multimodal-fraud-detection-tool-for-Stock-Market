# --- Dashboard Stats State ---
from fastapi.responses import JSONResponse
from threading import Lock
dashboard_stats = {
    "total_checks": 0,
    "fraud_alerts": 0,
    "unique_advisors_verified": set(),
}
stats_lock = Lock()

# --- Imports and Setup ---

import os
import shutil
import requests
import tempfile
import pandas as pd
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, Form
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from chromadb import Client
from chromadb.config import Settings
import re
import sys
import os

# Add the current directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Use absolute imports
from yfinance_verifier import verify_company_yfinance
from hybrid_verification_agent import hybrid_verify_message
from document_fraud_detector import verify_document

# --- FastAPI App Setup (must be before any @app decorators) ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routes from regulatory module
from regulatory_routes import router as regulatory_router
app.include_router(regulatory_router)

# Import routes from market analysis module
from market_analysis_routes import router as market_analysis_router
app.include_router(market_analysis_router)

# Import routes from corporate announcement module
from corporate_announcement_routes import router as corporate_announcement_router
app.include_router(corporate_announcement_router)

# Import database management routes
from database_management import router as db_management_router
app.include_router(db_management_router)

# Import and include Telegram monitoring routes
try:
    from telegram_routes import router as telegram_router
    app.include_router(telegram_router)
    print("✅ Telegram monitoring routes loaded")
except ImportError as e:
    print(f"⚠️ Telegram monitoring not available: {e}")
except Exception as e:
    print(f"❌ Error loading Telegram routes: {e}")

# Import and include multi-platform monitoring routes
try:
    from multi_platform_routes import router as multi_platform_router
    app.include_router(multi_platform_router)
    print("✅ Multi-platform monitoring routes loaded")
except ImportError as e:
    print(f"⚠️ Multi-platform monitoring not available: {e}")
except Exception as e:
    print(f"❌ Error loading multi-platform routes: {e}")

# Add memory management and cleanup functions
import time
import threading
import gc

# Track application startup time
startup_time = time.time()
from corporate_announcement_routes import response_cache, cache_lock
from announcement_utils import STOCK_DATA_CACHE, stock_data_lock, MESSAGE_CACHE, cache_lock as message_cache_lock

def cleanup_expired_caches():
    """Periodically clean up expired cache entries to free memory"""
    while True:
        try:
            current_time = time.time()
            # Clean up API response cache
            with cache_lock:
                expired_keys = []
                for key, value in response_cache.items():
                    if current_time - value["timestamp"] > 1800:  # 30 minutes
                        expired_keys.append(key)
                        
                for key in expired_keys:
                    del response_cache[key]
                    
                if expired_keys:
                    print(f"Cleaned {len(expired_keys)} expired API cache entries")
            
            # Clean up stock data cache
            with stock_data_lock:
                expired_keys = []
                for key, value in STOCK_DATA_CACHE.items():
                    if (datetime.now() - value["timestamp"]).total_seconds() > 7200:  # 2 hours
                        expired_keys.append(key)
                        
                for key in expired_keys:
                    del STOCK_DATA_CACHE[key]
                    
                if expired_keys:
                    print(f"Cleaned {len(expired_keys)} expired stock data cache entries")
            
            # Clean up message analysis cache
            with message_cache_lock:
                expired_keys = []
                for key, value in MESSAGE_CACHE.items():
                    if current_time - value["timestamp"] > 3600:  # 1 hour
                        expired_keys.append(key)
                        
                for key in expired_keys:
                    del MESSAGE_CACHE[key]
                    
                if expired_keys:
                    print(f"Cleaned {len(expired_keys)} expired message cache entries")
            
            # Run garbage collection
            gc.collect()
            
        except Exception as e:
            print(f"Error in cache cleanup: {str(e)}")
        
        # Sleep for 15 minutes before next cleanup
        time.sleep(900)

# Use FastAPI startup and shutdown events for better resource management
cleanup_thread = None

@app.on_event("startup")
def startup_event():
    """Startup handler to initialize resources"""
    global cleanup_thread
    
    # Start the cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_expired_caches, daemon=True)
    cleanup_thread.start()
    
    # Warm up caches for common symbols
    from announcement_utils import prefetch_data
    from concurrent.futures import ThreadPoolExecutor
    
    common_symbols = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS"]
    
    # Start prefetch in background using thread pool for better management
    def prefetch_startup_data():
        try:
            with ThreadPoolExecutor(max_workers=3) as executor:
                executor.map(prefetch_data, common_symbols)
            print(f"Prefetched data for {len(common_symbols)} common symbols")
        except Exception as e:
            print(f"Error during prefetch: {str(e)}")
    
    threading.Thread(target=prefetch_startup_data, daemon=True).start()
        
    print("FastAPI startup complete with optimized caching")

@app.on_event("shutdown")
def shutdown_event():
    """Shutdown handler to clean up resources"""
    # Clear caches to free memory
    with cache_lock:
        response_cache.clear()
    
    with stock_data_lock:
        STOCK_DATA_CACHE.clear()
    
    with message_cache_lock:
        MESSAGE_CACHE.clear()
    
    # Force garbage collection
    gc.collect()
    print("FastAPI shutdown complete with memory cleanup")

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint with system performance metrics
    """
    # Get cache stats
    api_cache_size = 0
    stock_cache_size = 0
    message_cache_size = 0
    
    with cache_lock:
        api_cache_size = len(response_cache)
    
    with stock_data_lock:
        stock_cache_size = len(STOCK_DATA_CACHE)
    
    with message_cache_lock:
        message_cache_size = len(MESSAGE_CACHE)
    
    # Get system metrics
    memory_percent = 0
    cpu_percent = 0
    
    try:
        # Try to import psutil for system metrics
        import psutil
        memory_usage = psutil.virtual_memory()
        memory_percent = memory_usage.percent
        cpu_percent = psutil.cpu_percent(interval=0.1)
    except ImportError:
        # Log that psutil is not available but continue
        print("psutil not available for system metrics")
    except Exception as e:
        print(f"Error getting system metrics: {str(e)}")
    
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "caches": {
            "api_responses": api_cache_size,
            "stock_data": stock_cache_size,
            "message_analysis": message_cache_size
        },
        "system": {
            "memory_percent": memory_percent,
            "cpu_percent": cpu_percent
        },
        "uptime_seconds": int(time.time() - startup_time)
    }

# --- Hybrid Verification Endpoint ---
from fastapi import Request

@app.post("/api/hybrid_verify")
async def hybrid_verify(request: Request):
    try:
        data = await request.json()
        message = data.get("message", "")
        if not message:
            return {"error": "No message provided."}
            
        # Log the incoming message for debugging
        print(f"[API] Received verification request for message: {message[:50]}...")
        
        # Track stats
        with stats_lock:
            dashboard_stats["total_checks"] += 1
            
        # Call the verification function with error handling
        try:
            result = hybrid_verify_message(message)
        except Exception as e:
            print(f"[ERROR] Error in hybrid_verify_message: {str(e)}")
            # Return a more user-friendly error response
            return {
                "summary": "Error",
                "is_valid": False,
                "reason": f"An error occurred during verification: {str(e)}",
                "classification": "ERROR",
                "verified_companies": [],
                "suspicious_companies": [],
                "error": str(e)
            }
            
        # If we found fraud, track in stats
        if result and not result.get("is_valid", True):
            with stats_lock:
                dashboard_stats["fraud_alerts"] += 1
                
        return result
        
    except Exception as e:
        print(f"[API ERROR] Error processing request: {str(e)}")
        return {"error": f"Error processing request: {str(e)}"}

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# Load advisor data once at startup
ADVISOR_CSV = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sebi_advisors_clean.csv")
if os.path.exists(ADVISOR_CSV):
    advisor_df = pd.read_csv(ADVISOR_CSV)
else:
    advisor_df = pd.DataFrame()

# --- Data Models ---
class VerificationRequest(BaseModel):
    content: str

class VerificationResponse(BaseModel):
    is_valid: bool
    message: str
    details: dict = None

class CompanyVerificationRequest(BaseModel):
    query: str  # company name or symbol

class CompanyVerificationResponse(BaseModel):
    nse: dict
    bse: dict

# --- Helper Functions ---
def gemini_embed(text):
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent?key={GEMINI_API_KEY}"
    data = {"content": {"parts": [{"text": text}]}}
    r = requests.post(endpoint, json=data)
    r.raise_for_status()
    return r.json()['embedding']['values']

from llm_utils import gemini_llm

# Import the new rules-based verification module
from regulatory_verification import (
    verify_regulatory_compliance,
    get_relevant_regulations,
    get_public_company_data,
    verify_ipo_status
)

# --- ChromaDB Setup ---
# Use absolute path for chroma_db
chroma_db_path = os.path.join(os.path.dirname(__file__), "chroma_db")
chroma_client = Client(Settings(persist_directory=chroma_db_path))
sebi_collection = chroma_client.get_or_create_collection("sebi_docs")

# --- Specialized Agents: Using Rules-Based Approach ---

def sebi_agent(user_text, company_name=None):
    """
    Rules-based SEBI regulations verification
    No longer primarily dependent on LLM
    """
    try:
        # Use the rules-based verification module
        result = verify_regulatory_compliance(user_text, company_name)
        return {
            "source": "SEBI",
            "is_valid": result.get("is_valid", False),
            "message": result.get("reason", ""),
            "context": result.get("relevant_regulations", []),
            "violations": result.get("compliance_check", {}).get("violations", [])
        }
    except Exception as e:
        return {"source": "SEBI", "is_valid": False, "message": f"SEBI agent error: {e}", "context": ""}

def bse_nse_agent(user_text, company_name=None):
    """
    Get market data from public sources instead of direct BSE/NSE APIs
    """
    try:
        # Get company data from public sources
        company_data = get_public_company_data(company_name) if company_name else None
        
        # Check for IPO
        ipo_data = None
        if not company_data or not company_data.get("found", False):
            ipo_data = verify_ipo_status(company_name) if company_name else None
        
        return {
            "source": "Market Data",
            "is_valid": company_data.get("found", False) if company_data else False,
            "company_data": company_data,
            "ipo_data": ipo_data
        }
    except Exception as e:
        return {"source": "Market Data", "is_valid": False, "message": f"Market data error: {e}"}
    # For now, return inconclusive
    return {"source": "BSE/NSE", "is_valid": None, "message": "BSE/NSE agent not yet implemented.", "context": ""}

def news_agent(user_text):
    # Placeholder: In production, query trusted news/scam alert sources.
    # For now, return inconclusive
    return {"source": "News", "is_valid": None, "message": "News agent not yet implemented.", "context": ""}

# --- Controller Agent ---
def controller_agent(user_text):
    # 0. Advisor verification: scan for advisor names or registration numbers
    advisor_result = None
    found_advisors = []
    if not advisor_df.empty:
        # Check for registration numbers (e.g., INH000011431)
        regnos = re.findall(r'IN[HR]\d{9,}', user_text, re.IGNORECASE)
        for reg in regnos:
            match = advisor_df[advisor_df['Registration No.'].str.upper() == reg.upper()]
            if not match.empty:
                found_advisors.append(match.iloc[0].to_dict())
        # Check for advisor names (case-insensitive substring match)
        for name in advisor_df['Name']:
            if name.lower() in user_text.lower():
                match = advisor_df[advisor_df['Name'] == name]
                if not match.empty:
                    found_advisors.append(match.iloc[0].to_dict())
        if found_advisors:
            return {
                "source": "SEBI Advisor List",
                "is_valid": True,
                "message": f"Registered with SEBI: {[a['Name'] for a in found_advisors]}",
                "context": found_advisors
            }
        else:
            # If a regno pattern is found but not in list, flag as not registered
            if regnos:
                return {
                    "source": "SEBI Advisor List",
                    "is_valid": False,
                    "message": f"Advisor registration number(s) {regnos} not found in SEBI list.",
                    "context": {}
                }
            # If a name is given but not found, flag as not registered
            if user_text.strip():
                return {
                    "source": "SEBI Advisor List",
                    "is_valid": False,
                    "message": "Advisor not found in SEBI list. They may not be registered.",
                    "context": {}
                }
    # If no advisor data, fallback
    return {
        "source": "SEBI Advisor List",
        "is_valid": False,
        "message": "No SEBI advisor data available for verification.",
        "context": {}
    }

# --- API Endpoint ---
@app.post("/api/verify", response_model=VerificationResponse)
def verify_content(request: VerificationRequest):
    with stats_lock:
        dashboard_stats["total_checks"] += 1
    # Use controller agent for verification
    result = controller_agent(request.content)
    # If fraud detected, increment fraud_alerts
    if result.get("is_valid") is False:
        with stats_lock:
            dashboard_stats["fraud_alerts"] += 1
    # If advisor(s) verified, add to set
    if result.get("source") == "SEBI Advisor List" and result.get("is_valid"):
        with stats_lock:
            for adv in result.get("context", []):
                dashboard_stats["unique_advisors_verified"].add(adv.get("Registration No.", ""))
    return result

# --- Dashboard Stats Endpoint ---
@app.get("/api/dashboard_stats")
def get_dashboard_stats():
    with stats_lock:
        return JSONResponse({
            "total_checks": dashboard_stats["total_checks"],
            "fraud_alerts": dashboard_stats["fraud_alerts"],
            "unique_advisors_verified": len(dashboard_stats["unique_advisors_verified"]),
        })

# --- Agent Status Endpoint ---
@app.get("/api/agent-status")
def get_agent_status():
    # Return current agent status - for now static, but can be made dynamic
    agent_statuses = [
        {
            "name": "Content Analysis Agents",
            "status": "active" if dashboard_stats["total_checks"] > 0 else "idle",
            "processed": dashboard_stats["total_checks"],
            "color": "#4caf50"
        },
        {
            "name": "Social Media Agents",
            "status": "processing" if dashboard_stats["fraud_alerts"] > 0 else "idle",
            "processed": dashboard_stats["fraud_alerts"],
            "color": "#ff9800"
        },
        {
            "name": "Advisor Verification Agents",
            "status": "active" if len(dashboard_stats["unique_advisors_verified"]) > 0 else "idle",
            "processed": len(dashboard_stats["unique_advisors_verified"]),
            "color": "#2196f3"
        },
        {
            "name": "Risk Assessment Agents",
            "status": "active" if dashboard_stats["fraud_alerts"] > 0 else "idle",
            "processed": dashboard_stats["total_checks"] - dashboard_stats["fraud_alerts"],
            "color": "#9c27b0"
        }
    ]
    return JSONResponse(agent_statuses)

# --- Text Verification Endpoint ---
class TextVerificationRequest(BaseModel):
    content: str

@app.post("/api/verify-text")
def verify_text_api(request: TextVerificationRequest):
    try:
        print(f"Received text verification request: {request}")
        
        # Emergency fallback response - absolutely minimal to ensure it works
        # Uncomment this to force a simple valid response
        # return {
        #    "status": "success",
        #    "verification_status": "Clean",
        #    "is_suspicious": False,
        #    "risk_score": 0,
        #    "message": "Content appears authentic.",
        #    "reason": "Emergency fallback response.",
        #    "classification": "NEUTRAL",
        #    "verified_companies": [],
        #    "suspicious_companies": [],
        #    "processing_time": 0.1,
        #    "timestamp": datetime.now().isoformat()
        # }
        
        user_text = request.content.strip()
        if not user_text:
            return {
                "status": "error",
                "message": "No content provided.",
                "is_suspicious": False,
                "risk_score": 0
            }
        
        # Use the hybrid verification agent
        print(f"Processing text: {user_text[:100]}...")
        result = hybrid_verify_message(user_text)
        print(f"Verification result: {result}")
        
        # Update dashboard stats
        with stats_lock:
            dashboard_stats["total_checks"] += 1
            if result.get("is_suspicious"):
                dashboard_stats["fraud_alerts"] += 1
        
        # Check for contradictions in the response
        classification = result.get("classification", "")
        is_valid = result.get("is_valid", True)
        reason = result.get("reason", "")
        
        # Ensure classification has a valid value
        if not classification:
            classification = "UNKNOWN"
            result["classification"] = classification
        
        # If classification is NEWS but summary is Fraudulent/Scam, fix the contradiction
        if classification == "NEWS" and result.get("summary", "") == "Fraudulent/Scam":
            print(f"WARNING: Fixing contradiction - NEWS classified as Fraudulent")
            is_valid = True
            result["summary"] = "Authentic/News"
        
        # Special handling for NEWS classification - always mark as not suspicious
        if classification == "NEWS":
            print(f"Setting NEWS classification to not suspicious")
            is_valid = True
            
        # Convert is_valid to is_suspicious for frontend consistency
        is_suspicious = not is_valid
        
        # Calculate risk score based on classification and alerts
        risk_score = 0
        if classification == "SCAM":
            risk_score = 90
        elif classification == "UNKNOWN":
            risk_score = 50
        elif result.get("pump_dump_alerts"):
            max_risk = max([alert.get("risk_score", 0) for alert in result.get("pump_dump_alerts", [])] or [0])
            risk_score = max(risk_score, max_risk)
        elif result.get("sentiment_alerts"):
            max_confidence = max([alert.get("confidence", 0) * 100 for alert in result.get("sentiment_alerts", [])] or [0])
            risk_score = max(risk_score, max_confidence)
        
        # Safety check for result
        if not result or not isinstance(result, dict):
            print(f"WARNING: hybrid_verify_message returned unexpected result: {result}")
            return {
                "status": "error",
                "message": "Invalid response from verification system",
                "is_suspicious": False,
                "risk_score": 0.0
            }
            
        # Create response data with defaults for all fields
        response_data = {
            "status": "success",
            "verification_status": "Suspicious" if is_suspicious else "Clean",
            "is_suspicious": is_suspicious,
            "risk_score": int(risk_score),  # Ensure it's an integer, not float
            "message": result.get("summary", "No summary available"),
            "reason": result.get("reason", "No reason available"),
            "classification": classification,  # Use our sanitized classification
            "verified_companies": result.get("verified_companies", []),
            "suspicious_companies": result.get("suspicious_companies", []),
            "sebi_rag": result.get("sebi_rag", ""),
            "pump_dump_alerts": result.get("pump_dump_alerts", []),
            "sentiment_alerts": result.get("sentiment_alerts", []),
            "campaign_alerts": result.get("campaign_alerts", []),
            "processing_time": result.get("elapsed_seconds", 0.0),
            "timestamp": datetime.now().isoformat()
        }
        
        # Double check that no values are None/null - replace with defaults if they are
        for key in response_data:
            if response_data[key] is None:
                if key in ["verified_companies", "suspicious_companies", "pump_dump_alerts", 
                          "sentiment_alerts", "campaign_alerts"]:
                    response_data[key] = []
                elif key == "risk_score":
                    response_data[key] = 0
                elif key == "is_suspicious":
                    response_data[key] = False
                elif key in ["message", "reason", "classification", "sebi_rag"]:
                    response_data[key] = ""
                elif key == "processing_time":
                    response_data[key] = 0.0
        
        # Print the response for debugging
        print(f"Sending response: {response_data}")
        return response_data
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in text verification: {str(e)}\n{error_details}")
        
        # Always return a valid, complete response even when errors occur
        # This ensures the frontend doesn't break due to missing fields
        return {
            "status": "error",
            "verification_status": "Error",
            "is_suspicious": False,
            "risk_score": 0,
            "message": f"Error processing text: {str(e)}",
            "reason": "An error occurred during verification.",
            "classification": "ERROR",
            "verified_companies": [],
            "suspicious_companies": [],
            "pump_dump_alerts": [],
            "sentiment_alerts": [],
            "campaign_alerts": [],
            "processing_time": 0.0,
            "timestamp": datetime.now().isoformat(),
            "error_details": str(error_details)
        }

@app.post("/verify_company", response_model=CompanyVerificationResponse)
def verify_company_api(req: CompanyVerificationRequest):
    result = verify_company_yfinance(req.query)
    
# --- Document Verification Endpoint ---
@app.post("/api/verify_document")
async def verify_document_api(file: UploadFile = File(...)):
    # Create a temporary file to store the uploaded file
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
        # Copy uploaded file to the temporary file
        shutil.copyfileobj(file.file, temp_file)
        temp_path = temp_file.name
    
    try:
        # Determine file type based on extension
        file_type = None
        if file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
            file_type = "image"
        elif file.filename.lower().endswith('.pdf'):
            file_type = "pdf"
            
        # Process the document
        result = verify_document(temp_path, file_type)
        
        # Update dashboard stats
        with stats_lock:
            dashboard_stats["total_checks"] += 1
            if result.get("is_suspicious"):
                dashboard_stats["fraud_alerts"] += 1
                
        return result
    except Exception as e:
        return {"status": "error", "message": f"Error processing document: {str(e)}"}
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    return CompanyVerificationResponse(nse=result.get('nse', {}), bse=result.get('bse', {}))
