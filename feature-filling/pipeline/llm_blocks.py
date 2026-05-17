"""
LLM-based feature extraction — 7 blocks, one Ollama call each.
Each block receives the relevant slice of the normalized profile as JSON,
plus the feature definitions from the spec, and returns structured JSON.
"""
import json
import time
import ollama

MODEL = "qwen2.5:1.5b"
MAX_RETRIES = 3

SYSTEM_PROMPT = (
    "You are a feature extractor for a founder scoring system. "
    "You receive profile data in JSON. Extract exactly the features listed. "
    "Return ONLY valid JSON with the exact keys shown. "
    "Use null for any feature not determinable from the data. "
    "Never guess. Never invent values not present in the profile."
)


def _llm_call(user_content: str, block_name: str) -> dict:
    for attempt in range(MAX_RETRIES):
        try:
            response = ollama.chat(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                format="json",
            )
            raw = response["message"]["content"]
            return json.loads(raw)
        except json.JSONDecodeError as e:
            if attempt == MAX_RETRIES - 1:
                print(f"  [WARN] {block_name} JSON parse failed after {MAX_RETRIES} attempts: {e}")
                return {}
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                print(f"  [WARN] {block_name} LLM call failed: {e}")
                return {}
            time.sleep(1)
    return {}


def _coerce(val, typ):
    """Coerce val to typ, returning None on failure."""
    if val is None:
        return None
    if typ == "int":
        try:
            return int(val)
        except (TypeError, ValueError):
            return None
    if typ == "float":
        try:
            return float(val)
        except (TypeError, ValueError):
            return None
    if typ == "float01":
        # float capped to [0, 1]
        try:
            return max(0.0, min(1.0, float(val)))
        except (TypeError, ValueError):
            return None
    if typ == "binary":
        if val in (0, 1):
            return val
        if isinstance(val, bool):
            return 1 if val else 0
        try:
            v = int(val)
            return v if v in (0, 1) else None
        except (TypeError, ValueError):
            return None
    if typ == "str":
        return str(val)
    return val


def _validate(raw: dict, schema: dict) -> dict:
    """Apply schema coercions; fill missing keys with None."""
    out = {}
    for key, typ in schema.items():
        out[key] = _coerce(raw.get(key), typ)
    return out


# ── Block 1 — Academic ─────────────────────────────────────────────────────────

def block1_academic(profile: dict) -> dict:
    edu_data = json.dumps(profile.get("education", []), default=str)
    awards_data = json.dumps(profile.get("awards", []), default=str)

    prompt = f"""=== EDUCATION DATA ===
{edu_data}

=== AWARDS/HONORS ===
{awards_data}

Extract these 7 features. Return JSON with exactly these keys:

edu_institution_tier (int):
  1 = top Tunisian: ESPRIT, ENIT, ENSI, Polytechnique Tunis, INSAT, SUP'COM, ESEN
  2 = other Tunisian institution — includes: ISET (any campus), ISG, IHEC, FSEG, FST, FSS, FSHS, ISIMG, ISSAT, ISI, ISAMM, ESCT, ESSEC, universities of Tunis/Sfax/Sousse/Monastir/Gafsa/Bizerte/Kairouan/Zaghouan and any school in Tunisia
  3 = internationally ranked foreign university (QS/THE top 500)
  4 = other foreign institution
  Best tier across multiple degrees. null if no education.
  IMPORTANT: any school with "Zaghouan", "Tunisie", "Tunisia", "ISET", "ISG", "FST", "FSEG" in name = tier 1 or 2 (Tunisian).

edu_field_category (int):
  0 = engineering, computer science, IT, mathematics, electronics
  1 = business, management, finance, economics, MBA
  2 = natural sciences, physics, chemistry, biology
  3 = medicine, pharmacy, dentistry
  4 = law
  5 = other
  null if absent.

edu_degree_level (int):
  0 = high school / baccalaureate
  1 = bachelor / licence (3-year degree)
  2 = master / engineering degree (5 years) / MBA
  3 = PhD / doctorate
  Highest degree found. null if none.

edu_is_dropout (0 or 1):
  1 = education entry has a start year but no graduation year AND work history shows employment during expected study years. 0 otherwise. Do NOT set 1 if currently enrolled.

edu_has_international_degree (0 or 1):
  1 if at least one degree is from a non-Tunisian institution. 0 otherwise.

edu_has_exchange_program (0 or 1):
  1 if exchange, Erasmus, semester abroad, or joint degree is mentioned. 0 otherwise.

edu_has_academic_award (0 or 1):
  1 if any scholarship, award, honor, distinction, valedictorian, or prize is mentioned. 0 otherwise.

Return exactly:
{{"edu_institution_tier": ..., "edu_field_category": ..., "edu_degree_level": ..., "edu_is_dropout": ..., "edu_has_international_degree": ..., "edu_has_exchange_program": ..., "edu_has_academic_award": ...}}"""

    raw = _llm_call(prompt, "block1_academic")
    schema = {
        "edu_institution_tier": "int",
        "edu_field_category": "int",
        "edu_degree_level": "int",
        "edu_is_dropout": "binary",
        "edu_has_international_degree": "binary",
        "edu_has_exchange_program": "binary",
        "edu_has_academic_award": "binary",
    }
    return _validate(raw, schema)


