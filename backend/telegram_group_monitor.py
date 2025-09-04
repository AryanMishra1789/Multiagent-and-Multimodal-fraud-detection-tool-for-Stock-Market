#!/usr/bin/env python3
"""
Telegram Group Monitoring System for SEBI Fraud Detection
Monitors Telegram groups for suspicious investment messages and integrates with existing fraud detection pipeline
"""

import os
import asyncio
import logging
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from telethon import TelegramClient, events
from telethon.tl.types import Channel, Chat
from hybrid_verification_agent import hybrid_verify_message
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GroupAlert:
    group_id: int
    group_name: str
    message_id: int
    message_text: str
    sender_id: int
    sender_username: str
    timestamp: datetime
    fraud_analysis: Dict
    risk_score: float
    alert_level: str  # LOW, MEDIUM, HIGH, CRITICAL

class TelegramGroupMonitor:
    def __init__(self, api_id: str, api_hash: str, phone: str, db_path: str = "telegram_monitor.db"):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.db_path = db_path
        self.client = None
        self.monitored_groups = set()
        self.alert_callbacks = []
        self.running = False
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for storing alerts and group info"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitored_groups (
                group_id INTEGER PRIMARY KEY,
                group_name TEXT NOT NULL,
                group_username TEXT,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fraud_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                group_name TEXT,
                message_id INTEGER,
                message_text TEXT,
                sender_id INTEGER,
                sender_username TEXT,
                timestamp TIMESTAMP,
                fraud_analysis TEXT,
                risk_score REAL,
                alert_level TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES monitored_groups (group_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS message_stats (
                date DATE PRIMARY KEY,
                total_messages INTEGER DEFAULT 0,
                fraud_detected INTEGER DEFAULT 0,
                high_risk_alerts INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitored_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                group_name TEXT,
                message_id INTEGER,
                message_text TEXT,
                sender_id INTEGER,
                sender_username TEXT,
                timestamp TIMESTAMP,
                fraud_analysis TEXT,
                risk_score REAL,
                is_fraud BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES monitored_groups (group_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def initialize(self):
        """Initialize Telegram client"""
        try:
            self.client = TelegramClient('telegram_monitor_session', self.api_id, self.api_hash)
            await self.client.start(phone=self.phone)
            logger.info("Telegram client initialized successfully")
            
            # Load monitored groups from database
            await self._load_monitored_groups()
            
            # Register message handler
            @self.client.on(events.NewMessage)
            async def message_handler(event):
                await self._handle_new_message(event)
            
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Telegram client: {e}")
            return False
    
    async def _load_monitored_groups(self):
        """Load monitored groups from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT group_id FROM monitored_groups WHERE status = 'active'")
        
        for (group_id,) in cursor.fetchall():
            self.monitored_groups.add(group_id)
        
        conn.close()
        logger.info(f"Loaded {len(self.monitored_groups)} monitored groups")
    
    async def add_group_by_link(self, group_link: str) -> Dict:
        """Add a group/channel to monitoring by invite link or username"""
        try:
            # Support multiple link formats
            if group_link.startswith('@'):
                entity = await self.client.get_entity(group_link)
            elif 't.me/' in group_link or 'telegram.me/' in group_link:
                entity = await self.client.get_entity(group_link)
            else:
                return {"success": False, "error": "Invalid group/channel link format. Use @username or t.me/... format"}
            
            # Check if it's a group, channel, or supergroup
            if not isinstance(entity, (Channel, Chat)):
                return {"success": False, "error": "Link does not point to a group or channel"}
            
            # Determine entity type for better user feedback
            entity_type = "Channel" if getattr(entity, 'broadcast', False) else "Group"
            
            group_id = entity.id
            group_name = entity.title
            group_username = getattr(entity, 'username', None)
            
            # Add to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO monitored_groups (group_id, group_name, group_username)
                VALUES (?, ?, ?)
            ''', (group_id, group_name, group_username))
            conn.commit()
            conn.close()
            
            # Add to monitoring set
            self.monitored_groups.add(group_id)
            
            logger.info(f"Added {entity_type.lower()} to monitoring: {group_name} (ID: {group_id})")
            return {
                "success": True, 
                "group_id": group_id,
                "group_name": group_name,
                "entity_type": entity_type,
                "message": f"Successfully added {entity_type.lower()} '{group_name}' to monitoring"
            }
            
        except Exception as e:
            logger.error(f"Failed to add group {group_link}: {e}")
            return {"success": False, "error": str(e)}
    
    async def remove_group(self, group_id: int) -> Dict:
        """Remove a group from monitoring"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE monitored_groups SET status = 'inactive' WHERE group_id = ?", (group_id,))
            conn.commit()
            conn.close()
            
            self.monitored_groups.discard(group_id)
            
            logger.info(f"Removed group {group_id} from monitoring")
            return {"success": True, "message": "Group removed from monitoring"}
            
        except Exception as e:
            logger.error(f"Failed to remove group {group_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _handle_new_message(self, event):
        """Handle new messages from monitored groups"""
        try:
            # Check if message is from a monitored group
            chat_id = event.chat_id
            if chat_id not in self.monitored_groups:
                return
            
            message = event.message
            if not message.text:
                return  # Skip non-text messages
            
            # Get group and sender info
            chat = await event.get_chat()
            sender = await event.get_sender()
            
            group_name = getattr(chat, 'title', 'Unknown Group')
            sender_username = getattr(sender, 'username', 'Unknown')
            sender_id = getattr(sender, 'id', 0)
            
            # Analyze message for fraud using existing pipeline
            fraud_analysis = await self._analyze_message_async(message.text)
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(fraud_analysis)
            alert_level = self._get_alert_level(risk_score)
            is_fraud = risk_score > 30
            
            # Store ALL monitored messages
            await self._store_message(
                group_id=chat_id,
                group_name=group_name,
                message_id=message.id,
                message_text=message.text,
                sender_id=sender_id,
                sender_username=sender_username,
                timestamp=message.date,
                fraud_analysis=fraud_analysis,
                risk_score=risk_score,
                is_fraud=is_fraud
            )
            
            # Store alert if significant risk detected
            if risk_score > 30:  # Only store medium+ risk alerts
                alert = GroupAlert(
                    group_id=chat_id,
                    group_name=group_name,
                    message_id=message.id,
                    message_text=message.text,
                    sender_id=sender_id,
                    sender_username=sender_username,
                    timestamp=message.date,
                    fraud_analysis=fraud_analysis,
                    risk_score=risk_score,
                    alert_level=alert_level
                )
                
                await self._store_alert(alert)
                await self._notify_alert_callbacks(alert)
                
                logger.warning(f"FRAUD ALERT: {alert_level} risk in {group_name}: {message.text[:100]}...")
            
            # Update daily stats
            await self._update_daily_stats(risk_score > 30, risk_score > 70)
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def _analyze_message_async(self, message_text: str) -> Dict:
        """Analyze message using existing fraud detection pipeline (async wrapper)"""
        try:
            # Run the hybrid verification in a separate thread to avoid blocking
            loop = asyncio.get_event_loop()
            fraud_analysis = await loop.run_in_executor(
                None, hybrid_verify_message, message_text
            )
            return fraud_analysis
        except Exception as e:
            logger.error(f"Error analyzing message: {e}")
            return {"error": str(e), "is_valid": True, "risk_score": 0}
    
    def _calculate_risk_score(self, fraud_analysis: Dict) -> float:
        """Calculate risk score from fraud analysis"""
        try:
            # Base score from analysis
            base_score = 0
            
            if not fraud_analysis.get('is_valid', True):
                base_score += 50
            
            # Check classification
            classification = fraud_analysis.get('classification', '').upper()
            if classification == 'SCAM':
                base_score += 40
            elif classification in ['SUSPICIOUS', 'FRAUD']:
                base_score += 30
            
            # Check for pump & dump alerts
            pump_dump_alerts = fraud_analysis.get('pump_dump_alerts', [])
            if pump_dump_alerts:
                base_score += min(20, len(pump_dump_alerts) * 10)
            
            # Check for sentiment manipulation
            sentiment_alerts = fraud_analysis.get('sentiment_alerts', [])
            if sentiment_alerts:
                base_score += min(15, len(sentiment_alerts) * 5)
            
            # Check for coordinated campaigns
            campaign_alerts = fraud_analysis.get('campaign_alerts', [])
            if campaign_alerts:
                base_score += min(25, len(campaign_alerts) * 15)
            
            # Check for suspicious companies
            suspicious_companies = fraud_analysis.get('suspicious_companies', [])
            if suspicious_companies:
                base_score += min(20, len(suspicious_companies) * 10)
            
            return min(100, base_score)
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return 0
    
    def _get_alert_level(self, risk_score: float) -> str:
        """Get alert level based on risk score"""
        if risk_score >= 80:
            return "CRITICAL"
        elif risk_score >= 60:
            return "HIGH"
        elif risk_score >= 30:
            return "MEDIUM"
        else:
            return "LOW"
    
    async def _store_alert(self, alert: GroupAlert):
        """Store alert in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO fraud_alerts 
                (group_id, group_name, message_id, message_text, sender_id, sender_username, 
                 timestamp, fraud_analysis, risk_score, alert_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert.group_id, alert.group_name, alert.message_id, alert.message_text[:500],
                alert.sender_id, alert.sender_username, alert.timestamp,
                json.dumps(alert.fraud_analysis), alert.risk_score, alert.alert_level
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error storing alert: {e}")
    
    async def _store_message(self, group_id: int, group_name: str, message_id: int, 
                           message_text: str, sender_id: int, sender_username: str,
                           timestamp, fraud_analysis: Dict, risk_score: float, is_fraud: bool):
        """Store monitored message in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO monitored_messages 
                (group_id, group_name, message_id, message_text, sender_id, sender_username, 
                 timestamp, fraud_analysis, risk_score, is_fraud)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                group_id, group_name, message_id, message_text[:1000],  # Store more text for messages
                sender_id, sender_username, timestamp,
                json.dumps(fraud_analysis), risk_score, is_fraud
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error storing message: {e}")
    
    async def _update_daily_stats(self, is_fraud: bool, is_high_risk: bool):
        """Update daily statistics"""
        try:
            today = datetime.now().date()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO message_stats (date, total_messages, fraud_detected, high_risk_alerts)
                VALUES (?, 0, 0, 0)
            ''', (today,))
            
            cursor.execute('''
                UPDATE message_stats 
                SET total_messages = total_messages + 1,
                    fraud_detected = fraud_detected + ?,
                    high_risk_alerts = high_risk_alerts + ?
                WHERE date = ?
            ''', (1 if is_fraud else 0, 1 if is_high_risk else 0, today))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error updating daily stats: {e}")
    
    async def _notify_alert_callbacks(self, alert: GroupAlert):
        """Notify registered alert callbacks"""
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    def add_alert_callback(self, callback):
        """Add callback function for new alerts"""
        self.alert_callbacks.append(callback)
    
    def get_monitored_groups(self) -> List[Dict]:
        """Get list of monitored groups"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT group_id, group_name, group_username, added_date, status
            FROM monitored_groups WHERE status = 'active'
        ''')
        
        groups = []
        for row in cursor.fetchall():
            groups.append({
                "group_id": row[0],
                "group_name": row[1], 
                "group_username": row[2],
                "added_date": row[3],
                "status": row[4]
            })
        
        conn.close()
        return groups
    
    def get_recent_alerts(self, limit: int = 50) -> List[Dict]:
        """Get recent fraud alerts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT group_name, message_text, sender_username, timestamp, 
                   risk_score, alert_level, fraud_analysis
            FROM fraud_alerts 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))
        
        alerts = []
        for row in cursor.fetchall():
            try:
                fraud_analysis = json.loads(row[6]) if row[6] else {}
            except:
                fraud_analysis = {}
                
            alerts.append({
                "group_name": row[0],
                "message_text": row[1],
                "sender_username": row[2],
                "timestamp": row[3],
                "risk_score": row[4],
                "alert_level": row[5],
                "fraud_analysis": fraud_analysis
            })
        
        conn.close()
        return alerts
    
    def get_recent_messages(self, limit: int = 100, group_id: int = None) -> List[Dict]:
        """Get recent monitored messages (all messages, not just alerts)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if group_id:
            cursor.execute('''
                SELECT group_name, message_text, sender_username, timestamp, 
                       risk_score, is_fraud, fraud_analysis, group_id
                FROM monitored_messages 
                WHERE group_id = ?
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (group_id, limit))
        else:
            cursor.execute('''
                SELECT group_name, message_text, sender_username, timestamp, 
                       risk_score, is_fraud, fraud_analysis, group_id
                FROM monitored_messages 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
        
        messages = []
        for row in cursor.fetchall():
            try:
                fraud_analysis = json.loads(row[6]) if row[6] else {}
            except:
                fraud_analysis = {}
                
            # Determine alert level from risk score
            risk_score = row[4]
            if risk_score >= 70:
                alert_level = "HIGH"
            elif risk_score >= 30:
                alert_level = "MEDIUM"  
            else:
                alert_level = "LOW"
                
            messages.append({
                "group_name": row[0],
                "message_text": row[1],
                "sender_username": row[2],
                "timestamp": row[3],
                "risk_score": risk_score,
                "is_fraud": bool(row[5]),
                "alert_level": alert_level,
                "fraud_analysis": fraud_analysis,
                "group_id": row[7]
            })
        
        conn.close()
        return messages
    
    def get_monitoring_stats(self) -> Dict:
        """Get monitoring statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total groups
        cursor.execute("SELECT COUNT(*) FROM monitored_groups WHERE status = 'active'")
        total_groups = cursor.fetchone()[0]
        
        # Total alerts
        cursor.execute("SELECT COUNT(*) FROM fraud_alerts")
        total_alerts = cursor.fetchone()[0]
        
        # Recent stats (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        cursor.execute('''
            SELECT SUM(total_messages), SUM(fraud_detected), SUM(high_risk_alerts)
            FROM message_stats WHERE date >= ?
        ''', (week_ago.date(),))
        
        stats_row = cursor.fetchone()
        weekly_messages = stats_row[0] or 0
        weekly_fraud = stats_row[1] or 0
        weekly_high_risk = stats_row[2] or 0
        
        conn.close()
        
        return {
            "total_groups": total_groups,
            "total_alerts": total_alerts,
            "weekly_messages": weekly_messages,
            "weekly_fraud_detected": weekly_fraud,
            "weekly_high_risk": weekly_high_risk,
            "fraud_detection_rate": (weekly_fraud / weekly_messages * 100) if weekly_messages > 0 else 0
        }
    
    async def start_monitoring(self):
        """Start the monitoring service"""
        if not self.client:
            if not await self.initialize():
                return False
        
        self.running = True
        logger.info("Telegram group monitoring started")
        
        try:
            await self.client.run_until_disconnected()
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
        finally:
            self.running = False
    
    async def stop_monitoring(self):
        """Stop the monitoring service"""
        self.running = False
        if self.client:
            await self.client.disconnect()
        logger.info("Telegram group monitoring stopped")

# Global monitor instance
_monitor_instance = None

def get_monitor_instance() -> Optional[TelegramGroupMonitor]:
    """Get the global monitor instance"""
    return _monitor_instance

def init_monitor(api_id: str, api_hash: str, phone: str) -> TelegramGroupMonitor:
    """Initialize the global monitor instance"""
    global _monitor_instance
    _monitor_instance = TelegramGroupMonitor(api_id, api_hash, phone)
    return _monitor_instance

# Example usage and testing
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Get Telegram credentials from environment
    API_ID = os.getenv("TELEGRAM_API_ID")
    API_HASH = os.getenv("TELEGRAM_API_HASH") 
    PHONE = os.getenv("TELEGRAM_PHONE")
    
    if not all([API_ID, API_HASH, PHONE]):
        print("Please set TELEGRAM_API_ID, TELEGRAM_API_HASH, and TELEGRAM_PHONE in .env file")
        exit(1)
    
    async def test_monitor():
        monitor = TelegramGroupMonitor(API_ID, API_HASH, PHONE)
        
        # Test alert callback
        def alert_callback(alert: GroupAlert):
            print(f"🚨 FRAUD ALERT: {alert.alert_level}")
            print(f"Group: {alert.group_name}")
            print(f"Message: {alert.message_text[:100]}...")
            print(f"Risk Score: {alert.risk_score}/100")
            print("-" * 50)
        
        monitor.add_alert_callback(alert_callback)
        
        if await monitor.initialize():
            print("✅ Monitor initialized")
            print(f"📊 Monitoring stats: {monitor.get_monitoring_stats()}")
            print(f"📱 Monitored groups: {len(monitor.get_monitored_groups())}")
            
            # Start monitoring (this will run until interrupted)
            await monitor.start_monitoring()
        else:
            print("❌ Failed to initialize monitor")
    
    # Run the test
    asyncio.run(test_monitor())
