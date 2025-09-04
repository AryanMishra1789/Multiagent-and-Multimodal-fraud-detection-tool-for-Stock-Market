from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Union
import asyncio
from datetime import datetime

from reddit_monitor import reddit_monitor
from discord_monitor import discord_monitor
from telegram_routes import monitor as telegram_monitor  # Use existing Telegram monitor instance

router = APIRouter(prefix="/api/social", tags=["Multi-Platform Social Media Monitoring"])

# Request models
class AddPlatformGroupRequest(BaseModel):
    platform: str  # "reddit", "discord", "telegram"
    group_identifier: str  # subreddit name, server ID, or telegram group

class RemovePlatformGroupRequest(BaseModel):
    platform: str
    group_identifier: str

# Initialize all platforms
@router.on_event("startup")
async def startup_event():
    """Initialize all social media monitoring platforms"""
    # Initialize Reddit
    reddit_monitor.initialize()
    
    # Initialize Discord
    await discord_monitor.initialize()
    
    # Add default subreddits for demonstration
    default_subreddits = [
        "investing", "IndiaInvestments", "SecurityAnalysis", 
        "ValueInvesting", "StockMarket", "cryptocurrency"
    ]
    for subreddit in default_subreddits:
        reddit_monitor.add_subreddit(subreddit)

@router.get("/status")
async def get_multi_platform_status():
    """Get status of all social media monitoring platforms"""
    return {
        "platforms": {
            "telegram": (
                await get_telegram_status_safe()
            ),
            "reddit": reddit_monitor.get_status(),
            "discord": discord_monitor.get_status()
        },
        "total_active_platforms": sum([
            1 for status in [
                (await get_telegram_status_safe()).get("active", False),
                reddit_monitor.get_status()["active"],
                discord_monitor.get_status()["active"]
            ] if status
        ])
    }

async def get_telegram_status_safe():
    try:
        if telegram_monitor:
            # emulate /api/telegram/status response schema minimally
            is_authenticated = False
            if telegram_monitor.client:
                try:
                    if telegram_monitor.client.is_connected():
                        is_authenticated = await telegram_monitor.client.is_user_authorized()
                except Exception:
                    pass
            stats = telegram_monitor.get_monitoring_stats()
            return {
                "active": getattr(telegram_monitor, 'running', False),
                "authenticated": is_authenticated,
                "stats": stats,
            }
    except Exception:
        pass
    return {"active": False, "error": "Not configured"}

@router.get("/stats")
async def get_multi_platform_stats():
    """Get combined statistics from all platforms"""
    telegram_stats = {}
    try:
        if telegram_monitor:
            telegram_stats = telegram_monitor.get_monitoring_stats()
    except Exception:
        telegram_stats = {"total_groups": 0, "weekly_messages": 0, "weekly_fraud_detected": 0, "weekly_high_risk": 0}
    
    reddit_stats = reddit_monitor.get_monitoring_stats()
    discord_stats = discord_monitor.get_monitoring_stats()
    
    return {
        "combined": {
            "total_groups": (
                telegram_stats.get("total_groups", 0) + 
                reddit_stats.get("total_subreddits", 0) + 
                discord_stats.get("total_servers", 0)
            ),
            "weekly_messages": (
                telegram_stats.get("weekly_messages", 0) + 
                reddit_stats.get("weekly_posts", 0) + 
                discord_stats.get("weekly_messages", 0)
            ),
            "weekly_fraud_detected": (
                telegram_stats.get("weekly_fraud_detected", 0) + 
                reddit_stats.get("weekly_fraud_detected", 0) + 
                discord_stats.get("weekly_fraud_detected", 0)
            ),
            "weekly_high_risk": (
                telegram_stats.get("weekly_high_risk", 0) + 
                reddit_stats.get("weekly_high_risk", 0) + 
                discord_stats.get("weekly_high_risk", 0)
            )
        },
        "by_platform": {
            "telegram": telegram_stats,
            "reddit": reddit_stats,
            "discord": discord_stats
        }
    }

