import json

import audit.audit_logger as audit_logger


def test_log_opportunity_creates_audit_record(
    tmp_path,
    monkeypatch
):

    test_audit_file = tmp_path / "audit_log.json"

    monkeypatch.setattr(
        audit_logger,
        "AUDIT_FILE",
        str(test_audit_file)
    )

    audit_logger.log_opportunity(
        customer_id="TEST001",
        product="Wireless Mouse",
        decision="PURSUE",
        expected_revenue=1020,
        safety_gate="Opportunity passed safety validation.",
        merchant_approval="APPROVED",
        action_status="PAYMENT_LINK_CREATED",
        reason="Test audit record.",
        payment_link_id="plink_TEST123",
        payment_link_url="https://rzp.io/rzp/TEST123",
        payment_link_status="created"
    )

    assert test_audit_file.exists()

    with open(
        test_audit_file,
        "r",
        encoding="utf-8"
    ) as file:

        logs = json.load(file)

    assert len(logs) == 1

    record = logs[0]

    assert record["customer_id"] == "TEST001"

    assert record["product"] == "Wireless Mouse"

    assert record["decision"] == "PURSUE"

    assert record["expected_revenue"] == 1020

    assert record["merchant_approval"] == "APPROVED"

    assert record["action_status"] == "PAYMENT_LINK_CREATED"

    assert record["payment_link_id"] == "plink_TEST123"

    assert record["payment_link_status"] == "created"