import yfinance as yf

def verify_company_yfinance(symbol_or_name):
    """
    Verifies if a company is listed on US, NSE or BSE using yfinance.
    Accepts symbol (e.g., 'NVDA', 'RELIANCE', 'TCS') or name (partial match).
    Returns dict with status and details for different exchanges.
    """
    # Fuzzy mapping for common companies
    name_to_symbol = {
        # US companies
        "NVIDIA": "NVDA",
        "NVDA": "NVDA",
        "APPLE": "AAPL",
        "AAPL": "AAPL",
        "MICROSOFT": "MSFT", 
        "MSFT": "MSFT",
        "GOOGLE": "GOOGL",
        "ALPHABET": "GOOGL",
        "GOOGL": "GOOGL",
        "AMAZON": "AMZN",
        "AMZN": "AMZN",
        "META": "META",
        "FACEBOOK": "META",
        "TESLA": "TSLA",
        "TSLA": "TSLA",
        "AMD": "AMD",
        "INTEL": "INTC",
        "INTC": "INTC",
        "GOLDMAN SACHS": "GS",
        "GS": "GS",
        "MORGAN STANLEY": "MS",
        "MS": "MS",
        "WALMART": "WMT",
        "IBM": "IBM",
        "CISCO": "CSCO",
        "ORACLE": "ORCL",
        "QUALCOMM": "QCOM",
        "BROADCOM": "AVGO",
        # ETFs
        "SMH": "SMH",  # VanEck Semiconductor ETF
        "SPDR": "SPY", # SPDR S&P 500 ETF
        "SPY": "SPY",
        "QQQ": "QQQ",  # Invesco QQQ (NASDAQ-100)
        "VTI": "VTI",  # Vanguard Total Stock Market ETF
        # Indian companies
        "HDFC BANK": "HDFCBANK",
        "HDFCBANK": "HDFCBANK",
        "RELIANCE": "RELIANCE",
        "TATA CONSULTANCY SERVICES": "TCS",
        "TCS": "TCS",
        "INFOSYS": "INFY",
        "INFY": "INFY",
        "ICICI BANK": "ICICIBANK",
        "ICICIBANK": "ICICIBANK",
        "STATE BANK OF INDIA": "SBIN",
        "SBI": "SBIN",
        "SBIN": "SBIN",
        "BHARTI AIRTEL": "BHARTIARTL",
        "HINDUSTAN UNILEVER": "HINDUNILVR",
        "ITC": "ITC",
        "KOTAK MAHINDRA BANK": "KOTAKBANK",
        # Indices
        "S&P 500": "^GSPC",
        "S&P500": "^GSPC",
        "DOW": "^DJI",
        "DOW JONES": "^DJI",
        "NASDAQ": "^IXIC",
        "NIFTY": "^NSEI",
        "NIFTY 50": "^NSEI",
        "SENSEX": "^BSESN",
        # Add more as needed
    }
    # Try to map name to symbol
    key = symbol_or_name.strip().upper()
    symbol = name_to_symbol.get(key, key)
    results = {}
    
    # List of known ETFs for faster identification
    known_etfs = ["SMH", "SPY", "QQQ", "VTI", "VOO", "VGT", "XLK", "DIA", "IWM", "EEM"]
    known_indices = ["^GSPC", "^DJI", "^IXIC", "^NSEI", "^BSESN"]
    
    # Add special case for ETFs
    if symbol in known_etfs:
        results['etf'] = {
            'found': True, 
            'symbol': symbol, 
            'name': f"{symbol} ETF"
        }
    
    # Add special case for market indices
    if symbol in known_indices or symbol.startswith("^"):
        results['index'] = {
            'found': True, 
            'symbol': symbol, 
            'name': f"{symbol} Index"
        }
    
    # Check if it's in our mapping (pre-verified)
    if key in name_to_symbol or symbol in name_to_symbol.values():
        results['trusted_mapping'] = True
    
    # Try all possible symbol formats for maximum coverage
    formats_to_try = [
        (symbol, 'us', 'US Stock'),                  # NVDA
        (f"{symbol}.NS", 'nse', 'NSE (India)'),      # NVDA.NS
        (f"{symbol}.BO", 'bse', 'BSE (India)'),      # NVDA.BO
        (f"{symbol}:US", 'us_alt', 'US Alt'),        # NVDA:US
        (f"{symbol}-US", 'us_alt2', 'US Alt2')       # NVDA-US
    ]
    
    # Try each format
    for fmt_symbol, market_key, market_name in formats_to_try:
        try:
            ticker = yf.Ticker(fmt_symbol)
            info = ticker.info
            print(f"[DEBUG] yfinance {market_name} lookup for {fmt_symbol}")
            
            # More robust check for valid ticker
            is_valid = False
            if info:
                if info.get('regularMarketPrice') is not None:
                    is_valid = True
                elif info.get('shortName') or info.get('longName'):
                    # If we have a name but not price, it might still be valid
                    is_valid = True
                elif info.get('symbol') == fmt_symbol:
                    # If symbol matches what we asked for
                    is_valid = True
            
            if is_valid:
                results[market_key] = {
                    'found': True, 
                    'symbol': fmt_symbol, 
                    'name': info.get('shortName', info.get('longName', fmt_symbol)),
                    'details': info
                }
            else:
                results[market_key] = {'found': False, 'symbol': fmt_symbol}
        except Exception as e:
            print(f"[ERROR] yfinance {market_name} lookup failed for {fmt_symbol}: {e}")
            results[market_key] = {'found': False, 'symbol': fmt_symbol, 'error': str(e)}
        
    # Final check - if found in any exchange or is a known entity, mark as verified
    found_anywhere = (
        results.get('us', {}).get('found', False) or
        results.get('us_alt', {}).get('found', False) or 
        results.get('us_alt2', {}).get('found', False) or
        results.get('nse', {}).get('found', False) or
        results.get('bse', {}).get('found', False) or
        'etf' in results or
        'index' in results or
        results.get('trusted_mapping', False)
    )
    
    if found_anywhere:
        results['trusted_mapping'] = True
    else:
        results['trusted_mapping'] = False
        
    # Add a simple summary result for quick access
    results['verified'] = found_anywhere
    
    return results

if __name__ == "__main__":
    print(verify_company_yfinance("TCS"))
    print(verify_company_yfinance("RELIANCE"))