# ── Block 2 — Professional Experience ─────────────────────────────────────────

def block2_experience(profile: dict, tier1: dict) -> dict:
    exp_data = json.dumps(profile.get("experience", []), default=str)
    total_years = tier1.get("exp_total_years", 0) or 0
    seniority_hint = ""

    prompt = f"""=== EXPERIENCE DATA ===
{exp_data}

=== CONTEXT ===
Total years of experience (computed): {total_years}

Extract these features. Return JSON with exactly these keys:

exp_has_bigtech_experience (0 or 1): 1 if any role at Google, Meta, Apple, Microsoft, Amazon, Netflix, Uber, Stripe, Spotify, Salesforce, IBM, Oracle, SAP, Accenture, McKinsey, BCG, Bain, or similarly large global tech/consulting firm.

exp_has_startup_experience (0 or 1): 1 if any role at an early-stage startup (seed/series A, small team, or explicitly called startup).

exp_has_consulting_experience (0 or 1): 1 if any role with title/company containing consulting, consultant, advisory, conseil.

exp_has_corporate_experience (0 or 1): 1 if any role at a large corporation (100+ employees, non-startup).

exp_has_academic_research_experience (0 or 1): 1 if any academic role: researcher, PhD student, postdoc, research assistant, professor, teaching assistant.

exp_has_international_experience (0 or 1): 1 if any role was outside Tunisia (based on company location, job description, or explicitly stated).

exp_has_remote_foreign_employer (0 or 1): 1 if any role was remote for a foreign company while presumably based in Tunisia.

exp_seniority_level_current (int): seniority of the most recent role.
  0 = intern, trainee, junior, assistant
  1 = engineer, analyst, developer, associate (no senior qualifier)
  2 = senior, confirmed, lead engineer
  3 = lead, manager, head of, principal
  4 = director, VP, C-level, partner, founder
  null if no experience.

exp_seniority_progression_rate (float): current_seniority_level / total_years_of_experience. Example: level 3 in 4 years = 0.75. null if only one role ever or total_years = 0.

exp_domain_consistency_score (float 0-1): proportion of roles in the dominant domain. 1.0 if only one role. 0 = completely scattered, 1 = fully focused.

exp_has_quit_stable_job_signal (0 or 1): 1 if most recently completed role was at a corporate/large company AND no new employment started after it AND gap is under 18 months. 0 otherwise.

exp_number_of_promotions_detected (int): count of upward title transitions within same company (junior→senior, engineer→lead, analyst→manager). Lateral moves don't count. 0 if none.

exp_has_management_experience (0 or 1): 1 if any role with manager, head of, director, VP, C-level, or explicitly managing a team.

exp_management_years (float): total years in roles with direct report responsibility. 0 if none.

Return exactly:
{{"exp_has_bigtech_experience": ..., "exp_has_startup_experience": ..., "exp_has_consulting_experience": ..., "exp_has_corporate_experience": ..., "exp_has_academic_research_experience": ..., "exp_has_international_experience": ..., "exp_has_remote_foreign_employer": ..., "exp_seniority_level_current": ..., "exp_seniority_progression_rate": ..., "exp_domain_consistency_score": ..., "exp_has_quit_stable_job_signal": ..., "exp_number_of_promotions_detected": ..., "exp_has_management_experience": ..., "exp_management_years": ...}}"""

    raw = _llm_call(prompt, "block2_experience")
    schema = {
        "exp_has_bigtech_experience": "binary",
        "exp_has_startup_experience": "binary",
        "exp_has_consulting_experience": "binary",
        "exp_has_corporate_experience": "binary",
        "exp_has_academic_research_experience": "binary",
        "exp_has_international_experience": "binary",
        "exp_has_remote_foreign_employer": "binary",
        "exp_seniority_level_current": "int",
        "exp_seniority_progression_rate": "float",
        "exp_domain_consistency_score": "float",
        "exp_has_quit_stable_job_signal": "binary",
        "exp_number_of_promotions_detected": "int",
        "exp_has_management_experience": "binary",
        "exp_management_years": "float",
    }
    return _validate(raw, schema)


