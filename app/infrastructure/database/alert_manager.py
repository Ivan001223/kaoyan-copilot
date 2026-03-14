import json
import os
import time
from typing import Any, Optional

ALERTS_FILE = os.path.join("data", "alerts.json")


class AlertManager:
    def __init__(self) -> None:
        self._ensure_data_dir()

    def _ensure_data_dir(self) -> None:
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(ALERTS_FILE):
            with open(ALERTS_FILE, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "radar": {"last_check": None, "status": "暂无数据", "alerts": []},
                        "politics": {"last_check": None, "status": "暂无数据", "news": []},
                        "radar_history": [],
                        "politics_history": [],
                    },
                    f,
                )

    def _load_data(self) -> dict[str, Any]:
        try:
            with open(ALERTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "radar_history" not in data:
                    data["radar_history"] = []
                if "politics_history" not in data:
                    data["politics_history"] = []

                data["radar_history"] = [item for item in data["radar_history"] if item.get("has_update", False)]
                data["politics_history"] = [item for item in data["politics_history"] if item.get("has_news", False)]

                return data
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_data(self, data: dict[str, Any]) -> None:
        with open(ALERTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_alerts(self) -> dict[str, Any]:
        data = self._load_data()

        if data["radar_history"]:
            latest_meaningful = data["radar_history"][0]
            data["radar"]["school_name"] = latest_meaningful.get("school_name", data["radar"].get("school_name"))
            data["radar"]["message"] = latest_meaningful.get("message")
            data["radar"]["url"] = latest_meaningful.get("url")

        if data["politics_history"]:
            latest_meaningful = data["politics_history"][0]
            data["politics"]["news"] = latest_meaningful.get("news", [])
            data["politics"]["has_news"] = True

        return data

    def update_radar(
        self, school_name: str, has_update: bool, message: str, url: Optional[str] = None
    ) -> dict[str, Any]:
        data = self._load_data()

        record = {
            "timestamp": int(time.time()),
            "school_name": school_name,
            "has_update": has_update,
            "message": message,
            "url": url,
        }

        data["radar"] = {
            "last_check": record["timestamp"],
            "school_name": school_name,
            "has_update": has_update,
            "message": message,
            "url": url,
        }

        if has_update:
            is_duplicate = any(item["message"] == message for item in data["radar_history"][:5])
            if not is_duplicate:
                data["radar_history"].insert(0, record)
                data["radar_history"] = data["radar_history"][:50]

        self._save_data(data)
        return data["radar"]

    def update_politics(self, has_news: bool, news_items: list) -> dict[str, Any]:
        data = self._load_data()

        record = {
            "timestamp": int(time.time()),
            "has_news": has_news,
            "news": news_items,
        }

        data["politics"] = {
            "last_check": record["timestamp"],
            "has_news": has_news,
            "news": news_items,
        }

        if has_news:
            if news_items:
                first_title = news_items[0].get("title")
                is_duplicate = False
                for item in data["politics_history"][:5]:
                    if item.get("news") and item["news"][0].get("title") == first_title:
                        is_duplicate = True
                        break

                if not is_duplicate:
                    data["politics_history"].insert(0, record)
                    data["politics_history"] = data["politics_history"][:50]

        self._save_data(data)
        return data["politics"]


alert_manager = AlertManager()
