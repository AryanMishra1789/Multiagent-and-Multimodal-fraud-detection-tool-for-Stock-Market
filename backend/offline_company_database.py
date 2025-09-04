#!/usr/bin/env python3
"""
Offline Company Database - No API dependency
Pre-populated with major Indian and US companies

This module provides functions to:
1. Lookup companies by name or symbol
2. Check if a company is legitimate
3. Get company information

It's designed to work offline without external API dependencies
for quick verification of company mentions in text.
"""

import json
import os
from pathlib import Path

# Major Indian Companies (NSE/BSE)
INDIAN_COMPANIES = {
    # IT Sector
    'TCS': {'full_name': 'Tata Consultancy Services', 'sector': 'IT', 'exchange': 'NSE', 'symbol': 'TCS', 'mcap': 'large'},
    'INFY': {'full_name': 'Infosys Limited', 'sector': 'IT', 'exchange': 'NSE', 'symbol': 'INFY', 'mcap': 'large'},
    'WIPRO': {'full_name': 'Wipro Limited', 'sector': 'IT', 'exchange': 'NSE', 'symbol': 'WIPRO', 'mcap': 'large'},
    'HCLTECH': {'full_name': 'HCL Technologies', 'sector': 'IT', 'exchange': 'NSE', 'symbol': 'HCLTECH', 'mcap': 'large'},
    
    # Banking & Financial
    'HDFCBANK': {'full_name': 'HDFC Bank Limited', 'sector': 'Banking', 'exchange': 'NSE', 'symbol': 'HDFCBANK', 'mcap': 'large'},
    'ICICIBANK': {'full_name': 'ICICI Bank Limited', 'sector': 'Banking', 'exchange': 'NSE', 'symbol': 'ICICIBANK', 'mcap': 'large'},
    'SBIN': {'full_name': 'State Bank of India', 'sector': 'Banking', 'exchange': 'NSE', 'symbol': 'SBIN', 'mcap': 'large'},
    'AXISBANK': {'full_name': 'Axis Bank Limited', 'sector': 'Banking', 'exchange': 'NSE', 'symbol': 'AXISBANK', 'mcap': 'large'},
    
    # Energy & Oil
    'RELIANCE': {'full_name': 'Reliance Industries Limited', 'sector': 'Energy', 'exchange': 'NSE', 'symbol': 'RELIANCE', 'mcap': 'large'},
    'ONGC': {'full_name': 'Oil and Natural Gas Corporation', 'sector': 'Energy', 'exchange': 'NSE', 'symbol': 'ONGC', 'mcap': 'large'},
    'IOC': {'full_name': 'Indian Oil Corporation', 'sector': 'Energy', 'exchange': 'NSE', 'symbol': 'IOC', 'mcap': 'large'},
    
    # Automobile
    'MARUTI': {'full_name': 'Maruti Suzuki India Limited', 'sector': 'Auto', 'exchange': 'NSE', 'symbol': 'MARUTI', 'mcap': 'large'},
    'TATAMOTORS': {'full_name': 'Tata Motors Limited', 'sector': 'Auto', 'exchange': 'NSE', 'symbol': 'TATAMOTORS', 'mcap': 'large'},
    'M&M': {'full_name': 'Mahindra & Mahindra', 'sector': 'Auto', 'exchange': 'NSE', 'symbol': 'M&M', 'mcap': 'large'},
    
    # Pharma
    'SUNPHARMA': {'full_name': 'Sun Pharmaceutical Industries', 'sector': 'Pharma', 'exchange': 'NSE', 'symbol': 'SUNPHARMA', 'mcap': 'large'},
    'DRREDDY': {'full_name': 'Dr. Reddys Laboratories', 'sector': 'Pharma', 'exchange': 'NSE', 'symbol': 'DRREDDY', 'mcap': 'large'},
    
    # Consumer Goods
    'HINDUNILVR': {'full_name': 'Hindustan Unilever Limited', 'sector': 'FMCG', 'exchange': 'NSE', 'symbol': 'HINDUNILVR', 'mcap': 'large'},
    'ITC': {'full_name': 'ITC Limited', 'sector': 'FMCG', 'exchange': 'NSE', 'symbol': 'ITC', 'mcap': 'large'},
    
    # Telecom
    'BHARTIARTL': {'full_name': 'Bharti Airtel Limited', 'sector': 'Telecom', 'exchange': 'NSE', 'symbol': 'BHARTIARTL', 'mcap': 'large'},
    'JIO': {'full_name': 'Reliance Jio', 'sector': 'Telecom', 'exchange': 'NSE', 'symbol': 'RJIO', 'mcap': 'large'},
}

