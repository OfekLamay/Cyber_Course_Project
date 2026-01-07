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

# -----------------------
# Enforce storage policy
# -----------------------
storage_policy = SIGN_IN_CONFIG.get("storage_policy", {})

# Decide whether in-memory storage is allowed
FORBID_IN_MEMORY_STORAGE = not storage_policy.get("allow_in_memory", True)

# Choose backend
required_backend = storage_policy.get("required_backend", "cache")  # default to cache
if required_backend not in ("cache", "database", "file"):
    raise ImproperlyConfigured(
        f"Invalid sign-in storage backend '{required_backend}'. "
        "Supported options are: 'cache', 'database', 'file'."
    )

# Optional: warn if in-memory storage is allowed but you want cache
if not FORBID_IN_MEMORY_STORAGE and required_backend != "cache":
    warnings.warn(
        "In-memory storage is allowed, but the backend is not 'cache'. "
        "Consider using cache for better persistence and safety."
    )

# Expose for other modules
STORAGE_BACKEND = required_backend