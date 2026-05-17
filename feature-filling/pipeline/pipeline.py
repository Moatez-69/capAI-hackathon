"""
Main feature-filling pipeline orchestrator.

Input:  raw LinkedIn JSON profile (any scraper format)
Output: filled feature vector + completeness score + confidence tier
"""
from .normalize import normalize_profile
from .tier1_rules import extract_tier1, apply_keyword_fallbacks, KEYWORD_AUTHORITATIVE
from .llm_blocks import extract_llm_features
from .missing_data import apply_missing_data, compute_completeness, ALL_FEATURES


def run(raw_profile: dict, verbose: bool = True) -> dict:
    """
    Full pipeline: raw JSON → filled feature vector.

    Returns a dict with:
      feature_vector   — all ~101 features (values or None)
      completeness_score — float 0-1
      confidence_tier    — string label
      mnar_flags         — list of _MISSING flags added
      role               — inferred founder role
      name               — founder name
    """
    if verbose:
        name = raw_profile.get("fullName") or raw_profile.get("name") or "Unknown"
        print(f"\n=== CapAI Feature Pipeline: {name} ===")

    # Step 1: Normalize variable field names
    if verbose:
        print("Step 1: Normalizing profile...")
    profile = normalize_profile(raw_profile)

    # Step 2: Tier 1 — rule-based extraction
    if verbose:
        print("Step 2: Tier 1 rule-based extraction...")
    tier1_features = extract_tier1(profile)

    # Step 3: LLM block extraction (7 calls)
    if verbose:
        print("Step 3: LLM block extraction (7 calls)...")
    llm_features = extract_llm_features(profile, tier1_features, verbose=verbose)

    # Step 4: Merge features — keyword rules win for authoritative features,
    # LLM non-null values win for everything else
    raw_features = {}
    raw_features.update(tier1_features)
    # LLM fills everything it can (non-null overrides Tier 1 where both exist)
    for k, v in llm_features.items():
        if v is not None:
            raw_features[k] = v
        elif k not in raw_features:
            raw_features[k] = None
    # Keyword rules always override for authoritative features
    keyword_features = apply_keyword_fallbacks(profile, raw_features)
    for k in KEYWORD_AUTHORITATIVE:
        if keyword_features.get(k) is not None:
            raw_features[k] = keyword_features[k]
    # Also fill remaining Nones from keyword fallbacks
    for k, v in keyword_features.items():
        if k not in KEYWORD_AUTHORITATIVE and raw_features.get(k) is None and v is not None:
            raw_features[k] = v

    # Step 5: Infer role from raw features (before imputation)
    role = _infer_role(raw_features)
    if verbose:
        print(f"  Inferred role: {role}")

    # Step 6: Apply missing data framework
    if verbose:
        print("Step 4: Applying missing data framework...")
    filled_features, mnar_flags = apply_missing_data(raw_features, role=role)

    # Step 7: Ensure all expected features are present in output
    feature_vector = {f: filled_features.get(f) for f in ALL_FEATURES}
    # Also include any MNAR flags
    for flag in mnar_flags:
        feature_vector[flag] = filled_features.get(flag, 0)

    # Step 8: Compute completeness
    completeness, confidence_tier = compute_completeness(feature_vector)
    if verbose:
        print(f"\nCompleteness: {completeness:.0%}  |  Confidence: {confidence_tier}")

    return {
        "name": profile["name"],
        "role": role,
        "feature_vector": feature_vector,
        "completeness_score": completeness,
        "confidence_tier": confidence_tier,
        "mnar_flags": mnar_flags,
    }


def _infer_role(features: dict) -> str:
    """
    Infer founder role from raw features (before imputation).
    Mirrors the scoring system's classification logic.

    Returns one of: "technical", "operator", "commercial", "domain"
    """
    # Technical signals
    tech_score = 0
    if features.get("tech_has_github"):
        tech_score += 2
    if (features.get("tech_github_total_repos") or 0) >= 5:
        tech_score += 1
    if (features.get("tech_linkedin_skills_technical_count") or 0) >= 5:
        tech_score += 1
    if features.get("tech_has_technical_blog"):
        tech_score += 1
    if features.get("tech_has_publications"):
        tech_score += 1

    # Operator signals (repeat founder + commercial mix)
    operator_score = 0
    if (features.get("entre_number_of_prior_ventures") or 0) >= 1:
        operator_score += 3
    if features.get("entre_has_prior_exit"):
        operator_score += 2
    if features.get("entre_has_raised_before"):
        operator_score += 1
    if features.get("exp_has_management_experience"):
        operator_score += 1

    # Commercial signals
    commercial_score = 0
    comm_flags = [
        "comm_has_sales_experience", "comm_has_bd_experience",
        "comm_has_marketing_experience", "comm_has_gtm_experience",
        "comm_has_public_speaking_record",
    ]
    commercial_score += sum(1 for f in comm_flags if features.get(f))

    # Domain signals (very high consistency + intent)
    domain_score = 0
    if (features.get("exp_domain_consistency_score") or 0) >= 0.8:
        domain_score += 2
    if features.get("intent_linkedin_headline_founding_signal"):
        domain_score += 1
    if (features.get("net_startup_community_presence_score") or 0) >= 0.5:
        domain_score += 1

    scores = {
        "technical": tech_score,
        "operator": operator_score,
        "commercial": commercial_score,
        "domain": domain_score,
    }
    return max(scores, key=scores.get)
