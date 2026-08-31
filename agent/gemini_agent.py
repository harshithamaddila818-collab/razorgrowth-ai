# -*- coding: utf-8 -*-

"""
RazorGrowth AI - Agent 2
Gemini Decision Engine

Responsibilities:
- Evaluate qualified opportunities
- Decide PURSUE or SKIP
- Explain the decision
- Suggest an advisory action
- Identify risk
- Calculate expected revenue
- Require merchant approval

IMPORTANT:
- Gemini never creates payment links
- Gemini never approves merchants
- Gemini never executes payments
- Gemini never directly contacts customers
- All external actions remain behind the approval gate
"""

import json
from typing import Any


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = "gemini-2.5-flash"

VALID_DECISIONS = {
    "PURSUE",
    "SKIP"
}


# ============================================================
# SAFE HELPERS
# ============================================================

def safe_float(
    value,
    default=0.0
):
    """
    Safely convert a value to float.
    """

    try:

        if value is None:
            return default

        return float(value)

    except (
        TypeError,
        ValueError
    ):

        return default


def normalize_decision(
    value
):
    """
    Normalize Gemini's decision.
    """

    if value is None:
        return ""

    return str(
        value
    ).strip().upper()


# ============================================================
# PROMPT BUILDER
# ============================================================

def build_decision_prompt(
    opportunities
):
    """
    Build a strict Gemini decision prompt.
    """

    opportunity_data = []

    for opportunity in opportunities:

        opportunity_data.append(
            {
                "customer_id":
                    opportunity.get(
                        "customer_id"
                    ),

                "product":
                    opportunity.get(
                        "recommendation"
                    ),

                "trigger_product":
                    opportunity.get(
                        "trigger_product"
                    ),

                "potential_revenue":
                    safe_float(
                        opportunity.get(
                            "potential_revenue",
                            0
                        )
                    ),

                "confidence":
                    safe_float(
                        opportunity.get(
                            "confidence",
                            0
                        )
                    ),

                "opportunity_score":
                    safe_float(
                        opportunity.get(
                            "opportunity_score",
                            0
                        )
                    ),

                "priority":
                    opportunity.get(
                        "priority"
                    ),

                "customer_value":
                    opportunity.get(
                        "customer_value"
                    ),

                "customer_value_score":
                    safe_float(
                        opportunity.get(
                            "customer_value_score",
                            0
                        )
                    ),

                "evidence":
                    opportunity.get(
                        "reason",
                        ""
                    )
            }
        )

    return f"""
You are RazorGrowth AI, an advisory merchant
growth decision engine.

Your task is to evaluate deterministic,
pre-qualified cross-sell opportunities.

IMPORTANT SAFETY RULES:

1. Use ONLY the supplied information.
2. Never invent customer information.
3. Never invent purchase history.
4. Never invent product compatibility facts.
5. Never guarantee a purchase.
6. Never execute a payment.
7. Never create a payment link.
8. Never approve an opportunity on behalf of a merchant.
9. Every external action requires merchant approval.
10. Recommendations are advisory only.
11. Clearly mention uncertainty and risk.
12. Prefer evidence-based opportunities.
13. If evidence is weak, choose SKIP.
14. Return ONLY valid JSON.
15. Do not return markdown.
16. Do not return ```json fences.
17. Return exactly one result for every supplied opportunity.

DECISION RULES:

- Choose PURSUE when the opportunity is strongly supported
  by the supplied transaction evidence and deterministic score.

- Choose SKIP when evidence is weak, confidence is low,
  or the recommendation is not sufficiently justified.

EXPECTED REVENUE:

expected_revenue =
potential_revenue * confidence

Round expected_revenue to 2 decimal places.

For every opportunity return exactly:

{{
    "customer_id": "...",
    "product": "...",
    "decision": "PURSUE or SKIP",
    "reason": "...",
    "suggested_action": "...",
    "risk": "...",
    "expected_revenue": 0,
    "requires_merchant_approval": true
}}

For SKIP opportunities:

- expected_revenue must be 0
- requires_merchant_approval must be true
- explain why the opportunity should not be pursued

For PURSUE opportunities:

- expected_revenue must be based ONLY on
  potential_revenue * confidence
- requires_merchant_approval must be true
- suggested_action must remain advisory

SUPPLIED OPPORTUNITIES:

{json.dumps(
    opportunity_data,
    indent=2
)}

Return ONLY a JSON array.
"""


# ============================================================
# JSON EXTRACTION
# ============================================================

def extract_json(
    text
):
    """
    Extract a JSON array from Gemini output.

    Handles accidental markdown fences safely.
    """

    if text is None:

        raise ValueError(
            "Gemini returned an empty response."
        )

    text = str(
        text
    ).strip()

    if not text:

        raise ValueError(
            "Gemini returned an empty response."
        )

    # Remove markdown fences if Gemini
    # accidentally returns them.
    if text.startswith("```"):

        lines = text.splitlines()

        cleaned_lines = []

        for line in lines:

            stripped = line.strip()

            if stripped.startswith("```"):

                continue

            cleaned_lines.append(
                line
            )

        text = "\n".join(
            cleaned_lines
        ).strip()

    # Find JSON array boundaries.
    start = text.find("[")

    end = text.rfind("]")

    if start == -1 or end == -1:

        raise ValueError(
            "Gemini response does not contain a JSON array."
        )

    text = text[
        start:end + 1
    ]

    try:

        return json.loads(
            text
        )

    except json.JSONDecodeError as error:

        raise ValueError(
            f"Invalid JSON returned by Gemini: {error}"
        ) from error


# ============================================================
# RESULT VALIDATION
# ============================================================

