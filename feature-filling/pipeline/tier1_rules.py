"""
Tier 1 rule-based feature extraction.
Pure arithmetic and logic from the normalized profile — no LLM needed.
Covers ~34 of the 102 features.
"""
import re
from datetime import date
from .normalize import REFERENCE_DATE, duration_months

# ── Lookup tables ──────────────────────────────────────────────────────────────

TECHNICAL_SKILLS = {
    # Languages — only unambiguous names (avoid single letters like "r", "c")
    "python", "javascript", "typescript", "java", "c++", "c#", "golang",
    "rust", "swift", "kotlin", "scala", "ruby", "php", "matlab", "julia",
    "haskell", "elixir", "clojure", "dart", "groovy", "perl", "fortran",
    # Web frameworks
    "react", "angular", "vue", "node.js", "nodejs", "django", "flask", "fastapi",
    "spring", "rails", "express", "next.js", "nextjs", "nuxt", "svelte",
    "laravel", "symfony", "asp.net",
    # Cloud / DevOps
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s",
    "terraform", "jenkins", "ansible", "ci/cd", "devops", "linux", "bash",
    "nginx", "prometheus", "grafana", "helm",
    # Databases
    "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "dynamodb", "cassandra", "neo4j", "sqlite", "oracle", "mssql", "clickhouse",
    # ML / AI
    "machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn",
    "keras", "nlp", "computer vision", "data science", "hugging face",
    "xgboost", "lightgbm", "spark", "hadoop", "airflow",
    # Mobile
    "ios", "android", "react native", "flutter", "xamarin",
    # Other tech
    "api", "rest api", "graphql", "microservices", "blockchain", "solidity",
    "git", "github", "gitlab", "jira", "agile", "scrum", "tdd",
}

ADVISORY_TITLE_KEYWORDS = {"advisor", "adviser", "advisory", "mentor", "board member", "board of directors"}
FOUNDER_TITLE_KEYWORDS = {"founder", "co-founder", "cofounder"}

# Compiled word-boundary patterns for reliable technical skill matching
_TECH_PATTERNS = [re.compile(r'\b' + re.escape(kw) + r'\b') for kw in TECHNICAL_SKILLS]


def _is_technical_skill(skill_name: str) -> bool:
    """True if the skill name matches a known technical keyword at a word boundary."""
    name = skill_name.lower()
    return any(pat.search(name) for pat in _TECH_PATTERNS)

# ── Classification lookup tables ───────────────────────────────────────────────

TOP_TUNISIAN_SCHOOLS = {
    "esprit", "enit", "ensi", "polytechnique tunis", "insat", "sup'com", "supcom",
    "esen", "ihec", "hec tunis",
}

TUNISIAN_SCHOOL_MARKERS = {
    "tunis", "tunisie", "tunisian", "sfax", "sousse", "monastir", "bizerte",
    "gafsa", "kairouan", "zaghouan", "nabeul", "ariana", "ben arous", "manouba",
    "iset", "isg", "fseg", "fst", "fss", "fshs", "isimg", "issat", "isi",
    "isamm", "esct", "essec", "islas", "isbm", "eniso", "enim", "insat", "uni",
}

EDU_FIELD_KEYWORDS = {
    0: {"engineering", "computer science", "informatique", "génie", "genie",
        "it ", "information technology", "mathematics", "mathématiques", "math",
        "electronics", "électronique", "electronique", "software", "systems",
        "télécommunications", "telecommunications", "networks", "réseaux"},
    1: {"business", "management", "finance", "economics", "économie",
        "commerce", "mba", "gestion", "marketing", "accounting", "comptabilité",
        "administration", "entrepreneurship", "supply chain", "logistics"},
    2: {"physics", "physique", "chemistry", "chimie", "biology", "biologie",
        "natural sciences", "sciences naturelles", "biochemistry",
        "environmental", "geology", "science"},
    3: {"medicine", "médecine", "pharmacy", "pharmacie", "dentistry",
        "médical", "medical", "nursing", "infirmier", "health sciences"},
    4: {"law", "droit", "juridique", "legal", "justice"},
}

