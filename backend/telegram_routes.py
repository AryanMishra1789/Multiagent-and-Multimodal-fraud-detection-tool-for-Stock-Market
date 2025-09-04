#!/usr/bin/env python3
"""
Telegram Monitoring API Routes
Provides REST API endpoints for managing Telegram group monitoring
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import logging
from telegram_group_monitor import get_monitor_instance, init_monitor
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

router = APIRouter(prefix="/api/telegram", tags=["Telegram Monitoring"])
logger = logging.getLogger(__name__)

# Pydantic models for request/response
class AddGroupRequest(BaseModel):
    group_link: str

class AddGroupResponse(BaseModel):
    success: bool
    message: str
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    error: Optional[str] = None

class RemoveGroupRequest(BaseModel):
    group_id: int

class MonitoringStats(BaseModel):
    total_groups: int
    total_alerts: int
    weekly_messages: int
    weekly_fraud_detected: int
    weekly_high_risk: int
    fraud_detection_rate: float

class GroupInfo(BaseModel):
    group_id: int
    group_name: str
    group_username: Optional[str]
    added_date: str
    status: str

class FraudAlert(BaseModel):
    group_name: str
    message_text: str
    sender_username: str
    timestamp: str
    risk_score: float
    alert_level: str
    fraud_analysis: Dict

class MonitoredMessage(BaseModel):
    group_name: str
    message_text: str
    sender_username: str
    timestamp: str
    risk_score: float
    is_fraud: bool
    alert_level: str
    fraud_analysis: Dict
    group_id: int

class AuthRequest(BaseModel):
    code: str

class AuthResponse(BaseModel):
    success: bool
    message: str
    authenticated: bool = False

# Initialize monitor on startup
def initialize_telegram_monitor():
    """Initialize Telegram monitor with environment variables"""
    try:
        api_id = os.getenv("TELEGRAM_API_ID")
        api_hash = os.getenv("TELEGRAM_API_HASH")
        phone = os.getenv("TELEGRAM_PHONE")
        
        if not all([api_id, api_hash, phone]):
            logger.warning("Telegram credentials not found in environment variables")
            return None
        
        monitor = init_monitor(api_id, api_hash, phone)
        logger.info("Telegram monitor initialized")
        return monitor
    except Exception as e:
        logger.error(f"Failed to initialize Telegram monitor: {e}")
        return None

# Global monitor instance
monitor = initialize_telegram_monitor()

@router.get("/status")
async def get_monitoring_status():
    """Get the current status of Telegram monitoring"""
    global monitor
    if not monitor:
        return JSONResponse(
            status_code=503,
            content={
                "active": False,
                "error": "Telegram monitoring not configured. Please set TELEGRAM_API_ID, TELEGRAM_API_HASH, and TELEGRAM_PHONE in environment variables."
            }
        )
    
    try:
        # Check if client is authenticated
        is_authenticated = False
        if monitor.client and monitor.client.is_connected():
            is_authenticated = await monitor.client.is_user_authorized()
        
        stats = monitor.get_monitoring_stats()
        return {
            "active": monitor.running if hasattr(monitor, 'running') else False,
            "authenticated": is_authenticated,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/authenticate")
async def authenticate_telegram():
    """Send authentication code to phone"""
    global monitor
    if not monitor:
        raise HTTPException(status_code=503, detail="Telegram monitoring not configured")
    
    try:
        # Initialize client and request code
        if not monitor.client:
            await monitor.initialize()
        
        if not monitor.client.is_connected():
            await monitor.client.connect()
        
        if not await monitor.client.is_user_authorized():
            # This will send a code to the phone
            return {"success": True, "message": "Authentication code sent to your phone. Please check and submit the code."}
        else:
            return {"success": True, "message": "Already authenticated", "authenticated": True}
            
    except Exception as e:
        logger.error(f"Error during authentication: {e}")
        return {"success": False, "error": str(e)}

@router.post("/verify_code", response_model=AuthResponse)
async def verify_authentication_code(request: AuthRequest):
    """Verify the authentication code"""
    global monitor
    if not monitor:
        raise HTTPException(status_code=503, detail="Telegram monitoring not configured")
    
    try:
        if not monitor.client:
            await monitor.initialize()
        
        # Sign in with the code
        await monitor.client.sign_in(code=request.code)
        
        # Check if authentication was successful
        if await monitor.client.is_user_authorized():
            return AuthResponse(
                success=True,
                message="Successfully authenticated with Telegram",
                authenticated=True
            )
        else:
            return AuthResponse(
                success=False,
                message="Authentication failed. Please try again."
            )
            
    except Exception as e:
        logger.error(f"Error verifying authentication code: {e}")
        return AuthResponse(
            success=False,
            message=f"Failed to verify code: {str(e)}"
        )

@router.post("/add_group", response_model=AddGroupResponse)
async def add_group_to_monitoring(request: AddGroupRequest, background_tasks: BackgroundTasks):
    """Add a Telegram group to monitoring by invite link"""
    global monitor
    if not monitor:
        raise HTTPException(
            status_code=503, 
            detail="Telegram monitoring not configured"
        )
    
    try:
        # Validate group link format
        link = request.group_link.strip()
        if not (link.startswith('@') or 't.me/' in link or 'telegram.me/' in link):
            return AddGroupResponse(
                success=False,
                error="Invalid group link format. Use @username or t.me/... format"
            )
        
        # Initialize client if not already done
        if not monitor.client:
            await monitor.initialize()
        
        # Check if authenticated
        if not await monitor.client.is_user_authorized():
            return AddGroupResponse(
                success=False,
                error="Telegram client not authenticated. Please authenticate first using the /authenticate endpoint."
            )
        
        # Add group
        result = await monitor.add_group_by_link(link)
        
        if result["success"]:
            return AddGroupResponse(
                success=True,
                message=result["message"],
                group_id=result["group_id"],
                group_name=result["group_name"]
            )
        else:
            return AddGroupResponse(
                success=False,
                error=result["error"]
            )
    
    except Exception as e:
        logger.error(f"Error adding group {request.group_link}: {e}")
        return AddGroupResponse(
            success=False,
            error=f"Failed to add group: {str(e)}"
        )

@router.post("/remove_group")
async def remove_group_from_monitoring(request: RemoveGroupRequest):
    """Remove a group from monitoring"""
    global monitor
    if not monitor:
        raise HTTPException(status_code=503, detail="Telegram monitoring not configured")
    
    try:
        result = await monitor.remove_group(request.group_id)
        return result
    except Exception as e:
        logger.error(f"Error removing group {request.group_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/groups", response_model=List[GroupInfo])
async def get_monitored_groups():
    """Get list of all monitored groups"""
    global monitor
    if not monitor:
        raise HTTPException(status_code=503, detail="Telegram monitoring not configured")
    
    try:
        groups = monitor.get_monitored_groups()
        return [GroupInfo(**group) for group in groups]
    except Exception as e:
        logger.error(f"Error getting monitored groups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts", response_model=List[FraudAlert])
async def get_recent_alerts(limit: int = 50):
    """Get recent fraud alerts from monitored groups"""
    global monitor
    if not monitor:
        raise HTTPException(status_code=503, detail="Telegram monitoring not configured")
    
    try:
        alerts = monitor.get_recent_alerts(limit)
        return [FraudAlert(**alert) for alert in alerts]
    except Exception as e:
        logger.error(f"Error getting recent alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages", response_model=List[MonitoredMessage])
async def get_recent_messages(limit: int = 100, group_id: Optional[int] = None):
    """Get recent monitored messages (all messages, not just fraud alerts)"""
    global monitor
    if not monitor:
        raise HTTPException(status_code=503, detail="Telegram monitoring not configured")
    
    try:
        messages = monitor.get_recent_messages(limit, group_id)
        return [MonitoredMessage(**message) for message in messages]
    except Exception as e:
        logger.error(f"Error getting recent messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=MonitoringStats)
async def get_monitoring_statistics():
    """Get monitoring statistics"""
    global monitor
    if not monitor:
        raise HTTPException(status_code=503, detail="Telegram monitoring not configured")
    
    try:
        stats = monitor.get_monitoring_stats()
        return MonitoringStats(**stats)
    except Exception as e:
        logger.error(f"Error getting monitoring stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start")
async def start_monitoring(background_tasks: BackgroundTasks):
    """Start Telegram monitoring in background"""
    global monitor
    if not monitor:
        raise HTTPException(status_code=503, detail="Telegram monitoring not configured")
    
    try:
        if hasattr(monitor, 'running') and monitor.running:
            return {"message": "Monitoring is already running"}
        
        # Start monitoring in background task
        background_tasks.add_task(monitor.start_monitoring)
        
        return {"message": "Telegram monitoring started"}
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
async def stop_monitoring():
    """Stop Telegram monitoring"""
    global monitor
    if not monitor:
        raise HTTPException(status_code=503, detail="Telegram monitoring not configured")
    
    try:
        await monitor.stop_monitoring()
        return {"message": "Telegram monitoring stopped"}
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test_analysis")
async def test_fraud_analysis(message: str):
    """Test fraud analysis on a sample message"""
    global monitor
    if not monitor:
        raise HTTPException(status_code=503, detail="Telegram monitoring not configured")
    
    try:
        # Test the fraud analysis pipeline
        analysis = await monitor._analyze_message_async(message)
        risk_score = monitor._calculate_risk_score(analysis)
        alert_level = monitor._get_alert_level(risk_score)
        
        return {
            "message": message,
            "fraud_analysis": analysis,
            "risk_score": risk_score,
            "alert_level": alert_level
        }
    except Exception as e:
        logger.error(f"Error testing analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for Telegram monitoring service"""
    global monitor
    
    status = {
        "service": "telegram_monitoring",
        "status": "healthy" if monitor else "unavailable",
        "timestamp": str(asyncio.get_event_loop().time())
    }
    
    if monitor:
        try:
            stats = monitor.get_monitoring_stats()
            status["groups_monitored"] = stats["total_groups"]
            status["total_alerts"] = stats["total_alerts"]
        except Exception as e:
            status["status"] = "degraded"
            status["error"] = str(e)
    
    return status