# Major US Companies
US_COMPANIES = {
    # Technology
    'AAPL': {'full_name': 'Apple Inc.', 'sector': 'Technology', 'exchange': 'NASDAQ', 'symbol': 'AAPL', 'mcap': 'large'},
    'MSFT': {'full_name': 'Microsoft Corporation', 'sector': 'Technology', 'exchange': 'NASDAQ', 'symbol': 'MSFT', 'mcap': 'large'},
    'GOOGL': {'full_name': 'Alphabet Inc.', 'sector': 'Technology', 'exchange': 'NASDAQ', 'symbol': 'GOOGL', 'mcap': 'large'},
    'AMZN': {'full_name': 'Amazon.com Inc.', 'sector': 'Technology', 'exchange': 'NASDAQ', 'symbol': 'AMZN', 'mcap': 'large'},
    'META': {'full_name': 'Meta Platforms Inc.', 'sector': 'Technology', 'exchange': 'NASDAQ', 'symbol': 'META', 'mcap': 'large'},
    'NVDA': {'full_name': 'NVIDIA Corporation', 'sector': 'Technology', 'exchange': 'NASDAQ', 'symbol': 'NVDA', 'mcap': 'large'},
    'TSLA': {'full_name': 'Tesla Inc.', 'sector': 'Automotive', 'exchange': 'NASDAQ', 'symbol': 'TSLA', 'mcap': 'large'},
    'NFLX': {'full_name': 'Netflix Inc.', 'sector': 'Technology', 'exchange': 'NASDAQ', 'symbol': 'NFLX', 'mcap': 'large'},
    
    # Financial
    'JPM': {'full_name': 'JPMorgan Chase & Co.', 'sector': 'Financial', 'exchange': 'NYSE', 'symbol': 'JPM', 'mcap': 'large'},
    'BAC': {'full_name': 'Bank of America Corporation', 'sector': 'Financial', 'exchange': 'NYSE', 'symbol': 'BAC', 'mcap': 'large'},
    'WFC': {'full_name': 'Wells Fargo & Company', 'sector': 'Financial', 'exchange': 'NYSE', 'symbol': 'WFC', 'mcap': 'large'},
    
    # Healthcare
    'JNJ': {'full_name': 'Johnson & Johnson', 'sector': 'Healthcare', 'exchange': 'NYSE', 'symbol': 'JNJ', 'mcap': 'large'},
    'PFE': {'full_name': 'Pfizer Inc.', 'sector': 'Healthcare', 'exchange': 'NYSE', 'symbol': 'PFE', 'mcap': 'large'},
}

# Known Penny Stocks (Higher fraud risk)
PENNY_STOCKS = {
    'SUZLON': {'risk_level': 'high', 'reason': 'volatile_penny_stock'},
    'YESBANK': {'risk_level': 'high', 'reason': 'recent_troubles'},
    'RPOWER': {'risk_level': 'high', 'reason': 'debt_issues'},
}

# ETFs and Index Funds (Low fraud risk)
ETFS_AND_INDICES = {
    'NIFTYBEES': {'type': 'ETF', 'tracks': 'NIFTY50', 'risk_level': 'low'},
    'SENSEXETF': {'type': 'ETF', 'tracks': 'SENSEX', 'risk_level': 'low'},
    'SPY': {'type': 'ETF', 'tracks': 'S&P500', 'risk_level': 'low'},
    'QQQ': {'type': 'ETF', 'tracks': 'NASDAQ100', 'risk_level': 'low'},
}

def verify_company_offline(company_name):
    """
    Verify company existence using offline database
    No API calls required
    """
    company = company_name.upper().strip()
    
    # Check Indian companies
    if company in INDIAN_COMPANIES:
        return {
            'verified': True,
            'market': 'Indian',
            'data': INDIAN_COMPANIES[company],
            'method': 'offline_database'
        }
    
    # Check US companies
    if company in US_COMPANIES:
        return {
            'verified': True,
            'market': 'US',
            'data': US_COMPANIES[company],
            'method': 'offline_database'
        }
    
    # Check ETFs
    if company in ETFS_AND_INDICES:
        return {
            'verified': True,
            'market': 'ETF/Index',
            'data': ETFS_AND_INDICES[company],
            'method': 'offline_database'
        }
    
    # Check penny stocks
    if company in PENNY_STOCKS:
        return {
            'verified': True,
            'market': 'Penny Stock',
            'data': PENNY_STOCKS[company],
            'fraud_risk': 'HIGH',
            'method': 'offline_database'
        }
    
    return {
        'verified': False,
        'reason': 'Company not in database',
        'method': 'offline_database'
    }