EDU_DEGREE_KEYWORDS = {
    3: {"phd", "doctorate", "doctorat", "dr.", "thèse"},
    2: {"master", "msc", "m.sc", "mba", "m.b.a", "ingénieur", "ingenieur",
        "engineer", "licence professionnelle", "diplôme d'ingénieur",
        "diplome d ingenieur", "magister", "mastère"},
    1: {"bachelor", "licence", "l3", "b.sc", "bsc", "b.a.", "ba",
        "undergraduate", "licence 3", "bts", "dut"},
    0: {"baccalauréat", "baccalaureat", "bac", "high school", "lycée",
        "a-level", "ib diploma"},
}

SENIORITY_KEYWORDS = {
    4: {"founder", "co-founder", "cofounder", "ceo", "cto", "coo", "cpo",
        "cfo", "chief", "director", "vp ", "vice president", "president",
        "partner", "managing director", "md ", "executive director"},
    3: {"lead", "manager", "head of", "head,", "principal", "senior manager",
        "department head", "team lead", "group lead", "scrum master"},
    2: {"senior", "sr.", "sr ", "confirmed", "lead engineer", "staff engineer",
        "expert", "specialist", "confirmed"},
    1: {"engineer", "developer", "analyst", "associate", "consultant",
        "designer", "researcher", "scientist", "coordinator", "officer"},
    0: {"intern", "trainee", "stagiaire", "junior", "assistant", "apprentice"},
}


def infer_institution_tier(school: str) -> int | None:
    s = school.lower()
    if any(kw in s for kw in TOP_TUNISIAN_SCHOOLS):
        return 1
    if any(kw in s for kw in TUNISIAN_SCHOOL_MARKERS):
        return 2
    if school.strip():
        return 4  # Unknown foreign — conservative
    return None


def infer_edu_field(field: str, degree: str = "") -> int | None:
    text = (field + " " + degree).lower()
    for cat, keywords in EDU_FIELD_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return cat
    return 5  # other


def infer_degree_level(degree: str) -> int | None:
    d = degree.lower()
    for level in (3, 2, 1, 0):
        if any(kw in d for kw in EDU_DEGREE_KEYWORDS[level]):
            return level
    return None


def infer_seniority(title: str) -> int | None:
    t = title.lower()
    for level in (4, 3, 2, 1, 0):
        if any(kw in t for kw in SENIORITY_KEYWORDS[level]):
            return level
    return None


FOUNDING_HEADLINE_KEYWORDS = {
    "founder", "co-founder", "cofounder", "building", "ceo", "cto", "coo", "cpo",
    "creating", "launching", "making", "started", "working on",
}

STARTUP_ACT_KEYWORDS = {
    "startup act", "startup act tunisia", "labellisé startup act",
    "labellise startup act", "registered under startup act",
}

DOMAIN_PATTERNS = re.compile(
    r'\b[\w-]+\.(gg|com|io|app|ai|co|net|org|tech|dev|fr|tn)\b', re.IGNORECASE
)


def infer_headline_founding_signal(headline: str) -> int:
    h = headline.lower()
    return 1 if any(kw in h for kw in FOUNDING_HEADLINE_KEYWORDS) else 0


def infer_startup_act_label(profile: dict) -> int:
    """1 if any profile text mentions Startup Act Tunisia registration."""
    texts = [
        profile.get("about", ""),
        profile.get("headline", ""),
        *[j.get("description", "") for j in profile.get("experience", [])],
    ]
    combined = " ".join(texts).lower()
    return 1 if any(kw in combined for kw in STARTUP_ACT_KEYWORDS) else 0


