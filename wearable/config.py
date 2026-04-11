import base64

# Thryve QA credentials (hackathon)
_WEB_AUTH = base64.b64encode(b"aihackxalan-api:XmgFAj3OwHEErG4s").decode()
_APP_AUTH = base64.b64encode(
    b"dDccECwGgWbklgwz:TGmmgBMk8N4Rl3zsZcfAbaFVauEJ77nOs0VBYi9z7ZjQVvl9JB0qVjZMBn6zHjp7"
).decode()

THRYVE_HEADERS = {
    "Authorization": f"Basic {_WEB_AUTH}",
    "AppAuthorization": f"Basic {_APP_AUTH}",
    "Content-Type": "application/x-www-form-urlencoded",
}

THRYVE_BASE_URL = "https://api-qa.thryve.de"

# Pre-made Whoop demo profile (Active Gym Guy) — rich risk score data
DEMO_END_USER_ID = "2bfaa7e6f9455ceafa0a59fd5b80496c"

# Metrics to fetch
VALUE_TYPES = "3001,3100,2201,2000,2532,2533,2534,2535,2538"
