import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Optional

from app.collectors.linkedin import collect_linkedin
from app.collectors.github import collect_github
from app.collectors.web import collect_web
from app.collectors.product_hunt import collect_product_hunt
from app.collectors.devto import collect_devto
from app.enrichment.identity_resolution import resolve_identities
from app.models.founder import FounderProfile, FounderInput, Metadata, GitHubData, WebPresence

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../../output")


async def run_pipeline(input_data: FounderInput) -> FounderProfile:
    sources: list[str] = []
    missing: list[str] = []

    # step 1: LinkedIn
    linkedin_profile = await collect_linkedin(input_data.linkedin_url)
    if linkedin_profile:
        sources.append("linkedin")
    else:
        missing.append("linkedin")

    # step 2: identity resolution
    identities = {}
    if linkedin_profile:
        identities = resolve_identities(linkedin_profile)

    github_username: Optional[str] = (
        input_data.github_username or identities.get("github_username")
    )
    personal_website: Optional[str] = identities.get("personal_website")
    twitter_handle: Optional[str] = identities.get("twitter_handle")

    # step 3: GitHub (+ auto-detect personal website from blog field)
    github_data = GitHubData()
    if github_username:
        try:
            github_data = await collect_github(github_username)
            sources.append("github")
            # auto-wire GitHub blog URL if identity resolution found nothing
            if not personal_website and github_data.profile and github_data.profile.blog:
                blog = github_data.profile.blog.strip()
                if blog.startswith("http"):
                    personal_website = blog
                    print(f"[pipeline] personal website from GitHub blog: {personal_website}")
        except Exception as e:
            print(f"[pipeline] github collect failed: {e}")
            missing.append("github")
    else:
        missing.append("github")

    # step 4: web presence
    web_presence = WebPresence(
        personal_website=personal_website,
        startup_website=identities.get("startup_website"),
        twitter_handle=twitter_handle,
    )
    if personal_website:
        try:
            scraped = collect_web(personal_website)
            web_presence.technologies = scraped.technologies
            web_presence.social_links = scraped.social_links
            web_presence.page_title = scraped.page_title
            web_presence.meta_description = scraped.meta_description
            if scraped.startup_website and not web_presence.startup_website:
                web_presence.startup_website = scraped.startup_website
            sources.append("web")
        except Exception as e:
            print(f"[pipeline] web collect failed: {e}")
            missing.append("web")
    else:
        missing.append("web")

    # step 5: Product Hunt + DEV.to — run concurrently in threads (sync libs)
    loop = asyncio.get_event_loop()

    product_hunt_data, devto_data = await asyncio.gather(
        loop.run_in_executor(None, collect_product_hunt, input_data.name),
        loop.run_in_executor(None, collect_devto, input_data.name, github_username),
        return_exceptions=True,
    )

    if isinstance(product_hunt_data, Exception):
        print(f"[pipeline] product hunt failed: {product_hunt_data}")
        product_hunt_data = None
    if isinstance(devto_data, Exception):
        print(f"[pipeline] devto failed: {devto_data}")
        devto_data = None

    if product_hunt_data:
        sources.append("product_hunt")
    else:
        missing.append("product_hunt")

    if devto_data:
        sources.append("devto")
    else:
        missing.append("devto")

    profile = FounderProfile(
        name=input_data.name,
        linkedin=linkedin_profile,
        github=github_data,
        web_presence=web_presence,
        product_hunt=product_hunt_data,
        devto=devto_data,
        metadata=Metadata(
            collected_at=datetime.now(timezone.utc).isoformat(),
            sources=sources,
            missing_fields=missing,
        ),
    )

    _export(profile)
    return profile


def _export(profile: FounderProfile) -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    safe_name = profile.name.replace(" ", "_").lower()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = os.path.join(OUTPUT_DIR, f"{safe_name}_{ts}.json")
    with open(path, "w") as f:
        json.dump(profile.model_dump(), f, indent=2, default=str)
    print(f"[pipeline] exported → {path}")
