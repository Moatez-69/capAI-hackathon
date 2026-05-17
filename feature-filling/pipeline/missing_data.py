"""
Missing data framework: MCAR / MAR / MNAR handling per spec.

MNAR features — features whose absence is informative (never impute, add _MISSING flag).
MAR features  — impute using role context.
MCAR features — treat as zero or use role-based default.
"""

# Features where absence carries a negative signal — add _MISSING binary flag
MNAR_FEATURES = {
    "entre_number_of_prior_ventures",
    "entre_prior_venture_failure_rate",
    "exp_avg_tenure_months",
    # tech_has_github is handled separately (absence = real zero)
}

# Features whose expected presence depends on role
# Role: "technical" | "operator" | "commercial" | "domain"
MAR_DEFAULTS_BY_ROLE = {
    "technical": {
        "exp_has_bigtech_experience": 0,
        "exp_has_startup_experience": 0,
        "comm_has_sales_experience": 0,
        "comm_has_bd_experience": 0,
        "comm_has_marketing_experience": 0,
    },
    "operator": {
        "tech_github_total_repos": 0,
        "tech_github_public_repos": 0,
        "tech_github_total_stars_received": 0,
        "tech_github_has_ml_repos": 0,
        "tech_github_has_web_repos": 0,
        "tech_github_has_mobile_repos": 0,
    },
    "commercial": {
        "tech_github_total_repos": 0,
        "tech_github_public_repos": 0,
        "tech_github_total_stars_received": 0,
        "tech_has_github": 0,
    },
    "domain": {},
}

# Features that are always zero when absent (MCAR — missing completely at random)
MCAR_ZERO_DEFAULTS = {
    "edu_is_dropout": 0,
    "edu_has_international_degree": 0,
    "edu_has_exchange_program": 0,
    "edu_has_academic_award": 0,
    "edu_studied_abroad_duration_months": 0,
    "exp_total_years": 0,
    "exp_number_of_employers": 0,
    "exp_number_of_promotions_detected": 0,
    "exp_has_management_experience": 0,
    "exp_management_years": 0,
    "exp_has_bigtech_experience": 0,
    "exp_has_startup_experience": 0,
    "exp_has_consulting_experience": 0,
    "exp_has_corporate_experience": 0,
    "exp_has_academic_research_experience": 0,
    "exp_has_international_experience": 0,
    "exp_has_remote_foreign_employer": 0,
    "exp_has_quit_stable_job_signal": 0,
    "entre_number_of_prior_ventures": 0,
    "entre_has_prior_venture": 0,
    "entre_is_repeat_founder": 0,
    "entre_has_prior_exit": 0,
    "entre_has_prior_acquisition": 0,
    "entre_has_raised_before": 0,
    "entre_has_been_early_employee_startup": 0,
    "entre_prior_venture_domain_match": 0,
    "tech_has_github": 0,
    "tech_has_publications": 0,
    "tech_has_patents": 0,
    "tech_has_technical_blog": 0,
    "tech_has_cloud_certification": 0,
    "tech_has_ml_certification": 0,
    "tech_linkedin_skills_technical_count": 0,
    "tech_github_has_ml_repos": 0,
    "tech_github_has_web_repos": 0,
    "tech_github_has_mobile_repos": 0,
    "tech_github_has_popular_repo": 0,
    "comm_has_sales_experience": 0,
    "comm_has_bd_experience": 0,
    "comm_has_marketing_experience": 0,
    "comm_has_product_management_experience": 0,
    "comm_has_gtm_experience": 0,
    "comm_has_board_membership": 0,
    "comm_has_advisory_role": 0,
    "comm_number_of_advisory_roles": 0,
    "comm_has_public_speaking_record": 0,
    "comm_speaking_events_count": 0,
    "comm_has_press_mentions": 0,
    "comm_press_mentions_count": 0,
    "comm_press_outlet_quality_max": 0,
    "comm_has_thought_leadership_content": 0,
    "net_hackathon_participations_count": 0,
    "net_hackathon_wins_count": 0,
    "net_has_investor_connections": 0,
    "net_has_founder_connections": 0,
    "net_accelerator_alumni": 0,
    "net_incubator_alumni": 0,
    "net_accelerator_tier": 0,
    "net_is_startup_act_registered": 0,
    "intent_has_quit_job_recently": 0,
    "intent_has_registered_domain": 0,
    "intent_has_github_org": 0,
    "intent_has_startup_act_label": 0,
    "intent_linkedin_headline_founding_signal": 0,
    "intent_has_producthunt_launch": 0,
    "intent_has_app_store_listing": 0,
    "intent_attended_startup_events_last_6m": 0,
    "intent_won_hackathon_last_12m": 0,
    "net_startup_community_presence_score": 0.0,
    "exp_domain_consistency_score": None,
}

