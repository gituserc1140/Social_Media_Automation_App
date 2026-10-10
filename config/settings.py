"""Configuration settings with sensible placeholders.

These settings are intentionally simple. For production use consider reading
secrets from environment variables, a .env file, or a secret manager.
"""

import os

API_BASE_URL = os.getenv("API_BASE_URL", "https://api.example.com")
API_KEY = os.getenv("API_KEY", None)
DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "10"))
