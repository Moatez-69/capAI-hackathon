"""
Normalize variable-field-name LinkedIn profiles to a canonical internal format.
Different scrapers use different field names; this maps all known variants
to a consistent structure before any feature extraction happens.
"""
import re
from datetime import date, datetime

REFERENCE_DATE = date(2024, 12, 31)  # "use today (2024)" per spec


def _pick(d, *keys, default=None):
    for k in keys:
        if k in d:
            return d[k]
    return default


def _parse_date(val):
    if val is None:
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, dict):
        year = val.get("year")
        month = val.get("month", 1)
        day = val.get("day", 1)
        if year:
            try:
                return date(int(year), int(month), int(day))
            except (ValueError, TypeError):
                try:
                    return date(int(year), 1, 1)
                except Exception:
                    return None
        return None
    if isinstance(val, (int, float)):
        try:
            return date(int(val), 1, 1)
        except Exception:
            return None
    if isinstance(val, str):
        val = val.strip()
        if not val or val.lower() in ("present", "current", "now", "today"):
            return None
        for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
            try:
                return datetime.strptime(val, fmt).date()
            except ValueError:
                pass
        for fmt in ("%B %Y", "%b %Y", "%B, %Y", "%b, %Y"):
            try:
                return datetime.strptime(val, fmt).date()
            except ValueError:
                pass
        m = re.search(r'\b(19|20)\d{2}\b', val)
        if m:
            return date(int(m.group()), 1, 1)
    return None


def duration_months(start, end=None):
    if start is None:
        return None
    ref = end if end else REFERENCE_DATE
    months = (ref.year - start.year) * 12 + (ref.month - start.month)
    return max(0, months)


def normalize_profile(raw: dict) -> dict:
    p = raw

    name_raw = _pick(p, "fullName", "full_name", "name", "person_name", default="")
    if isinstance(name_raw, dict):
        first = name_raw.get("first", name_raw.get("firstName", ""))
        last = name_raw.get("last", name_raw.get("lastName", ""))
        name = f"{first} {last}".strip()
    else:
        name = str(name_raw or "")

    headline = str(_pick(p, "headline", "title", "tagline", default="") or "")
    about = str(_pick(p, "about", "summary", "description", "bio", default="") or "")

    location_raw = _pick(p, "location", "locationName", "geo", default="")
    if isinstance(location_raw, dict):
        location_raw = location_raw.get("name", location_raw.get("country", ""))
    location = str(location_raw or "")

    connections = _parse_int(_pick(p, "connections", "connectionsCount", "connection_count", default=None))
    followers = _parse_int(_pick(p, "followers", "followersCount", "follower_count", default=None))

    exp_raw = _pick(p, "experience", "experiences", "positions", "work", "workExperience", "jobs", default=[])
    experience = [_normalize_job(j) for j in (exp_raw or [])]

    edu_raw = _pick(p, "education", "educations", "schools", "academic_background", default=[])
    education = [_normalize_edu(e) for e in (edu_raw or [])]

    skills_raw = _pick(p, "skills", "skill_list", "skillEndorsements", "topSkills", default=[])
    skills = _normalize_skills(skills_raw or [])

    github_raw = _pick(p, "github", "githubProfile", "github_data", "github_stats", default=None)
    if github_raw is None:
        urls = _pick(p, "websites", "website", "links", "urls", default=[])
        if isinstance(urls, str):
            urls = [urls]
        for url in (urls or []):
            if "github.com" in str(url):
                github_raw = {"url": url}
                break
    github = _normalize_github(github_raw or {})

    certs_raw = _pick(p, "certifications", "certificates", "licensesCertifications", default=[])
    certifications = [_normalize_cert(c) for c in (certs_raw or [])]

    publications = list(_pick(p, "publications", "articles", default=[]) or [])
    patents = list(_pick(p, "patents", default=[]) or [])
    awards = list(_pick(p, "honors", "awards", "honorsAwards", "achievements", default=[]) or [])
    volunteer = list(_pick(p, "volunteer", "volunteering", "communityInvolvement", default=[]) or [])

    return {
        "name": name,
        "headline": headline,
        "about": about,
        "location": location,
        "connections": connections,
        "followers": followers,
        "experience": experience,
        "education": education,
        "skills": skills,
        "github": github,
        "certifications": certifications,
        "publications": publications,
        "patents": patents,
        "awards": awards,
        "volunteer": volunteer,
        "_raw": raw,
    }


