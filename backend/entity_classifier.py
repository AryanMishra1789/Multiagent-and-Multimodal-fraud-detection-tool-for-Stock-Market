#!/usr/bin/env python3
"""
Entity Classification Demo Script
Shows how to use the financial_institutions_db and offline_company_database
to properly classify mentioned entities in financial text.
"""

import sys
import argparse
from financial_institutions_db import is_legitimate_financial_entity, get_financial_entity_info
from offline_company_database import is_legitimate_company, get_company_info

def classify_entity(entity_name):
    """
    Classify an entity name as:
    1. Financial Institution (broker, media, etc.)
    2. Legitimate Company (publicly traded)
    3. Unknown/Suspicious Entity
    """
    # First, check if it's a financial institution
    if is_legitimate_financial_entity(entity_name):
        entity_info = get_financial_entity_info(entity_name)
        return {
            "name": entity_name,
            "classification": "Financial Institution",
            "entity_type": entity_info.get("type", "unknown"),
            "full_name": entity_info.get("full_name", entity_name),
            "description": entity_info.get("description", ""),
            "legitimate": True
        }
    
    # Next, check if it's a legitimate company
    if is_legitimate_company(entity_name):
        company_info = get_company_info(entity_name)
        return {
            "name": entity_name,
            "classification": "Legitimate Company",
            "symbol": next((k for k, v in company_info.items() if v == company_info), entity_name),
            "full_name": company_info.get("full_name", entity_name),
            "sector": company_info.get("sector", "unknown"),
            "exchange": company_info.get("exchange", "unknown"),
            "legitimate": True
        }
    
    # If not found in either database, it's suspicious/unknown
    return {
        "name": entity_name,
        "classification": "Unknown/Suspicious Entity",
        "legitimate": False
    }

def process_text(text):
    """
    Process text containing entity mentions.
    This is a simplified version - in practice you'd use NER or the LLM
    to extract entities before classification.
    """
    # In a real scenario, we'd extract entities properly
    # For this demo, we'll just split by commas and clean up
    entities = [e.strip() for e in text.split(',')]
    results = []
    
    for entity in entities:
        if entity:  # Skip empty strings
            classification = classify_entity(entity)
            results.append(classification)
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Classify entities mentioned in financial text")
    parser.add_argument("--text", "-t", help="Text containing entity mentions")
    parser.add_argument("--entity", "-e", help="Single entity to classify")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    
    args = parser.parse_args()
    
    if args.interactive:
        print("=== Entity Classification Interactive Mode ===")
        print("Enter entities separated by commas, or 'q' to quit")
        while True:
            text = input("> ")
            if text.lower() == 'q':
                break
            
            results = process_text(text)
            print("\nResults:")
            for r in results:
                if r["legitimate"]:
                    print(f"✅ {r['name']}: {r['classification']} - {r.get('full_name', '')}")
                    if "description" in r:
                        print(f"   Description: {r['description']}")
                    if "sector" in r:
                        print(f"   Sector: {r['sector']}, Exchange: {r['exchange']}")
                else:
                    print(f"❌ {r['name']}: {r['classification']}")
            print()
    
    elif args.entity:
        result = classify_entity(args.entity)
        if result["legitimate"]:
            print(f"✅ {result['name']} is classified as: {result['classification']}")
            for k, v in result.items():
                if k not in ["name", "classification", "legitimate"]:
                    print(f"  {k}: {v}")
        else:
            print(f"❌ {result['name']} is classified as: {result['classification']}")
    
    elif args.text:
        results = process_text(args.text)
        for r in results:
            if r["legitimate"]:
                print(f"✅ {r['name']}: {r['classification']}")
            else:
                print(f"❌ {r['name']}: {r['classification']}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
