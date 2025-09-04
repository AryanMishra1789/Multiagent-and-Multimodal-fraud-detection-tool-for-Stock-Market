import time
import yfinance as yf
from collections import defaultdict, deque, Counter
import numpy as np
from datetime import datetime, timedelta
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants for analysis windows
MENTION_WINDOW_SECONDS = 3600        # 1 hour buckets for social mentions
MENTION_HISTORY_HOURS = 24           # Keep 24 hours of mention history
PRICE_HISTORY_DAYS = 30              # 30 days of price history for baseline
VOLUME_LOOKBACK_DAYS = 10            # 10 days for volume analysis
PRICE_VOLATILITY_WINDOW = 20         # 20 days for volatility calculation
ANOMALY_THRESHOLD = 2.5              # Z-score threshold for anomalies
SENTIMENT_HISTORY_DAYS = 7           # 7 days of sentiment tracking

# Data structures for tracking
mention_history = defaultdict(lambda: deque(maxlen=MENTION_HISTORY_HOURS))  # symbol -> deque of (timestamp, count)
sentiment_history = defaultdict(lambda: deque(maxlen=SENTIMENT_HISTORY_DAYS*24))  # symbol -> deque of (timestamp, sentiment_score)
price_history = {}                   # symbol -> DataFrame with OHLCV
last_price_update = {}               # symbol -> timestamp
known_pump_patterns = []             # Stored patterns for known pump schemes

# Call this for each incoming message with the symbol and sentiment score
def record_mention(symbol, sentiment_score=0.0):
    """Record a mention of a symbol with optional sentiment score"""
    now = int(time.time())
    hour_bucket = now // MENTION_WINDOW_SECONDS
    dq = mention_history[symbol]
    if dq and dq[-1][0] == hour_bucket:
        dq[-1] = (hour_bucket, dq[-1][1] + 1)
    else:
        dq.append((hour_bucket, 1))
    
    # Record sentiment
    sentiment_history[symbol].append((now, sentiment_score))
    logger.debug(f"Recorded mention for {symbol} with sentiment {sentiment_score}")

def get_price_history(symbol, force_update=False):
    """Get historical price data with caching"""
    # Expanded mapping for special cases
    symbol_map = {
        # US companies
        "GOLDMAN SACHS": "GS",
        "MORGAN STANLEY": "MS",
        "NVIDIA": "NVDA",
        "NVDA": "NVDA",
        "AMD": "AMD",
        "APPLE": "AAPL",
        "MICROSOFT": "MSFT",
        "GOOGLE": "GOOGL",
        "ALPHABET": "GOOGL",
        "AMAZON": "AMZN",
        "META": "META",
        "FACEBOOK": "META",
        "TESLA": "TSLA",
        "INTEL": "INTC",
        # ETFs
        "SMH": "SMH",
        "SPDR": "SPY",
        "QQQ": "QQQ",
        # Indian companies
        "TCS": "TCS",
        "STATE BANK OF INDIA": "SBIN",
        "SBI": "SBIN",
        "HDFC BANK": "HDFCBANK",
        "RELIANCE": "RELIANCE",
        # Indices
        "S&P 500": "^GSPC",
        "S&P500": "^GSPC",
        "DOW": "^DJI",
        "NASDAQ": "^IXIC",
        "NIFTY": "^NSEI",
        "SENSEX": "^BSESN"
    }
    
    # Use the mapping if available
    actual_symbol = symbol_map.get(symbol.upper(), symbol)
    
    # For US stocks, try direct symbol first, then exchanges
    # Include more formats to maximize chances of finding data
    yf_symbols = [
        actual_symbol,           # US stocks (NVDA)
        f"{actual_symbol}.NS",   # NSE (SBIN.NS)
        f"{actual_symbol}.BO",   # BSE (SBIN.BO)
        f"{actual_symbol}:US",   # Alternative US format
        f"{actual_symbol}-US"    # Another alternative format
    ]
    
    # Special handling for indices
    if actual_symbol.startswith('^'):
        # Prioritize the index symbol
        yf_symbols.insert(0, actual_symbol)
    
    # Check if we need to update (once per day per symbol)
    now = datetime.now()
    if symbol in price_history and not force_update:
        last_update = last_price_update.get(symbol, datetime.min)
        if (now - last_update).total_seconds() < 86400:  # 24 hours
            return price_history[symbol]
    
    # Try to fetch data from any exchange
    for yf_symbol in yf_symbols:
        try:
            logger.info(f"Attempting to fetch data for {symbol} using {yf_symbol}")
            df = yf.download(yf_symbol, period=f"{PRICE_HISTORY_DAYS}d", interval="1d", auto_adjust=True)
            
            if not df.empty and len(df) > 2:  # Need at least 3 days of data
                # Ensure the DataFrame has the right columns
                required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    logger.warning(f"Data for {yf_symbol} missing columns: {missing_columns}")
                    continue
                
                price_history[symbol] = df
                last_price_update[symbol] = now
                logger.info(f"Updated price history for {symbol} from {yf_symbol}")
                return df
            else:
                logger.warning(f"Empty or insufficient data for {yf_symbol}")
        except Exception as e:
            logger.warning(f"Failed to get data for {yf_symbol}: {e}")
    
    # If we reach here, all attempts failed
    logger.warning(f"Could not fetch price data for {symbol}")
    return None

