import os
import json
import time
from typing import Dict, Any, Optional

ALERTS_FILE = os.path.join("data", "alerts.json")

class AlertManager:
    def __init__(self):
        self._ensure_data_dir()
        
    def _ensure_data_dir(self):
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(ALERTS_FILE):
            with open(ALERTS_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "radar": {"last_check": None, "status": "暂无数据", "alerts": []},
                    "politics": {"last_check": None, "status": "暂无数据", "news": []},
                    "radar_history": [],
                    "politics_history": []
                }, f)

    def _load_data(self) -> Dict[str, Any]:
        try:
            with open(ALERTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Migration for existing data
                if "radar_history" not in data: data["radar_history"] = []
                if "politics_history" not in data: data["politics_history"] = []
                
                # Cleanup: Filter out history items where has_update/has_news is False
                # This ensures we respect the user's rule even for existing data
                data["radar_history"] = [item for item in data["radar_history"] if item.get("has_update", False)]
                data["politics_history"] = [item for item in data["politics_history"] if item.get("has_news", False)]
                
                return data
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_data(self, data: Dict[str, Any]):
        with open(ALERTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_alerts(self) -> Dict[str, Any]:
        data = self._load_data()
        
        # Display Logic: 
        # For "radar" and "politics" fields (used for the dashboard card),
        # we want to show the LATEST MEANINGFUL update (from history), 
        # but keep the "last_check" time as the actual last check time.
        
        # 1. Radar Display
        if data["radar_history"]:
            latest_meaningful = data["radar_history"][0] # History is sorted new->old
            # Merge: Use message/url from history, but last_check from current status
            data["radar"]["school_name"] = latest_meaningful.get("school_name", data["radar"].get("school_name"))
            data["radar"]["message"] = latest_meaningful.get("message")
            data["radar"]["url"] = latest_meaningful.get("url")
            # We artificially set has_update to True for display so it shows content
            # But in the frontend we might want to differentiate "New Just Now" vs "Old News"
            # For now, let's just ensure the content is there.
        
        # 2. Politics Display
        if data["politics_history"]:
            latest_meaningful = data["politics_history"][0]
            data["politics"]["news"] = latest_meaningful.get("news", [])
            data["politics"]["has_news"] = True # Force show content

        return data

    def update_radar(self, school_name: str, has_update: bool, message: str, url: Optional[str] = None):
        data = self._load_data()
        
        # New Record
        record = {
            "timestamp": int(time.time()),
            "school_name": school_name,
            "has_update": has_update,
            "message": message,
            "url": url
        }
        
        # Update Latest (Always update to show last check time)
        data["radar"] = {
            "last_check": record["timestamp"],
            "school_name": school_name,
            "has_update": has_update,
            "message": message,
            "url": url
        }
        
        # Append to History ONLY if has_update is True
        if has_update:
            # Optional: Check for duplicate message to be extra safe
            is_duplicate = any(item['message'] == message for item in data["radar_history"][:5])
            if not is_duplicate:
                data["radar_history"].insert(0, record)
                data["radar_history"] = data["radar_history"][:50]
        
        self._save_data(data)
        return data["radar"]

    def update_politics(self, has_news: bool, news_items: list):
        data = self._load_data()
        
        # New Record
        record = {
            "timestamp": int(time.time()),
            "has_news": has_news,
            "news": news_items
        }
        
        # Update Latest
        data["politics"] = {
            "last_check": record["timestamp"],
            "has_news": has_news,
            "news": news_items
        }
        
        # Append to History ONLY if has_news is True
        if has_news:
            # Deduplication: Check if the first news title exists in recent history
            if news_items:
                first_title = news_items[0].get('title')
                is_duplicate = False
                for item in data["politics_history"][:5]:
                    if item.get('news') and item['news'][0].get('title') == first_title:
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    data["politics_history"].insert(0, record)
                    data["politics_history"] = data["politics_history"][:50]
        
        self._save_data(data)
        return data["politics"]

alert_manager = AlertManager()