def infer_registered_domain(profile: dict) -> int:
    """1 if a domain-like URL appears in about, headline, or experience."""
    texts = [
        profile.get("about", ""),
        profile.get("headline", ""),
        *[j.get("description", "") for j in profile.get("experience", [])],
        *[j.get("company", "") for j in profile.get("experience", [])],
    ]
    combined = " ".join(texts)
    return 1 if DOMAIN_PATTERNS.search(combined) else 0


  # Features where keyword rules are authoritative — LLM result is ignored
KEYWORD_AUTHORITATIVE = {
    "edu_institution_tier",
    "edu_field_category",
    "edu_degree_level",
    "edu_has_international_degree",
    "exp_seniority_level_current",
    "intent_linkedin_headline_founding_signal",
    "intent_has_startup_act_label",
    "intent_has_registered_domain",
}


def apply_keyword_fallbacks(profile: dict, features: dict) -> dict:
    """
    Compute features that are reliably derived from keyword lookups.
    For KEYWORD_AUTHORITATIVE features: always overwrites whatever LLM returned.
    For others: fills only when the existing value is None.
    """
    result = dict(features)
    education = profile.get("education", [])
    jobs = profile.get("experience", [])
    headline = profile.get("headline", "")

    # edu_institution_tier — always use rule (LLM hallucinates Tunisian rankings)
    if education:
        tiers = [infer_institution_tier(e.get("school", "")) for e in education]
        tiers = [t for t in tiers if t is not None]
        if tiers:
            result["edu_institution_tier"] = min(tiers)

    # edu_field_category — always use rule
    if education:
        for e in education:
            cat = infer_edu_field(e.get("field", ""), e.get("degree", ""))
            if cat is not None:
                result["edu_field_category"] = cat
                break

    # edu_degree_level — always use rule
    if education:
        levels = [infer_degree_level(e.get("degree", "")) for e in education]
        levels = [l for l in levels if l is not None]
        if levels:
            result["edu_degree_level"] = max(levels)

    # edu_has_international_degree — always use rule
    if education:
        intl = 0
        for e in education:
            t = infer_institution_tier(e.get("school", ""))
            if t in (3, 4):
                intl = 1
                break
        result["edu_has_international_degree"] = intl

    # exp_seniority_level_current — always use rule
    if jobs:
        current_jobs = [j for j in jobs if j.get("is_current")]
        if not current_jobs:
            current_jobs = sorted(jobs, key=lambda j: j.get("start") or date.min, reverse=True)[:1]
        for j in current_jobs:
            s = infer_seniority(j.get("title", ""))
            if s is not None:
                result["exp_seniority_level_current"] = s
                break

    # intent_linkedin_headline_founding_signal — always use rule (headline text is deterministic)
    result["intent_linkedin_headline_founding_signal"] = infer_headline_founding_signal(headline)

    # intent_has_startup_act_label — always use rule (keyword match in profile text)
    result["intent_has_startup_act_label"] = infer_startup_act_label(profile)

    # intent_has_registered_domain — always use rule (URL pattern match)
    result["intent_has_registered_domain"] = infer_registered_domain(profile)

    return result


# ── Helper: interval union ─────────────────────────────────────────────────────

def _union_months(intervals):
    """Total months covered by a set of (start, end) date pairs, merging overlaps."""
    valid = [(s, e) for s, e in intervals if s is not None]
    if not valid:
        return 0
    valid.sort(key=lambda x: x[0])
    merged = [list(valid[0])]
    for s, e in valid[1:]:
        if s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    total = sum(
        (e.year - s.year) * 12 + (e.month - s.month)
        for s, e in merged
    )
    return max(0, total)


# ── Block 1 — Academic ─────────────────────────────────────────────────────────

