import discord
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
from dataclasses import dataclass
import re
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env if present
load_dotenv()

@dataclass
class DiscordMessage:
    id: str
    server_name: str
    channel_name: str
    content: str
    author: str
    created_at: datetime
    message_url: str
    is_fraud: bool = False
    risk_score: int = 0
    alert_level: str = "low"
    analysis_summary: str = ""

class DiscordMonitor:
    def __init__(self):
        self.client = None
        self.monitored_servers = {}  # server_id: server_name
        self.is_running = False
        self.recent_messages = []
        self.fraud_keywords = [
            "guaranteed returns", "risk-free", "double your money", "get rich quick",
            "secret strategy", "insider tip", "100% profit", "no loss", "sure shot",
            "guaranteed profit", "foolproof method", "instant money", "easy money",
            "quick cash", "investment opportunity", "limited time", "exclusive offer",
            "financial freedom", "passive income guaranteed", "trading bot", "auto profit",
            "pump and dump", "moon shot", "diamond hands", "to the moon"
        ]
        self.high_risk_patterns = [
            r"\d+% return",  # Percentage returns
            r"₹\s*\d+\s*lakh",  # Large amounts in lakhs
            r"\$\s*\d+k",  # Dollar amounts
            r"buy.*now",  # Urgency patterns
            r"limited.*time",  # Limited time offers
            r"dm.*me",  # Direct message requests
            r"contact.*\d+",  # Contact numbers
            r"crypto.*signal",  # Crypto signals
        ]
        
    async def initialize(self):
        """Initialize Discord bot connection"""
        try:
            bot_token = os.getenv('DISCORD_BOT_TOKEN')
            
            if not bot_token:
                logger.error("Discord bot token not found in environment variables")
                return False
            
            # Create Discord client with necessary intents
            intents = discord.Intents.default()
            intents.message_content = True
            intents.guilds = True
            
            self.client = discord.Client(intents=intents)
            
            @self.client.event
            async def on_ready():
                logger.info(f'Discord bot logged in as {self.client.user}')
                self.is_running = True
            
            @self.client.event
            async def on_message(message):
                await self.process_message(message)
            
            # Start the bot (non-blocking)
            asyncio.create_task(self.client.start(bot_token))
            
            # Wait a bit for connection
            await asyncio.sleep(2)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Discord bot: {e}")
            return False
    
    async def add_server(self, server_id: str) -> Dict:
        """Add a Discord server to monitoring"""
        try:
            if not self.client:
                return {"success": False, "error": "Discord client not initialized"}
            
            guild = self.client.get_guild(int(server_id))
            if not guild:
                return {"success": False, "error": "Server not found or bot not in server"}
            
            self.monitored_servers[server_id] = guild.name
            logger.info(f"Added Discord server {guild.name} to monitoring")
            
            return {
                "success": True,
                "server_name": guild.name,
                "message": f"Successfully added {guild.name} to monitoring"
            }
            
        except Exception as e:
            logger.error(f"Failed to add Discord server {server_id}: {e}")
            return {
                "success": False,
                "error": f"Failed to add server: {str(e)}"
            }
    
    def remove_server(self, server_id: str) -> Dict:
        """Remove a Discord server from monitoring"""
        if server_id in self.monitored_servers:
            server_name = self.monitored_servers.pop(server_id)
            return {"success": True, "message": f"Removed {server_name} from monitoring"}
        return {"success": False, "error": "Server not found in monitoring list"}
    
    def get_monitored_servers(self) -> List[Dict]:
        """Get list of monitored Discord servers"""
        return [
            {
                "server_id": server_id,
                "server_name": server_name,
                "added_date": datetime.now().isoformat(),
                "status": "active"
            }
            for server_id, server_name in self.monitored_servers.items()
        ]
    
    def analyze_fraud_risk(self, content: str) -> tuple[bool, int, str, str]:
        """Analyze message for fraud indicators"""
        text = content.lower()
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
        
        # Discord-specific risk factors
        if any(word in text for word in ["pump", "dump", "moon", "diamond hands"]):
            risk_score += 25
            fraud_indicators.append("Crypto manipulation language detected")
        
        if any(word in text for word in ["signal", "call", "entry", "target"]):
            risk_score += 20
            fraud_indicators.append("Trading signal detected")
        
        if "dm me" in text or "private message" in text:
            risk_score += 30
            fraud_indicators.append("Suspicious private communication request")
        
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
    
    async def process_message(self, message):
        """Process incoming Discord message"""
        if message.author == self.client.user:
            return  # Ignore bot's own messages
        
        if str(message.guild.id) not in self.monitored_servers:
            return  # Only process messages from monitored servers
        
        # Analyze for fraud
        is_fraud, risk_score, alert_level, analysis = self.analyze_fraud_risk(message.content)
        
        discord_message = DiscordMessage(
            id=str(message.id),
            server_name=message.guild.name,
            channel_name=message.channel.name,
            content=message.content,
            author=str(message.author),
            created_at=message.created_at,
            message_url=message.jump_url,
            is_fraud=is_fraud,
            risk_score=risk_score,
            alert_level=alert_level,
            analysis_summary=analysis
        )
        
        # Store recent messages (keep last 1000)
        self.recent_messages.append(discord_message)
        if len(self.recent_messages) > 1000:
            self.recent_messages = self.recent_messages[-1000:]
        
        # Log high-risk messages
        if risk_score >= 60:
            logger.warning(f"High-risk Discord message detected: {message.content[:100]}...")
    
    def get_recent_messages(self, limit: int = 50) -> List[DiscordMessage]:
        """Get recent messages from monitored servers"""
        return sorted(self.recent_messages, key=lambda x: x.created_at, reverse=True)[:limit]
    
    def get_fraud_alerts(self, limit: int = 20) -> List[Dict]:
        """Get recent fraud alerts from Discord"""
        fraud_messages = [msg for msg in self.recent_messages if msg.is_fraud]
        fraud_messages.sort(key=lambda x: x.created_at, reverse=True)
        
        return [
            {
                "alert_id": msg.id,
                "platform": "discord",
                "source": f"{msg.server_name}#{msg.channel_name}",
                "content": msg.content,
                "risk_score": msg.risk_score,
                "alert_level": msg.alert_level,
                "timestamp": msg.created_at.isoformat(),
                "url": msg.message_url,
                "analysis": msg.analysis_summary
            }
            for msg in fraud_messages[:limit]
        ]
    
    def get_monitoring_stats(self) -> Dict:
        """Get Discord monitoring statistics"""
        if not self.client or not self.is_running:
            return {
                "total_servers": 0,
                "weekly_messages": 0,
                "weekly_fraud_detected": 0,
                "weekly_high_risk": 0,
                "active": False
            }
        
        # Calculate weekly stats (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        weekly_messages = [
            msg for msg in self.recent_messages 
            if msg.created_at > week_ago
        ]
        
        return {
            "total_servers": len(self.monitored_servers),
            "weekly_messages": len(weekly_messages),
            "weekly_fraud_detected": len([m for m in weekly_messages if m.is_fraud]),
            "weekly_high_risk": len([m for m in weekly_messages if m.risk_score >= 80]),
            "active": self.is_running
        }
    
    def get_status(self) -> Dict:
        """Get Discord monitoring status"""
        return {
            "active": self.is_running,
            "monitored_servers": len(self.monitored_servers),
            "error": None if self.is_running else "Discord bot not running"
        }

# Global instance
discord_monitor = DiscordMonitor()
