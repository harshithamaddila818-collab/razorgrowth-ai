import os
import uuid
import time

from dotenv import load_dotenv
import razorpay


# --------------------------------------------------
# Load environment variables
# --------------------------------------------------

load_dotenv()


# --------------------------------------------------
# Razorpay credentials
# --------------------------------------------------

key_id = os.getenv("RAZORPAY_KEY_ID")
key_secret = os.getenv("RAZORPAY_KEY_SECRET")

if not key_id or not key_secret:
    raise ValueError(
        "Razorpay credentials not found in .env"
    )


# --------------------------------------------------
# Razorpay Client
# --------------------------------------------------

client = razorpay.Client(
    auth=(key_id, key_secret)
)


# --------------------------------------------------
# Create TEST Payment Link
# --------------------------------------------------

def create_test_payment_link(customer_id, product):

    reference_id = (
        f"RGAI_{uuid.uuid4().hex[:10]}"
    )

    data = {
        # ₹10 = 1000 paise
        # TEST amount only
        "amount": 1000,

        "currency": "INR",

        "accept_partial": False,

        "reference_id": reference_id,

        "description": (
            f"RazorGrowth AI Test Offer - {product}"
        ),

        "customer": {
            "name": f"Customer {customer_id}",
            "email": "test@example.com",

            # Test contact
            "contact": "+919876543210"
        },

        "notify": {
            "sms": False,
            "email": False
        }
    }


    # --------------------------------------------------
    # Retry configuration
    # --------------------------------------------------

    max_retries = 3

    for attempt in range(max_retries):

        try:

            print(
                f"Creating payment link "
                f"(attempt {attempt + 1}/{max_retries})..."
            )

            payment_link = (
                client.payment_link.create(data)
            )

            return payment_link


        except Exception as error:

            error_message = str(error).lower()


            # ------------------------------------------
            # Rate Limit Handling
            # ------------------------------------------

            if (
                "too many requests"
                in error_message
            ):

                if attempt < max_retries - 1:

                    wait_time = 10 * (attempt + 1)

                    print(
                        "\n⚠️ Razorpay rate limit reached."
                    )

                    print(
                        f"Waiting {wait_time} seconds "
                        "before retry..."
                    )

                    time.sleep(wait_time)

                else:

                    print(
                        "\n❌ Razorpay rate limit "
                        "still active after retries."
                    )

                    raise


            # ------------------------------------------
            # Other Errors
            # ------------------------------------------

            else:

                raise


# --------------------------------------------------
# Direct Test
# --------------------------------------------------

if __name__ == "__main__":

    try:

        result = create_test_payment_link(
            "C003",
            "Wireless Mouse"
        )


        print(
            "\n✅ Payment Link created successfully!"
        )

        print(
            "Payment Link ID:",
            result["id"]
        )

        print(
            "Payment Link URL:",
            result["short_url"]
        )

        print(
            "Status:",
            result["status"]
        )


    except Exception as error:

        print(
            "\n❌ Payment Link creation failed."
        )

        print(
            "Error:",
            error
        )