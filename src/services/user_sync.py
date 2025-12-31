"""
Cross-Platform User Synchronization Service
Handles real-time sync between Telegram bot and web platform users
"""

import asyncio
import aiohttp
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3

logger = logging.getLogger(__name__)

@dataclass
class UserSyncData:
    """User data structure for synchronization"""
    telegram_id: int
    web_user_id: Optional[str]
    username: str
    first_name: str
    is_premium: bool
    subscription_expires: Optional[str]
    daily_generations: int
    total_generations: int
    last_activity: str
    premium_activated_at: Optional[str]
    sync_status: str = "pending"
    last_synced: Optional[str] = None

class UserSyncManager:
    """Manages user synchronization between platforms"""
    
    def __init__(self):
        self.api_base_url = os.getenv("WEB_API_BASE_URL", "https://bin-search-api.arturovillanueva1994.workers.dev")
        self.sync_db_path = Path(__file__).parent.parent.parent / "data" / "user_sync.db"
        self.sync_interval = int(os.getenv("SYNC_INTERVAL_SECONDS", "300"))  # 5 minutes
        self.batch_size = int(os.getenv("SYNC_BATCH_SIZE", "50"))
        
        # Create sync database
        self._init_sync_db()
        
        # In-memory cache for quick lookups
        self.user_cache: Dict[int, UserSyncData] = {}
        self.pending_syncs: Set[int] = set()
        
    def _init_sync_db(self):
        """Initialize SQLite database for sync tracking"""
        self.sync_db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.sync_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sync (
                telegram_id INTEGER PRIMARY KEY,
                web_user_id TEXT,
                username TEXT,
                first_name TEXT,
                is_premium BOOLEAN,
                subscription_expires TEXT,
                daily_generations INTEGER,
                total_generations INTEGER,
                last_activity TEXT,
                premium_activated_at TEXT,
                sync_status TEXT,
                last_synced TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                event_type TEXT,
                event_data TEXT,
                status TEXT,
                created_at TEXT,
                processed_at TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        
        logger.info(f"Sync database initialized at {self.sync_db_path}")
    
    def save_user_sync_data(self, user_data: UserSyncData):
        """Save user sync data to database"""
        conn = sqlite3.connect(self.sync_db_path)
        cursor = conn.cursor()
        
        now = datetime.utcnow().isoformat()
        
        cursor.execute("""
            INSERT OR REPLACE INTO user_sync 
            (telegram_id, web_user_id, username, first_name, is_premium, 
             subscription_expires, daily_generations, total_generations, 
             last_activity, premium_activated_at, sync_status, last_synced, 
             created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                    COALESCE((SELECT created_at FROM user_sync WHERE telegram_id = ?), ?), ?)
        """, (
            user_data.telegram_id, user_data.web_user_id, user_data.username,
            user_data.first_name, user_data.is_premium, user_data.subscription_expires,
            user_data.daily_generations, user_data.total_generations,
            user_data.last_activity, user_data.premium_activated_at,
            user_data.sync_status, user_data.last_synced,
            user_data.telegram_id, now, now
        ))
        
        conn.commit()
        conn.close()
        
        # Update cache
        self.user_cache[user_data.telegram_id] = user_data
    
    def get_user_sync_data(self, telegram_id: int) -> Optional[UserSyncData]:
        """Get user sync data from cache or database"""
        # Check cache first
        if telegram_id in self.user_cache:
            return self.user_cache[telegram_id]
        
        # Load from database
        conn = sqlite3.connect(self.sync_db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM user_sync WHERE telegram_id = ?", (telegram_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            user_data = UserSyncData(
                telegram_id=row[0],
                web_user_id=row[1],
                username=row[2] or "",
                first_name=row[3] or "",
                is_premium=bool(row[4]),
                subscription_expires=row[5],
                daily_generations=row[6] or 0,
                total_generations=row[7] or 0,
                last_activity=row[8] or datetime.utcnow().isoformat(),
                premium_activated_at=row[9],
                sync_status=row[10] or "pending",
                last_synced=row[11]
            )
            self.user_cache[telegram_id] = user_data
            return user_data
        
        return None
    
    def queue_sync_event(self, telegram_id: int, event_type: str, event_data: Dict):
        """Queue a sync event for processing"""
        conn = sqlite3.connect(self.sync_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sync_events (telegram_id, event_type, event_data, status, created_at)
            VALUES (?, ?, ?, 'pending', ?)
        """, (
            telegram_id, event_type, json.dumps(event_data), datetime.utcnow().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        # Add to pending syncs
        self.pending_syncs.add(telegram_id)
        logger.debug(f"Queued sync event: {event_type} for user {telegram_id}")
    
    async def sync_user_to_web(self, telegram_id: int) -> bool:
        """Sync single user data to web platform"""
        try:
            from src.services.api_auth import auth
            
            user_data = self.get_user_sync_data(telegram_id)
            if not user_data:
                logger.warning(f"No sync data found for user {telegram_id}")
                return False
            
            # Create sync payload
            sync_payload = {
                "telegram_id": telegram_id,
                "username": user_data.username,
                "first_name": user_data.first_name,
                "is_premium": user_data.is_premium,
                "subscription_expires": user_data.subscription_expires,
                "daily_generations": user_data.daily_generations,
                "total_generations": user_data.total_generations,
                "last_activity": user_data.last_activity,
                "premium_activated_at": user_data.premium_activated_at,
                "sync_timestamp": datetime.utcnow().isoformat(),
                "source": "telegram-bot"
            }
            
            headers = auth.create_api_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/api/v1/users/sync-from-telegram",
                    json=sync_payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        web_user_id = result.get("user_id")
                        
                        # Update sync status
                        user_data.web_user_id = web_user_id
                        user_data.sync_status = "synced"
                        user_data.last_synced = datetime.utcnow().isoformat()
                        
                        self.save_user_sync_data(user_data)
                        
                        logger.info(f"Successfully synced user {telegram_id} to web platform")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to sync user {telegram_id}: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Sync error for user {telegram_id}: {e}")
            return False
    
    async def sync_premium_status_from_web(self, telegram_id: int) -> Optional[bool]:
        """Sync premium status from web platform to bot"""
        try:
            from src.services.api_auth import auth
            
            headers = auth.create_api_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/api/v1/users/telegram/{telegram_id}/premium-status",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        is_premium = data.get("is_premium", False)
                        subscription_expires = data.get("subscription_expires")
                        premium_activated_at = data.get("premium_activated_at")
                        
                        # Update local data
                        user_data = self.get_user_sync_data(telegram_id)
                        if not user_data:
                            user_data = UserSyncData(
                                telegram_id=telegram_id,
                                web_user_id=data.get("user_id"),
                                username="",
                                first_name="",
                                is_premium=is_premium,
                                subscription_expires=subscription_expires,
                                daily_generations=0,
                                total_generations=0,
                                last_activity=datetime.utcnow().isoformat(),
                                premium_activated_at=premium_activated_at
                            )
                        else:
                            user_data.is_premium = is_premium
                            user_data.subscription_expires = subscription_expires
                            user_data.premium_activated_at = premium_activated_at
                            user_data.last_synced = datetime.utcnow().isoformat()
                        
                        self.save_user_sync_data(user_data)
                        
                        logger.info(f"Premium status synced for user {telegram_id}: {is_premium}")
                        return is_premium
                    else:
                        logger.warning(f"Failed to sync premium status for user {telegram_id}: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Premium status sync error for user {telegram_id}: {e}")
            return None
    
    async def process_pending_syncs(self):
        """Process all pending sync events"""
        conn = sqlite3.connect(self.sync_db_path)
        cursor = conn.cursor()
        
        # Get pending sync events
        cursor.execute("""
            SELECT id, telegram_id, event_type, event_data 
            FROM sync_events 
            WHERE status = 'pending' 
            ORDER BY created_at 
            LIMIT ?
        """, (self.batch_size,))
        
        events = cursor.fetchall()
        
        for event_id, telegram_id, event_type, event_data_json in events:
            try:
                event_data = json.loads(event_data_json)
                
                if event_type == "user_activity":
                    await self.sync_user_to_web(telegram_id)
                elif event_type == "premium_upgrade":
                    await self.sync_premium_status_from_web(telegram_id)
                elif event_type == "generation_activity":
                    # Update generation count
                    user_data = self.get_user_sync_data(telegram_id)
                    if user_data:
                        user_data.daily_generations = event_data.get("daily_count", 0)
                        user_data.total_generations = event_data.get("total_count", 0)
                        self.save_user_sync_data(user_data)
                
                # Mark event as processed
                cursor.execute("""
                    UPDATE sync_events 
                    SET status = 'processed', processed_at = ? 
                    WHERE id = ?
                """, (datetime.utcnow().isoformat(), event_id))
                
            except Exception as e:
                logger.error(f"Error processing sync event {event_id}: {e}")
                cursor.execute("""
                    UPDATE sync_events 
                    SET status = 'failed', processed_at = ? 
                    WHERE id = ?
                """, (datetime.utcnow().isoformat(), event_id))
        
        conn.commit()
        conn.close()
        
        if events:
            logger.info(f"Processed {len(events)} sync events")
    
    async def start_sync_service(self):
        """Start the continuous sync service"""
        logger.info("Starting cross-platform user sync service")
        
        while True:
            try:
                await self.process_pending_syncs()
                
                # Clean up old processed events (older than 7 days)
                cutoff_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
                conn = sqlite3.connect(self.sync_db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM sync_events WHERE processed_at < ?", (cutoff_date,))
                conn.commit()
                conn.close()
                
            except Exception as e:
                logger.error(f"Sync service error: {e}")
            
            await asyncio.sleep(self.sync_interval)

# Global sync manager instance
sync_manager = UserSyncManager()

# Utility functions for bot integration
def record_user_activity(telegram_id: int, username: str = "", first_name: str = ""):
    """Record user activity for sync"""
    user_data = sync_manager.get_user_sync_data(telegram_id)
    if not user_data:
        user_data = UserSyncData(
            telegram_id=telegram_id,
            web_user_id=None,
            username=username,
            first_name=first_name,
            is_premium=False,
            subscription_expires=None,
            daily_generations=0,
            total_generations=0,
            last_activity=datetime.utcnow().isoformat(),
            premium_activated_at=None
        )
    else:
        user_data.last_activity = datetime.utcnow().isoformat()
        if username:
            user_data.username = username
        if first_name:
            user_data.first_name = first_name
    
    sync_manager.save_user_sync_data(user_data)
    sync_manager.queue_sync_event(telegram_id, "user_activity", {
        "username": username,
        "first_name": first_name,
        "timestamp": user_data.last_activity
    })

def record_generation_activity(telegram_id: int, cards_generated: int):
    """Record card generation for sync"""
    user_data = sync_manager.get_user_sync_data(telegram_id)
    if user_data:
        user_data.total_generations += cards_generated
        user_data.daily_generations += cards_generated
        sync_manager.save_user_sync_data(user_data)
        
        sync_manager.queue_sync_event(telegram_id, "generation_activity", {
            "cards_generated": cards_generated,
            "total_count": user_data.total_generations,
            "daily_count": user_data.daily_generations
        })

async def check_premium_status(telegram_id: int) -> bool:
    """Check premium status with sync fallback"""
    # Try to sync from web first
    premium_status = await sync_manager.sync_premium_status_from_web(telegram_id)
    
    if premium_status is not None:
        return premium_status
    
    # Fallback to local data
    user_data = sync_manager.get_user_sync_data(telegram_id)
    if user_data:
        return user_data.is_premium
    
    return False

async def start_sync_service():
    """Start the sync service (call this in bot startup)"""
    await sync_manager.start_sync_service()