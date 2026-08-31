import json
from pathlib import Path


def find_existing_payment_link(logs, customer_id, product):
    """
    Test version of duplicate-payment lookup logic.
    """

    for log in logs:

        if (
            log.get("customer_id") == customer_id
            and log.get("product") == product
            and log.get("action_status")
            == "PAYMENT_LINK_CREATED"
            and log.get("payment_link_url")
        ):
            return log

    return None


def test_duplicate_payment_link_is_detected():

    logs = [
        {
            "customer_id": "C003",
            "product": "Wireless Mouse",
            "action_status": "PAYMENT_LINK_CREATED",
            "payment_link_id": "plink_TEST123",
            "payment_link_url": "https://rzp.io/test123"
        }
    ]

    result = find_existing_payment_link(
        logs,
        "C003",
        "Wireless Mouse"
    )

    assert result is not None
    assert result["payment_link_id"] == "plink_TEST123"


def test_different_customer_is_not_duplicate():

    logs = [
        {
            "customer_id": "C003",
            "product": "Wireless Mouse",
            "action_status": "PAYMENT_LINK_CREATED",
            "payment_link_id": "plink_TEST123",
            "payment_link_url": "https://rzp.io/test123"
        }
    ]

    result = find_existing_payment_link(
        logs,
        "C004",
        "Wireless Mouse"
    )

    assert result is None


def test_different_product_is_not_duplicate():

    logs = [
        {
            "customer_id": "C003",
            "product": "Wireless Mouse",
            "action_status": "PAYMENT_LINK_CREATED",
            "payment_link_id": "plink_TEST123",
            "payment_link_url": "https://rzp.io/test123"
        }
    ]

    result = find_existing_payment_link(
        logs,
        "C003",
        "Phone Case"
    )

    assert result is None


def test_rejected_opportunity_is_not_duplicate():

    logs = [
        {
            "customer_id": "C003",
            "product": "Wireless Mouse",
            "action_status": "REJECTED",
            "payment_link_url": None
        }
    ]

    result = find_existing_payment_link(
        logs,
        "C003",
        "Wireless Mouse"
    )

    assert result is None