# ── Block 3 — Entrepreneurial History ─────────────────────────────────────────

def block3_entrepreneurial(profile: dict, tier1: dict) -> dict:
    exp_data = json.dumps(profile.get("experience", []), default=str)
    about = profile.get("about", "")
    n_prior = tier1.get("entre_number_of_prior_ventures", 0)

    prompt = f"""=== EXPERIENCE DATA ===
{exp_data}

=== ABOUT / SUMMARY ===
{about}

=== CONTEXT ===
Number of prior ventures (computed): {n_prior}

Extract these features. Return JSON with exactly these keys:

entre_prior_venture_success_rate (float 0-1): proportion of prior ventures with positive outcome (acquired, raised Series A+, still operating 3+ years, IPO). Unknown ventures excluded from denominator. null if no prior ventures.

entre_prior_venture_failure_rate (float 0-1): proportion of prior ventures that shut down or lasted under 12 months with no outcome. null if no prior ventures.

entre_has_prior_exit (0 or 1): 1 if exited a founded company via acquisition or merger. Look for: acquired by, merged with, exited, sold to.

entre_has_prior_acquisition (0 or 1): 1 if a founded company was acquired. 0 otherwise.

entre_has_raised_before (0 or 1): 1 if raised external funding (seed, pre-seed, series A, angel, grant, funding round) for any founded company.

entre_total_prior_funding_raised_usd (float): total USD raised across all prior ventures. Convert TND (1 USD ≈ 3.1 TND) and EUR (1 USD ≈ 1.1 EUR). null if none found.

entre_prior_venture_domain_match (0 or 1): 1 if any prior venture shares the same domain as the most recent (current) founding role. 0 otherwise.

entre_has_been_early_employee_startup (0 or 1): 1 if was among first employees at a startup (not as founder): "first X employees", joined within 1 year of company founding, or early-stage explicitly mentioned. 0 otherwise.

Return exactly:
{{"entre_prior_venture_success_rate": ..., "entre_prior_venture_failure_rate": ..., "entre_has_prior_exit": ..., "entre_has_prior_acquisition": ..., "entre_has_raised_before": ..., "entre_total_prior_funding_raised_usd": ..., "entre_prior_venture_domain_match": ..., "entre_has_been_early_employee_startup": ...}}"""

    raw = _llm_call(prompt, "block3_entrepreneurial")
    schema = {
        "entre_prior_venture_success_rate": "float",
        "entre_prior_venture_failure_rate": "float",
        "entre_has_prior_exit": "binary",
        "entre_has_prior_acquisition": "binary",
        "entre_has_raised_before": "binary",
        "entre_total_prior_funding_raised_usd": "float",
        "entre_prior_venture_domain_match": "binary",
        "entre_has_been_early_employee_startup": "binary",
    }
    return _validate(raw, schema)


# ── Block 4 — Technical Depth ──────────────────────────────────────────────────

