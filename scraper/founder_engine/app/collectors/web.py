import re
import requests
from bs4 import BeautifulSoup
from typing import Optional

from app.models.founder import WebPresence

TECH_SIGNATURES = {
    "React": ["react", "_next", "__react"],
    "Next.js": ["_next/static", "__NEXT_DATA__"],
    "Vue": ["vue.js", "vue.min.js", "__vue__"],
    "Nuxt": ["_nuxt/"],
    "Angular": ["ng-version", "angular"],
    "Svelte": ["svelte"],
    "WordPress": ["wp-content", "wp-includes"],
    "Tailwind": ["tailwind"],
    "Bootstrap": ["bootstrap"],
    "Django": ["csrftoken", "django"],
    "Flask": ["werkzeug"],
    "FastAPI": ["fastapi"],
    "Vercel": ["vercel"],
    "Netlify": ["netlify"],
    "Ghost": ["ghost-theme"],
    "Webflow": ["webflow"],
    "Framer": ["framer.com"],
}

SOCIAL_PATTERNS = [
    r"https?://(?:www\.)?twitter\.com/[A-Za-z0-9_]+",
    r"https?://(?:www\.)?x\.com/[A-Za-z0-9_]+",
    r"https?://(?:www\.)?linkedin\.com/in/[A-Za-z0-9_-]+",
    r"https?://(?:www\.)?github\.com/[A-Za-z0-9_-]+",
    r"https?://(?:www\.)?instagram\.com/[A-Za-z0-9_.]+",
    r"https?://(?:www\.)?youtube\.com/(?:c/|channel/|@)[A-Za-z0-9_-]+",
]


def collect_web(url: str) -> WebPresence:
    presence = WebPresence(personal_website=url)

    try:
        resp = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        resp.raise_for_status()
        html = resp.text
        soup = BeautifulSoup(html, "html.parser")

        # title
        title_tag = soup.find("title")
        if title_tag:
            presence.page_title = title_tag.get_text(strip=True)

        # meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            presence.meta_description = meta_desc.get("content", "").strip()

        # technologies
        html_lower = html.lower()
        for tech, sigs in TECH_SIGNATURES.items():
            if any(s in html_lower for s in sigs):
                presence.technologies.append(tech)

        # social links
        found_links: set[str] = set()
        for pattern in SOCIAL_PATTERNS:
            matches = re.findall(pattern, html, re.IGNORECASE)
            found_links.update(matches)
        presence.social_links = list(found_links)

        # startup/company refs — collect all anchor hrefs
        all_links = [a.get("href", "") for a in soup.find_all("a", href=True)]
        external = [l for l in all_links if l.startswith("http") and url not in l]
        # pick first non-social external link as potential startup site
        social_domains = {"twitter.com", "x.com", "linkedin.com", "github.com",
                          "instagram.com", "youtube.com", "facebook.com"}
        for link in external:
            domain = re.sub(r"https?://(?:www\.)?", "", link).split("/")[0]
            if domain and not any(s in domain for s in social_domains):
                presence.startup_website = link
                break

    except Exception as e:
        print(f"[web] error fetching {url}: {e}")

    return presence