def extract_academic_tier1(profile: dict) -> dict:
    education = profile.get("education", [])

    # edu_years_since_graduation: years since most recent completed degree
    completed = [e for e in education if e.get("end") and not e.get("is_current")]
    if completed:
        latest_grad = max(e["end"] for e in completed)
        years_since = (REFERENCE_DATE.year - latest_grad.year) + (
            (REFERENCE_DATE.month - latest_grad.month) / 12
        )
        edu_years_since_graduation = round(years_since, 1)
    else:
        edu_years_since_graduation = None

    # edu_studied_abroad_duration_months: sum months at non-Tunisian institutions
    TUNISIAN_MARKERS = {"tunis", "tunisie", "tunisia", "sfax", "sousse", "monastir",
                        "bizerte", "gafsa", "kairouan", "zaghouan", "nabeul"}
    abroad_months = 0
    for e in education:
        school = (e.get("school") or "").lower()
        location_field = (e.get("description") or "").lower()
        is_tunisian = any(m in school or m in location_field for m in TUNISIAN_MARKERS)
        # Also flag exchange/Erasmus mentions
        is_exchange = any(kw in (e.get("description") or "").lower()
                          for kw in ("exchange", "erasmus", "semester abroad", "abroad"))
        if not is_tunisian or is_exchange:
            dur = duration_months(e.get("start"), e.get("end") if not e.get("is_current") else None)
            if dur:
                abroad_months += dur

    return {
        "edu_years_since_graduation": edu_years_since_graduation,
        "edu_studied_abroad_duration_months": abroad_months,
    }


# ── Block 2 — Professional Experience ─────────────────────────────────────────

def extract_experience_tier1(profile: dict) -> dict:
    jobs = profile.get("experience", [])

    # exp_total_years: union of all job intervals
    intervals = [
        (j["start"], j["end"] or REFERENCE_DATE)
        for j in jobs if j.get("start")
    ]
    total_months = _union_months(intervals)
    exp_total_years = round(total_months / 12, 1) if total_months else 0

    # exp_number_of_employers: distinct company names
    companies = {j["company"].lower().strip() for j in jobs if j.get("company")}
    exp_number_of_employers = len(companies)

    # exp_avg_tenure_months + exp_longest_tenure_months: per-company total duration
    company_durations: dict[str, float] = {}
    for j in jobs:
        c = (j.get("company") or "").lower().strip()
        dur = j.get("duration_months")
        if c and dur is not None:
            company_durations[c] = company_durations.get(c, 0) + dur

    if company_durations:
        durations = list(company_durations.values())
        exp_avg_tenure_months = round(sum(durations) / len(durations), 1)
        exp_longest_tenure_months = round(max(durations), 1)
    else:
        exp_avg_tenure_months = None
        exp_longest_tenure_months = None

    return {
        "exp_total_years": exp_total_years,
        "exp_number_of_employers": exp_number_of_employers,
        "exp_avg_tenure_months": exp_avg_tenure_months,
        "exp_longest_tenure_months": exp_longest_tenure_months,
    }


# ── Block 3 — Entrepreneurial History ─────────────────────────────────────────

def extract_entrepreneurial_tier1(profile: dict) -> dict:
    jobs = profile.get("experience", [])

    # Identify all founder roles
    founder_jobs = [
        j for j in jobs
        if any(kw in (j.get("title") or "").lower() for kw in FOUNDER_TITLE_KEYWORDS)
    ]

    if not founder_jobs:
        return {
            "entre_number_of_prior_ventures": 0,
            "entre_has_prior_venture": 0,
            "entre_is_repeat_founder": 0,
            "entre_avg_time_between_ventures_months": None,
        }

    # Sort by start date descending; most recent = current venture
    founder_jobs_sorted = sorted(
        founder_jobs,
        key=lambda j: j.get("start") or date.min,
        reverse=True,
    )
    current_company = (founder_jobs_sorted[0].get("company") or "").lower().strip()

    # Prior ventures: distinct companies that are not the current one
    seen: set[str] = {current_company}
    prior_ventures = []
    for j in founder_jobs_sorted[1:]:
        c = (j.get("company") or "").lower().strip()
        if c and c not in seen:
            seen.add(c)
            prior_ventures.append(j)

    n_prior = len(prior_ventures)

    # Average gap between consecutive ventures
    avg_gap = None
    if n_prior >= 2:
        # Sort prior ventures by start ascending
        pv_sorted = sorted(prior_ventures, key=lambda j: j.get("start") or date.min)
        gaps = []
        for i in range(1, len(pv_sorted)):
            prev_end = pv_sorted[i - 1].get("end")
            next_start = pv_sorted[i].get("start")
            if prev_end and next_start:
                gap = duration_months(prev_end, next_start)
                if gap is not None:
                    gaps.append(gap)
        avg_gap = round(sum(gaps) / len(gaps), 1) if gaps else None

    return {
        "entre_number_of_prior_ventures": n_prior,
        "entre_has_prior_venture": 1 if n_prior > 0 else 0,
        "entre_is_repeat_founder": 1 if n_prior > 0 else 0,
        "entre_avg_time_between_ventures_months": avg_gap,
    }