def block4_technical(profile: dict) -> dict:
    github_data = json.dumps(profile.get("github", {}), default=str)
    certs_data = json.dumps(profile.get("certifications", []), default=str)
    about = profile.get("about", "")
    headline = profile.get("headline", "")

    prompt = f"""=== GITHUB DATA ===
{github_data}

=== CERTIFICATIONS ===
{certs_data}

=== HEADLINE & ABOUT ===
{headline}
{about}

Extract these features. Return JSON with exactly these keys:

tech_github_has_ml_repos (0 or 1): 1 if any GitHub repo involves ML/AI (tensorflow, pytorch, sklearn, keras in deps/names; topics: machine-learning, deep-learning, data-science; names containing ml, ai, model, neural, nlp, cv). null if no GitHub.

tech_github_has_web_repos (0 or 1): 1 if any GitHub repo is a web application (react, vue, angular, html, css, django, flask, nextjs, express). null if no GitHub.

tech_github_has_mobile_repos (0 or 1): 1 if any GitHub repo is a mobile app (ios, android, flutter, react-native, swift, kotlin). null if no GitHub.

tech_github_open_source_contributions (int): number of contributions to external open source projects (not own repos). null if no GitHub or no data.

tech_has_technical_blog (0 or 1): 1 if maintains technical writing (medium.com, dev.to, hashnode, substack, personal blog with technical content). 0 otherwise.

tech_has_cloud_certification (0 or 1): 1 if holds a cloud certification (AWS, Azure, GCP, Terraform, Kubernetes, DevOps). 0 otherwise.

tech_has_ml_certification (0 or 1): 1 if holds a machine learning or AI certification (DeepLearning.AI, Coursera ML, Google ML, TensorFlow dev cert, etc.). 0 otherwise.

Return exactly:
{{"tech_github_has_ml_repos": ..., "tech_github_has_web_repos": ..., "tech_github_has_mobile_repos": ..., "tech_github_open_source_contributions": ..., "tech_has_technical_blog": ..., "tech_has_cloud_certification": ..., "tech_has_ml_certification": ...}}"""

    raw = _llm_call(prompt, "block4_technical")
    schema = {
        "tech_github_has_ml_repos": "binary",
        "tech_github_has_web_repos": "binary",
        "tech_github_has_mobile_repos": "binary",
        "tech_github_open_source_contributions": "int",
        "tech_has_technical_blog": "binary",
        "tech_has_cloud_certification": "binary",
        "tech_has_ml_certification": "binary",
    }
    return _validate(raw, schema)


# ── Block 5 — Commercial & Leadership ─────────────────────────────────────────

def block5_commercial(profile: dict) -> dict:
    exp_data = json.dumps(profile.get("experience", []), default=str)
    about = profile.get("about", "")
    headline = profile.get("headline", "")

    prompt = f"""=== EXPERIENCE DATA ===
{exp_data}

=== HEADLINE & ABOUT ===
{headline}
{about}

Extract these features. Return JSON with exactly these keys:

comm_has_sales_experience (0 or 1): 1 if any role has sales, account executive, AE, SDR, BDR, revenue in title or description.

comm_has_bd_experience (0 or 1): 1 if any role has business development, BD, partnerships in title or description.

comm_has_marketing_experience (0 or 1): 1 if any role has marketing, brand, content, SEO, growth in title or description.

comm_has_product_management_experience (0 or 1): 1 if any role has product manager, PM, product owner, product lead in title.

comm_has_gtm_experience (0 or 1): 1 if any role involves GTM, go-to-market, growth, launch strategy, market entry, demand generation, acquisition.

comm_has_board_membership (0 or 1): 1 if any board member, board director, board of directors role.

comm_has_advisory_role (0 or 1): 1 if any advisor, adviser, or mentor role.

comm_has_public_speaking_record (0 or 1): 1 if any mention of speaking at conferences, panels, workshops, podcasts, or keynotes.

comm_speaking_events_count (int): count of distinct public speaking appearances (conferences, panels, podcasts, workshops, university talks). 0 if none.

comm_has_press_mentions (0 or 1): 1 if any press mention, article, interview, or media feature found in profile. 0 otherwise.

comm_press_mentions_count (int): number of press mentions found. 0 if none.

comm_press_outlet_quality_max (int):
  0 = no press
  1 = local blog, small website, university publication
  2 = national outlet (Tunisian national press, national TV)
  3 = regional tech outlet (Wamda, Magnitt, AfricaTech, ArabNet, Jeune Afrique)
  4 = international outlet (TechCrunch, Forbes, Reuters, BBC, Bloomberg)
  Return maximum tier found.

comm_has_thought_leadership_content (0 or 1): 1 if wrote articles, newsletter, LinkedIn posts with substantial content, or published opinion pieces. 0 otherwise.

Return exactly:
{{"comm_has_sales_experience": ..., "comm_has_bd_experience": ..., "comm_has_marketing_experience": ..., "comm_has_product_management_experience": ..., "comm_has_gtm_experience": ..., "comm_has_board_membership": ..., "comm_has_advisory_role": ..., "comm_has_public_speaking_record": ..., "comm_speaking_events_count": ..., "comm_has_press_mentions": ..., "comm_press_mentions_count": ..., "comm_press_outlet_quality_max": ..., "comm_has_thought_leadership_content": ...}}"""

    raw = _llm_call(prompt, "block5_commercial")
    schema = {
        "comm_has_sales_experience": "binary",
        "comm_has_bd_experience": "binary",
        "comm_has_marketing_experience": "binary",
        "comm_has_product_management_experience": "binary",
        "comm_has_gtm_experience": "binary",
        "comm_has_board_membership": "binary",
        "comm_has_advisory_role": "binary",
        "comm_has_public_speaking_record": "binary",
        "comm_speaking_events_count": "int",
        "comm_has_press_mentions": "binary",
        "comm_press_mentions_count": "int",
        "comm_press_outlet_quality_max": "int",
        "comm_has_thought_leadership_content": "binary",
    }
    return _validate(raw, schema)