@router.get("/groups")
async def get_all_monitored_groups():
    """Get all monitored groups across all platforms"""
    groups = []
    
    # Telegram groups
    try:
        if telegram_monitor:
            telegram_groups = telegram_monitor.get_monitored_groups()
            for group in telegram_groups:
                groups.append({
                    "platform": "telegram",
                    "group_id": group.get("group_id"),
                    "group_name": group.get("group_name"),
                    "added_date": group.get("added_date"),
                    "status": group.get("status", "active")
                })
    except Exception as e:
        print(f"Error getting Telegram groups: {e}", exc_info=True)
    
    # Reddit subreddits
    reddit_subreddits = reddit_monitor.get_monitored_subreddits()
    for subreddit in reddit_subreddits:
        groups.append({
            "platform": "reddit",
            "group_id": subreddit["subreddit_id"],
            "group_name": subreddit["subreddit_name"],
            "added_date": subreddit["added_date"],
            "status": subreddit["status"]
        })
    
    # Discord servers
    discord_servers = discord_monitor.get_monitored_servers()
    for server in discord_servers:
        groups.append({
            "platform": "discord",
            "group_id": server["server_id"],
            "group_name": server["server_name"],
            "added_date": server["added_date"],
            "status": server["status"]
        })
    
    return {"groups": groups, "total_count": len(groups)}

@router.post("/add_group")
async def add_group_to_monitoring(request: AddPlatformGroupRequest):
    """Add a group/channel to monitoring for specified platform"""
    platform = request.platform.lower()
    
    if platform == "reddit":
        result = reddit_monitor.add_subreddit(request.group_identifier)
        return result
    
    elif platform == "discord":
        result = await discord_monitor.add_server(request.group_identifier)
        return result
    
    elif platform == "telegram":
        try:
            if telegram_monitor:
                print(f"Attempting to add Telegram group: {request.group_identifier}")
                result = await telegram_monitor.add_group_by_link(request.group_identifier)
                print(f"Telegram monitor response: {result}")
                # Normalize response to current schema
                if result.get("success"):
                    print(f"Successfully added group. Result: {result}")
                    return result
                error_msg = result.get("error", "Failed to add Telegram group")
                print(f"Error adding group: {error_msg}")
                return {"success": False, "error": error_msg}
            else:
                error_msg = "Telegram monitoring not configured"
                print(error_msg)
                return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Failed to add Telegram group: {e}"
            print(error_msg, exc_info=True)
            return {"success": False, "error": error_msg}
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")

from fastapi import Body

@router.delete("/remove_group")
async def remove_group_from_monitoring(
    platform: Optional[str] = None,
    group_identifier: Optional[str] = None,
    request: Optional[dict] = Body(None)
):
    """Remove a group/channel from monitoring
    
    Supports both URL parameters and request body:
    - URL params: platform, group_identifier
    - Request body: { "platform": "...", "group_identifier": "..." } or { "platform": "...", "groupIdentifier": "..." }
    """
    # Get values from URL params or request body
    if request:
        # Handle both snake_case and camelCase in request body
        platform = platform or request.get('platform')
        group_identifier = group_identifier or request.get('group_identifier') or request.get('groupIdentifier')
    
    if platform:
        platform = platform.lower()
    else:
        raise HTTPException(status_code=400, detail="Platform is required")
    
    if not platform or not group_identifier:
        raise HTTPException(status_code=400, detail="Both platform and group_identifier are required")
    
    if platform == "reddit":
        result = reddit_monitor.remove_subreddit(group_identifier)
        return result
    
    elif platform == "discord":
        result = discord_monitor.remove_server(group_identifier)
        return result
    
    elif platform == "telegram":
        try:
            if telegram_monitor:
                # group_identifier could be group id or link; try to parse to int
                gid = None
                try:
                    gid = int(group_identifier)
                except Exception:
                    # If not an int, try to resolve via list
                    for g in telegram_monitor.get_monitored_groups():
                        if group_identifier in [str(g.get("group_id")), g.get("group_name"), g.get("group_username", "")]:
                            gid = g.get("group_id")
                            break
                if gid is None:
                    return {"success": False, "error": "Telegram group not found"}
                result = await telegram_monitor.remove_group(gid)
                return result
            else:
                return {"success": False, "error": "Telegram monitoring not configured"}
        except Exception as e:
            return {"success": False, "error": f"Failed to remove Telegram group: {e}"}
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")