# Analyze for spikes in mentions
def detect_mention_spike(symbol, threshold=3.0):
    """Detect unusual spikes in social media mentions"""
    dq = mention_history[symbol]
    if len(dq) < 2:
        return False, 0.0
    counts = [c for _, c in dq]
    avg = sum(counts[:-1]) / max(1, len(counts) - 1)
    last = counts[-1]
    if avg == 0:
        return False, 0.0
    ratio = last / avg
    return ratio > threshold, ratio

def analyze_sentiment_shift(symbol):
    """Detect shifts in sentiment (negative to positive or vice versa)"""
    dq = sentiment_history[symbol]
    if len(dq) < 10:  # Need at least 10 data points
        return False, 0.0
    
    # Compute average sentiment for first and second half
    timestamps = [t for t, _ in dq]
    sentiments = [s for _, s in dq]
    half_point = len(sentiments) // 2
    
    first_half_avg = sum(sentiments[:half_point]) / half_point if half_point else 0
    second_half_avg = sum(sentiments[half_point:]) / (len(sentiments) - half_point) if len(sentiments) > half_point else 0
    
    # Check for significant shift
    shift = second_half_avg - first_half_avg
    significant_shift = abs(shift) > 0.3  # Threshold for significant shift
    
    return significant_shift, shift