# ── Block 6 — Network & Community ─────────────────────────────────────────────

def block6_network(profile: dict, tier1: dict) -> dict:
    exp_data = json.dumps(profile.get("experience", []), default=str)
    about = profile.get("about", "")
    volunteer_data = json.dumps(profile.get("volunteer", []), default=str)
    connections = profile.get("connections")
    n_hackathons = tier1.get("net_hackathon_participations_count", 0)

    prompt = f"""=== EXPERIENCE DATA ===
{exp_data}

=== VOLUNTEER / COMMUNITY ===
{volunteer_data}

=== ABOUT ===
{about}

=== CONTEXT ===
LinkedIn connections: {connections}
Hackathon participations (computed): {n_hackathons}

Extract these features. Return JSON with exactly these keys:

net_has_investor_connections (0 or 1): 1 if profile mentions connections, network, or relationships with investors, VCs, or angels.

net_has_founder_connections (0 or 1): 1 if profile mentions connections or network with other founders or startup community.

net_hackathon_wins_count (int): number of hackathon wins, prizes, or first-place finishes mentioned. 0 if none.

net_accelerator_alumni (0 or 1): 1 if attended any accelerator program (Y Combinator, Flat6Labs, Seedstars, Startupbootcamp, 500 Startups, etc.).

net_incubator_alumni (0 or 1): 1 if attended any incubator program (university incubator, government incubator, etc.).

net_accelerator_tier (int):
  0 = no accelerator
  1 = local/regional accelerator (Flat6Labs Tunisia, ESPRIT Startup, etc.)
  2 = reputable African/MENA accelerator (Flat6Labs Cairo, Seedstars, ArabNet, Wamda)
  3 = top global accelerator (Y Combinator, Techstars, 500 Startups, Startupbootcamp)

net_is_startup_act_registered (0 or 1): 1 if profile mentions Startup Act, labellisé Startup Act, registered under startup act Tunisia, or similar. 0 otherwise.

net_startup_community_presence_score (float 0-1): sum these signals:
  +0.20 if accelerator or incubator alumni
  +0.15 if attended or spoken at startup events
  +0.15 if investor connections mentioned
  +0.15 if founder connections mentioned
  +0.15 if hackathon participation history
  +0.10 if STARTUP ACT registered
  +0.10 if ecosystem tenure over 2 years
  Cap at 1.0.

Return exactly:
{{"net_has_investor_connections": ..., "net_has_founder_connections": ..., "net_hackathon_wins_count": ..., "net_accelerator_alumni": ..., "net_incubator_alumni": ..., "net_accelerator_tier": ..., "net_is_startup_act_registered": ..., "net_startup_community_presence_score": ...}}"""

    raw = _llm_call(prompt, "block6_network")
    schema = {
        "net_has_investor_connections": "binary",
        "net_has_founder_connections": "binary",
        "net_hackathon_wins_count": "int",
        "net_accelerator_alumni": "binary",
        "net_incubator_alumni": "binary",
        "net_accelerator_tier": "int",
        "net_is_startup_act_registered": "binary",
        "net_startup_community_presence_score": "float01",
    }
    return _validate(raw, schema)


