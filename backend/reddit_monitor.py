import praw
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
from dataclasses import dataclass
import json
import re
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env if present
load_dotenv()

@dataclass
class RedditPost:
    id: str
    subreddit: str
    title: str
    content: str
    author: str
    created_utc: float
    score: int
    num_comments: int
    url: str
    is_fraud: bool = False
    risk_score: int = 0
    alert_level: str = "low"
    analysis_summary: str = ""

class RedditMonitor:
    def __init__(self):
        self.reddit = None
        self.monitored_subreddits = set()
        self.fraud_keywords = [
            "guaranteed returns", "risk-free", "double your money", "get rich quick",
            "secret strategy", "insider tip", "100% profit", "no loss", "sure shot",
            "guaranteed profit", "foolproof method", "instant money", "easy money",
            "quick cash", "investment opportunity", "limited time", "exclusive offer",
            "financial freedom", "passive income guaranteed", "trading bot", "auto profit"
        ]
        self.high_risk_patterns = [
            r"\d+% return",  # Percentage returns
            r"₹\s*\d+\s*lakh",  # Large amounts in lakhs
            r"\$\s*\d+k",  # Dollar amounts
            r"whatsapp.*group",  # WhatsApp group invites
            r"telegram.*channel",  # Telegram channel invites
            r"dm.*me",  # Direct message requests
            r"contact.*\d+",  # Contact numbers
        ]
        
    def initialize(self):
        """Initialize Reddit API connection"""
        try:
            client_id = os.getenv('REDDIT_CLIENT_ID')
            client_secret = os.getenv('REDDIT_CLIENT_SECRET')
            user_agent = os.getenv('REDDIT_USER_AGENT', 'SEBI_Fraud_Monitor_v1.0')
            
            if not client_id or not client_secret:
                logger.error("Reddit API credentials not found in environment variables")
                return False
                
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            # Ensure read-only mode for app-only credentials
            self.reddit.read_only = True
            
            # Test connection (read-only) by fetching a single post from r/all
            _ = next(self.reddit.subreddit("all").hot(limit=1), None)
            logger.info("Reddit API initialized successfully (read-only)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Reddit API: {e}")
            return False
    
    def add_subreddit(self, subreddit_name: str) -> Dict:
        """Add a subreddit to monitoring"""
        try:
            # Remove 'r/' prefix if present
            subreddit_name = subreddit_name.replace('r/', '')
            
            # Check if subreddit exists
            subreddit = self.reddit.subreddit(subreddit_name)
            subreddit.id  # This will raise an exception if subreddit doesn't exist
            
            self.monitored_subreddits.add(subreddit_name)
            logger.info(f"Added subreddit r/{subreddit_name} to monitoring")
            
            return {
                "success": True,
                "subreddit_name": f"r/{subreddit_name}",
                "message": f"Successfully added r/{subreddit_name} to monitoring"
            }
            
        except Exception as e:
            logger.error(f"Failed to add subreddit {subreddit_name}: {e}")
            return {
                "success": False,
                "error": f"Failed to add subreddit: {str(e)}"
            }
    
    def remove_subreddit(self, subreddit_name: str) -> Dict:
        """Remove a subreddit from monitoring"""
        subreddit_name = subreddit_name.replace('r/', '')
        if subreddit_name in self.monitored_subreddits:
            self.monitored_subreddits.remove(subreddit_name)
            return {"success": True, "message": f"Removed r/{subreddit_name} from monitoring"}
        return {"success": False, "error": "Subreddit not found in monitoring list"}
    
    def get_monitored_subreddits(self) -> List[Dict]:
        """Get list of monitored subreddits"""
        return [
            {
                "subreddit_id": name,
                "subreddit_name": f"r/{name}",
                "added_date": datetime.now().isoformat(),
                "status": "active"
            }
            for name in self.monitored_subreddits
        ]
    
    def analyze_fraud_risk(self, title: str, content: str) -> tuple[bool, int, str, str]:
        """Analyze post for fraud indicators"""
        text = f"{title} {content}".lower()
        risk_score = 0
        fraud_indicators = []
        
        # Check for fraud keywords
        for keyword in self.fraud_keywords:
            if keyword in text:
                risk_score += 15
                fraud_indicators.append(f"Suspicious keyword: '{keyword}'")
        
        # Check for high-risk patterns
        for pattern in self.high_risk_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                risk_score += 20
                fraud_indicators.append(f"High-risk pattern: {matches[0]}")
        
        # Additional risk factors
        if any(word in text for word in ["guaranteed", "risk-free", "sure shot"]):
            risk_score += 25
            fraud_indicators.append("Unrealistic guarantees detected")
        
        if any(word in text for word in ["whatsapp", "telegram", "dm me", "contact"]):
            risk_score += 20
            fraud_indicators.append("Suspicious contact methods")
        
        # Cap risk score at 100
        risk_score = min(risk_score, 100)
        
        # Determine alert level and fraud status
        is_fraud = risk_score >= 60
        if risk_score >= 80:
            alert_level = "critical"
        elif risk_score >= 60:
            alert_level = "high"
        elif risk_score >= 40:
            alert_level = "medium"
        else:
            alert_level = "low"
        
        analysis_summary = "; ".join(fraud_indicators) if fraud_indicators else "No significant fraud indicators detected"
        
        return is_fraud, risk_score, alert_level, analysis_summary
    
    def get_recent_posts(self, limit: int = 50) -> List[RedditPost]:
        """Get recent posts from monitored subreddits"""
        if not self.reddit or not self.monitored_subreddits:
            return []
        
        posts = []
        
        try:
            for subreddit_name in self.monitored_subreddits:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Get recent posts (hot, new, rising)
                for submission in subreddit.hot(limit=limit//len(self.monitored_subreddits) or 10):
                    # Analyze for fraud
                    is_fraud, risk_score, alert_level, analysis = self.analyze_fraud_risk(
                        submission.title, 
                        submission.selftext or ""
                    )
                    
                    post = RedditPost(
                        id=submission.id,
                        subreddit=f"r/{subreddit_name}",
                        title=submission.title,
                        content=submission.selftext or "",
                        author=str(submission.author) if submission.author else "[deleted]",
                        created_utc=submission.created_utc,
                        score=submission.score,
                        num_comments=submission.num_comments,
                        url=f"https://reddit.com{submission.permalink}",
                        is_fraud=is_fraud,
                        risk_score=risk_score,
                        alert_level=alert_level,
                        analysis_summary=analysis
                    )
                    
                    posts.append(post)
            
            # Sort by creation time (newest first)
            posts.sort(key=lambda x: x.created_utc, reverse=True)
            return posts[:limit]
            
        except Exception as e:
            logger.error(f"Error fetching Reddit posts: {e}")
            return []
    
    def get_fraud_alerts(self, limit: int = 20) -> List[Dict]:
        """Get recent fraud alerts from Reddit"""
        posts = self.get_recent_posts(limit * 2)  # Get more posts to filter for fraud
        fraud_posts = [post for post in posts if post.is_fraud][:limit]
        
        return [
            {
                "alert_id": post.id,
                "platform": "reddit",
                "source": post.subreddit,
                "content": post.title,
                "risk_score": post.risk_score,
                "alert_level": post.alert_level,
                "timestamp": datetime.fromtimestamp(post.created_utc).isoformat(),
                "url": post.url,
                "analysis": post.analysis_summary
            }
            for post in fraud_posts
        ]
    
    def get_monitoring_stats(self) -> Dict:
        """Get Reddit monitoring statistics"""
        if not self.reddit or not self.monitored_subreddits:
            return {
                "total_subreddits": 0,
                "weekly_posts": 0,
                "weekly_fraud_detected": 0,
                "weekly_high_risk": 0,
                "active": False
            }
        
        # Get recent posts for stats
        recent_posts = self.get_recent_posts(100)
        
        # Calculate weekly stats (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        weekly_posts = [
            post for post in recent_posts 
            if datetime.fromtimestamp(post.created_utc) > week_ago
        ]
        
        return {
            "total_subreddits": len(self.monitored_subreddits),
            "weekly_posts": len(weekly_posts),
            "weekly_fraud_detected": len([p for p in weekly_posts if p.is_fraud]),
            "weekly_high_risk": len([p for p in weekly_posts if p.risk_score >= 80]),
            "active": True
        }
    
    def get_status(self) -> Dict:
        """Get Reddit monitoring status"""
        return {
            "active": self.reddit is not None,
            "monitored_subreddits": len(self.monitored_subreddits),
            "error": None if self.reddit else "Reddit API not initialized"
        }

# Global instance
reddit_monitor = RedditMonitor()
