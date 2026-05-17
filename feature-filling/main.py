#!/usr/bin/env python3
"""
CapAI Feature Pipeline CLI

Usage:
  python main.py <profile.json>           # fill features, print human-readable table
  python main.py <profile.json> --json    # output feature vector as JSON
  python main.py data/demo_mottaki.json   # run demo
"""
import sys
import json
import argparse
from pathlib import Path

from pipeline.pipeline import run as fill_features


def main():
    parser = argparse.ArgumentParser(
        description="CapAI — Founder feature vector extraction"
    )
    parser.add_argument("profile", help="Path to LinkedIn profile JSON")
    parser.add_argument("--json", action="store_true", help="Output feature vector as JSON")
    parser.add_argument("--quiet", action="store_true", help="Suppress pipeline progress output")
    args = parser.parse_args()

    profile_path = Path(args.profile)
    if not profile_path.exists():
        print(f"Error: file not found: {profile_path}", file=sys.stderr)
        sys.exit(1)

    with open(profile_path) as f:
        raw_profile = json.load(f)

    result = fill_features(raw_profile, verbose=not args.quiet)

    if args.json:
        output = {
            "name": result["name"],
            "role": result["role"],
            "completeness_score": result["completeness_score"],
            "confidence_tier": result["confidence_tier"],
            "mnar_flags": result["mnar_flags"],
            "feature_vector": result["feature_vector"],
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        _print_features(result)


def _print_features(result: dict):
    fv = result["feature_vector"]

    print(f"\n{'=' * 60}")
    print(f"  FEATURE VECTOR — {result['name']}")
    print(f"{'=' * 60}")
    print(f"  Role       : {result['role'].upper()}")
    print(f"  Completeness: {result['completeness_score']:.0%}  |  {result['confidence_tier']}")

    blocks = [
        ("BLOCK 1 — Academic", [
            "edu_institution_tier", "edu_field_category", "edu_degree_level",
            "edu_is_dropout", "edu_has_international_degree", "edu_has_exchange_program",
            "edu_has_academic_award", "edu_years_since_graduation",
            "edu_studied_abroad_duration_months",
        ]),
        ("BLOCK 2 — Professional Experience", [
            "exp_total_years", "exp_number_of_employers", "exp_avg_tenure_months",
            "exp_has_bigtech_experience", "exp_has_startup_experience",
            "exp_has_consulting_experience", "exp_has_corporate_experience",
            "exp_has_academic_research_experience", "exp_has_international_experience",
            "exp_has_remote_foreign_employer", "exp_seniority_level_current",
            "exp_seniority_progression_rate", "exp_domain_consistency_score",
            "exp_has_quit_stable_job_signal", "exp_longest_tenure_months",
            "exp_number_of_promotions_detected", "exp_has_management_experience",
            "exp_management_years",
        ]),
        ("BLOCK 3 — Entrepreneurial History", [
            "entre_number_of_prior_ventures", "entre_has_prior_venture",
            "entre_prior_venture_success_rate", "entre_prior_venture_failure_rate",
            "entre_has_prior_exit", "entre_has_prior_acquisition",
            "entre_has_raised_before", "entre_total_prior_funding_raised_usd",
            "entre_is_repeat_founder", "entre_avg_time_between_ventures_months",
            "entre_prior_venture_domain_match", "entre_has_been_early_employee_startup",
        ]),
        ("BLOCK 4 — Technical Depth", [
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
        ]),
        ("BLOCK 5 — Commercial & Leadership", [
            "comm_has_sales_experience", "comm_has_bd_experience",
            "comm_has_marketing_experience", "comm_has_product_management_experience",
            "comm_has_gtm_experience", "comm_has_board_membership", "comm_has_advisory_role",
            "comm_number_of_advisory_roles", "comm_has_public_speaking_record",
            "comm_speaking_events_count", "comm_has_press_mentions",
            "comm_press_mentions_count", "comm_press_outlet_quality_max",
            "comm_has_thought_leadership_content", "comm_linkedin_followers",
        ]),
        ("BLOCK 6 — Network & Community", [
            "net_linkedin_connections_tier", "net_has_investor_connections",
            "net_has_founder_connections", "net_hackathon_participations_count",
            "net_hackathon_wins_count", "net_accelerator_alumni", "net_incubator_alumni",
            "net_accelerator_tier", "net_startup_community_presence_score",
            "net_is_startup_act_registered", "net_ecosystem_tenure_months",
        ]),
        ("BLOCK 7 — Founding Intent", [
            "intent_has_quit_job_recently", "intent_quit_months_ago",
            "intent_has_registered_domain", "intent_domain_registration_months_ago",
            "intent_has_github_org", "intent_github_org_age_months",
            "intent_has_startup_act_label", "intent_startup_act_months_ago",
            "intent_linkedin_headline_founding_signal", "intent_has_producthunt_launch",
            "intent_has_app_store_listing", "intent_attended_startup_events_last_6m",
            "intent_won_hackathon_last_12m",
        ]),
    ]

    for block_name, keys in blocks:
        print(f"\n  {block_name}")
        print("  " + "-" * 45)
        for key in keys:
            val = fv.get(key)
            print(f"  {key:<45}: {val}")

    if result["mnar_flags"]:
        print(f"\n  MNAR FLAGS: {', '.join(result['mnar_flags'])}")

    print(f"\n{'=' * 60}\n")


if __name__ == "__main__":
    main()