def detect_price_volume_spike(symbol, lookback_days=5, threshold=2.0):
    """Detect unusual price and volume patterns"""
    # List of well-known ETFs, indices and major companies that are less likely to be manipulated
    well_known_entities = [
        'SPY', 'QQQ', 'VTI', 'VOO', 'SMH', 'DIA', 'IWM', 'EEM',  # ETFs
        '^GSPC', '^DJI', '^IXIC', '^NSEI', '^BSESN',  # Indices
        'MSFT', 'AAPL', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA'  # Major companies
    ]
    
    # Check if this is a well-known entity (for logging)
    is_well_known = symbol in well_known_entities or any(symbol.startswith(item) for item in well_known_entities)
    if is_well_known:
        logger.info(f"{symbol} identified as well-known index/ETF/major company - reducing risk profile")
    
    df = get_price_history(symbol)
    
    if df is None or df.empty or len(df) < 2:
        return {
            'price_spike': False, 
            'volume_spike': False,
            'price_change_pct': 0.0,
            'volume_ratio': 0.0,
            'price_z_score': 0.0,
            'is_well_known': is_well_known
        }
    
    # Check if Volume column exists (some indices don't have volume data)
    has_volume = 'Volume' in df.columns
    
    # Get recent data
    recent_df = df.tail(lookback_days)
    
    # Volume analysis (if volume data is available)
    if has_volume:
        try:
            # Use proper scalar values for calculations to avoid Series operations
            if len(df) > lookback_days:
                avg_vol = df['Volume'].iloc[:-lookback_days].mean()
            else:
                avg_vol = df['Volume'].mean()
            
            # Fix for the FutureWarning - use .iloc[0] instead of float()
            last_vol = df['Volume'].iloc[-1]
            if hasattr(last_vol, 'iloc'):  # Check if it's a Series
                last_vol = last_vol.iloc[0]
            else:
                last_vol = float(last_vol)
                
            # Same for avg_vol
            if hasattr(avg_vol, 'iloc'):  # Check if it's a Series
                avg_vol = avg_vol.iloc[0]
            else:
                avg_vol = float(avg_vol)
                
            vol_ratio = last_vol / max(1.0, avg_vol)  # Ensure we're working with scalars
            volume_spike = vol_ratio > threshold
        except Exception as e:
            logger.error(f"Error in volume analysis for {symbol}: {e}")
            volume_spike = False
            vol_ratio = 0.0
    else:
        # No volume data
        volume_spike = False
        vol_ratio = 0.0
    
    # Price analysis - multiple methods
    try:
        # 1. Recent price change vs historical volatility
        # Handle potential broadcasting errors by ensuring we have proper arrays
        try:
            prices = df['Close'].values
        except Exception:
            # If we can't get values directly, try to get as list first
            try:
                prices = df['Close'].tolist()
            except Exception:
                # As a last resort, handle one value at a time
                prices = [float(df['Close'].iloc[i]) for i in range(len(df))]
                
        # Handle empty price data
        if len(prices) < 2:
            return {
                'price_spike': False, 
                'volume_spike': volume_spike,
                'price_change_pct': 0.0,
                'volume_ratio': vol_ratio,
                'price_z_score': 0.0
            }
        
        # Safe calculation of returns with proper shape handling
        try:
            returns = np.diff(prices) / prices[:-1]
        except Exception as e:
            logger.warning(f"Error calculating returns for {symbol}: {e} - using safer method")
            returns = [(prices[i+1]/prices[i])-1 for i in range(len(prices)-1)]
        
        # Calculate recent return (handle case with limited data)
        lookback_index = min(5, len(prices)-1)
        if lookback_index > 0:
            recent_return = (prices[-1] / prices[-lookback_index]) - 1
        else:
            recent_return = 0.0
            
        # Calculate historical volatility (with proper handling of window size)
        window_size = min(PRICE_VOLATILITY_WINDOW, len(returns))
        if window_size > 0:
            volatility = np.std(returns[-window_size:])
            mean_return = np.mean(returns[-window_size:])
        else:
            volatility = 0
            mean_return = 0
        
        # Z-score of recent return
        if volatility > 0:
            z_score = (recent_return - mean_return) / volatility
        else:
            z_score = 0
            
        price_spike = abs(z_score) > ANOMALY_THRESHOLD
        
        # 2. Detect classic pump patterns (sharp rise followed by distribution)
        pattern_match = detect_pump_pattern(recent_df)
        
    except Exception as e:
        logger.error(f"Error in price analysis for {symbol}: {e}")
        price_spike = False
        z_score = 0
        recent_return = 0
        pattern_match = False
    
    return {
        'price_spike': price_spike, 
        'volume_spike': volume_spike,
        'price_change_pct': recent_return * 100,
        'volume_ratio': vol_ratio,
        'price_z_score': z_score,
        'pattern_match': pattern_match
    }

def detect_pump_pattern(df):
    """Detect classic pump and dump chart patterns"""
    if len(df) < 5:
        return False
    
    # Pattern 1: Sharp rise in price with increasing volume, followed by price decline
    try:
        # Calculate daily returns and volume changes
        df = df.copy()
        
        # Check if Volume column exists
        has_volume = 'Volume' in df.columns
        
        # Calculate returns safely
        try:
            df['return'] = df['Close'].pct_change()
        except Exception as e:
            logger.warning(f"Error calculating returns: {e}")
            return False
        
        # Calculate volume changes if volume data exists
        if has_volume:
            try:
                df['vol_change'] = df['Volume'].pct_change()
                # Look for days with both price and volume spikes
                spike_days = (df['return'] > 0.05) & (df['vol_change'] > 0.5)
            except Exception as e:
                logger.warning(f"Error calculating volume changes: {e}")
                # Use only price spikes if volume calculation fails
                spike_days = df['return'] > 0.08  # Higher threshold for price-only signals
        else:
            # Use only price spikes if no volume data
            spike_days = df['return'] > 0.08  # Higher threshold for price-only signals
        
        if spike_days.sum() >= 1:
            spike_idx = df.index[spike_days].tolist()
            
            # For each spike day, check if there's a price decline afterward
            for idx in spike_idx:
                pos = df.index.get_loc(idx)
                if pos < len(df) - 2:  # Ensure we have data after the spike
                    post_spike = df.iloc[pos+1:pos+3]
                    if (post_spike['return'] < 0).any():
                        return True
    
    except Exception as e:
        logger.error(f"Error in pump pattern detection: {e}")
        
    return False

