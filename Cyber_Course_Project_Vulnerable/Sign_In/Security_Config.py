import json
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
import warnings

# Load the JSON config
SIGN_IN_CONFIG_PATH = Path(__file__).resolve().parent / "Sign_In_Configurations/Sign_In_Configurations.json"
with open(SIGN_IN_CONFIG_PATH, "r") as f:
    SIGN_IN_RAW = json.load(f)

try:
    SIGN_IN_CONFIG = SIGN_IN_RAW["sign_in_attempts"]
except KeyError as e:
    raise ImproperlyConfigured(f"Missing required sign-in configuration: {e}")

storage_policy = SIGN_IN_CONFIG.get("storage_policy", {})

FORBID_IN_MEMORY_STORAGE = not storage_policy.get("allow_in_memory", True)

required_backend = storage_policy.get("required_backend", "cache")  
if required_backend not in ("cache", "database", "file"):
    raise ImproperlyConfigured(
        f"Invalid sign-in storage backend '{required_backend}'. "
        "Supported options are: 'cache', 'database', 'file'."
    )
STORAGE_BACKEND = required_backend