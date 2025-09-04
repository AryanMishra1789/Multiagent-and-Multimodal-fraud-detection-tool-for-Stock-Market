#!/usr/bin/env python3
"""
Wikipedia Entity Verifier

This module provides functions to verify if an entity exists on Wikipedia,
which helps identify legitimate financial institutions, brokerages, 
and other entities that might not be publicly traded companies.

No API key is required, and rate limits are very generous.
"""

import requests
import time
import json
from pathlib import Path
from urllib.parse import quote

# Cache for Wikipedia verification results to minimize redundant API calls
WIKI_VERIFICATION_CACHE = {}

# Persistent cache file path
CACHE_DIR = Path(__file__).parent / "data"
CACHE_DIR.mkdir(exist_ok=True)
WIKI_CACHE_FILE = CACHE_DIR / "wikipedia_verification_cache.json"

# Load cache from file if it exists
def load_wiki_cache():
    global WIKI_VERIFICATION_CACHE
    if WIKI_CACHE_FILE.exists():
        try:
            with open(WIKI_CACHE_FILE, 'r') as f:
                WIKI_VERIFICATION_CACHE = json.load(f)
                print(f"[INFO] Loaded {len(WIKI_VERIFICATION_CACHE)} Wikipedia cache entries")
        except Exception as e:
            print(f"[ERROR] Failed to load Wikipedia cache: {e}")
            WIKI_VERIFICATION_CACHE = {}

# Save cache to file
def save_wiki_cache():
    if not WIKI_VERIFICATION_CACHE:
        return
        
    try:
        with open(WIKI_CACHE_FILE, 'w') as f:
            json.dump(WIKI_VERIFICATION_CACHE, f, indent=2)
        print(f"[INFO] Saved {len(WIKI_VERIFICATION_CACHE)} Wikipedia cache entries")
    except Exception as e:
        print(f"[ERROR] Failed to save Wikipedia cache: {e}")

# Load cache on module import
load_wiki_cache()

def verify_entity_wikipedia(entity_name, categories_check=True):
    """
    Verify if an entity exists on Wikipedia, which indicates it's likely legitimate.
    
    Args:
        entity_name (str): The name of the entity to verify
        categories_check (bool): Whether to also check categories to determine entity type
        
    Returns:
        dict: Result of verification with 'exists' boolean and additional entity info
    """
    if not entity_name:
        return {"exists": False, "reason": "Empty entity name"}
    
    # Clean and normalize the entity name
    clean_name = entity_name.strip()
    
    # Check cache first to avoid redundant API calls
    if clean_name.upper() in WIKI_VERIFICATION_CACHE:
        return WIKI_VERIFICATION_CACHE[clean_name.upper()]
    
    # Base result structure
    result = {
        "exists": False,
        "entity_type": None,
        "description": None,
        "page_id": None,
        "source": "wikipedia"
    }
    
    try:
        # Step 1: Check if a Wikipedia page exists for this entity
        api_url = f"https://en.wikipedia.org/w/api.php?action=query&titles={quote(clean_name)}&format=json"
        response = requests.get(api_url, headers={'User-Agent': 'SebiVerifier/1.0'})
        data = response.json()
        
        # Parse the response
        pages = data.get('query', {}).get('pages', {})
        
        # If the page exists, it won't have a 'missing' key
        if pages:
            # Get the first page id (there should only be one)
            page_id = list(pages.keys())[0]
            
            if int(page_id) > 0:  # Positive page ID means the page exists
                page_data = pages[page_id]
                result["exists"] = True
                result["page_id"] = int(page_id)
                result["title"] = page_data.get('title')
                
                # Step 2: If requested, get categories to determine entity type
                if categories_check:
                    time.sleep(0.1)  # Small delay to be nice to the API
                    categories_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=categories&pageids={page_id}&format=json"
                    cat_response = requests.get(categories_url, headers={'User-Agent': 'SebiVerifier/1.0'})
                    cat_data = cat_response.json()
                    
                    # Extract categories
                    categories = []
                    if 'query' in cat_data and 'pages' in cat_data['query'] and page_id in cat_data['query']['pages']:
                        if 'categories' in cat_data['query']['pages'][page_id]:
                            for cat in cat_data['query']['pages'][page_id]['categories']:
                                cat_title = cat.get('title', '').replace('Category:', '')
                                categories.append(cat_title)
                    
                    result["categories"] = categories
                    
                    # Determine entity type based on categories
                    entity_type = determine_entity_type(categories)
                    result["entity_type"] = entity_type
                
                # Step 3: Get a short description
                time.sleep(0.1)  # Small delay to be nice to the API
                extract_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro&explaintext&pageids={page_id}&format=json"
                extract_response = requests.get(extract_url, headers={'User-Agent': 'SebiVerifier/1.0'})
                extract_data = extract_response.json()
                
                if 'query' in extract_data and 'pages' in extract_data['query'] and page_id in extract_data['query']['pages']:
                    extract = extract_data['query']['pages'][page_id].get('extract', '')
                    # Limit to first paragraph or first 200 chars
                    first_para = extract.split('\n')[0] if extract else ''
                    description = first_para[:200] + ('...' if len(first_para) > 200 else '')
                    result["description"] = description
    
    except Exception as e:
        result["error"] = str(e)
        print(f"Wikipedia verification error for '{clean_name}': {e}")
    
    # Cache the result to avoid redundant API calls
    WIKI_VERIFICATION_CACHE[clean_name.upper()] = result
    
    # Save to persistent cache occasionally (every 10 new entries)
    if len(WIKI_VERIFICATION_CACHE) % 10 == 0:
        save_wiki_cache()
    
    return result