# Main pump-and-dump detection function
def analyze_pump_and_dump(symbol):
    """Comprehensive analysis for potential pump and dump schemes"""
    logger.info(f"Starting pump-and-dump analysis for {symbol}")
    
    # Special cases for well-known entities (indices, ETFs, major companies)
    well_known_list = [
        "^GSPC", "^DJI", "^IXIC", "^NSEI", "^BSESN",  # Indices
        "SPY", "QQQ", "SMH", "VTI", "VOO", "DIA", "IWM", "EEM",  # ETFs
        "NVDA", "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "TSLA",  # Major US companies
        "TCS", "RELIANCE", "SBIN", "INFY", "HDFCBANK"  # Major Indian companies
    ]
    
    # Enhanced matching for well-known entities
    if (symbol.upper() in [x.upper() for x in well_known_list] or 
        symbol.upper().startswith("^") or 
        any(item.upper() in symbol.upper() for item in ["S&P", "DOW", "NASDAQ", "NIFTY", "SENSEX", "INDEX", "ETF"])):
        logger.info(f"{symbol} identified as well-known index/ETF/major company - reducing risk profile")
        is_well_known = True
    else:
        is_well_known = False
    
    # First check for symbol validity
    try:
        price_data = get_price_history(symbol)
        if price_data is None or price_data.empty:
            logger.warning(f"No price data available for {symbol}")
            return {
                "symbol": symbol,
                "valid_symbol": False,
                "flagged": False,
                "risk_score": 0,
                "risk_factors": ["No price data available"],
                "price_spike": False,
                "volume_spike": False,
                "unusual_pattern": False,
                "current_price": 0,
                "price_change_pct": 0
            }
        
        if len(price_data) < 3:
            logger.warning(f"Insufficient price data for {symbol} (only {len(price_data)} days)")
            return {
                "symbol": symbol,
                "valid_symbol": True,
                "flagged": False,
                "risk_score": 0,
                "risk_factors": ["Insufficient price history for analysis"],
                "price_spike": False,
                "volume_spike": False,
                "unusual_pattern": False,
                "current_price": price_data['Close'].iloc[-1] if len(price_data) > 0 else 0,
                "price_change_pct": 0
            }
        
        # Check for mention patterns
        try:
            mention_spike, mention_ratio = detect_mention_spike(symbol)
            logger.debug(f"{symbol} mention spike: {mention_spike}, ratio: {mention_ratio}")
        except Exception as e:
            logger.error(f"Error in detect_mention_spike for {symbol}: {e}")
            mention_spike, mention_ratio = False, 0
            
        try:
            sentiment_shift, sentiment_delta = analyze_sentiment_shift(symbol)
            logger.debug(f"{symbol} sentiment shift: {sentiment_shift}, delta: {sentiment_delta}")
        except Exception as e:
            logger.error(f"Error in analyze_sentiment_shift for {symbol}: {e}")
            sentiment_shift, sentiment_delta = False, 0
            
        try:
            price_vol_analysis = detect_price_volume_spike(symbol)
            logger.debug(f"{symbol} price-volume analysis: {price_vol_analysis}")
        except Exception as e:
            logger.error(f"Error in detect_price_volume_spike for {symbol}: {e}")
            price_vol_analysis = {
                'price_spike': False, 
                'volume_spike': False, 
                'price_z_score': 0, 
                'volume_ratio': 0,
                'price_change_pct': 0
            }
    except Exception as e:
        logger.error(f"Critical error in analyze_pump_and_dump for {symbol}: {e}", exc_info=True)
        return {
            "symbol": symbol,
            "valid_symbol": False,
            "flagged": False,
            "risk_score": 0,
            "risk_factors": [f"Error analyzing data: {str(e)}"],
            "price_spike": False,
            "volume_spike": False,
            "unusual_pattern": False,
            "current_price": 0,
            "price_change_pct": 0
        }
    
    # Determine overall risk
    risk_factors = []
    
    if mention_spike:
        risk_factors.append(f"Unusual spike in social media mentions ({mention_ratio:.1f}x normal)")
    
    if price_vol_analysis.get('price_spike', False):
        risk_factors.append(f"Abnormal price movement (z-score: {price_vol_analysis.get('price_z_score', 0):.2f})")
        
    if price_vol_analysis.get('volume_spike', False):
        risk_factors.append(f"Unusual trading volume ({price_vol_analysis.get('volume_ratio', 0):.1f}x normal)")
        
    if price_vol_analysis.get('pattern_match', False):
        risk_factors.append("Matches known pump and dump chart pattern")
    
    if sentiment_shift and sentiment_delta > 0:
        risk_factors.append(f"Suspicious shift to positive sentiment (+{sentiment_delta:.2f})")
    
    # Calculate risk score (0-100)
    risk_score = 0
    if mention_spike: risk_score += 25
    if price_vol_analysis.get('price_spike', False): risk_score += 25
    if price_vol_analysis.get('volume_spike', False): risk_score += 20
    if price_vol_analysis.get('pattern_match', False): risk_score += 20
    if sentiment_shift and sentiment_delta > 0: risk_score += 10
    
    # Reduce risk score for well-known entities
    if is_well_known:
        logger.info(f"Reducing risk score for well-known symbol {symbol}")
        risk_score = max(0, risk_score - 30)  # Significant reduction for major indices/ETFs
    
    # Determine if this should be flagged as suspicious
    flagged = risk_score >= 50
    
    try:
        # Get current price data
        current_price = price_data['Close'].iloc[-1] if not price_data.empty and len(price_data) > 0 else 0
    except Exception as e:
        current_price = 0
        print(f"Error getting current price for {symbol}: {e}")
    
    # Create a simplified response that's compatible with our UI
    result = {
        "symbol": symbol,
        "valid_symbol": True,
        "mention_spike": mention_spike,
        "mention_ratio": mention_ratio,
        "sentiment_shift": sentiment_shift,
        "sentiment_delta": sentiment_delta,
        "price_spike": price_vol_analysis.get('price_spike', False),
        "is_well_known": is_well_known,
        "volume_spike": price_vol_analysis.get('volume_spike', False),
        "unusual_pattern": price_vol_analysis.get('pattern_match', False),
        "current_price": current_price,
        "price_change_pct": price_vol_analysis.get('price_change_pct', 0),
        "risk_factors": risk_factors,
        "risk_score": risk_score,
        "flagged": flagged,
        "analysis_timestamp": datetime.now().isoformat(),
    }
    
    return result

