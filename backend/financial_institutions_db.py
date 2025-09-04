#!/usr/bin/env python3
"""
Financial Institutions Database
Contains information about brokerages, financial institutions, and financial media outlets
that should not be flagged as suspicious entities.
"""

# Global brokerage firms and investment banks
GLOBAL_BROKERAGES = {
    'CLSA': {
        'full_name': 'Credit Lyonnais Securities Asia',
        'type': 'brokerage',
        'description': 'Global investment bank and brokerage firm headquartered in Hong Kong',
        'legitimate': True
    },
    'GOLDMAN SACHS': {
        'full_name': 'Goldman Sachs Group, Inc.',
        'type': 'investment_bank',
        'description': 'Global investment banking and financial services firm',
        'legitimate': True
    },
    'MORGAN STANLEY': {
        'full_name': 'Morgan Stanley',
        'type': 'investment_bank',
        'description': 'Global investment banking and financial services firm',
        'legitimate': True
    },
    'JP MORGAN': {
        'full_name': 'JPMorgan Chase & Co.',
        'type': 'investment_bank',
        'description': 'Global investment banking and financial services firm',
        'legitimate': True
    },
    'CITI': {
        'full_name': 'Citigroup Inc.',
        'type': 'investment_bank',
        'description': 'Global investment banking and financial services firm',
        'legitimate': True
    },
    'UBS': {
        'full_name': 'UBS Group AG',
        'type': 'investment_bank',
        'description': 'Swiss multinational investment bank and financial services company',
        'legitimate': True
    },
    'CREDIT SUISSE': {
        'full_name': 'Credit Suisse Group AG',
        'type': 'investment_bank',
        'description': 'Swiss multinational investment bank and financial services company',
        'legitimate': True
    },
    'BARCLAYS': {
        'full_name': 'Barclays PLC',
        'type': 'investment_bank',
        'description': 'British multinational investment bank and financial services company',
        'legitimate': True
    },
    'DEUTSCHE BANK': {
        'full_name': 'Deutsche Bank AG',
        'type': 'investment_bank',
        'description': 'German multinational investment bank and financial services company',
        'legitimate': True
    },
    'HSBC': {
        'full_name': 'HSBC Holdings plc',
        'type': 'investment_bank',
        'description': 'British multinational investment bank and financial services company',
        'legitimate': True
    },
    'BNP PARIBAS': {
        'full_name': 'BNP Paribas SA',
        'type': 'investment_bank',
        'description': 'French multinational investment bank and financial services company',
        'legitimate': True
    },
    'NOMURA': {
        'full_name': 'Nomura Holdings, Inc.',
        'type': 'investment_bank',
        'description': 'Japanese financial holding company and investment bank',
        'legitimate': True
    }
}

# Indian brokerage firms and financial institutions
INDIAN_BROKERAGES = {
    'ZERODHA': {
        'full_name': 'Zerodha',
        'type': 'brokerage',
        'description': 'Indian financial services company and discount broker',
        'legitimate': True
    },
    'UPSTOX': {
        'full_name': 'Upstox',
        'type': 'brokerage',
        'description': 'Indian discount broker and trading platform',
        'legitimate': True
    },
    'ANGEL ONE': {
        'full_name': 'Angel One Limited',
        'type': 'brokerage',
        'description': 'Indian stock broker and financial services firm',
        'legitimate': True
    },
    'MOTILAL OSWAL': {
        'full_name': 'Motilal Oswal Financial Services',
        'type': 'brokerage',
        'description': 'Indian financial services firm',
        'legitimate': True
    },
    'IIFL': {
        'full_name': 'India Infoline Finance Limited',
        'type': 'brokerage',
        'description': 'Indian financial services company',
        'legitimate': True
    },
    'HDFC SECURITIES': {
        'full_name': 'HDFC Securities',
        'type': 'brokerage',
        'description': 'Indian stock broker and financial services firm',
        'legitimate': True
    },
    'ICICI DIRECT': {
        'full_name': 'ICICI Direct',
        'type': 'brokerage',
        'description': 'Indian financial services firm',
        'legitimate': True
    },
    'KOTAK SECURITIES': {
        'full_name': 'Kotak Securities',
        'type': 'brokerage',
        'description': 'Indian stock broker and financial services firm',
        'legitimate': True
    },
    'SHAREKHAN': {
        'full_name': 'Sharekhan',
        'type': 'brokerage',
        'description': 'Indian stock broker owned by BNP Paribas',
        'legitimate': True
    },
    'AXIS DIRECT': {
        'full_name': 'Axis Direct',
        'type': 'brokerage',
        'description': 'Indian stock broker and financial services firm',
        'legitimate': True
    }
}

