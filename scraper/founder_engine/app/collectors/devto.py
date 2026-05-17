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


def collect_devto(name: str, github_username: Optional[str] = None) -> Optional[DevToData]:
    candidates = _username_candidates(name)
    if github_username:
        candidates.insert(0, github_username.lower())

    for username in candidates:
        user = _fetch_user(username)
        if user and not user.get("error"):
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
