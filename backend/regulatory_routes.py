"""
Add a new endpoint for the rules-based regulatory verification
"""

from fastapi import APIRouter, Request
from regulatory_verification import verify_regulatory_compliance

router = APIRouter()

@router.post("/api/regulatory_verify")
async def regulatory_verify(request: Request):
    """
    Endpoint for rules-based regulatory compliance verification
    Not dependent on LLM
    """
    try:
        data = await request.json()
        message = data.get("message", "")
        company = data.get("company", None)
        
        if not message:
            return {"error": "No message provided."}
            
        # Use the rules-based verification system
        result = verify_regulatory_compliance(message, company)
        
        return result
        
    except Exception as e:
        print(f"[API ERROR] Error in regulatory verification: {str(e)}")
        return {"error": f"Error processing request: {str(e)}"}