@router.get("/messages")
async def get_recent_messages(limit: int = 100, platform: Optional[str] = None):
    """Get recent messages from all platforms or specific platform"""
    all_messages = []
    
    if not platform or platform.lower() == "reddit":
        reddit_posts = reddit_monitor.get_recent_posts(limit)
        for post in reddit_posts:
            # Determine status based on fraud analysis
            if post.is_fraud:
                status = "Fraud"
            elif post.risk_score >= 40:
                status = "Suspicious"
            else:
                status = "Legitimate"
            
            all_messages.append({
                "platform": "reddit",
                "message_id": post.id,
                "source": post.subreddit,
                "content": post.title,
                "full_content": post.content,
                "author": post.author,
                "timestamp": datetime.fromtimestamp(post.created_utc).isoformat(),
                "url": post.url,
                "is_fraud": post.is_fraud,
                "risk_score": post.risk_score,
                "alert_level": post.alert_level,
                "analysis_summary": post.analysis_summary,
                "status": status,
                "engagement": {"score": post.score, "comments": post.num_comments}
            })
    
    if not platform or platform.lower() == "discord":
        discord_messages = discord_monitor.get_recent_messages(limit)
        for msg in discord_messages:
            all_messages.append({
                "platform": "discord",
                "message_id": msg.id,
                "source": f"{msg.server_name}#{msg.channel_name}",
                "content": msg.content,
                "full_content": msg.content,
                "author": msg.author,
                "timestamp": msg.created_at.isoformat(),
                "url": msg.message_url,
                "is_fraud": msg.is_fraud,
                "risk_score": msg.risk_score,
                "alert_level": msg.alert_level,
                "analysis_summary": msg.analysis_summary,
                "engagement": {}
            })
    
    if not platform or platform.lower() == "telegram":
        try:
            if telegram_monitor:
                telegram_messages = telegram_monitor.get_recent_messages(limit)
                for msg in telegram_messages:
                    # Determine status based on fraud analysis (same logic as Reddit)
                    if msg.get("is_fraud", False):
                        status = "Fraud"
                    elif msg.get("risk_score", 0) >= 40:
                        status = "Suspicious"
                    else:
                        status = "Legitimate"
                    
                    all_messages.append({
                        "platform": "telegram",
                        "message_id": f"{msg.get('group_id', '')}-{msg.get('timestamp', '')}",
                        "source": msg.get("group_name", "Unknown"),
                        "content": msg.get("message_text", ""),
                        "full_content": msg.get("message_text", ""),
                        "author": msg.get("sender_username", "Unknown"),
                        "timestamp": msg.get("timestamp", ""),
                        "url": f"https://t.me/{msg.get('group_name', '')}",
                        "is_fraud": msg.get("is_fraud", False),
                        "risk_score": msg.get("risk_score", 0),
                        "alert_level": msg.get("alert_level", "low"),
                        "analysis_summary": msg.get("analysis_summary", ""),
                        "status": status,
                        "engagement": {}
                    })
        except Exception:
            pass
    
    # Sort by timestamp (newest first)
    all_messages.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return {"messages": all_messages[:limit], "total_count": len(all_messages)}

@router.get("/alerts")
async def get_fraud_alerts(limit: int = 50, platform: Optional[str] = None):
    """Get fraud alerts from all platforms or specific platform"""
    all_alerts = []
    
    if not platform or platform.lower() == "reddit":
        reddit_alerts = reddit_monitor.get_fraud_alerts(limit)
        all_alerts.extend(reddit_alerts)
    
    if not platform or platform.lower() == "discord":
        discord_alerts = discord_monitor.get_fraud_alerts(limit)
        all_alerts.extend(discord_alerts)
    
    if not platform or platform.lower() == "telegram":
        try:
            if telegram_monitor:
                telegram_alerts = telegram_monitor.get_recent_alerts(limit)
                # Convert telegram alerts to standard format
                for alert in telegram_alerts:
                    all_alerts.append({
                        "alert_id": alert.get("alert_id"),
                        "platform": "telegram",
                        "source": alert.get("group_name"),
                        "content": alert.get("message_text"),
                        "risk_score": alert.get("risk_score"),
                        "alert_level": alert.get("alert_level"),
                        "timestamp": alert.get("timestamp"),
                        "url": f"https://t.me/{alert.get('group_name', '')}",
                        "analysis": alert.get("reason", "")
                    })
        except Exception:
            pass
    
    # Sort by timestamp (newest first)
    all_alerts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return {"alerts": all_alerts[:limit], "total_count": len(all_alerts)}

@router.get("/platforms")
async def get_supported_platforms():
    """Get list of supported social media platforms"""
    return {
        "platforms": [
            {
                "name": "telegram",
                "display_name": "Telegram",
                "description": "Monitor Telegram groups and channels",
                "free": True,
                "requires_setup": True,
                "setup_requirements": ["TELEGRAM_API_ID", "TELEGRAM_API_HASH", "TELEGRAM_PHONE"]
            },
            {
                "name": "reddit",
                "display_name": "Reddit",
                "description": "Monitor Reddit subreddits",
                "free": True,
                "requires_setup": True,
                "setup_requirements": ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"]
            },
            {
                "name": "discord",
                "display_name": "Discord",
                "description": "Monitor Discord servers and channels",
                "free": True,
                "requires_setup": True,
                "setup_requirements": ["DISCORD_BOT_TOKEN"]
            }
        ]
    }
