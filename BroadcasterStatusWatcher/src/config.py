import json
import os

WATCH_INTERVAL_SECONDS = int(os.getenv("WATCH_INTERVAL_SECONDS", 10))
CHANNEL_IDS_TO_WATCH = [s.strip() for s in os.getenv("CHANNEL_IDS", "").split(",") if s.strip()]
HEADERS = json.loads(os.getenv("HEADERS_JSON", "{}"))
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
CHZZK_LIVE_STATUS_STREAM = "chzzk_live_status_events"
