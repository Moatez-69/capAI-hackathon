import re
import requests
from typing import Optional

from app.models.founder import DevToData, DevToArticle

BASE = "https://dev.to/api"
HEADERS = {"User-Agent": "founder-engine/1.0"}


def _username_candidates(name: str) -> list[str]:
    parts = name.lower().split()
    candidates = [
        "".join(parts),
        "_".join(parts),
        parts[0],
        parts[-1],
        parts[0] + parts[-1][0] if len(parts) > 1 else parts[0],
    ]
    return list(dict.fromkeys(candidates))  # dedupe, preserve order


def _fetch_user(username: str) -> Optional[dict]:
    try:
        resp = requests.get(f"{BASE}/users/by_username?url={username}", headers=HEADERS, timeout=8)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def _fetch_articles(username: str) -> list[DevToArticle]:
    try:
        resp = requests.get(
            f"{BASE}/articles",
            params={"username": username, "per_page": 20},
            headers=HEADERS,
            timeout=8,
        )
        if resp.status_code == 200:
            articles = []
            for a in resp.json():
                articles.append(DevToArticle(
                    title=a.get("title", ""),
                    url=a.get("url", ""),
                    tags=a.get("tag_list", []),
                    reactions=a.get("positive_reactions_count", 0),
                    comments=a.get("comments_count", 0),
                    published_at=a.get("published_at"),
                ))
            return articles
    except Exception:
        pass
    return []


def _name_matches(user: dict, full_name: str, username: str) -> bool:
    """Verify the DEV.to profile actually matches the founder."""
    expected_parts = full_name.lower().split()
    profile_name = (user.get("name") or "").lower()

    # all name parts must appear in profile name
    all_match = all(part in profile_name for part in expected_parts)
    if all_match:
        return True

    # if username is a single common word (e.g. "scott"), require full name match
    if len(username) < 8 and "_" not in username:
        return False

    # at least first AND last name must match
    if len(expected_parts) >= 2:
        return expected_parts[0] in profile_name and expected_parts[-1] in profile_name

    return False


def collect_devto(name: str, github_username: Optional[str] = None) -> Optional[DevToData]:
    candidates = _username_candidates(name)
    if github_username:
        candidates.insert(0, github_username.lower())

    for username in candidates:
        user = _fetch_user(username)
        if user and not user.get("error"):
            if not _name_matches(user, name, username):
                print(f"[devto] @{username} exists but name '{user.get('name')}' doesn't match '{name}' — skipping")
                continue
            print(f"[devto] found profile: @{username}")
            articles = _fetch_articles(username)
            return DevToData(
                username=username,
                name=user.get("name"),
                bio=user.get("summary"),
                twitter_username=user.get("twitter_username"),
                github_username=user.get("github_username"),
                website_url=user.get("website_url"),
                joined_at=user.get("joined_at"),
                profile_url=f"https://dev.to/{username}",
                articles=articles,
            )

    print(f"[devto] no profile found for '{name}'")
    return None
