from fastapi import APIRouter, HTTPException
from typing import Dict

from reddit_monitor import reddit_monitor

router = APIRouter(prefix="/api/reddit", tags=["Reddit Monitoring"]) 

@router.post("/init")
def reddit_init() -> Dict:
    try:
        ok = reddit_monitor.initialize()
        if not ok:
            raise HTTPException(status_code=500, detail="Failed to initialize Reddit API. Check env vars.")
        return {"status": "ok", "message": "Reddit initialized (read-only)."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-subreddit")
def add_subreddit(payload: Dict) -> Dict:
    try:
        # Ensure initialized
        if reddit_monitor.reddit is None:
            if not reddit_monitor.initialize():
                raise HTTPException(status_code=500, detail="Reddit API init failed. Configure credentials.")
        name = str(payload.get("subreddit", "")).strip()
        if not name:
            raise HTTPException(status_code=400, detail="subreddit is required")
        return reddit_monitor.add_subreddit(name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/remove-subreddit")
def remove_subreddit(payload: Dict) -> Dict:
    name = str(payload.get("subreddit", "")).strip()
    if not name:
        raise HTTPException(status_code=400, detail="subreddit is required")
    return reddit_monitor.remove_subreddit(name)

@router.get("/subreddits")
def list_subreddits():
    return reddit_monitor.get_monitored_subreddits()

@router.get("/alerts")
def reddit_alerts(limit: int = 20):
    return reddit_monitor.get_fraud_alerts(limit=limit)

@router.get("/stats")
def reddit_stats():
    return reddit_monitor.get_monitoring_stats()

@router.get("/status")
def reddit_status():
    return reddit_monitor.get_status()
