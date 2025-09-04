#!/usr/bin/env python3
"""
Database Management Utilities

Provides API endpoints and utilities to manage the financial institutions
and company databases. This allows adding new entities without modifying 
source code files directly.
"""

import json
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, List, Optional

# Create a directory for data storage if it doesn't exist
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# File paths for additional data
ADDITIONAL_COMPANIES_FILE = DATA_DIR / "additional_companies.json"
ADDITIONAL_FINANCIAL_ENTITIES_FILE = DATA_DIR / "additional_financial_entities.json"

# Create router for FastAPI integration
router = APIRouter(prefix="/api/database", tags=["database"])

# --- Database management functions ---

def load_additional_data(file_path):
    """Load additional data from a JSON file."""
    if file_path.exists():
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            # If the file exists but is not valid JSON, return empty dict
            return {}
    return {}

def save_additional_data(data, file_path):
    """Save additional data to a JSON file."""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving data to {file_path}: {e}")
        return False

# --- API Endpoints ---

@router.post("/add-financial-entity")
async def add_financial_entity(entity_data: Dict[str, Any] = Body(...)):
    """
    Add a new financial entity to the database.
    Required fields:
    - name (str): The entity name/identifier
    - full_name (str): The full name of the entity
    - type (str): The type of entity (e.g., brokerage, media, investment_bank)
    - description (str): A description of the entity
    
    Returns the added entity data.
    """
    # Basic validation
    required_fields = ["name", "full_name", "type", "description"]
    for field in required_fields:
        if field not in entity_data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    # Load existing additional entities
    additional_entities = load_additional_data(ADDITIONAL_FINANCIAL_ENTITIES_FILE)
    
    # Add the new entity
    entity_name = entity_data["name"].strip().upper()
    entity_data["legitimate"] = True  # All manually added entities are considered legitimate
    additional_entities[entity_name] = entity_data
    
    # Save the updated data
    if not save_additional_data(additional_entities, ADDITIONAL_FINANCIAL_ENTITIES_FILE):
        raise HTTPException(status_code=500, detail="Failed to save financial entity data")
    
    return {"status": "success", "entity": entity_data}

@router.post("/add-company")
async def add_company(company_data: Dict[str, Any] = Body(...)):
    """
    Add a new company to the database.
    Required fields:
    - symbol (str): The stock symbol or ticker
    - full_name (str): The full name of the company
    - sector (str): The business sector
    - exchange (str): The stock exchange (e.g., NSE, NYSE, NASDAQ)
    
    Returns the added company data.
    """
    # Basic validation
    required_fields = ["symbol", "full_name", "sector", "exchange"]
    for field in required_fields:
        if field not in company_data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    # Load existing additional companies
    additional_companies = load_additional_data(ADDITIONAL_COMPANIES_FILE)
    
    # Add the new company
    symbol = company_data["symbol"].strip().upper()
    additional_companies[symbol] = company_data
    
    # Save the updated data
    if not save_additional_data(additional_companies, ADDITIONAL_COMPANIES_FILE):
        raise HTTPException(status_code=500, detail="Failed to save company data")
    
    return {"status": "success", "company": company_data}

@router.get("/list-financial-entities")
async def list_financial_entities():
    """
    List all additional financial entities in the database.
    Returns a list of financial entities.
    """
    additional_entities = load_additional_data(ADDITIONAL_FINANCIAL_ENTITIES_FILE)
    return {"financial_entities": additional_entities}

@router.get("/list-companies")
async def list_companies():
    """
    List all additional companies in the database.
    Returns a list of companies.
    """
    additional_companies = load_additional_data(ADDITIONAL_COMPANIES_FILE)
    return {"companies": additional_companies}

# --- Import this module in main.py and include the router ---
# Example:
# from database_management import router as db_router
# app.include_router(db_router)