# All 101 expected features
ALL_FEATURES = [
    # Block 1
    "edu_institution_tier", "edu_field_category", "edu_degree_level",
    "edu_is_dropout", "edu_has_international_degree", "edu_has_exchange_program",
    "edu_has_academic_award", "edu_years_since_graduation",
    "edu_studied_abroad_duration_months",
    # Block 2
    "exp_total_years", "exp_number_of_employers", "exp_avg_tenure_months",
    "exp_has_bigtech_experience", "exp_has_startup_experience",
    "exp_has_consulting_experience", "exp_has_corporate_experience",
    "exp_has_academic_research_experience", "exp_has_international_experience",
    "exp_has_remote_foreign_employer", "exp_seniority_level_current",
    "exp_seniority_progression_rate", "exp_domain_consistency_score",
    "exp_has_quit_stable_job_signal", "exp_longest_tenure_months",
    "exp_number_of_promotions_detected", "exp_has_management_experience",
    "exp_management_years",
    # Block 3
    "entre_number_of_prior_ventures", "entre_has_prior_venture",
    "entre_prior_venture_success_rate", "entre_prior_venture_failure_rate",
    "entre_has_prior_exit", "entre_has_prior_acquisition",
    "entre_has_raised_before", "entre_total_prior_funding_raised_usd",
    "entre_is_repeat_founder", "entre_avg_time_between_ventures_months",
    "entre_prior_venture_domain_match", "entre_has_been_early_employee_startup",
    # Block 4
    "tech_has_github", "tech_github_account_age_months",
    "tech_github_total_repos", "tech_github_public_repos",
    "tech_github_total_stars_received", "tech_github_total_forks_received",
    "tech_github_followers", "tech_github_contribution_streak_days",
    "tech_github_commits_last_12m", "tech_github_languages_count",
    "tech_github_primary_language", "tech_github_has_ml_repos",
    "tech_github_has_web_repos", "tech_github_has_mobile_repos",
    "tech_github_open_source_contributions", "tech_github_has_popular_repo",
    "tech_has_technical_blog", "tech_has_publications", "tech_has_patents",
    "tech_linkedin_skills_technical_count", "tech_linkedin_skills_endorsement_max",
    "tech_has_cloud_certification", "tech_has_ml_certification",
    # Block 5
    "comm_has_sales_experience", "comm_has_bd_experience",
    "comm_has_marketing_experience", "comm_has_product_management_experience",
    "comm_has_gtm_experience", "comm_has_board_membership", "comm_has_advisory_role",
    "comm_number_of_advisory_roles", "comm_has_public_speaking_record",
    "comm_speaking_events_count", "comm_has_press_mentions",
    "comm_press_mentions_count", "comm_press_outlet_quality_max",
    "comm_has_thought_leadership_content", "comm_linkedin_followers",
    # Block 6
    "net_linkedin_connections_tier", "net_has_investor_connections",
    "net_has_founder_connections", "net_hackathon_participations_count",
    "net_hackathon_wins_count", "net_accelerator_alumni", "net_incubator_alumni",
    "net_accelerator_tier", "net_startup_community_presence_score",
    "net_is_startup_act_registered", "net_ecosystem_tenure_months",
    # Block 7
    "intent_has_quit_job_recently", "intent_quit_months_ago",
    "intent_has_registered_domain", "intent_domain_registration_months_ago",
    "intent_has_github_org", "intent_github_org_age_months",
    "intent_has_startup_act_label", "intent_startup_act_months_ago",
    "intent_linkedin_headline_founding_signal", "intent_has_producthunt_launch",
    "intent_has_app_store_listing", "intent_attended_startup_events_last_6m",
    "intent_won_hackathon_last_12m",
]

# Features excluded from completeness denominator (numeric helpers, not binary signals)
COMPLETENESS_EXCLUDED = {
    "tech_github_primary_language",  # string, not scored
    "intent_domain_registration_months_ago",
    "intent_github_org_age_months",
    "intent_startup_act_months_ago",
    "edu_studied_abroad_duration_months",  # always 0 if not abroad
}


def apply_missing_data(features: dict, role: str = "operator") -> tuple[dict, list[str]]:
    """
    Apply MCAR/MAR/MNAR handling to a raw feature dict.
    Returns (filled_features, mnar_flags_added).
    """
    filled = dict(features)
    mnar_flags = []

    # MNAR: never impute — add _MISSING flag
    for feat in MNAR_FEATURES:
        if filled.get(feat) is None:
            filled[f"{feat}_MISSING"] = 1
            mnar_flags.append(f"{feat}_MISSING")
        else:
            filled[f"{feat}_MISSING"] = 0

    # tech_has_github: absence = real zero (not imputed)
    if filled.get("tech_has_github") is None:
        filled["tech_has_github"] = 0

    # GitHub features: if no GitHub, zero everything out (no penalty for commercial role)
    if filled.get("tech_has_github") == 0 and role == "commercial":
        for feat in ALL_FEATURES:
            if feat.startswith("tech_github_") and filled.get(feat) is None:
                filled[feat] = 0

    # MAR: impute with role-based defaults
    role_defaults = MAR_DEFAULTS_BY_ROLE.get(role, {})
    for feat, default_val in role_defaults.items():
        if filled.get(feat) is None:
            filled[feat] = default_val

    # MCAR: treat as zero
    for feat, default_val in MCAR_ZERO_DEFAULTS.items():
        if filled.get(feat) is None:
            filled[feat] = default_val

    return filled, mnar_flags


def compute_completeness(features: dict) -> tuple[float, str]:
    """
    Return (completeness_score 0-1, confidence_tier).
    Only counts features in ALL_FEATURES, excluding COMPLETENESS_EXCLUDED.
    """
    relevant = [f for f in ALL_FEATURES if f not in COMPLETENESS_EXCLUDED]
    present = sum(1 for f in relevant if features.get(f) is not None)
    score = present / len(relevant) if relevant else 0.0

    if score >= 0.85:
        tier = "high — proceed with alert"
    elif score >= 0.65:
        tier = "medium — flag for manual review"
    elif score >= 0.40:
        tier = "low — request missing data before scoring"
    else:
        tier = "insufficient — do not score"

    return round(score, 3), tier