def scan_multiple_symbols(symbols):
    """Run analysis on multiple symbols and return high-risk ones"""
    results = []
    for symbol in symbols:
        result = analyze_pump_and_dump(symbol)
        if result.get("flagged", False):
            results.append(result)
    return results

def alert_high_risk_stocks():
    """Generate alerts for high-risk stocks being mentioned"""
    # Get symbols that have been mentioned recently
    active_symbols = list(mention_history.keys())
    
    if not active_symbols:
        return []
    
    # Analyze them for pump and dump patterns
    alerts = []
    for symbol in active_symbols:
        result = analyze_pump_and_dump(symbol)
        if result.get("flagged", False) and result.get("risk_score", 0) > 70:
            alerts.append(result)
    
    # Log alerts
    for alert in alerts:
        logger.warning(f"HIGH RISK ALERT: {alert['symbol']} - Risk Score: {alert['risk_score']} - {', '.join(alert['risk_factors'])}")
        
    return alerts

if __name__ == "__main__":
    # Test both Indian and US stocks
    print("\n===== Testing Indian Stock =====")
    # Simulate mentions for TCS
    for _ in range(10):
        record_mention("TCS", sentiment_score=-0.2)
    time.sleep(1)
    for _ in range(50):
        record_mention("TCS", sentiment_score=0.8)
    print(analyze_pump_and_dump("TCS"))
    
    print("\n===== Testing US Stock =====")
    # Simulate mentions for NVIDIA
    for _ in range(10):
        record_mention("NVIDIA", sentiment_score=0.1)
    time.sleep(1)
    for _ in range(30):
        record_mention("NVIDIA", sentiment_score=0.7)
    print(analyze_pump_and_dump("NVIDIA"))
    
    print("\n===== Testing ETF =====")
    # Simulate mentions for semiconductor ETF
    for _ in range(5):
        record_mention("SMH", sentiment_score=0.2)
    print(analyze_pump_and_dump("SMH"))
    
    print("\n===== Testing Index =====")
    # Test a market index
    print(analyze_pump_and_dump("S&P500"))
    
    print("\n===== Testing Edge Cases =====")
    # Testing with partial names
    print("Testing MSFT:")
    print(analyze_pump_and_dump("MSFT"))
    
    print("\nTesting with spelled out name:")
    print(analyze_pump_and_dump("Microsoft"))
    
    print("\n===== Testing Non-existent Companies =====")
    print("Testing fake company:")
    print(analyze_pump_and_dump("FakeCompanyXYZ"))
    
    print("\n===== High Risk Alerts =====")
    print(alert_high_risk_stocks())
