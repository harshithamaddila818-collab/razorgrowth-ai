from backend.approval_gate import validate_opportunity


def test_valid_opportunity_passes_safety_gate():

    opportunity = {
        "customer_id": "C003",
        "product": "Wireless Mouse",
        "decision": "PURSUE",
        "reason": "Customer purchased a laptop.",
        "suggested_action": "Recommend a wireless mouse.",
        "risk": "Customer may already own one.",
        "expected_revenue": 1020,
        "requires_merchant_approval": True,
    }

    valid, message = validate_opportunity(
        opportunity
    )

    assert valid is True
    assert isinstance(message, str)


def test_invalid_decision_is_blocked():

    opportunity = {
        "customer_id": "C003",
        "product": "Wireless Mouse",
        "decision": "INVALID",
        "reason": "Test",
        "suggested_action": "Test",
        "risk": "Test",
        "expected_revenue": 1020,
        "requires_merchant_approval": True,
    }

    valid, message = validate_opportunity(
        opportunity
    )

    assert valid is False
    assert isinstance(message, str)