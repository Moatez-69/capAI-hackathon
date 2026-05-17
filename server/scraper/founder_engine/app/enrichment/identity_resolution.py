import re
import requests
from bs4 import BeautifulSoup
from typing import Optional
from app.models.founder import LinkedInProfile


GITHUB_PATTERN = re.compile(r"github\.com/([A-Za-z0-9_-]+)", re.IGNORECASE)
TWITTER_PATTERN = re.compile(r"(?:twitter|x)\.com/([A-Za-z0-9_]+)", re.IGNORECASE)
URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
LINKEDIN_PROFILE_PATTERN = re.compile(r"https?://(?:www\.)?linkedin\.com/in/([A-Za-z0-9_-]+)", re.IGNORECASE)
GITHUB_PROFILE_PATTERN = re.compile(r"https?://(?:www\.)?github\.com/([A-Za-z0-9_-]+)", re.IGNORECASE)

GITHUB_SKIP_SLUGS = {
    "features", "pricing", "about", "enterprise", "topics", "explore",
    "marketplace", "sponsors", "login", "signup", "orgs", "settings",
    "notifications", "pulls", "issues", "actions", "codespaces",
}

SEARCH_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _extract_linkedin_from_html(html: str) -> Optional[str]:
    """Scan raw HTML for any linkedin.com/in/ profile URL."""
    for match in LINKEDIN_PROFILE_PATTERN.finditer(html):
        slug = match.group(1)
        # skip generic/nav slugs
        if slug.lower() not in ("login", "signup", "feed", "jobs", "learning", "pub"):
            return f"https://www.linkedin.com/in/{slug}"
    return None


def _search_ddg(query: str) -> Optional[str]:
    try:
        session = requests.Session()
        # warm up session to get cookies
        session.get("https://duckduckgo.com/", headers=SEARCH_HEADERS, timeout=8)
        resp = session.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers=SEARCH_HEADERS,
            timeout=10,
        )
        if resp.status_code == 200 and "linkedin.com/in/" in resp.text:
            url = _extract_linkedin_from_html(resp.text)
            if url:
                print(f"[identity] found LinkedIn via DDG: {url}")
                return url
    except Exception as e:
        print(f"[identity] DDG error: {e}")
    return None


def _search_bing(query: str) -> Optional[str]:
    try:
        resp = requests.get(
            "https://www.bing.com/search",
            params={"q": query},
            headers=SEARCH_HEADERS,
            timeout=10,
        )
        if resp.status_code == 200 and "linkedin.com/in/" in resp.text:
            url = _extract_linkedin_from_html(resp.text)
            if url:
                print(f"[identity] found LinkedIn via Bing: {url}")
                return url
    except Exception as e:
        print(f"[identity] Bing error: {e}")
    return None


def _search_brave(query: str) -> Optional[str]:
    try:
        resp = requests.get(
            "https://search.brave.com/search",
            params={"q": query},
            headers=SEARCH_HEADERS,
            timeout=10,
        )
        if resp.status_code == 200 and "linkedin.com/in/" in resp.text:
            url = _extract_linkedin_from_html(resp.text)
            if url:
                print(f"[identity] found LinkedIn via Brave: {url}")
                return url
    except Exception as e:
        print(f"[identity] Brave error: {e}")
    return None


def _extract_github_username_from_html(html: str) -> Optional[str]:
    for match in GITHUB_PROFILE_PATTERN.finditer(html):
        slug = match.group(1)
        if slug.lower() not in GITHUB_SKIP_SLUGS and "." not in slug:
            return slug
    return None


def _verify_github_username(username: str, full_name: str) -> bool:
    """Confirm username is a real user account. Name match is best-effort —
    many devs use handles instead of real names, so we trust the search engine."""
    try:
        resp = requests.get(
            f"https://api.github.com/users/{username}",
            headers={"Accept": "application/vnd.github+json"},
            timeout=8,
        )
        if resp.status_code != 200:
            return False
        data = resp.json()
        # reject org accounts
        if data.get("type", "").lower() == "organization":
            return False
        profile_name = (data.get("name") or "").lower()
        name_parts = [p for p in full_name.lower().split() if len(p) > 2]
        # strong match: all name parts in profile name
        if name_parts and all(part in profile_name for part in name_parts):
            return True
        # weak match: at least one name part in profile — accept since search already matched
        if name_parts and any(part in profile_name for part in name_parts):
            return True
        # no name on profile (display name blank) — still accept, search engine matched it
        if not profile_name:
            return True
        # profile has a name but nothing matches — likely wrong person
        return False
    except Exception:
        return False


