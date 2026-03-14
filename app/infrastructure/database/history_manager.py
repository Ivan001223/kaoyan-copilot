import json
import os
import time
from typing import Any, Optional

HISTORY_FILE = os.path.join("data", "chat_history.json")


class HistoryManager:
    def __init__(self) -> None:
        self._ensure_data_dir()

    def _ensure_data_dir(self) -> None:
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def _load_data(self) -> dict[str, Any]:
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_data(self, data: dict[str, Any]) -> None:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_history(self, user_id: str) -> list[dict[str, Any]]:
        data = self._load_data()
        user_sessions = data.get(user_id, {})
        sessions_list = list(user_sessions.values())
        sessions_list.sort(key=lambda x: x.get("updated_at", 0), reverse=True)
        return sessions_list

    def save_session(
        self, user_id: str, session_id: str, messages: list[dict[str, Any]], title: Optional[str] = None
    ) -> dict[str, Any]:
        data = self._load_data()
        if user_id not in data:
            data[user_id] = {}

        now = int(time.time())

        if session_id in data[user_id]:
            session = data[user_id][session_id]
            old_len = len(session.get("messages", []))
            new_len = len(messages)

            session["messages"] = messages
            if title:
                session["title"] = title

            if new_len > old_len:
                session["updated_at"] = now
        else:
            if not title:
                first_user_msg = next((m for m in messages if m.get("role") == "user"), None)
                if first_user_msg:
                    content = first_user_msg.get("content", "")
                    title = content[:20] + "..." if len(content) > 20 else content
                else:
                    title = "新对话"

            data[user_id][session_id] = {
                "id": session_id,
                "title": title,
                "created_at": now,
                "updated_at": now,
                "messages": messages,
            }

        self._save_data(data)
        return data[user_id][session_id]

    def delete_session(self, user_id: str, session_id: str) -> bool:
        data = self._load_data()
        if user_id in data and session_id in data[user_id]:
            del data[user_id][session_id]
            self._save_data(data)
            return True
        return False


history_manager = HistoryManager()
