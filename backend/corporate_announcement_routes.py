"""
Corporate Announcement verification routes for the SEBI hackathon project.
These endpoints provide analysis of corporate announcements to detect misleading information.
"""

from fastapi import APIRouter, Body, BackgroundTasks
from typing import Optional, Dict
import time
import re
from datetime import datetime
import logging
import functools
import threading
from corporate_announcement_verifier import verify_corporate_announcement
from pydantic import BaseModel

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Response cache to avoid repeated processing
response_cache = {}
cache_lock = threading.Lock()
CACHE_TTL = 300  # 5 minutes cache TTL

def cache_api_response(ttl=CACHE_TTL):
    """
    Decorator to cache API responses for specified time-to-live
    
    Args:
        ttl: Time-to-live for cache in seconds
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate a cache key based on function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check if response is cached
            with cache_lock:
                if cache_key in response_cache:
                    cached_item = response_cache[cache_key]
                    if time.time() - cached_item["timestamp"] < ttl:
                        logger.info(f"Cache hit for {func.__name__}")
                        return cached_item["data"]
            
            # Get fresh response
            response = await func(*args, **kwargs)
            
            # Cache the response
            with cache_lock:
                response_cache[cache_key] = {
                    "data": response,
                    "timestamp": time.time()
                }
            
            return response
        return wrapper
    return decorator

# Create router
router = APIRouter()

class AnnouncementRequest(BaseModel):
    symbol: str
    announcement_text: Optional[str] = None
    announcement_date: Optional[str] = None

def cache_api_response(ttl=CACHE_TTL):
    """Decorator to cache API responses"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from args
            request = None
            for arg in args:
                if hasattr(arg, "symbol"):
                    request = arg
                    break
            
            if not request:
                # No cacheable request found, just execute the function
                return await func(*args, **kwargs)
            
            # Create cache key
            cache_key = f"{func.__name__}:{request.symbol}:{request.announcement_text}:{request.announcement_date}"
            
            # Check cache
            with cache_lock:
                if cache_key in response_cache:
                    entry = response_cache[cache_key]
                    if (datetime.now() - entry["timestamp"]).total_seconds() < ttl:
                        logger.info(f"Cache hit for {func.__name__}")
                        return entry["result"]
            
            # Execute function
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Store in cache
            with cache_lock:
                response_cache[cache_key] = {
                    "result": result,
                    "timestamp": datetime.now()
                }
            
            # Log performance
            logger.info(f"API call {func.__name__} completed in {execution_time:.2f}s")
            
            return result
        return wrapper
    return decorator

@router.post("/api/verify_corporate_announcement")
@cache_api_response(ttl=300)
async def verify_announcement(request: AnnouncementRequest, background_tasks: BackgroundTasks):
    """
    Verify a corporate announcement for misleading or false information.
    
    This endpoint analyzes corporate announcements to detect:
    1. Exaggerated financial claims
    2. Discrepancies between announcements and actual performance
    3. Unusual market reactions following announcements
    4. Regulatory compliance issues
    5. Pump and dump schemes and penny stock fraud
    
    Parameters:
    - symbol: Company ticker/symbol
    - announcement_text: Specific announcement text to verify (optional)
    - announcement_date: Date of announcement to verify (optional)
    """
    # Start timer for performance tracking
    start_time = time.time()
    
    # Import optimized utilities for faster processing
    from announcement_utils import detect_pump_and_dump_language, fast_stock_check
    from announcement_utils_optimized import ultra_fast_stock_check
    
    # Start with basic response template to avoid repeating code
    base_response = {
        "symbol": request.symbol,
        "verification_timestamp": datetime.now().isoformat(),
        "announcement_date": request.announcement_date or datetime.now().strftime("%d-%b-%Y")
    }
    
    # OPTIMIZATION 1: First check if this is a clear pump-and-dump message
    if request.announcement_text:
        # Ultra-fast check for obvious scam keywords before doing any analysis
        text_lower = request.announcement_text.lower()
        obvious_scam = False
        scam_reason = None
        
        if "multibagger penny stock" in text_lower:
            obvious_scam = True
            scam_reason = "Message promotes a 'Multibagger Penny Stock' which is a classic pump-and-dump scheme"
        elif re.search(r"([1-9][0-9]{2,})%\s*returns?\s*in\s*\d+\s*days?", text_lower):
            # Extract the percentage for the reason
            match = re.search(r"([1-9][0-9]{2,})%\s*returns?\s*in\s*(\d+)\s*days?", text_lower)
            if match:
                percent, days = match.groups()
                obvious_scam = True
                scam_reason = f"Message promotes an unrealistic {percent}% return in just {days} days, which is a classic pump-and-dump scheme"
        
        if obvious_scam:
            logger.info(f"Fast detection identified obvious scam: {scam_reason}")
            return {
                **base_response,
                "is_misleading": True,
                "risk_score": 95,
                "risk_level": "high",
                "risk_factors": [scam_reason],
                "processing_time_ms": int((time.time() - start_time) * 1000)
            }
            
        # OPTIMIZATION 2: Check for pump and dump language
        pump_dump_result = detect_pump_and_dump_language(request.announcement_text)
        if pump_dump_result.get("is_pump_and_dump", False) and pump_dump_result.get("confidence", 0) > 0.7:
            # Short-circuit with fast response for obvious pump-and-dump schemes
            return {
                **base_response,
                "is_misleading": True,
                "risk_score": 95,
                "risk_level": "high",
                "risk_factors": [
                    f"Detected pump-and-dump scheme ({pump_dump_result['confidence']:.2f} confidence)",
                    "Contains unrealistic return promises" if "unrealistic_returns" in pump_dump_result.get("indicators", []) else "",
                    "References penny stocks with suspicious claims" if "penny_stock" in pump_dump_result.get("indicators", []) else "",
                ],
                "processing_time_ms": int((time.time() - start_time) * 1000)
            }
    
    # OPTIMIZATION 3: Ultra-fast check for suspicious stock symbols
    # First with ultra_fast_stock_check (no API dependencies)
    ultra_check = ultra_fast_stock_check(request.symbol)
    if not ultra_check.get("valid", True) and ultra_check.get("confidence", "") == "high":
        logger.info(f"Ultra-fast detection identified suspicious symbol: {request.symbol}")
        return {
            **base_response,
            "is_misleading": True,
            "risk_score": 90,
            "risk_level": "high",
            "verification_method": "ultra_fast",
            "risk_factors": [
                f"Suspicious stock symbol pattern: {ultra_check.get('reason')}",
                "Matches known scam symbol patterns"
            ],
            "processing_time_ms": int((time.time() - start_time) * 1000)
        }
        
    # Then with the regular fast_stock_check (cached data)
    stock_check = fast_stock_check(request.symbol)
    if not stock_check.get("exists", True) and "fake" in str(stock_check.get("warning", "")):
        logger.info(f"Detected potentially fake stock symbol: {request.symbol}")
        return {
            **base_response,
            "is_misleading": True,
            "risk_score": 90,
            "risk_level": "high",
            "verification_method": "fast_check",
            "risk_factors": ["Potentially fake or non-existent stock symbol commonly used in scams"],
            "processing_time_ms": int((time.time() - start_time) * 1000)
        }
    
    # Proceed with full verification for other cases
    result = verify_corporate_announcement(
        symbol=request.symbol,
        announcement_text=request.announcement_text,
        announcement_date=request.announcement_date
    )
    
    # Add processing time
    result["processing_time_ms"] = int((time.time() - start_time) * 1000)
    
    return result

