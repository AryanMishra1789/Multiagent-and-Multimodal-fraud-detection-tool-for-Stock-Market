"""
Optimized utilities for announcement verification
This module contains improved versions of functions that reduce API dependency
and improve performance.
"""

import logging
import concurrent.futures
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Import the original utilities
from announcement_utils import (
    fast_stock_check, detect_pump_and_dump_language, check_announcement_credibility,
    analyze_announcement_sentiment, get_cached_stock_data, calculate_price_impact
)

logger = logging.getLogger(__name__)

def analyze_in_parallel_optimized(
    text: str, 
    symbol: str, 
    announcement_date: str, 
    fast_mode: bool = True, 
    max_timeout: int = 15
) -> Dict:
    """
    Optimized version of analyze_in_parallel with better timeout handling
    and early termination for obvious scams.
    
    Args:
        text: Text to analyze
        symbol: Stock symbol
        announcement_date: Date of announcement
        fast_mode: Use fast mode to avoid slow API calls
        max_timeout: Maximum seconds to wait for all tasks
        
    Returns:
        Combined results from all analyses
    """
    start_time = time.time()
    results = {}
    
    # First, check if this is an obvious pump and dump message - if so, skip expensive analysis
    pump_dump_check = detect_pump_and_dump_language(text)
    is_likely_pump_dump = pump_dump_check.get("is_pump_and_dump", False)
    
    # Define tasks to run in parallel
    def text_analysis_task():
        # Run all text analysis functions
        sentiment = analyze_announcement_sentiment(text)
        credibility = check_announcement_credibility(text)
        
        return {
            "sentiment": sentiment,
            "credibility_score": credibility,
            "pump_and_dump": pump_dump_check
        }
    
    def stock_analysis_task():
        try:
            # First do a quick check without API calls
            quick_check = fast_stock_check(symbol)
            
            # If it's a known scam pattern, skip expensive analysis
            if not quick_check.get("exists", True) and "fake" in str(quick_check.get("warning", "")):
                logger.info(f"Skipping stock data fetch for likely fake symbol: {symbol}")
                return {
                    "symbol": symbol,
                    "warning": "Potential fake stock symbol",
                    "price_change_1d": None,
                    "volume_ratio": None
                }
            
            # Parse date with multiple format support
            try:
                date = datetime.strptime(announcement_date, "%d-%b-%Y")
            except ValueError:
                try:
                    date = datetime.strptime(announcement_date, "%Y-%m-%d")
                except ValueError:
                    try:
                        date = datetime.strptime(announcement_date, "%d-%m-%Y")
                    except ValueError:
                        # Default to current date if all parsing fails
                        date = datetime.now()
            
            # Use smaller date range in fast mode
            if fast_mode:
                start_date = date - timedelta(days=14)  # 2 weeks before
                end_date = date + timedelta(days=14)    # 2 weeks after
            else:
                start_date = date - timedelta(days=30)  # 1 month before
                end_date = date + timedelta(days=30)    # 1 month after
            
            # Try with different symbol formats
            symbols_to_try = [symbol]
            if not any(suffix in symbol for suffix in [".NS", ".BO"]):
                symbols_to_try.extend([f"{symbol}.NS", f"{symbol}.BO"])
            
            # Get stock data with a short timeout
            stock_data = None
            for sym in symbols_to_try:
                try:
                    # Use a shorter internal timeout for each attempt
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(
                            get_cached_stock_data, 
                            sym, start_date, end_date, fast_mode=fast_mode
                        )
                        stock_data = future.result(timeout=5.0)  # 5 second timeout per symbol
                        
                    if stock_data is not None and not stock_data.empty:
                        break
                except concurrent.futures.TimeoutError:
                    logger.warning(f"Stock data fetch timed out for {sym}")
                    continue
                except Exception as e:
                    logger.warning(f"Error fetching stock data for {sym}: {e}")
                    continue
            
            if stock_data is not None and not stock_data.empty:
                impact = calculate_price_impact(stock_data, date)
                impact["symbol"] = symbol  # Ensure symbol is included
                return impact
            
            return {"symbol": symbol, "error": "No stock data available"}
            
        except Exception as e:
            logger.error(f"Error in stock analysis task: {e}")
            return {"symbol": symbol, "error": str(e)}
    
    # Run tasks based on what's needed
    tasks = {}
    
    # Always run text analysis
    tasks["text_analysis"] = text_analysis_task
    
    # Only run stock analysis if needed
    if not is_likely_pump_dump:
        tasks["stock_analysis"] = stock_analysis_task
    else:
        # For pump and dump schemes, skip stock analysis
        results["stock_analysis"] = {
            "symbol": symbol,
            "warning": "Skipped stock analysis for detected pump and dump scheme",
            "skipped_for_performance": True,
            "price_change_1d": None,
            "volume_ratio": None
        }
    
    # Execute the needed tasks with a global timeout
    futures = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # Submit all the tasks that need to be run
        for task_name, task_func in tasks.items():
            if task_name not in results:  # Don't submit tasks we already have results for
                futures[executor.submit(task_func)] = task_name
        
        # Process the results as they complete
        for future in concurrent.futures.as_completed(futures, timeout=max_timeout):
            task_name = futures[future]
            try:
                results[task_name] = future.result()
            except concurrent.futures.TimeoutError:
                logger.warning(f"Task {task_name} timed out")
                if task_name == "text_analysis":
                    results[task_name] = {
                        "sentiment": {"score": 0, "label": "neutral"},
                        "credibility_score": 0.2 if is_likely_pump_dump else 0.5,
                        "pump_and_dump": pump_dump_check,
                        "timed_out": True
                    }
                elif task_name == "stock_analysis":
                    results[task_name] = {
                        "symbol": symbol,
                        "warning": "Stock analysis timed out",
                        "timed_out": True,
                        "price_change_1d": None,
                        "volume_ratio": None
                    }
            except Exception as e:
                logger.error(f"Task {task_name} failed with error: {e}")
                if task_name == "text_analysis":
                    results[task_name] = {
                        "sentiment": {"score": 0, "label": "neutral"},
                        "credibility_score": 0.2 if is_likely_pump_dump else 0.5,
                        "pump_and_dump": pump_dump_check,
                        "error": str(e)
                    }
                elif task_name == "stock_analysis":
                    results[task_name] = {
                        "symbol": symbol,
                        "warning": f"Error in stock analysis: {str(e)}",
                        "error": str(e),
                        "price_change_1d": None,
                        "volume_ratio": None
                    }
    
    # Cancel any remaining futures
    for future in futures:
        if not future.done():
            future.cancel()
    
    # Ensure all results are present
    for task_name in tasks:
        if task_name not in results:
            if task_name == "text_analysis":
                results[task_name] = {
                    "sentiment": {"score": 0, "label": "neutral"},
                    "credibility_score": 0.2 if is_likely_pump_dump else 0.5,
                    "pump_and_dump": pump_dump_check,
                    "missing": True
                }
            elif task_name == "stock_analysis":
                results[task_name] = {
                    "symbol": symbol,
                    "warning": "Stock analysis task did not complete",
                    "missing": True,
                    "price_change_1d": None,
                    "volume_ratio": None
                }
    
    # Add performance metrics
    elapsed = time.time() - start_time
    results["performance"] = {
        "elapsed_seconds": elapsed,
        "fast_mode": fast_mode,
        "early_scam_detection": is_likely_pump_dump
    }
    
    return results