def _search_github_ddg(query: str) -> Optional[str]:
    try:
        session = requests.Session()
        session.get("https://duckduckgo.com/", headers=SEARCH_HEADERS, timeout=8)
        resp = session.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers=SEARCH_HEADERS,
            timeout=10,
        )
        if resp.status_code == 200 and "github.com/" in resp.text:
            return _extract_github_username_from_html(resp.text)
    except Exception:
        pass
    return None


def _search_github_bing(query: str) -> Optional[str]:
    try:
        resp = requests.get(
            "https://www.bing.com/search",
            params={"q": query},
            headers=SEARCH_HEADERS,
            timeout=10,
        )
        if resp.status_code == 200 and "github.com/" in resp.text:
            return _extract_github_username_from_html(resp.text)
    except Exception:
        pass
    return None


def _search_github_brave(query: str) -> Optional[str]:
    try:
        resp = requests.get(
            "https://search.brave.com/search",
            params={"q": query},
            headers=SEARCH_HEADERS,
            timeout=10,
        )
        if resp.status_code == 200 and "github.com/" in resp.text:
            return _extract_github_username_from_html(resp.text)
    except Exception:
        pass
    return None


def find_github_username(name: str) -> Optional[str]:
    """Search multiple engines for the founder's GitHub username, then verify via API."""
    queries = [
        f'"{name}" site:github.com',
        f'{name} github profile',
        f'{name} github developer',
    ]

    seen: set[str] = set()
    for query in queries:
        for engine_fn in [_search_github_ddg, _search_github_bing, _search_github_brave]:
            username = engine_fn(query)
            if username and username not in seen:
                seen.add(username)
                if _verify_github_username(username, name):
                    print(f"[identity] found GitHub via search: @{username}")
                    return username
                else:
                    print(f"[identity] GitHub @{username} skipped — likely wrong person")

    print(f"[identity] could not find GitHub username for '{name}'")
    return None


def find_linkedin_url(name: str) -> Optional[str]:
    """Search multiple engines for the founder's LinkedIn profile URL."""
    query = f'"{name}" site:linkedin.com/in'

    for engine in [_search_ddg, _search_bing, _search_brave]:
        result = engine(query)
        if result:
            return result

    print(f"[identity] could not find LinkedIn URL for '{name}'")
    return None


def resolve_identities(profile: LinkedInProfile) -> dict:
    """Extract GitHub username, personal site, startup site, Twitter handle from LinkedIn data."""
    result = {
        "github_username": None,
        "personal_website": None,
        "startup_website": None,
        "twitter_handle": None,
    }

    # aggregate all text fields to search
    text_blobs = [
        profile.url or "",
        profile.about or "",
        profile.headline or "",
    ]
    for exp in profile.experience:
        text_blobs.append(exp.description or "")
        text_blobs.append(exp.company or "")

    combined = " ".join(text_blobs)

    # GitHub
    gh_match = GITHUB_PATTERN.search(combined)
    if gh_match:
        username = gh_match.group(1)
        # skip org pages (typically have path segments after)
        if username.lower() not in ("features", "pricing", "about", "enterprise", "topics"):
            result["github_username"] = username

    # Twitter
    tw_match = TWITTER_PATTERN.search(combined)
    if tw_match:
        handle = tw_match.group(1)
        if handle.lower() not in ("home", "share", "intent"):
            result["twitter_handle"] = handle

    # personal / startup websites
    urls = URL_PATTERN.findall(combined)
    skip_domains = {"linkedin.com", "github.com", "twitter.com", "x.com",
                    "instagram.com", "youtube.com", "facebook.com"}
    websites = []
    for url in urls:
        domain = re.sub(r"https?://(?:www\.)?", "", url).split("/")[0].lower()
        if domain and not any(s in domain for s in skip_domains):
            websites.append(url)

    if websites:
        result["personal_website"] = websites[0]
    if len(websites) > 1:
        result["startup_website"] = websites[1]

    # heuristic: if name looks like github username, try it
    if not result["github_username"] and profile.about:
        # look for @username patterns
        at_match = re.search(r"@([A-Za-z0-9_-]{3,39})", profile.about)
        if at_match:
            result["github_username"] = at_match.group(1)

    return result