@router.get("/api/recent_announcements/{symbol}")
@cache_api_response(ttl=600)  # Cache for 10 minutes
async def get_recent_announcements(symbol: str, exchange: str = "both", background_tasks: BackgroundTasks = None):
    """
    Get recent corporate announcements for a company.
    
    Parameters:
    - symbol: Company ticker/symbol
    - exchange: Stock exchange (bse, nse, or both)
    """
    from corporate_announcement_verifier import corporate_verifier
    
    # Start a timer to measure performance
    start_time = time.time()
    
    # Get announcements with proper error handling
    try:
        announcements = corporate_verifier.fetch_recent_announcements(symbol, exchange)
        result = {
            "symbol": symbol,
            "exchange": exchange,
            "announcements_count": len(announcements),
            "announcements": announcements,
            "processing_time_ms": int((time.time() - start_time) * 1000)
        }
        
        # Prefetch additional data in background if needed
        if background_tasks and announcements:
            from announcement_utils import prefetch_data
            background_tasks.add_task(prefetch_data, symbol)
        
        return result
    except Exception as e:
        logger.error(f"Error fetching announcements: {str(e)}")
        return {
            "symbol": symbol,
            "exchange": exchange,
            "announcements_count": 0,
            "announcements": [],
            "error": str(e),
            "processing_time_ms": int((time.time() - start_time) * 1000)
        }

@router.get("/api/announcement_market_impact/{symbol}")
@cache_api_response(ttl=1800)  # Cache for 30 minutes
async def get_announcement_impact(symbol: str, announcement_date: str):
    """
    Analyze the market impact of a specific announcement.
    
    Parameters:
    - symbol: Company ticker/symbol
    - announcement_date: Date of the announcement (DD-MM-YYYY or DD-Mon-YYYY format)
    """
    from corporate_announcement_verifier import corporate_verifier
    
    # Start a timer to measure performance
    start_time = time.time()
    
    try:
        # Use optimized stock data retrieval
        from announcement_utils import get_cached_stock_data
        
        # Parse announcement date
        try:
            date_obj = datetime.strptime(announcement_date, "%d-%m-%Y")
        except ValueError:
            try:
                date_obj = datetime.strptime(announcement_date, "%d-%b-%Y")
            except ValueError:
                return {
                    "symbol": symbol,
                    "announcement_date": announcement_date,
                    "error": "Invalid date format. Use DD-MM-YYYY or DD-Mon-YYYY",
                    "processing_time_ms": int((time.time() - start_time) * 1000)
                }
        
        # Get market reaction
        reaction = corporate_verifier.get_stock_reaction(symbol, announcement_date)
        
        return {
            "symbol": symbol,
            "announcement_date": announcement_date,
            "market_reaction": reaction,
            "processing_time_ms": int((time.time() - start_time) * 1000)
        }
    except Exception as e:
        logger.error(f"Error analyzing announcement impact: {str(e)}")
        return {
            "symbol": symbol,
            "announcement_date": announcement_date,
            "error": str(e),
            "processing_time_ms": int((time.time() - start_time) * 1000)
        }