# ── Block 7 — Founding Intent ──────────────────────────────────────────────────

def block7_intent(profile: dict, tier1: dict) -> dict:
    exp_data = json.dumps(profile.get("experience", []), default=str)
    headline = profile.get("headline", "")
    about = profile.get("about", "")
    quit_months = tier1.get("intent_quit_months_ago")

    prompt = f"""=== EXPERIENCE DATA ===
{exp_data}

=== HEADLINE ===
{headline}

=== ABOUT ===
{about}

=== CONTEXT ===
Months since last role ended (computed): {quit_months}

Extract these features. Return JSON with exactly these keys:

intent_has_quit_job_recently (0 or 1): 1 if the most recently ended role ended within the last 18 months AND no new employment started after it. 0 otherwise.

intent_has_registered_domain (0 or 1): 1 if profile mentions owning a domain, having a website, or a company website URL is listed. 0 otherwise.

intent_has_startup_act_label (0 or 1): 1 if profile explicitly mentions Startup Act Tunisia, labellisé Startup Act, or similar label. 0 otherwise.

intent_linkedin_headline_founding_signal (0 or 1):
  1 if headline contains: building, founder, co-founder, CEO at [own company], creating, launching, making, started, working on.
  "ex-X | building Y" counts as 1.
  0 if describes employment at another company or is generic.

intent_has_producthunt_launch (0 or 1): 1 if product launch on Product Hunt is mentioned. 0 otherwise.

intent_has_app_store_listing (0 or 1): 1 if a live app on App Store or Google Play is mentioned. 0 otherwise.

intent_attended_startup_events_last_6m (int): count of distinct startup events in the last 6 months (hackathons, pitch competitions, startup weekends, demo days, investor meetups). 0 if none.

intent_won_hackathon_last_12m (0 or 1): 1 if a hackathon win is mentioned within the last 12 months. 0 otherwise.

Return exactly:
{{"intent_has_quit_job_recently": ..., "intent_has_registered_domain": ..., "intent_has_startup_act_label": ..., "intent_linkedin_headline_founding_signal": ..., "intent_has_producthunt_launch": ..., "intent_has_app_store_listing": ..., "intent_attended_startup_events_last_6m": ..., "intent_won_hackathon_last_12m": ...}}"""

    raw = _llm_call(prompt, "block7_intent")
    schema = {
        "intent_has_quit_job_recently": "binary",
        "intent_has_registered_domain": "binary",
        "intent_has_startup_act_label": "binary",
        "intent_linkedin_headline_founding_signal": "binary",
        "intent_has_producthunt_launch": "binary",
        "intent_has_app_store_listing": "binary",
        "intent_attended_startup_events_last_6m": "int",
        "intent_won_hackathon_last_12m": "binary",
    }
    return _validate(raw, schema)


# ── Aggregate LLM extractor ────────────────────────────────────────────────────

def extract_llm_features(profile: dict, tier1: dict, verbose: bool = True) -> dict:
    blocks = [
        ("Block 1 — Academic", lambda: block1_academic(profile)),
        ("Block 2 — Experience", lambda: block2_experience(profile, tier1)),
        ("Block 3 — Entrepreneurial", lambda: block3_entrepreneurial(profile, tier1)),
        ("Block 4 — Technical", lambda: block4_technical(profile)),
        ("Block 5 — Commercial", lambda: block5_commercial(profile)),
        ("Block 6 — Network", lambda: block6_network(profile, tier1)),
        ("Block 7 — Intent", lambda: block7_intent(profile, tier1)),
    ]
    features = {}
    for name, fn in blocks:
        if verbose:
            print(f"  {name}...")
        result = fn()
        features.update(result)
    return features
