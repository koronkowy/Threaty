import json
import time
import os

LOG_FILE = 'api_errors_log.json'

def log_api_error(status_code):
    if status_code not in [429, 503]:
        return

    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []

    logs.append({"timestamp": time.time(), "status_code": status_code})

    with open(LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=2)

def update_badges():
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []

    current_time = time.time()
    twenty_four_hours = 24 * 60 * 60

    # Filter out older than 24 hours
    recent_logs = [log for log in logs if current_time - log['timestamp'] <= twenty_four_hours]

    with open(LOG_FILE, 'w') as f:
        json.dump(recent_logs, f, indent=2)

    count_429 = sum(1 for log in recent_logs if log['status_code'] == 429)
    count_503 = sum(1 for log in recent_logs if log['status_code'] == 503)

    badge_429 = {
        "schemaVersion": 1,
        "label": "Gemini 429 Errors (24h)",
        "message": str(count_429),
        "color": "critical" if count_429 > 1 else "success"
    }

    badge_503 = {
        "schemaVersion": 1,
        "label": "Gemini 503 Errors (24h)",
        "message": str(count_503),
        "color": "critical" if count_503 > 1 else "success"
    }

    with open('badge_429.json', 'w') as f:
        json.dump(badge_429, f, indent=2)

    with open('badge_503.json', 'w') as f:
        json.dump(badge_503, f, indent=2)

if __name__ == '__main__':
    update_badges()
