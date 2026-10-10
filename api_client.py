"""API client module for external API calls.

This module provides a small request wrapper `make_request()` and a minimal
`fetch_data()` function that returns placeholder data. Replace or extend
`fetch_data()` with real API logic, authentication, and parsing for your API.
"""

import os
import requests
from typing import Any, Dict, Optional
from config import settings


def make_request(path: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None, method: str = "GET", timeout: Optional[int] = None) -> Any:
    """Simple HTTP request helper.

    - Builds a URL from settings.API_BASE_URL and path
    - Uses requests.request and returns parsed JSON
    - Raises on HTTP errors
    """
    base = settings.API_BASE_URL.rstrip("/")
    url = f"{base}/{path.lstrip('/')}"
    timeout = timeout or settings.DEFAULT_TIMEOUT
    headers = headers or {}

    resp = requests.request(method, url, params=params, headers=headers, timeout=timeout)
    resp.raise_for_status()

    # Attempt to parse JSON, fall back to raw text
    try:
        return resp.json()
    except ValueError:
        return resp.text


def fetch_data(params: Optional[Dict[str, Any]] = None, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Minimal example function that returns placeholder data or forwards a real request.

    Replace this implementation with your API-specific calls. Keep the function
    signature as a single integration point for the UI.

    Behavior:
    - If the configured API_BASE_URL is the default example domain, returns a
      small static example payload so the UI shows content without a real API.
    - Otherwise, attempts to call the API (path 'data' by default) and returns
      the parsed result, or an error payload on failure.
    """
    params = params or {}

    # if still pointing at the example placeholder base, return fake data
    if (not settings.API_BASE_URL) or ("example.com" in settings.API_BASE_URL):
        return {
            "title": "Micro-app sample",
            "description": "Replace api_client.fetch_data() with calls to your API",
            "items": [
                {"id": 1, "name": "Example item A", "value": 100},
                {"id": 2, "name": "Example item B", "value": 200},
            ],
        }

    # attempt a real API call to the generic 'data' path. Adapt path as needed.
    headers = {}
    if api_key:
        # common pattern: send key as Authorization header; adjust per API
        headers["Authorization"] = f"Bearer {api_key}"
    elif settings.API_KEY:
        headers["Authorization"] = f"Bearer {settings.API_KEY}"

    try:
        result = make_request(path="data", params=params, headers=headers)
        # ensure we return a dict the UI can consume; adapt parsing here
        if isinstance(result, dict):
            return result
        else:
            return {"title": "API result", "description": "Non-JSON response", "items": [{"id": 1, "name": str(result), "value": 0}]}
    except Exception as exc:
        return {"title": "Error", "description": str(exc), "items": []}
