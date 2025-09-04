"""
Historical market data analyzer for detecting deceptive patterns.

This module enhances the SEBI Hackathon project with AI-driven analysis of
historical market data to identify potentially misleading market behaviors.
"""
import yfinance as yf
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from collections import defaultdict
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants for analysis
MAX_HISTORY_PERIOD = "5y"  # Maximum history to retrieve
MANIPULATION_WINDOW_DAYS = 30  # Window for looking at manipulation patterns
VOLATILITY_WINDOW = 20  # Days for volatility calculation
TYPICAL_PATTERNS = {
    "pump_dump": {
        "description": "Sharp price increase followed by rapid decline, often with elevated volume",
        "risk_level": "high"
    },
    "bear_raid": {
        "description": "Coordinated short selling to drive prices down artificially",
        "risk_level": "high"
    },
    "painting_tape": {
        "description": "Artificial trading activity to create appearance of high volume",
        "risk_level": "high"
    },
    "spoofing": {
        "description": "Placing orders with no intention to execute to create false impression",
        "risk_level": "high"
    },
    "wash_trade": {
        "description": "Simultaneously buying and selling same security to create artificial activity",
        "risk_level": "high"
    },
    "momentum_ignition": {
        "description": "Initiating price movement to trigger algorithmic trading reactions",
        "risk_level": "medium"
    },
    "circular_trading": {
        "description": "Trading between related parties to create artificial price/volume",
        "risk_level": "high"
    }
}

