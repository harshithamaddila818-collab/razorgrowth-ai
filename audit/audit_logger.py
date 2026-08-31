import json
import os
from datetime import datetime


# --------------------------------------------------
# Audit log file
# --------------------------------------------------

AUDIT_FILE = os.path.join(
    os.path.dirname(__file__),
    "audit_log.json"
)


# --------------------------------------------------
# Save audit record
# --------------------------------------------------

def log_opportunity(
    customer_id,
    product,
    decision,
    expected_revenue,
    safety_gate,
    merchant_approval,
    action_status,
    reason,
    payment_link_id=None,
    payment_link_url=None,
    payment_link_status=None
):

    # ----------------------------------------------
    # Create audit record
    # ----------------------------------------------

    record = {
        "timestamp": datetime.now().isoformat(
            timespec="seconds"
        ),

        "customer_id": customer_id,

        "product": product,

        "decision": decision,

        "expected_revenue": expected_revenue,

        "safety_gate": safety_gate,

        "merchant_approval": merchant_approval,

        "action_status": action_status,

        "reason": reason,

        "payment_link_id": payment_link_id,

        "payment_link_url": payment_link_url,

        "payment_link_status": payment_link_status
    }


    # ----------------------------------------------
    # Read existing audit log
    # ----------------------------------------------

    if os.path.exists(AUDIT_FILE):

        try:

            with open(
                AUDIT_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                logs = json.load(file)

        except (
            json.JSONDecodeError,
            FileNotFoundError
        ):

            logs = []

    else:

        logs = []


    # ----------------------------------------------
    # Add new record
    # ----------------------------------------------

    logs.append(record)


    # ----------------------------------------------
    # Save audit log
    # ----------------------------------------------

    with open(
        AUDIT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            logs,
            file,
            indent=4,
            ensure_ascii=False
        )


    print(
        "📝 Audit record saved successfully."
    )

    return record


# --------------------------------------------------
# Test
# --------------------------------------------------

if __name__ == "__main__":

    test_record = log_opportunity(

        customer_id="TEST001",

        product="Wireless Mouse",

        decision="PURSUE",

        expected_revenue=1020,

        safety_gate=(
            "Opportunity passed safety validation."
        ),

        merchant_approval="APPROVED",

        action_status=(
            "PAYMENT_LINK_CREATED"
        ),

        reason=(
            "Test audit record."
        ),

        payment_link_id="plink_TEST123",

        payment_link_url=(
            "https://rzp.io/rzp/TEST123"
        ),

        payment_link_status="created"
    )


    print("\n=== Test Audit Record ===")

    print(
        json.dumps(
            test_record,
            indent=4,
            ensure_ascii=False
        )
    )