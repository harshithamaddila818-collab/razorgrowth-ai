import os
import sys
import json

# --------------------------------------------------
# Project Root Path
# --------------------------------------------------

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# --------------------------------------------------
# Imports
# --------------------------------------------------

from dotenv import load_dotenv
from google import genai

from audit.audit_logger import log_opportunity

from agent.growth_agent import (
    analyze_growth_opportunities
)

from backend.approval_gate import (
    validate_opportunity,
    merchant_approval
)

from backend.razorpay_client import (
    create_test_payment_link
)


# --------------------------------------------------
# Load Environment Variables
# --------------------------------------------------

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found in .env"
    )


# --------------------------------------------------
# Gemini Client
# --------------------------------------------------

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# --------------------------------------------------
# Batch AI Analysis
# --------------------------------------------------

def generate_batch_recommendations(
    opportunities
):

    opportunity_data = []

    for opportunity in opportunities:

        opportunity_data.append({

            "customer_id":
                opportunity["customer_id"],

            "product":
                opportunity["recommendation"],

            "potential_revenue":
                opportunity["potential_revenue"],

            "rule_confidence":
                opportunity["confidence"],

            "evidence":
                opportunity["reason"]
        })


    prompt = f"""
You are an AI merchant growth decision engine.

You are given revenue opportunities detected from
real merchant transaction data.

Your job is to evaluate EACH opportunity and return
a structured recommendation.

IMPORTANT RULES:

1. Use ONLY the information provided.
2. Do not invent customer information.
3. Do not claim a purchase is guaranteed.
4. Do not execute payments.
5. Do not create payment links.
6. Your recommendation is advisory only.
7. Every action must require merchant approval.
8. Mention important uncertainty or risk.
9. Keep recommendations concise.
10. Return ONLY valid JSON.

For each opportunity return:

{{
    "customer_id": "...",
    "product": "...",
    "decision": "PURSUE or SKIP",
    "reason": "...",
    "suggested_action": "...",
    "risk": "...",
    "expected_revenue": number,
    "requires_merchant_approval": true
}}

Expected revenue should be a conservative estimate
based on rule confidence.

Example:

Potential Revenue = 1200
Confidence = 0.85

Expected Revenue = 1200 * 0.85 = 1020

Opportunities:

{json.dumps(
    opportunity_data,
    indent=2
)}

Return ONLY a JSON array.
"""


    response = client.models.generate_content(

        model="gemini-2.5-flash",

        contents=prompt
    )


    text = response.text.strip()


    # --------------------------------------------------
    # Remove Markdown JSON fences
    # --------------------------------------------------

    if text.startswith("```"):

        text = text.replace(
            "```json",
            ""
        )

        text = text.replace(
            "```",
            ""
        )

        text = text.strip()


    return json.loads(text)


# --------------------------------------------------
# Main AI Growth Engine
# --------------------------------------------------

