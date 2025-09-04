from fastapi import APIRouter, HTTPException
from typing import Dict
import asyncio

from discord_monitor import discord_monitor

router = APIRouter()

@router.post("/api/discord/init")
async def discord_init() -> Dict:
    try:
        ok = await discord_monitor.initialize()
        if not ok:
            raise HTTPException(status_code=500, detail="Failed to initialize Discord bot. Check DISCORD_BOT_TOKEN.")
        return {"status": "ok", "message": "Discord bot initializing."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/discord/add-server")
async def discord_add_server(payload: Dict) -> Dict:
    try:
        server_id = str(payload.get("server_id", "")).strip()
        if not server_id:
            raise HTTPException(status_code=400, detail="server_id is required")
        if not discord_monitor.client:
            # Ensure initialized first
            ok = await discord_monitor.initialize()
            if not ok:
                raise HTTPException(status_code=500, detail="Failed to initialize Discord bot. Check DISCORD_BOT_TOKEN.")
        result = await discord_monitor.add_server(server_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/discord/status")
async def discord_status() -> Dict:
    return discord_monitor.get_status()

@router.get("/api/discord/alerts")
async def discord_alerts(limit: int = 20):
    return discord_monitor.get_fraud_alerts(limit=limit)

@router.get("/api/discord/stats")
async def discord_stats() -> Dict:
    return discord_monitor.get_monitoring_stats()