def get_fraud_risk_score(company_name):
    """
    Calculate fraud risk based on company characteristics
    """
    verification = verify_company_offline(company_name)
    
    if not verification['verified']:
        return 90  # Unknown company = high risk
    
    data = verification.get('data', {})
    
    # Low risk: Large cap, established companies
    if data.get('mcap') == 'large':
        return 10
    
    # Medium risk: Mid/small cap
    if data.get('mcap') in ['medium', 'small']:
        return 40
    
    # High risk: Penny stocks
    if verification['market'] == 'Penny Stock':
        return 85
    
    # ETFs are generally safe
    if verification['market'] == 'ETF/Index':
        return 5
    
    return 50  # Default medium risk

# --- Utility functions for company database management and lookup ---

# Combine all companies into one dictionary for easy lookup
ALL_COMPANIES = {**INDIAN_COMPANIES, **US_COMPANIES}

def is_legitimate_company(name):
    """
    Check if a company name or symbol is in our database of legitimate companies.
    Returns True if found, False otherwise.
    """
    if not name:
        return False
        
    name_upper = name.strip().upper()
    
    # Direct lookup by symbol
    if name_upper in ALL_COMPANIES:
        return True
        
    # Check full company names
    for company_data in ALL_COMPANIES.values():
        if company_data.get('full_name', '').upper() == name_upper:
            return True
        # Check if the name is a substring of the full name or vice versa
        if name_upper in company_data.get('full_name', '').upper() or company_data.get('full_name', '').upper() in name_upper:
            return True
            
    return False

def get_company_info(name):
    """
    Get company information from our database.
    Returns a dictionary with company info if found, None otherwise.
    """
    if not name:
        return None
        
    name_upper = name.strip().upper()
    
    # Direct lookup by symbol
    if name_upper in ALL_COMPANIES:
        return ALL_COMPANIES[name_upper]
        
    # Check full company names
    for symbol, company_data in ALL_COMPANIES.items():
        full_name = company_data.get('full_name', '').upper()
        if full_name == name_upper or name_upper in full_name or full_name in name_upper:
            return company_data
            
    return None

def save_company_to_database(symbol, company_info):
    """
    Save a new company to the database.
    This will create a JSON file with additional companies that can be loaded at runtime.
    """
    if not symbol:
        return False
        
    symbol_upper = symbol.strip().upper()
    
    # Don't overwrite existing entries
    if symbol_upper in ALL_COMPANIES:
        return False
        
    # Create a data directory if it doesn't exist
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Path to additional companies JSON file
    additional_file = data_dir / "additional_companies.json"
    
    # Load existing additional companies
    additional_companies = {}
    if additional_file.exists():
        try:
            with open(additional_file, 'r') as f:
                additional_companies = json.load(f)
        except Exception as e:
            print(f"Error loading additional companies file: {e}")
    
    # Add the new company
    additional_companies[symbol_upper] = company_info
    
    # Save the updated file
    try:
        with open(additional_file, 'w') as f:
            json.dump(additional_companies, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving additional companies file: {e}")
        return False

def load_additional_companies():
    """
    Load additional companies from the JSON file.
    Returns a dictionary of additional companies.
    """
    # Path to additional companies JSON file
    data_dir = Path(__file__).parent / "data"
    additional_file = data_dir / "additional_companies.json"
    
    # Load additional companies if the file exists
    if additional_file.exists():
        try:
            with open(additional_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading additional companies file: {e}")
    
    return {}

if __name__ == "__main__":
    # Test the offline verification
    test_companies = ['TCS', 'NVDA', 'FAKE_COMPANY', 'SUZLON']
    
    for company in test_companies:
        result = verify_company_offline(company)
        risk = get_fraud_risk_score(company)
        print(f"{company}: {result['verified']} (Risk: {risk})")
