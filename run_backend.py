"""
Launcher script for the SEBI Hackathon backend
This runs main.py as part of the backend package correctly
"""

import os
import sys

# Ensure the parent directory is in the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import and run the main app from the backend
from backend.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
