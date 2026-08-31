from unittest.mock import patch


def test_razorpay_client_initialization():

    fake_client = object()

    with patch(
        "razorpay.Client",
        return_value=fake_client
    ) as mock_client:

        import razorpay

        client = razorpay.Client(
            auth=(
                "test_key_id",
                "test_key_secret"
            )
        )

        assert client is fake_client

        mock_client.assert_called_once_with(
            auth=(
                "test_key_id",
                "test_key_secret"
            )
        )


def test_razorpay_payment_link_response():

    fake_payment_link = {
        "id": "plink_TEST123",
        "short_url": "https://rzp.io/rzp/TEST123",
        "status": "created"
    }

    assert fake_payment_link["id"].startswith(
        "plink_"
    )

    assert fake_payment_link["status"] == "created"

    assert fake_payment_link["short_url"].startswith(
        "https://rzp.io/"
    )