def determine_entity_type(categories):
    """
    Determine the type of entity based on Wikipedia categories.
    
    Args:
        categories (list): List of Wikipedia categories for the entity
        
    Returns:
        str: Entity type classification
    """
    categories_str = ' '.join(categories).lower()
    
    # Financial institutions detection
    if any(term in categories_str for term in ['investment bank', 'financial service', 'brokerage', 'stock broker']):
        return 'financial_institution'
        
    # Media detection
    if any(term in categories_str for term in ['news agency', 'newspaper', 'media company', 'television network']):
        return 'media'
        
    # Public company detection
    if any(term in categories_str for term in ['public company', 'listed company', 'companies listed on', 'stock exchange']):
        return 'public_company'
    
    # Return a general classification if no specific type is detected
    if 'company' in categories_str or 'corporation' in categories_str:
        return 'company'
    
    return 'entity'  # Generic entity

def is_financial_institution(entity_name):
    """
    Check if an entity is a financial institution according to Wikipedia.
    
    Args:
        entity_name (str): Name of the entity to check
        
    Returns:
        bool: True if the entity is a financial institution, False otherwise
    """
    result = verify_entity_wikipedia(entity_name)
    return result["exists"] and result.get("entity_type") == "financial_institution"

def is_legitimate_entity(entity_name):
    """
    Check if an entity exists on Wikipedia, indicating it's legitimate.
    
    Args:
        entity_name (str): Name of the entity to check
        
    Returns:
        bool: True if the entity exists on Wikipedia, False otherwise
    """
    result = verify_entity_wikipedia(entity_name, categories_check=False)
    return result["exists"]

# Simple test function
if __name__ == "__main__":
    test_entities = [
        "CLSA",
        "Goldman Sachs",
        "JP Morgan",
        "Bloomberg",
        "Fake Investment Bank XYZ"
    ]
    
    for entity in test_entities:
        result = verify_entity_wikipedia(entity)
        print(f"\n{entity}:")
        print(f"Exists: {result['exists']}")
        if result["exists"]:
            print(f"Entity Type: {result['entity_type']}")
            if result.get("description"):
                print(f"Description: {result['description']}")
