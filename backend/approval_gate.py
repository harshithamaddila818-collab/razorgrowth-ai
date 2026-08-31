def validate_opportunity(opportunity):

    required_fields = [
        "customer_id",
        "product",
        "expected_revenue",
        "decision",
        "requires_merchant_approval"
    ]

    for field in required_fields:
        if field not in opportunity:
            return False, f"Missing field: {field}"

    if opportunity["decision"] != "PURSUE":
        return False, "Opportunity was not approved by AI decision."

    if opportunity["expected_revenue"] <= 0:
        return False, "Expected revenue must be greater than zero."

    if opportunity["requires_merchant_approval"] is not True:
        return False, "Merchant approval requirement missing."

    return True, "Opportunity passed safety validation."


def merchant_approval():

    print("\n=== Merchant Approval ===")

    choice = input(
        "Approve this revenue opportunity? (yes/no): "
    ).strip().lower()

    if choice == "yes":
        return True

    return False