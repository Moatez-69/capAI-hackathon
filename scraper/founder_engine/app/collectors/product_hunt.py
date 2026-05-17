import re
import requests
from bs4 import BeautifulSoup
from typing import Optional

from app.models.founder import ProductHuntData, ProductHuntProduct

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


def _search_username(name: str) -> Optional[str]:
    """Try to find a Product Hunt username by searching for the founder name."""
    try:
        query = name.replace(" ", "+")
        resp = requests.get(
            f"https://www.producthunt.com/search/users?q={query}",
            headers=HEADERS,
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        # look for profile links like /@username — must be a clean profile URL, not subpages
        links = soup.find_all("a", href=re.compile(r"^/@[A-Za-z0-9_]+$"))
        if links:
            href = links[0].get("href", "")
            handle = href.lstrip("/@")
            # verify the linked name contains part of the founder name
            link_text = (links[0].get_text(strip=True) or "").lower()
            name_parts = name.lower().split()
            if not any(part in link_text for part in name_parts if len(part) > 2):
                return None
            return handle
    except Exception:
        pass
    return None


def _fetch_profile(handle: str) -> ProductHuntData:
    url = f"https://www.producthunt.com/@{handle}"
    ph = ProductHuntData(profile_url=url)

    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return ph

        soup = BeautifulSoup(resp.text, "html.parser")

        # follower count — look for text patterns like "123 Followers"
        follower_match = re.search(r"(\d[\d,]*)\s*[Ff]ollowers?", resp.text)
        if follower_match:
            ph.followers = int(follower_match.group(1).replace(",", ""))

        # products — cards with product links
        product_links = soup.find_all("a", href=re.compile(r"/posts/[^/]+$"))
        seen = set()
        for a in product_links:
            href = a.get("href", "")
            if href in seen:
                continue
            seen.add(href)

            name_el = a.find(["h3", "h2", "strong", "span"])
            name = name_el.get_text(strip=True) if name_el else href.split("/")[-1]
            if not name:
                continue

            ph.products.append(ProductHuntProduct(
                name=name,
                url=f"https://www.producthunt.com{href}",
            ))

    except Exception as e:
        print(f"[producthunt] error: {e}")

    return ph


def collect_product_hunt(name: str) -> Optional[ProductHuntData]:
    handle = _search_username(name)
    if not handle:
        print(f"[producthunt] no profile found for '{name}'")
        return None
    print(f"[producthunt] found handle: @{handle}")
    return _fetch_profile(handle)