class HistoricalMarketAnalyzer:
    """
    AI-driven historical market data analyzer that can detect patterns of
    potential market manipulation or misleading behavior.
    """
    
    def __init__(self):
        self.data_cache = {}
        self.pattern_cache = {}
        self.analysis_cache = {}
        self.session = requests.Session()
        self.session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    
    def get_historical_data(self, symbol: str, period: str = "1y", interval: str = "1d", force_refresh: bool = False) -> pd.DataFrame:
        """
        Fetch and cache historical market data for a symbol
        """
        cache_key = f"{symbol}_{period}_{interval}"
        
        # Return cached data if available and not forced to refresh
        if not force_refresh and cache_key in self.data_cache:
            return self.data_cache[cache_key]
        
        # Handle different market extensions
        symbol_variations = [
            symbol,
            f"{symbol}.NS",   # NSE
            f"{symbol}.BO",   # BSE
        ]
        
        for sym in symbol_variations:
            try:
                data = yf.download(sym, period=period, interval=interval, progress=False, session=self.session)
                if not data.empty and len(data) > 5:  # Ensure we have meaningful data
                    self.data_cache[cache_key] = data
                    return data
            except Exception as e:
                logger.warning(f"Error fetching data for {sym}: {e}")
        
        # If we reach here, all attempts failed
        return pd.DataFrame()
    
    def analyze_price_pattern(self, symbol: str, period: str = "1y") -> Dict:
        """
        Analyze price patterns to detect potential manipulative activities
        """
        # Get data
        data = self.get_historical_data(symbol, period)
        if data.empty:
            return {
                "symbol": symbol,
                "valid_data": False,
                "patterns_detected": [],
                "message": "Could not obtain valid market data"
            }
        
        # Calculate necessary metrics
        data['daily_return'] = data['Close'].pct_change()
        data['rolling_vol'] = data['daily_return'].rolling(window=VOLATILITY_WINDOW).std() * np.sqrt(252)
        if 'Volume' in data.columns:
            data['volume_ratio'] = data['Volume'] / data['Volume'].rolling(window=20).mean()
        
        patterns_detected = []
        
        # 1. Detect pump and dump patterns
        try:
            pump_dump = self._detect_pump_dump_pattern(data)
            if pump_dump['detected']:
                patterns_detected.append({
                    "pattern": "pump_dump",
                    "confidence": pump_dump['confidence'],
                    "details": pump_dump['details'],
                    "timeframe": pump_dump['timeframe']
                })
        except Exception as e:
            logger.error(f"Error detecting pump and dump for {symbol}: {e}")
        
        # 2. Detect unusual volatility
        try:
            unusual_vol = self._detect_unusual_volatility(data)
            if unusual_vol['detected']:
                patterns_detected.append({
                    "pattern": "unusual_volatility",
                    "confidence": unusual_vol['confidence'],
                    "details": unusual_vol['details'],
                    "timeframe": unusual_vol['timeframe']
                })
        except Exception as e:
            logger.error(f"Error detecting unusual volatility for {symbol}: {e}")
        
        # 3. Detect price manipulation patterns
        try:
            manipulation = self._detect_price_manipulation(data)
            if manipulation['detected']:
                patterns_detected.append({
                    "pattern": "price_manipulation",
                    "confidence": manipulation['confidence'],
                    "details": manipulation['details'],
                    "timeframe": manipulation['timeframe']
                })
        except Exception as e:
            logger.error(f"Error detecting price manipulation for {symbol}: {e}")
        
        # Determine overall risk level
        risk_level = "low"
        if len(patterns_detected) == 1:
            risk_level = "medium"
        elif len(patterns_detected) > 1:
            risk_level = "high"
        
        # Calculate recent performance metrics
        try:
            month_change = ((data['Close'].iloc[-1] / data['Close'].iloc[-min(20, len(data)-1)]) - 1) * 100
            three_month_change = ((data['Close'].iloc[-1] / data['Close'].iloc[-min(60, len(data)-1)]) - 1) * 100
            
            recent_performance = {
                "last_price": float(data['Close'].iloc[-1]),
                "one_month_change_pct": float(month_change),
                "three_month_change_pct": float(three_month_change),
                "current_volatility": float(data['rolling_vol'].iloc[-1]) if not pd.isna(data['rolling_vol'].iloc[-1]) else None
            }
        except:
            recent_performance = {
                "last_price": float(data['Close'].iloc[-1]) if not data.empty else None
            }
        
        return {
            "symbol": symbol,
            "valid_data": True,
            "risk_level": risk_level,
            "patterns_detected": patterns_detected,
            "recent_performance": recent_performance,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    def _detect_pump_dump_pattern(self, data: pd.DataFrame) -> Dict:
        """Detect classic pump and dump patterns"""
        result = {
            "detected": False,
            "confidence": 0,
            "details": "",
            "timeframe": ""
        }
        
        if len(data) < 20:
            return result
        
        # Look for sharp increase followed by decline
        # Calculate rolling returns for different periods
        data['5d_return'] = data['Close'].pct_change(periods=5)
        data['10d_return'] = data['Close'].pct_change(periods=10)
        
        # Look for periods of significant pump (>20% in 10 days) followed by dump
        for i in range(20, len(data)):
            # Check for pump phase
            if data['10d_return'].iloc[i-10] > 0.20:  # >20% gain in 10 days
                # Check for subsequent dump phase
                if data['5d_return'].iloc[i] < -0.10:  # >10% loss in 5 days
                    pump_date = data.index[i-10].strftime("%Y-%m-%d")
                    dump_date = data.index[i].strftime("%Y-%m-%d")
                    result = {
                        "detected": True,
                        "confidence": 0.8,
                        "details": f"Sharp price increase of {data['10d_return'].iloc[i-10]*100:.1f}% followed by decline of {data['5d_return'].iloc[i]*100:.1f}%",
                        "timeframe": f"{pump_date} to {dump_date}"
                    }
                    break
                    
        return result
    
    def _detect_unusual_volatility(self, data: pd.DataFrame) -> Dict:
        """Detect periods of unusual volatility"""
        result = {
            "detected": False,
            "confidence": 0,
            "details": "",
            "timeframe": ""
        }
        
        if len(data) < 30 or 'rolling_vol' not in data.columns:
            return result
        
        # Calculate average volatility and standard deviation
        avg_vol = data['rolling_vol'].mean()
        std_vol = data['rolling_vol'].std()
        
        # Look for volatility spikes (>3 standard deviations)
        vol_spikes = data[data['rolling_vol'] > avg_vol + 3*std_vol]
        
        if not vol_spikes.empty:
            spike_dates = [d.strftime("%Y-%m-%d") for d in vol_spikes.index]
            max_spike = vol_spikes['rolling_vol'].max()
            max_date = vol_spikes['rolling_vol'].idxmax().strftime("%Y-%m-%d")
            
            result = {
                "detected": True,
                "confidence": 0.7,
                "details": f"Unusual volatility spike detected ({max_spike*100:.1f}% annualized vs average {avg_vol*100:.1f}%)",
                "timeframe": f"{max_date}" if len(spike_dates) == 1 else f"{spike_dates[0]} to {spike_dates[-1]}"
            }
            
        return result
    
    def _detect_price_manipulation(self, data: pd.DataFrame) -> Dict:
        """Detect potential price manipulation patterns"""
        result = {
            "detected": False,
            "confidence": 0,
            "details": "",
            "timeframe": ""
        }
        
        if len(data) < 30 or 'Volume' not in data.columns:
            return result
        
        # Check for unusual volume spikes with price changes
        data['volume_spike'] = data['Volume'] > data['Volume'].rolling(window=30).mean() * 5
        data['price_reversal'] = (data['Close'] - data['Open']).abs() > 2 * data['Close'].rolling(window=20).std()
        
        # Look for days with both volume spikes and price reversals
        suspicious_days = data[data['volume_spike'] & data['price_reversal']]
        
        if len(suspicious_days) > 2:
            suspicious_dates = [d.strftime("%Y-%m-%d") for d in suspicious_days.index]
            
            result = {
                "detected": True,
                "confidence": 0.6,
                "details": f"Detected {len(suspicious_days)} instances of unusual volume combined with price reversals",
                "timeframe": f"{suspicious_dates[0]} to {suspicious_dates[-1]}"
            }
        
        return result
    
    def analyze_multiple_patterns(self, symbol: str) -> Dict:
        """Comprehensive market pattern analysis for a symbol"""
        # First get standard pattern analysis
        basic_analysis = self.analyze_price_pattern(symbol)
        
        # Add cross-validation with sector peers if possible
        try:
            # Attempt to get ticker info for sector
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if 'sector' in info:
                sector = info['sector']
                basic_analysis['sector'] = sector
                basic_analysis['compared_to_sector'] = "Analysis compared to sector peers not implemented yet"
        except Exception as e:
            logger.warning(f"Couldn't get sector information for {symbol}: {e}")
        
        # Add recommendations if patterns detected
        if basic_analysis['patterns_detected']:
            recommendations = [
                "Consider additional due diligence before trading based on this security",
                "Verify information from multiple sources before making investment decisions",
                "Be cautious of high-risk trading patterns in this security"
            ]
            basic_analysis['recommendations'] = recommendations
        
        # Add AI-generated summary
        pattern_names = [p['pattern'] for p in basic_analysis['patterns_detected']]
        if pattern_names:
            patterns_text = ', '.join([TYPICAL_PATTERNS.get(p, {}).get('description', p) for p in pattern_names if p in TYPICAL_PATTERNS])
            summary = f"Analysis detected potential {basic_analysis['risk_level']} risk patterns including: {patterns_text}."
            basic_analysis['ai_summary'] = summary
        else:
            basic_analysis['ai_summary'] = "No suspicious patterns detected in the analyzed historical data."
        
        return basic_analysis

# Initialize the analyzer
market_analyzer = HistoricalMarketAnalyzer()

def get_historical_analysis(symbol: str) -> Dict:
    """Public function to get historical analysis for a symbol"""
    return market_analyzer.analyze_multiple_patterns(symbol)

def compare_with_market(symbol: str, market_index: str = "^NSEI") -> Dict:
    """Compare a symbol's performance with the broader market"""
    try:
        # Get data for both symbol and market
        symbol_data = market_analyzer.get_historical_data(symbol, period="1y")
        market_data = market_analyzer.get_historical_data(market_index, period="1y")
        
        if symbol_data.empty or market_data.empty:
            return {
                "error": "Could not obtain data for symbol or market index"
            }
        
        # Align dates
        start_date = max(symbol_data.index[0], market_data.index[0])
        end_date = min(symbol_data.index[-1], market_data.index[-1])
        
        symbol_data = symbol_data.loc[start_date:end_date]
        market_data = market_data.loc[start_date:end_date]
        
        # Calculate returns
        symbol_return = (symbol_data['Close'].iloc[-1] / symbol_data['Close'].iloc[0]) - 1
        market_return = (market_data['Close'].iloc[-1] / market_data['Close'].iloc[0]) - 1
        
        # Calculate correlation
        symbol_returns = symbol_data['Close'].pct_change().dropna()
        market_returns = market_data['Close'].pct_change().dropna()
        
        # Make sure both series align
        common_dates = symbol_returns.index.intersection(market_returns.index)
        correlation = symbol_returns.loc[common_dates].corr(market_returns.loc[common_dates])
        
        # Calculate beta (market sensitivity)
        covariance = symbol_returns.loc[common_dates].cov(market_returns.loc[common_dates])
        market_variance = market_returns.loc[common_dates].var()
        beta = covariance / market_variance if market_variance != 0 else 0
        
        # Check if performance is unusual compared to market
        outperformance = symbol_return - market_return
        
        # Determine if outperformance is suspicious
        is_suspicious = abs(outperformance) > 0.5 and correlation < 0.3  # >50% diff with low correlation
        
        return {
            "symbol": symbol,
            "market_index": market_index,
            "correlation": float(correlation),
            "beta": float(beta),
            "symbol_return": float(symbol_return * 100),
            "market_return": float(market_return * 100),
            "outperformance": float(outperformance * 100),
            "unusual_performance": is_suspicious,
            "analysis": "Performance significantly deviates from market with low correlation" if is_suspicious else "Performance appears normal relative to market movements"
        }
        
    except Exception as e:
        return {
            "error": str(e)
        }

# Example usage if run as a script
if __name__ == "__main__":
    # Test with a few symbols
    print("\nTesting with TCS (Indian stock)...")
    print(get_historical_analysis("TCS"))
    
    print("\nTesting with RELIANCE (Indian stock)...")
    print(get_historical_analysis("RELIANCE"))
    
    print("\nComparing TCS with NSE index...")
    print(compare_with_market("TCS", "^NSEI"))