# Ultra-fast stock verification for emergencies
def ultra_fast_stock_check(symbol: str) -> Dict:
    """
    Even faster stock check when all other methods are too slow
    Uses only local checks with no API dependencies at all
    
    Args:
        symbol: Stock symbol to check
    
    Returns:
        Dict with basic validity information
    """
    # Basic format validation
    if not symbol or not isinstance(symbol, str):
        return {"valid": False, "reason": "Invalid symbol format"}
    
    # Strip any extensions
    base_symbol = symbol.split('.')[0] if '.' in symbol else symbol
    
    # Check for common scam indicators in symbol
    scam_indicators = ["XYZ", "ABC", "123", "PENNY", "MOON", "QUICK"]
    if any(indicator in base_symbol.upper() for indicator in scam_indicators):
        return {
            "valid": False,
            "reason": "Contains typical scam indicator patterns",
            "confidence": "high"
        }
    
    # Check symbol format
    if not re.match(r'^[A-Z0-9]{1,5}(?:\.NS|\.BO)?$', symbol.upper()):
        if len(base_symbol) > 5:
            return {
                "valid": False,
                "reason": "Symbol too long for standard stock tickers",
                "confidence": "medium"
            }
    
    # We can't definitively say it's invalid without checking with an API
    return {
        "valid": True,
        "confidence": "low",
        "reason": "Passed basic format validation"
    }

# Export the optimized functions
__all__ = ['analyze_in_parallel_optimized', 'ultra_fast_stock_check']
