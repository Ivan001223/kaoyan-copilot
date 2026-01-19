import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load env variables at module level
load_dotenv()

class ConfigManager:
    _instance = None
    CONFIG_FILE = "config.json"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._init_config()
        return cls._instance

    def _init_config(self):
        """Initialize configuration from file or defaults."""
        self.config = self._load_from_file() or self._load_defaults()
        # Merge defaults into loaded config to ensure structure exists
        # This handles cases where config.json exists but new fields were added to defaults
        # Simple deep merge
        defaults = self._load_defaults()
        self._deep_merge(self.config, defaults)
        
    def _load_defaults(self) -> Dict[str, Any]:
        """Load default configuration from environment variables."""
        return {
            "llm": {
                "api_key": os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", "")),
                "base_url": os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
                "model": os.getenv("LLM_MODEL", "gpt-4o") # Cloud model for text generation
            },
            "local_models": {
                "ocr_model": "Qwen/Qwen2.5-VL-3B-Instruct", # Local model for OCR (Non-quantized for compatibility)
                "embedding_model": "Qwen/Qwen3-VL-Embedding-2B", # Local model for Tokenizer/Embeddings
                "rerank_model": "Qwen/Qwen3-VL-Reranker-2B" # Local model for Reranking
            },
            "search": {
                "provider": os.getenv("SEARCH_PROVIDER", "duckduckgo"), # Options: duckduckgo, tavily
                "tavily_api_key": os.getenv("TAVILY_API_KEY", "")
            },
            "radar": {
                "enabled": True,
                "schedule_time": "08:00",
                "target_school": "中国科学院大学杭州高等研究所"
            },
            "politics": {
                "enabled": True,
                "schedule_time": "08:30"
            }
        }

    def _load_from_file(self) -> Optional[Dict[str, Any]]:
        """Load configuration from JSON file."""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config file: {e}")
                return None
        return None

    def _deep_merge(self, target: Dict, source: Dict):
        """Recursively merge source into target if keys are missing in target."""
        for key, value in source.items():
            if key not in target:
                target[key] = value
            elif isinstance(value, dict) and isinstance(target.get(key), dict):
                self._deep_merge(target[key], value)

    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration."""
        return self.config

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Helper to get a specific value safely."""
        return self.config.get(section, {}).get(key, default)

    def update_config(self, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update configuration and save to file."""
        # Update current config with new values (deep update)
        # Using a custom recursive update to merge partial updates
        self._recursive_update(self.config, new_config)
        self._save_to_file()
        return self.config

    def _recursive_update(self, target: Dict, source: Dict):
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                self._recursive_update(target[key], value)
            else:
                target[key] = value

    def _save_to_file(self):
        """Save current configuration to JSON file."""
        try:
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config file: {e}")

# Global instance for easy access
config_manager = ConfigManager()
