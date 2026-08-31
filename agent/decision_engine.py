"""
RazorGrowth AI - Opportunity Decision Engine

Deterministic scoring and prioritization layer.

This module:
- calculates opportunity scores
- assigns priorities
- ranks opportunities
- does NOT call Gemini
- does NOT create payment links
- does NOT approve merchants
"""

# ============================================================
# Configuration
# ============================================================

MIN_SCORE = 0.60
MAX_SCORE = 1.00

# Confidence/relevance is more important than revenue.
CONFIDENCE_WEIGHT = 0.80
REVENUE_WEIGHT = 0.20

# Revenue above this amount receives maximum
# revenue contribution to the score.
REVENUE_REFERENCE = 2500.0


# ============================================================
# Safe Float Conversion
# ============================================================

def safe_float(value, default=0.0):
    """
    Safely convert a value to float.
    """

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ============================================================
# Normalize Value
# ============================================================

def normalize(value, minimum=0.0, maximum=1.0):
    """
    Keep a numeric value inside a safe range.
    """

    value = safe_float(value)

    return max(
        minimum,
        min(maximum, value)
    )


# ============================================================
# Revenue Score
# ============================================================

def calculate_revenue_score(revenue):
    """
    Convert potential revenue into a normalized
    0-1 revenue contribution.

    Revenue is deliberately given lower weight than
    confidence so expensive products do not dominate
    the ranking.
    """

    revenue = max(
        0.0,
        safe_float(revenue)
    )

    if revenue <= 0:
        return 0.0

    return round(
        min(
            revenue / REVENUE_REFERENCE,
            1.0
        ),
        4
    )


# ============================================================
# Opportunity Score
# ============================================================

def calculate_opportunity_score(opportunity):
    """
    Calculate a deterministic opportunity score.

    Formula:

        Score =
            (Confidence × 0.80)
            +
            (Revenue Score × 0.20)

    Confidence is the dominant factor because the system
    should prioritize evidence/relevance over simply
    selecting expensive products.
    """

    confidence = normalize(
        opportunity.get(
            "confidence",
            0
        )
    )

    revenue = safe_float(
        opportunity.get(
            "potential_revenue",
            0
        )
    )

    revenue_score = calculate_revenue_score(
        revenue
    )

    score = (
        confidence * CONFIDENCE_WEIGHT
        +
        revenue_score * REVENUE_WEIGHT
    )

    return round(
        normalize(score),
        2
    )


# ============================================================
# Priority
# ============================================================

def get_priority(score):
    """
    Convert score into business priority.
    """

    score = safe_float(score)

    if score >= 0.80:
        return "HIGH"

    if score >= MIN_SCORE:
        return "MEDIUM"

    return "LOW"


# ============================================================
# Enrich Opportunity
# ============================================================

def enrich_opportunity(opportunity):
    """
    Preserve the original opportunity and add
    deterministic scoring information.
    """

    enriched = dict(
        opportunity
    )

    score = calculate_opportunity_score(
        enriched
    )

    enriched[
        "opportunity_score"
    ] = score

    enriched[
        "priority"
    ] = get_priority(
        score
    )

    return enriched


# ============================================================
# Rank Opportunities
# ============================================================

def rank_opportunities(opportunities):
    """
    Enrich and rank opportunities.

    Ranking order:
        1. Opportunity score
        2. Confidence
        3. Potential revenue
    """

    enriched = [
        enrich_opportunity(
            opportunity
        )
        for opportunity in opportunities
    ]

    return sorted(
        enriched,
        key=lambda opportunity: (
            opportunity.get(
                "opportunity_score",
                0
            ),
            safe_float(
                opportunity.get(
                    "confidence",
                    0
                )
            ),
            safe_float(
                opportunity.get(
                    "potential_revenue",
                    0
                )
            )
        ),
        reverse=True
    )


# ============================================================
# Select Best Opportunity Per Customer
# ============================================================

def select_best_opportunities(
    opportunities
):
    """
    Select only the strongest opportunity
    for each customer.

    This prevents the merchant from being flooded
    with many recommendations for the same customer.
    """

    ranked = rank_opportunities(
        opportunities
    )

    best_by_customer = {}

    for opportunity in ranked:

        customer_id = opportunity.get(
            "customer_id"
        )

        if not customer_id:
            continue

        if customer_id not in best_by_customer:

            best_by_customer[
                customer_id
            ] = opportunity

    return list(
        best_by_customer.values()
    )


# ============================================================
# Manual Test
# ============================================================

if __name__ == "__main__":

    sample_opportunities = [

        {
            "customer_id": "C001",
            "recommendation": "Wireless Mouse",
            "potential_revenue": 1200,
            "confidence": 0.85,
            "reason": "Laptop purchased without mouse."
        },

        {
            "customer_id": "C001",
            "recommendation": "Laptop Bag",
            "potential_revenue": 2200,
            "confidence": 0.82,
            "reason": "Laptop purchased without laptop bag."
        },

        {
            "customer_id": "C002",
            "recommendation": "Phone Case",
            "potential_revenue": 800,
            "confidence": 0.80,
            "reason": "Smartphone purchased without case."
        }
    ]

    print(
        "\n================================================="
    )

    print(
        "RazorGrowth AI - Decision Engine"
    )

    print(
        "=================================================\n"
    )

    ranked = rank_opportunities(
        sample_opportunities
    )

    print(
        "All ranked opportunities:\n"
    )

    for opportunity in ranked:

        print(
            f"{opportunity['customer_id']} | "
            f"{opportunity['recommendation']} | "
            f"Score: {opportunity['opportunity_score']} | "
            f"Priority: {opportunity['priority']}"
        )

    print(
        "\nBest opportunity per customer:\n"
    )

    best = select_best_opportunities(
        sample_opportunities
    )

    for opportunity in best:

        print(
            f"{opportunity['customer_id']} | "
            f"{opportunity['recommendation']} | "
            f"Score: {opportunity['opportunity_score']} | "
            f"Priority: {opportunity['priority']}"
        )