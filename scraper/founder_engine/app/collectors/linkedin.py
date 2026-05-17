import asyncio
import os
import aiohttp
from typing import Optional

from app.models.founder import (
    LinkedInProfile, ExperienceEntry, EducationEntry,
    CertificationEntry, RecommendationEntry, CompanyData,
)

REVERSECONTACT_API_KEY = os.getenv("REVERSECONTACT_API_KEY", "")
PERSON_URL = "https://api.reversecontact.com/v2/fetch/persons"
COMPANY_URL = "https://api.reversecontact.com/v2/fetch/companies"


def _auth_headers() -> dict:
    return {
        "Authorization": f"Bearer {REVERSECONTACT_API_KEY}",
        "Content-Type": "application/json",
    }


def _format_date_range(start: Optional[str], end: Optional[str]) -> Optional[str]:
    def _year(d: Optional[str]) -> Optional[str]:
        return d[:4] if d else None
    s, e = _year(start), _year(end)
    if s and e:
        return f"{s} – {e}"
    if s:
        return f"{s} – present"
    return None


async def _fetch_company(session: aiohttp.ClientSession, company_url: str) -> Optional[CompanyData]:
    try:
        async with session.post(
            COMPANY_URL,
            json={"url": company_url},
            timeout=aiohttp.ClientTimeout(total=20),
        ) as resp:
            if resp.status != 200:
                return None
            payload = await resp.json()
            if not payload.get("success"):
                return None
            d = payload.get("data", {})
            hq = d.get("headquarter") or {}
            hq_str = ", ".join(p for p in [hq.get("city"), hq.get("country")] if p) or None
            emp_range = d.get("employeeCountRange") or {}
            range_str = None
            if emp_range.get("start") and emp_range.get("end"):
                range_str = f"{emp_range['start']}–{emp_range['end']}"
            credits = payload.get("quotas", {}).get("workspace", {}).get("credits", {}).get("left")
            print(f"[linkedin] company enriched: {d.get('companyName')} — credits left: {credits}")
            return CompanyData(
                name=d.get("companyName"),
                linkedin_url=d.get("linkedinUrl"),
                website_url=d.get("websiteUrl"),
                description=d.get("description"),
                industry=d.get("industry"),
                employees_count=d.get("employeesCount"),
                employee_count_range=range_str,
                followers_count=d.get("followersCount"),
                founded_year=(d.get("foundedOn") or {}).get("year"),
                headquarters=hq_str,
                tagline=d.get("tagline"),
                specialities=d.get("specialities") or [],
            )
    except Exception as e:
        print(f"[linkedin] company fetch error: {e}")
    return None


async def collect_linkedin(url: str) -> LinkedInProfile:
    profile = LinkedInProfile(url=url)

    if not REVERSECONTACT_API_KEY:
        print("[linkedin] REVERSECONTACT_API_KEY not set — skipping")
        return profile

    try:
        async with aiohttp.ClientSession(headers=_auth_headers()) as session:
            # fetch person
            async with session.post(
                PERSON_URL,
                json={"url": url},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    print(f"[linkedin] API error {resp.status}")
                    return profile
                payload = await resp.json()

            if not payload.get("success"):
                print(f"[linkedin] API returned success=false: {payload.get('error')}")
                return profile

            d = payload.get("data", {})
            credits = payload.get("quotas", {}).get("workspace", {}).get("credits", {}).get("left")
            print(f"[linkedin] person collected — credits left: {credits}")

            # location
            loc = d.get("location") or {}
            location_str = ", ".join(p for p in [loc.get("city"), loc.get("state"), loc.get("country")] if p) or None

            # top-level profile fields
            profile.member_id = d.get("memberId")
            profile.public_id = d.get("publicId")
            profile.headline = d.get("headline")
            profile.location = location_str
            profile.country_code = loc.get("countryCode")
            profile.about = d.get("summary")
            profile.profile_image_url = d.get("photoUrl")
            profile.background_image_url = d.get("backgroundUrl")
            profile.followers_count = d.get("followersCount")
            profile.connections_count = d.get("connectionsCount")
            profile.is_open_to_work = d.get("isOpenToWork")
            profile.has_premium = d.get("hasPremium")
            profile.has_verification_badge = d.get("hasVerificationBadge")
            profile.creation_date = d.get("creationDate")
            profile.pronoun = d.get("pronoun")
            profile.spoken_languages = [l.get("name") for l in (d.get("languages") or []) if l.get("name")]
            profile.skills = [s for s in (d.get("skills") or []) if s]
            profile.test_scores = d.get("testScores") or []

            # recommendations
            for rec in d.get("recommendations") or []:
                profile.recommendations.append(RecommendationEntry(
                    recommender_name=rec.get("recommenderName") or rec.get("firstName"),
                    recommender_title=rec.get("recommenderTitle") or rec.get("headline"),
                    text=rec.get("text") or rec.get("description"),
                ))

            # certifications
            for cert in d.get("certifications") or []:
                profile.certifications.append(CertificationEntry(
                    name=cert.get("name"),
                    issuer=cert.get("authority"),
                    issued=cert.get("displaySource"),
                ))

            # education
            for edu in d.get("education") or []:
                dates = edu.get("startEndDate") or {}
                profile.education.append(EducationEntry(
                    institution=edu.get("schoolName"),
                    degree=edu.get("degreeName"),
                    field=edu.get("fieldOfStudy"),
                    years=_format_date_range(dates.get("start"), dates.get("end")),
                    description=edu.get("description"),
                    grade=edu.get("grade"),
                    school_url=edu.get("schoolUrl"),
                ))

            # experience entries (built first, enriched after)
            raw_experience = d.get("experience") or []
            for exp in raw_experience:
                dates = exp.get("startEndDate") or {}
                profile.experience.append(ExperienceEntry(
                    title=exp.get("title"),
                    company=exp.get("companyName"),
                    contract_type=exp.get("contractType"),
                    duration=_format_date_range(dates.get("start"), dates.get("end")),
                    location=exp.get("companyLocation"),
                    description=exp.get("description"),
                    company_linkedin_url=exp.get("companyUrl"),
                    company_logo_url=exp.get("companyLogoUrl"),
                ))

            # concurrently enrich companies that have a LinkedIn URL
            company_urls = [
                exp.get("companyUrl") for exp in raw_experience if exp.get("companyUrl")
            ]
            company_results = await asyncio.gather(
                *[_fetch_company(session, cu) for cu in company_urls]
            )

            # attach enrichment back to matching experience entries
            url_to_company: dict[str, CompanyData] = {
                cu: cd for cu, cd in zip(company_urls, company_results) if cd
            }
            for entry, raw_exp in zip(profile.experience, raw_experience):
                cu = raw_exp.get("companyUrl")
                if cu and cu in url_to_company:
                    entry.company_data = url_to_company[cu]

    except Exception as e:
        print(f"[linkedin] error: {e}")

    return profile