# ── Block 4 — Technical Depth ──────────────────────────────────────────────────

def extract_technical_tier1(profile: dict) -> dict:
    gh = profile.get("github", {})
    skills = profile.get("skills", [])
    publications = profile.get("publications", [])
    patents = profile.get("patents", [])

    has_github = 1 if gh.get("url") else 0

    # GitHub account age
    created = gh.get("account_created")
    github_age_months = duration_months(created) if created else None

    public_repos = gh.get("public_repos")
    total_repos = gh.get("total_repos") or public_repos
    stars = gh.get("stars_received")
    forks = gh.get("forks_received")
    gh_followers = gh.get("followers")
    streak = gh.get("contribution_streak")
    commits_12m = gh.get("commits_last_12m")

    languages = gh.get("languages") or []
    lang_count = len(languages) if languages else None
    primary_lang = languages[0] if languages else None

    # Popular repo: any repo with > 100 stars (if we have star data)
    has_popular_repo = None
    repos = gh.get("repos") or []
    if repos:
        max_stars = max((r.get("stars", r.get("stargazers_count", 0)) or 0 for r in repos), default=0)
        has_popular_repo = 1 if max_stars >= 100 else 0
    elif stars is not None:
        # Heuristic: if total stars >= 100, likely has at least one popular repo
        has_popular_repo = 1 if stars >= 100 else 0

    # Skills — word-boundary matching to avoid false positives (e.g. "r" in "strategic")
    tech_count = sum(1 for s in skills if _is_technical_skill(s["name"]))
    endorsements = [s["endorsements"] for s in skills if s.get("endorsements") is not None]
    endorsement_max = max(endorsements) if endorsements else None

    # Publications / patents
    has_publications = 1 if publications else 0
    has_patents = 1 if patents else 0

    return {
        "tech_has_github": has_github,
        "tech_github_account_age_months": github_age_months,
        "tech_github_total_repos": total_repos,
        "tech_github_public_repos": public_repos,
        "tech_github_total_stars_received": stars,
        "tech_github_total_forks_received": forks,
        "tech_github_followers": gh_followers,
        "tech_github_contribution_streak_days": streak,
        "tech_github_commits_last_12m": commits_12m,
        "tech_github_languages_count": lang_count,
        "tech_github_primary_language": primary_lang,
        "tech_github_has_popular_repo": has_popular_repo,
        "tech_has_publications": has_publications,
        "tech_has_patents": has_patents,
        "tech_linkedin_skills_technical_count": tech_count,
        "tech_linkedin_skills_endorsement_max": endorsement_max,
    }


# ── Block 5 — Commercial & Leadership ─────────────────────────────────────────

def extract_commercial_tier1(profile: dict) -> dict:
    jobs = profile.get("experience", [])
    profile_followers = profile.get("followers")

    # Advisory roles from titles
    advisory_jobs = [
        j for j in jobs
        if any(kw in (j.get("title") or "").lower() for kw in ADVISORY_TITLE_KEYWORDS)
    ]
    n_advisory = len({(j.get("company") or "").lower() for j in advisory_jobs if j.get("company")})

    return {
        "comm_number_of_advisory_roles": n_advisory,
        "comm_linkedin_followers": profile_followers,
        # speaking_events_count and press_mentions_count need LLM
    }


