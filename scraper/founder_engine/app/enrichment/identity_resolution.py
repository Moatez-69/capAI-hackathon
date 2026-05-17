import re
from typing import Optional
from app.models.founder import LinkedInProfile


GITHUB_PATTERN = re.compile(r"github\.com/([A-Za-z0-9_-]+)", re.IGNORECASE)
TWITTER_PATTERN = re.compile(r"(?:twitter|x)\.com/([A-Za-z0-9_]+)", re.IGNORECASE)
URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)


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
