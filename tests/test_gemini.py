import json
from unittest.mock import patch

from app import generate_batch_recommendations


def test_gemini_batch_response():

    fake_response = type(
        "FakeResponse",
        (),
        {
            "text": json.dumps(
                [
                    {
                        "customer_id": "C003",
                        "product": "Wireless Mouse",
                        "decision": "PURSUE",
                        "reason": "Laptop purchase indicates accessory opportunity.",
                        "suggested_action": "Recommend a compatible wireless mouse.",
                        "risk": "Customer may already own one.",
                        "expected_revenue": 1020,
                        "requires_merchant_approval": True
                    }
                ]
            )
        }
    )()

    fake_opportunities = [
        {
            "customer_id": "C003",
            "recommendation": "Wireless Mouse",
            "potential_revenue": 1200,
            "confidence": 0.85,
            "reason": "Customer purchased a laptop."
        }
    ]

    with patch(
        "app.client.models.generate_content",
        return_value=fake_response
    ):

        result = generate_batch_recommendations(
            fake_opportunities
        )

    assert isinstance(result, list)

    assert len(result) == 1

    assert result[0]["customer_id"] == "C003"

    assert result[0]["product"] == "Wireless Mouse"

    assert result[0]["decision"] == "PURSUE"

    assert result[0]["expected_revenue"] == 1020

    assert result[0]["requires_merchant_approval"] is True