# ── Block 6 — Network & Community ─────────────────────────────────────────────

def extract_network_tier1(profile: dict) -> dict:
    connections = profile.get("connections")
    jobs = profile.get("experience", [])

    # LinkedIn connections tier
    if connections is None:
        connections_tier = None
    elif connections >= 500:
        connections_tier = 4
    elif connections >= 300:
        connections_tier = 3
    elif connections >= 100:
        connections_tier = 2
    else:
        connections_tier = 1

    # Hackathon participations from experience titles
    hackathon_kw = {"hackathon", "hack", "hacking", "techcrunch disrupt", "startup weekend"}
    hackathon_jobs = [
        j for j in jobs
        if any(kw in (j.get("title") or "").lower() or kw in (j.get("company") or "").lower()
               for kw in hackathon_kw)
    ]
    n_hackathons = len(hackathon_jobs)

    # ecosystem_tenure_months: earliest startup / founder-related experience to today
    startup_kw = {"startup", "founder", "co-founder", "cofounder", "entrepreneur",
                  "accelerator", "incubator", "venture"}
    startup_jobs = [
        j for j in jobs
        if any(kw in (j.get("title") or "").lower() or kw in (j.get("company") or "").lower()
               or kw in (j.get("description") or "").lower()
               for kw in startup_kw)
        and j.get("start")
    ]
    if startup_jobs:
        earliest = min(j["start"] for j in startup_jobs)
        ecosystem_tenure = duration_months(earliest)
    else:
        ecosystem_tenure = None

    return {
        "net_linkedin_connections_tier": connections_tier,
        "net_hackathon_participations_count": n_hackathons,
        # hackathon_wins needs LLM
        "net_ecosystem_tenure_months": ecosystem_tenure,
    }


# ── Block 7 — Founding Intent ──────────────────────────────────────────────────

def extract_intent_tier1(profile: dict) -> dict:
    jobs = profile.get("experience", [])
    github = profile.get("github", {})

    # intent_quit_months_ago: months since most recently ended role (no new role after)
    ended_jobs = [j for j in jobs if j.get("end") and not j.get("is_current")]
    if ended_jobs:
        most_recent_end = max(j["end"] for j in ended_jobs)
        # Check if any job started after this end date
        later_jobs = [j for j in jobs if j.get("start") and j["start"] > most_recent_end]
        if not later_jobs:
            quit_months_ago = duration_months(most_recent_end)
        else:
            quit_months_ago = None
    else:
        quit_months_ago = None

    # intent_has_github_org: belongs to a GitHub organization
    orgs = github.get("organizations") or []
    has_github_org = 1 if orgs else 0

    # intent_github_org_age_months: from first org's created_at if available
    github_org_age = None
    for org in orgs:
        if isinstance(org, dict):
            created = org.get("created_at") or org.get("createdAt")
            if created:
                from .normalize import _parse_date
                d = _parse_date(created)
                if d:
                    github_org_age = duration_months(d)
                    break

    return {
        "intent_quit_months_ago": quit_months_ago,
        "intent_has_github_org": has_github_org,
        "intent_github_org_age_months": github_org_age,
        # intent_domain_registration_months_ago, intent_startup_act_months_ago
        # require structured data not typically in LinkedIn JSON — set null
        "intent_domain_registration_months_ago": None,
        "intent_startup_act_months_ago": None,
    }


# ── Aggregate Tier 1 extractor ─────────────────────────────────────────────────

def extract_tier1(profile: dict) -> dict:
    features = {}
    features.update(extract_academic_tier1(profile))
    features.update(extract_experience_tier1(profile))
    features.update(extract_entrepreneurial_tier1(profile))
    features.update(extract_technical_tier1(profile))
    features.update(extract_commercial_tier1(profile))
    features.update(extract_network_tier1(profile))
    features.update(extract_intent_tier1(profile))
    return features
