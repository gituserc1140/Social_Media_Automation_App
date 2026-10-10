"""Buffer GraphQL helpers for channel lookup and post scheduling."""

import json
from typing import Any
from urllib.parse import urlsplit

import requests


BUFFER_API_URL = "https://api.buffer.com"
SOCIAL_MEDIA_PAGE_HOSTS = {
    "facebook.com",
    "instagram.com",
    "tiktok.com",
    "twitter.com",
    "x.com",
    "youtu.be",
    "youtube.com",
}


def is_social_media_page_url(url: str) -> bool:
    """Identify common share/profile URLs that are not direct media files."""
    try:
        parsed = urlsplit(url)
        hostname = (parsed.hostname or "").lower()
    except ValueError:
        return False
    if hostname.startswith("www."):
        hostname = hostname[4:]
    if hostname not in SOCIAL_MEDIA_PAGE_HOSTS:
        return False

    path = parsed.path.lower()
    if hostname == "tiktok.com":
        return path.startswith("/@") or path.startswith("/t/")
    if hostname == "instagram.com":
        return path.startswith(("/p/", "/reel/", "/reels/", "/stories/"))
    if hostname in {"youtube.com", "youtu.be"}:
        return hostname == "youtu.be" or path.startswith(("/watch", "/shorts/", "/live/"))
    if hostname in {"x.com", "twitter.com"}:
        return "/status/" in path
    if hostname == "facebook.com":
        return path.startswith(("/watch", "/reel/", "/share/"))
    return False


def _request(query: str, api_key: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
    response = requests.post(
        BUFFER_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={"query": query, "variables": variables or {}},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("errors"):
        messages = "; ".join(
            str(error.get("message", "Unknown GraphQL error")) for error in payload["errors"]
        )
        raise RuntimeError(f"Buffer API error: {messages}")
    if not isinstance(payload.get("data"), dict):
        raise ValueError("Buffer returned a response without GraphQL data.")
    return payload["data"]


def get_organizations(api_key: str) -> list[dict[str, str]]:
    data = _request(
        "query GetOrganizations { account { organizations { id name } } }",
        api_key,
    )
    try:
        organizations = data["account"]["organizations"]
    except (KeyError, TypeError) as exc:
        raise ValueError("Buffer's response did not include organizations.") from exc
    return organizations


def get_channels(organization_id: str, api_key: str) -> list[dict[str, str]]:
    data = _request(
        "query GetChannels($organizationId: OrganizationId!) { "
        "channels(input: { organizationId: $organizationId }) { id name service } }",
        api_key,
        {"organizationId": organization_id},
    )
    try:
        return data["channels"]
    except (KeyError, TypeError) as exc:
        raise ValueError("Buffer's response did not include channels.") from exc


def create_post(
    *,
    channel_id: str,
    text: str,
    api_key: str,
    mode: str,
    due_at: str | None = None,
    media_url: str | None = None,
    media_kind: str | None = None,
) -> dict[str, Any]:
    """Queue a post or schedule it for a specific time."""
    if mode not in {"addToQueue", "customScheduled"}:
        raise ValueError("Choose either the next queue slot or a custom scheduled time.")
    if mode == "customScheduled" and not due_at:
        raise ValueError("A scheduled post requires a date and time.")
    if media_url and media_kind not in {"image", "video"}:
        raise ValueError("A media attachment must be an image or video.")

    fields = [
        f"text: {json.dumps(text)}",
        f"channelId: {json.dumps(channel_id)}",
        "schedulingType: automatic",
        f"mode: {mode}",
    ]
    if due_at:
        fields.append(f"dueAt: {json.dumps(due_at)}")
    if media_url and media_kind:
        fields.append(
            f"assets: [{{ {media_kind}: {{ url: {json.dumps(media_url)} }} }}]"
        )
    query = (
        "mutation CreatePost { createPost(input: { "
        + " ".join(fields)
        + " }) { ... on PostActionSuccess { post { id text dueAt } } "
        "... on MutationError { message } } }"
    )
    data = _request(query, api_key)
    result = data.get("createPost")
    if not isinstance(result, dict):
        raise ValueError("Buffer returned a response without a post result.")
    if result.get("message"):
        raise RuntimeError(f"Buffer could not create the post: {result['message']}")
    post = result.get("post")
    if not isinstance(post, dict):
        raise ValueError("Buffer's response did not include the created post.")
    return post
