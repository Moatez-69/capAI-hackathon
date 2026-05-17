import asyncio
import base64
import os
import aiohttp
from typing import Optional

from app.models.founder import GitHubData, GitHubProfile, GitHubRepo, GitHubActivity

GITHUB_API = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
README_MAX_CHARS = 3000
ACTIVITY_LIMIT = 30


def _headers() -> dict:
    h = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h


async def _fetch_readme(session: aiohttp.ClientSession, username: str, repo_name: str) -> Optional[str]:
    try:
        async with session.get(f"{GITHUB_API}/repos/{username}/{repo_name}/readme") as resp:
            if resp.status == 200:
                d = await resp.json()
                raw = base64.b64decode(d.get("content", "")).decode("utf-8", errors="ignore")
                return raw[:README_MAX_CHARS].strip() or None
    except Exception:
        pass
    return None


async def _fetch_language_bytes(session: aiohttp.ClientSession, username: str, repo_name: str) -> dict[str, int]:
    try:
        async with session.get(f"{GITHUB_API}/repos/{username}/{repo_name}/languages") as resp:
            if resp.status == 200:
                return await resp.json()
    except Exception:
        pass
    return {}


async def collect_github(username: str) -> GitHubData:
    data = GitHubData(username=username)

    async with aiohttp.ClientSession(headers=_headers()) as session:

        # profile + repos + orgs + events — fetch top-level concurrently
        async def fetch_profile():
            try:
                async with session.get(f"{GITHUB_API}/users/{username}") as resp:
                    if resp.status == 200:
                        return await resp.json()
            except Exception as e:
                print(f"[github] profile error: {e}")
            return {}

        async def fetch_repos():
            try:
                async with session.get(
                    f"{GITHUB_API}/users/{username}/repos",
                    params={"per_page": 100, "sort": "updated"},
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
            except Exception as e:
                print(f"[github] repos error: {e}")
            return []

        async def fetch_orgs():
            try:
                async with session.get(f"{GITHUB_API}/users/{username}/orgs") as resp:
                    if resp.status == 200:
                        return await resp.json()
            except Exception as e:
                print(f"[github] orgs error: {e}")
            return []

        async def fetch_events():
            try:
                async with session.get(
                    f"{GITHUB_API}/users/{username}/events/public",
                    params={"per_page": ACTIVITY_LIMIT},
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
            except Exception as e:
                print(f"[github] events error: {e}")
            return []

        profile_raw, raw_repos, raw_orgs, raw_events = await asyncio.gather(
            fetch_profile(), fetch_repos(), fetch_orgs(), fetch_events()
        )

        # build profile
        if profile_raw:
            data.profile = GitHubProfile(
                username=profile_raw.get("login", username),
                bio=profile_raw.get("bio"),
                followers=profile_raw.get("followers", 0),
                following=profile_raw.get("following", 0),
                public_repos=profile_raw.get("public_repos", 0),
                location=profile_raw.get("location"),
                company=profile_raw.get("company"),
                blog=profile_raw.get("blog"),
                avatar_url=profile_raw.get("avatar_url"),
            )

        # organizations
        data.organizations = [o.get("login", "") for o in raw_orgs]

        # activity events
        for ev in raw_events:
            data.recent_activity.append(GitHubActivity(
                type=ev.get("type", ""),
                repo_name=ev.get("repo", {}).get("name", ""),
                created_at=ev.get("created_at", ""),
            ))

        # fetch READMEs + language bytes concurrently for all repos
        readme_tasks = [_fetch_readme(session, username, r.get("name", "")) for r in raw_repos]
        lang_tasks = [_fetch_language_bytes(session, username, r.get("name", "")) for r in raw_repos]

        readmes, lang_bytes_list = await asyncio.gather(
            asyncio.gather(*readme_tasks),
            asyncio.gather(*lang_tasks),
        )

        total_lang_bytes: dict[str, int] = {}

        for r, readme, lang_bytes in zip(raw_repos, readmes, lang_bytes_list):
            for lang, count in lang_bytes.items():
                total_lang_bytes[lang] = total_lang_bytes.get(lang, 0) + count

            data.repositories.append(GitHubRepo(
                name=r.get("name", ""),
                description=r.get("description"),
                readme=readme,
                language=r.get("language"),
                language_bytes=lang_bytes,
                stars=r.get("stargazers_count", 0),
                forks=r.get("forks_count", 0),
                topics=r.get("topics", []),
                created_at=r.get("created_at"),
                updated_at=r.get("updated_at"),
                url=r.get("html_url", ""),
            ))

        data.language_bytes_total = dict(
            sorted(total_lang_bytes.items(), key=lambda x: x[1], reverse=True)
        )
        data.languages = list(data.language_bytes_total.keys())

    return data
