import os
import json

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

DEFAULT_CONFIG = {
    "download_dir": os.path.join(os.path.expanduser("~"), "Downloads", "MediaCloudSyncer"),
    "cache_dir": os.path.join(os.path.dirname(os.path.abspath(__file__)), "advanced_cache"),
    "delete_local_after_upload": False,
    "theme_mode": "Dark",  # Dark, Light, System
    "accent_theme": "blue",
    "default_format": "Video Only",
    "default_resolution": "Best Quality",
    "default_audio_codec": "mp3",
    "default_subtitle_lang": "en",
    "default_subtitle_format": "srt",
    "write_thumbnail": True,
    "write_info_json": False,
    "mega_email": "",
    "mega_password": "",
    "telegram_bot_token": "",
    "telegram_chat_id": "",
    "telegram_api_id": "",
    "telegram_api_hash": ""
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            # Ensure all keys exist
            merged = DEFAULT_CONFIG.copy()
            merged.update(cfg)
            return merged
    except Exception as e:
        print(f"Error loading config, resetting to default: {e}")
        return DEFAULT_CONFIG.copy()

def save_config(config_data):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False