def run_ai_growth_analysis():

    print(
        "\n=== RazorGrowth AI — "
        "Merchant Growth Engine ===\n"
    )


    # --------------------------------------------------
    # STEP 1 — Detect Growth Opportunities
    # --------------------------------------------------

    opportunities = analyze_growth_opportunities(
        "data/transactions.csv"
    )


    print(
        f"Detected {len(opportunities)} "
        "revenue opportunities."
    )


    if not opportunities:

        print(
            "\nNo revenue opportunities detected."
        )

        return


    # --------------------------------------------------
    # STEP 2 — Batch Gemini Analysis
    # --------------------------------------------------

    print(
        "\nSending ONE batch request "
        "to Gemini...\n"
    )


    try:

        results = generate_batch_recommendations(
            opportunities
        )

    except Exception as error:

        print(
            "\n❌ AI batch analysis failed."
        )

        print(
            "Error:",
            error
        )

        return


    # --------------------------------------------------
    # Revenue Tracker
    # --------------------------------------------------

    total_expected_revenue = 0


    # --------------------------------------------------
    # STEP 3 — Process Each Opportunity
    # --------------------------------------------------

    for result in results:

        print(
            "\n============================================================"
        )


        print(
            f"Customer: "
            f"{result['customer_id']}"
        )

        print(
            f"Product: "
            f"{result['product']}"
        )

        print(
            f"Decision: "
            f"{result['decision']}"
        )

        print(
            f"Reason: "
            f"{result['reason']}"
        )

        print(
            f"Expected Revenue: "
            f"₹{result['expected_revenue']:,.0f}"
        )

        print(
            f"Suggested Action: "
            f"{result['suggested_action']}"
        )

        print(
            f"Risk: "
            f"{result['risk']}"
        )

        print(
            f"Merchant Approval Required: "
            f"{result['requires_merchant_approval']}"
        )


        # --------------------------------------------------
        # STEP 4 — Safety Gate
        # --------------------------------------------------

        valid, validation_message = (
            validate_opportunity(result)
        )


        print(
            f"Safety Gate: "
            f"{validation_message}"
        )


        # --------------------------------------------------
        # Safety Failure
        # --------------------------------------------------

        if not valid:

            print(
                "❌ Opportunity blocked."
            )


            # Audit blocked opportunity

            try:

                log_opportunity(

                    customer_id=
                        result["customer_id"],

                    product=
                        result["product"],

                    decision=
                        result["decision"],

                    expected_revenue=
                        result["expected_revenue"],

                    safety_gate=
                        validation_message,

                    merchant_approval=
                        "NOT_REQUESTED",

                    action_status=
                        "BLOCKED",

                    reason=
                        result["reason"],

                    payment_link_id=None,

                    payment_link_url=None,

                    payment_link_status=
                        None
                )

                print(
                    "📝 Blocked opportunity "
                    "recorded in audit log."
                )

            except Exception as audit_error:

                print(
                    "⚠️ Audit logging failed:",
                    audit_error
                )


            print(
                "-" * 60
            )

            continue


        # --------------------------------------------------
        # STEP 5 — Merchant Approval
        # --------------------------------------------------

        approved = merchant_approval()


        # --------------------------------------------------
        # Merchant Rejected
        # --------------------------------------------------

        if not approved:

            print(
                "❌ Merchant rejected "
                "the opportunity."
            )


            # IMPORTANT:
            # Do NOT create payment link.

            try:

                log_opportunity(

                    customer_id=
                        result["customer_id"],

                    product=
                        result["product"],

                    decision=
                        result["decision"],

                    expected_revenue=
                        result["expected_revenue"],

                    safety_gate=
                        validation_message,

                    merchant_approval=
                        "REJECTED",

                    action_status=
                        "REJECTED",

                    reason=
                        result["reason"],

                    payment_link_id=None,

                    payment_link_url=None,

                    payment_link_status=
                        None
                )

                print(
                    "📝 Rejection recorded "
                    "in audit log."
                )

            except Exception as audit_error:

                print(
                    "⚠️ Audit logging failed:",
                    audit_error
                )


            print(
                "-" * 60
            )

            continue


        # --------------------------------------------------
        # Merchant Approved
        # --------------------------------------------------

        print(
            "✅ Merchant approved "
            "the opportunity."
        )


        # --------------------------------------------------
        # STEP 6 — Razorpay TEST Payment Link
        # --------------------------------------------------

        print(
            "\nCreating Razorpay "
            "TEST payment link..."
        )


        payment_link = None


        try:

            payment_link = (
                create_test_payment_link(

                    result["customer_id"],

                    result["product"]
                )
            )


            print(
                "\n✅ Razorpay Payment Link "
                "created successfully!"
            )


            print(
                "Payment Link ID:",
                payment_link["id"]
            )


            print(
                "Payment Link URL:",
                payment_link["short_url"]
            )


            print(
                "Payment Link Status:",
                payment_link["status"]
            )


        except Exception as error:

            print(
                "\n❌ Razorpay Payment Link "
                "creation failed."
            )


            print(
                "Error:",
                error
            )


            # --------------------------------------------------
            # STEP 7 — Audit Payment Failure
            # --------------------------------------------------

            try:

                log_opportunity(

                    customer_id=
                        result["customer_id"],

                    product=
                        result["product"],

                    decision=
                        result["decision"],

                    expected_revenue=
                        result["expected_revenue"],

                    safety_gate=
                        validation_message,

                    merchant_approval=
                        "APPROVED",

                    action_status=
                        "PAYMENT_LINK_FAILED",

                    reason=
                        result["reason"],

                    payment_link_id=None,

                    payment_link_url=None,

                    payment_link_status=
                        "failed"
                )


                print(
                    "📝 Payment failure "
                    "recorded in audit log."
                )


            except Exception as audit_error:

                print(
                    "⚠️ Audit logging failed:",
                    audit_error
                )


            print(
                "-" * 60
            )


            continue


        # --------------------------------------------------
        # STEP 8 — Audit Successful Payment Link
        # --------------------------------------------------

        try:

            log_opportunity(

                customer_id=
                    result["customer_id"],

                product=
                    result["product"],

                decision=
                    result["decision"],

                expected_revenue=
                    result["expected_revenue"],

                safety_gate=
                    validation_message,

                merchant_approval=
                    "APPROVED",

                action_status=
                    "PAYMENT_LINK_CREATED",

                reason=
                    result["reason"],

                payment_link_id=
                    payment_link["id"],

                payment_link_url=
                    payment_link["short_url"],

                payment_link_status=
                    payment_link["status"]
            )



        except Exception as audit_error:

            print(
                "⚠️ Audit logging failed:",
                audit_error
            )


        # --------------------------------------------------
        # STEP 9 — Add Revenue
        # --------------------------------------------------

        total_expected_revenue += (
            result["expected_revenue"]
        )


        print(
            "-" * 60
        )


    # --------------------------------------------------
    # STEP 10 — Final Growth Summary
    # --------------------------------------------------

    print(
        "\n=== Final Growth Summary ==="
    )


    print(
        f"Total Expected Revenue: "
        f"₹{total_expected_revenue:,.0f}"
    )


    print(
        "\n✅ RazorGrowth AI flow completed."
    )


# --------------------------------------------------
# Entry Point
# --------------------------------------------------

if __name__ == "__main__":

    run_ai_growth_analysis()