def _parse_int(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return int(val)
    if isinstance(val, str):
        m = re.search(r'\d[\d,]*', val)
        return int(m.group().replace(",", "")) if m else None
    return None


def _normalize_job(j: dict) -> dict:
    title = str(_pick(j, "title", "position", "jobTitle", "role", default="") or "")

    company_raw = _pick(j, "company", "companyName", "organization", "employer", "company_name", default="")
    if isinstance(company_raw, dict):
        company = str(company_raw.get("name", company_raw.get("companyName", "")) or "")
    else:
        company = str(company_raw or "")

    start = _parse_date(_pick(j, "startDate", "start_date", "startedOn", "start", "from", default=None))

    end_raw = _pick(j, "endDate", "end_date", "finishedOn", "end", "to", default=None)
    is_current_raw = _pick(j, "isCurrent", "is_current", "current", "isCurrentRole", default=None)

    if str(end_raw or "").lower() in ("present", "current", "now", ""):
        end = None
    else:
        end = _parse_date(end_raw)

    if is_current_raw is True:
        end = None

    description = str(_pick(j, "description", "summary", "duties", "responsibilities", default="") or "")
    location = str(_pick(j, "location", "locationName", default="") or "")

    return {
        "title": title,
        "company": company,
        "start": start,
        "end": end,
        "is_current": end is None and start is not None,
        "description": description,
        "location": location,
        "duration_months": duration_months(start, end),
    }


def _normalize_edu(e: dict) -> dict:
    school_raw = _pick(e, "school", "schoolName", "institution", "university", "college", default="")
    if isinstance(school_raw, dict):
        school = str(school_raw.get("name", "") or "")
    else:
        school = str(school_raw or "")

    degree = str(_pick(e, "degree", "degreeType", "degree_name", "degreeName", "qualification", default="") or "")
    field = str(_pick(e, "fieldOfStudy", "field_of_study", "field", "major", "subject", default="") or "")

    start = _parse_date(_pick(e, "startDate", "start_date", "startedOn", "start", default=None))

    end_raw = _pick(e, "endDate", "end_date", "finishedOn", "end", default=None)
    is_current_raw = _pick(e, "isCurrent", "is_current", "current", default=None)

    if str(end_raw or "").lower() in ("present", "current", "now"):
        end = None
    else:
        end = _parse_date(end_raw)

    if is_current_raw is True:
        end = None

    description = str(_pick(e, "description", "activities", "notes", default="") or "")

    return {
        "school": school,
        "degree": degree,
        "field": field,
        "start": start,
        "end": end,
        "is_current": is_current_raw or (end is None and start is not None),
        "description": description,
    }


def _normalize_skills(skills_raw) -> list:
    result = []
    for s in skills_raw:
        if isinstance(s, str):
            result.append({"name": s, "endorsements": None})
        elif isinstance(s, dict):
            name = str(_pick(s, "name", "skill", "title", default="") or "")
            endorsements = _pick(s, "endorsements", "endorsementCount", "endorsements_count", "numEndorsements", default=None)
            if isinstance(endorsements, (int, float)):
                endorsements = int(endorsements)
            result.append({"name": name, "endorsements": endorsements})
    return result


def _normalize_github(g: dict) -> dict:
    if not g:
        return {}

    account_created = _parse_date(_pick(g, "created_at", "createdAt", "account_created", "joined", default=None))

    languages_raw = _pick(g, "languages", "top_languages", "language_stats", default=[])
    if isinstance(languages_raw, dict):
        languages = list(languages_raw.keys())
    elif isinstance(languages_raw, list):
        languages = [l if isinstance(l, str) else (l.get("name", "") if isinstance(l, dict) else "") for l in languages_raw]
    else:
        languages = []

    repos_raw = _pick(g, "repos", "repositories", "repos_data", default=[])
    orgs_raw = _pick(g, "organizations", "orgs", default=[])

    return {
        "url": _pick(g, "url", "html_url", "github_url", "profile_url", default=None),
        "account_created": account_created,
        "public_repos": _parse_int(_pick(g, "public_repos", "publicRepos", "repos_count", default=None)),
        "total_repos": _parse_int(_pick(g, "total_repos", "totalRepos", default=None)),
        "followers": _parse_int(_pick(g, "followers", "followersCount", default=None)),
        "stars_received": _parse_int(_pick(g, "stars_received", "totalStars", "total_stars", default=None)),
        "forks_received": _parse_int(_pick(g, "forks_received", "totalForks", "total_forks", default=None)),
        "contribution_streak": _parse_int(_pick(g, "contribution_streak", "contributionStreak", "streak_days", default=None)),
        "commits_last_12m": _parse_int(_pick(g, "commits_last_12m", "commitsLastYear", "contributions_last_year", default=None)),
        "languages": [l for l in languages if l],
        "repos": repos_raw if isinstance(repos_raw, list) else [],
        "organizations": orgs_raw if isinstance(orgs_raw, list) else [],
    }


def _normalize_cert(c) -> dict:
    if isinstance(c, str):
        return {"name": c, "issuer": None, "date": None}
    if isinstance(c, dict):
        return {
            "name": str(_pick(c, "name", "title", "certName", "certificationName", default="") or ""),
            "issuer": str(_pick(c, "issuingOrganization", "issuer", "organization", "authority", default="") or ""),
            "date": _parse_date(_pick(c, "issuedOn", "issued_date", "date", "issuanceDate", default=None)),
        }
    return {"name": str(c), "issuer": None, "date": None}
