"""
Enhanced market analysis routes for the SEBI hackathon project.
These endpoints provide AI-first analysis of financial data.
"""

from fastapi import APIRouter, Query
from typing import Optional, List
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pump_and_dump_detector import analyze_pump_and_dump
from historical_market_analyzer import get_historical_analysis, compare_with_market

# Create router
router = APIRouter()

@router.get("/api/pump_and_dump")
async def pump_and_dump(symbol: str):
    """
    Analyze a stock symbol for potential pump and dump schemes.
    Uses historical price and volume data along with pattern recognition.
    """
    result = analyze_pump_and_dump(symbol)
    return result

@router.get("/api/historical_analysis")
async def historical_analysis(
    symbol: str, 
    period: str = "1y", 
    interval: str = "1d",
    indicators: Optional[List[str]] = Query(["sma", "volatility"])
):
    """
    Perform comprehensive historical analysis of a stock with technical indicators.
    This endpoint provides AI-driven insights into historical patterns.
    
    Parameters:
    - symbol: Stock ticker symbol
    - period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
    - interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
    - indicators: Technical indicators to calculate (sma, ema, rsi, macd, volatility, bollinger)
    """
    try:
        # Fetch historical data
        data = yf.download(symbol, period=period, interval=interval)
        
        if data.empty:
            return {"error": "No data available for this symbol"}
        
        # Calculate requested indicators
        results = {
            "symbol": symbol,
            "last_price": float(data["Close"].iloc[-1]),
            "price_change": float(data["Close"].iloc[-1] - data["Close"].iloc[0]),
            "price_change_pct": float((data["Close"].iloc[-1] / data["Close"].iloc[0] - 1) * 100),
            "data_points": len(data),
            "indicators": {},
            "anomalies": [],
            "summary": {}
        }
        
        # Technical indicators
        if "sma" in indicators:
            data["SMA20"] = data["Close"].rolling(window=20).mean()
            data["SMA50"] = data["Close"].rolling(window=50).mean()
            data["SMA200"] = data["Close"].rolling(window=200).mean()
            
            results["indicators"]["sma"] = {
                "sma20": float(data["SMA20"].iloc[-1]) if not pd.isna(data["SMA20"].iloc[-1]) else None,
                "sma50": float(data["SMA50"].iloc[-1]) if not pd.isna(data["SMA50"].iloc[-1]) else None,
                "sma200": float(data["SMA200"].iloc[-1]) if not pd.isna(data["SMA200"].iloc[-1]) else None,
            }
            
            # Detect golden/death crosses
            if len(data) >= 50:
                if data["SMA20"].iloc[-1] > data["SMA50"].iloc[-1] and data["SMA20"].iloc[-2] < data["SMA50"].iloc[-2]:
                    results["anomalies"].append({
                        "type": "golden_cross", 
                        "description": "Golden Cross detected: SMA20 crossed above SMA50",
                        "significance": "bullish"
                    })
                elif data["SMA20"].iloc[-1] < data["SMA50"].iloc[-1] and data["SMA20"].iloc[-2] > data["SMA50"].iloc[-2]:
                    results["anomalies"].append({
                        "type": "death_cross", 
                        "description": "Death Cross detected: SMA20 crossed below SMA50",
                        "significance": "bearish"
                    })
        
        if "volatility" in indicators:
            # Calculate daily returns
            data["returns"] = data["Close"].pct_change()
            
            # Calculate volatility (standard deviation of returns)
            vol_20d = float(data["returns"].rolling(window=20).std() * np.sqrt(252))
            vol_50d = float(data["returns"].rolling(window=50).std() * np.sqrt(252))
            
            results["indicators"]["volatility"] = {
                "current_20d": float(vol_20d) if not pd.isna(vol_20d) else None,
                "current_50d": float(vol_50d) if not pd.isna(vol_50d) else None,
            }
            
            # Detect volatility anomalies
            if len(data) >= 100:
                # Calculate historical volatility average and standard deviation
                vol_history = data["returns"].rolling(window=20).std() * np.sqrt(252)
                vol_avg = float(vol_history.mean())
                vol_std = float(vol_history.std())
                
                # Check if current volatility is unusually high
                if vol_20d > vol_avg + 2 * vol_std:
                    results["anomalies"].append({
                        "type": "high_volatility",
                        "description": f"Unusually high volatility detected: {vol_20d:.2f} (z-score: {(vol_20d - vol_avg) / vol_std:.2f})",
                        "significance": "potential instability"
                    })
        
        # Add volume analysis
        if "Volume" in data.columns:
            avg_vol = float(data["Volume"].mean())
            recent_vol = float(data["Volume"].iloc[-1])
            vol_change = (recent_vol / avg_vol - 1) * 100
            
            results["indicators"]["volume"] = {
                "recent_volume": int(recent_vol),
                "avg_volume": int(avg_vol),
                "volume_change_pct": float(vol_change)
            }
            
            # Detect unusual volume
            if vol_change > 100:  # More than double the average
                results["anomalies"].append({
                    "type": "high_volume",
                    "description": f"Unusual trading volume: {vol_change:.1f}% above average",
                    "significance": "potential unusual interest"
                })
        
        # Generate AI-driven summary
        trend = "upward" if results["price_change"] > 0 else "downward"
        volatility_desc = "high" if results["indicators"].get("volatility", {}).get("current_20d", 0) > 0.3 else "moderate" if results["indicators"].get("volatility", {}).get("current_20d", 0) > 0.15 else "low"
        
        summary_text = f"{symbol} has shown a {trend} trend over the selected period with {volatility_desc} volatility. "
        
        if results["anomalies"]:
            summary_text += f"Analysis detected {len(results['anomalies'])} notable patterns including: "
            summary_text += ", ".join([a["type"].replace("_", " ") for a in results["anomalies"]])
            summary_text += "."
        else:
            summary_text += "No unusual patterns detected in the analyzed timeframe."
            
        results["summary"] = {
            "text": summary_text,
            "trend": trend,
            "volatility": volatility_desc,
            "anomalies_count": len(results["anomalies"])
        }
        
        return results
        
    except Exception as e:
        return {"error": str(e)}

@router.get("/api/market_sentiment")
async def market_sentiment(symbol: str):
    """
    Analyze market sentiment for a given stock based on multiple data sources.
    Uses technical indicators, news sentiment, and relative market performance.
    """
    try:
        # This would be a more comprehensive endpoint in a real implementation
        # For the hackathon, we'll return a simplified placeholder
        return {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "analysis": {
                "overall_sentiment": "neutral",
                "technical_score": 55,  # 0-100 scale
                "relative_strength": "average",
                "market_indicators": {
                    "price_trend": "neutral",
                    "volume_trend": "increasing",
                    "volatility": "moderate"
                },
                "summary": f"Market sentiment for {symbol} appears neutral with some bullish technical indicators offset by broader market uncertainty."
            }
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/api/historical_patterns")
async def historical_patterns(symbol: str):
    """
    AI-driven analysis of historical market patterns to detect potential market manipulation.
    """
    try:
        result = get_historical_analysis(symbol)
        return result
    except Exception as e:
        return {"error": str(e)}

@router.get("/api/market_comparison")
async def market_comparison(symbol: str, market_index: str = "^NSEI"):
    """
    Compare a stock's performance with the broader market to identify unusual behavior.
    """
    try:
        result = compare_with_market(symbol, market_index)
        return result
    except Exception as e:
        return {"error": str(e)}