def validate_result_structure(
    result
):
    """
    Validate one Gemini result structurally.
    """

    required_fields = {
        "customer_id",
        "product",
        "decision",
        "reason",
        "suggested_action",
        "risk",
        "expected_revenue",
        "requires_merchant_approval"
    }

    if not isinstance(
        result,
        dict
    ):

        raise ValueError(
            "Gemini result must be an object."
        )

    missing_fields = (
        required_fields
        -
        set(
            result.keys()
        )
    )

    if missing_fields:

        raise ValueError(
            "Gemini result missing fields: "
            +
            ", ".join(
                sorted(
                    missing_fields
                )
            )
        )


# ============================================================
# RESULT NORMALIZATION
# ============================================================

def normalize_result(
    result,
    source_opportunity
):
    """
    Normalize and validate a Gemini result.

    Important:
    Revenue and customer/product identity are taken
    from deterministic source data, not trusted blindly
    from Gemini.
    """

    validate_result_structure(
        result
    )

    decision = normalize_decision(
        result.get(
            "decision"
        )
    )

    if decision not in VALID_DECISIONS:

        raise ValueError(
            f"Invalid Gemini decision: {decision}"
        )

    customer_id = str(
        source_opportunity.get(
            "customer_id"
        )
    )

    product = str(
        source_opportunity.get(
            "recommendation"
        )
    )

    potential_revenue = safe_float(
        source_opportunity.get(
            "potential_revenue",
            0
        )
    )

    confidence = safe_float(
        source_opportunity.get(
            "confidence",
            0
        )
    )

    deterministic_expected_revenue = round(
        potential_revenue * confidence,
        2
    )

    # Gemini's revenue calculation is advisory,
    # but we enforce deterministic calculation.
    if decision == "PURSUE":

        expected_revenue = (
            deterministic_expected_revenue
        )

    else:

        expected_revenue = 0.0

    normalized = {

        "customer_id":
            customer_id,

        "product":
            product,

        "decision":
            decision,

        "reason":
            str(
                result.get(
                    "reason",
                    ""
                )
            ).strip(),

        "suggested_action":
            str(
                result.get(
                    "suggested_action",
                    ""
                )
            ).strip(),

        "risk":
            str(
                result.get(
                    "risk",
                    ""
                )
            ).strip(),

        "expected_revenue":
            expected_revenue,

        "requires_merchant_approval":
            True
    }

    if not normalized[
        "reason"
    ]:

        raise ValueError(
            "Gemini result reason cannot be empty."
        )

    if not normalized[
        "risk"
    ]:

        raise ValueError(
            "Gemini result risk cannot be empty."
        )

    if not normalized[
        "suggested_action"
    ]:

        raise ValueError(
            "Gemini result suggested_action cannot be empty."
        )

    return normalized


# ============================================================
# BATCH VALIDATION
# ============================================================

def validate_batch_results(
    results,
    opportunities
):
    """
    Validate that Gemini returned exactly one result
    for every supplied opportunity.
    """

    if not isinstance(
        results,
        list
    ):

        raise ValueError(
            "Gemini response must be a JSON array."
        )

    if len(results) != len(
        opportunities
    ):

        raise ValueError(
            "Gemini returned "
            f"{len(results)} results for "
            f"{len(opportunities)} opportunities."
        )

    normalized_results = []

    for index, (
        result,
        opportunity
    ) in enumerate(
        zip(
            results,
            opportunities
        )
    ):

        try:

            normalized = normalize_result(
                result,
                opportunity
            )

            normalized_results.append(
                normalized
            )

        except Exception as error:

            raise ValueError(
                f"Invalid Gemini result at index "
                f"{index}: {error}"
            ) from error

    return normalized_results


# ============================================================
# GEMINI EXECUTION
# ============================================================

def analyze_opportunities(
    client,
    opportunities
):
    """
    Send a batch of opportunities to Gemini.

    The client is injected so tests can mock it easily.
    """

    if not opportunities:

        return []

    if client is None:

        raise ValueError(
            "Gemini client is not configured."
        )

    prompt = build_decision_prompt(
        opportunities
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    text = getattr(
        response,
        "text",
        None
    )

    results = extract_json(
        text
    )

    return validate_batch_results(
        results,
        opportunities
    )


# ============================================================
# SAFE ANALYSIS WRAPPER
# ============================================================

def safe_analyze_opportunities(
    client,
    opportunities
):
    """
    Production-safe wrapper.

    Returns:
        {
            "success": True,
            "results": [...]
        }

    or:

        {
            "success": False,
            "results": [],
            "error": "..."
        }
    """

    try:

        results = analyze_opportunities(
            client,
            opportunities
        )

        return {
            "success": True,
            "results": results,
            "error": None
        }

    except Exception as error:

        return {
            "success": False,
            "results": [],
            "error": str(
                error
            )
        }


# ============================================================
# MANUAL TEST
# ============================================================

if __name__ == "__main__":

    print(
        "=" * 70
    )

    print(
        "RazorGrowth AI - Agent 2"
    )

    print(
        "Gemini Decision Engine"
    )

    print(
        "=" * 70
    )

    print(
        "\nAgent 2 module loaded successfully."
    )

    print(
        "No Gemini API call is made during manual module loading."
    )

    print(
        "\nSafety properties:"
    )

    print(
        "✓ Advisory only"
    )

    print(
        "✓ No payment execution"
    )

    print(
        "✓ Merchant approval required"
    )

    print(
        "✓ Deterministic expected revenue"
    )

    print(
        "✓ Strict JSON validation"
    )

    print(
        "✓ PURSUE / SKIP validation"
    )