# Financial media outlets and research firms
FINANCIAL_MEDIA = {
    'BLOOMBERG': {
        'full_name': 'Bloomberg L.P.',
        'type': 'media',
        'description': 'Financial, software, data, and media company',
        'legitimate': True
    },
    'REUTERS': {
        'full_name': 'Reuters',
        'type': 'media',
        'description': 'International news organization',
        'legitimate': True
    },
    'CNBC': {
        'full_name': 'CNBC',
        'type': 'media',
        'description': 'American business and financial news television channel',
        'legitimate': True
    },
    'FINANCIAL TIMES': {
        'full_name': 'Financial Times',
        'type': 'media',
        'description': 'International daily newspaper focused on business and economic news',
        'legitimate': True
    },
    'THE ECONOMIST': {
        'full_name': 'The Economist',
        'type': 'media',
        'description': 'International weekly newspaper focused on current affairs and business',
        'legitimate': True
    },
    'WALL STREET JOURNAL': {
        'full_name': 'The Wall Street Journal',
        'type': 'media',
        'description': 'American business-focused daily newspaper',
        'legitimate': True
    },
    'MONEYCONTROL': {
        'full_name': 'Moneycontrol',
        'type': 'media',
        'description': 'Indian financial news and information website',
        'legitimate': True
    },
    'ECONOMIC TIMES': {
        'full_name': 'The Economic Times',
        'type': 'media',
        'description': 'Indian English-language business-focused daily newspaper',
        'legitimate': True
    },
    'BUSINESS STANDARD': {
        'full_name': 'Business Standard',
        'type': 'media',
        'description': 'Indian English-language daily business newspaper',
        'legitimate': True
    },
    'MINT': {
        'full_name': 'Mint',
        'type': 'media',
        'description': 'Indian financial daily newspaper',
        'legitimate': True
    },
    'LIVEMINT': {
        'full_name': 'Livemint',
        'type': 'media',
        'description': 'Indian financial news website',
        'legitimate': True
    }
}

# Combine all legitimate financial entities for easy lookup
ALL_FINANCIAL_ENTITIES = {**GLOBAL_BROKERAGES, **INDIAN_BROKERAGES, **FINANCIAL_MEDIA}

def is_legitimate_financial_entity(name):
    """
    Check if a given name is a legitimate financial institution, brokerage, or media outlet.
    Returns True if legitimate, False otherwise.
    """
    if not name:
        return False
        
    name_upper = name.strip().upper()
    
    # Direct lookup
    if name_upper in ALL_FINANCIAL_ENTITIES:
        return True
        
    # Check if the name is contained within any of the full names
    for entity in ALL_FINANCIAL_ENTITIES.values():
        full_name = entity.get('full_name', '').upper()
        if name_upper in full_name or full_name in name_upper:
            return True
    
    return False

def get_financial_entity_info(name):
    """
    Get information about a financial entity if it exists in our database.
    Returns a dictionary with entity information or None if not found.
    """
    if not name:
        return None
        
    name_upper = name.strip().upper()
    
    # Direct lookup
    if name_upper in ALL_FINANCIAL_ENTITIES:
        return ALL_FINANCIAL_ENTITIES[name_upper]
        
    # Check if the name is contained within any of the full names
    for key, entity in ALL_FINANCIAL_ENTITIES.items():
        full_name = entity.get('full_name', '').upper()
        if name_upper in full_name or full_name in name_upper:
            return entity
    
    return None

# Simple test function
if __name__ == "__main__":
    test_entities = [
        'CLSA', 
        'Goldman Sachs', 
        'Zerodha', 
        'CNBC',
        'Unknown Entity'
    ]
    
    for entity in test_entities:
        is_legit = is_legitimate_financial_entity(entity)
        info = get_financial_entity_info(entity)
        print(f"{entity}: Legitimate = {is_legit}")
        if info:
            print(f"  - Type: {info.get('type')}")
            print(f"  - Description: {info.get('description')}")
