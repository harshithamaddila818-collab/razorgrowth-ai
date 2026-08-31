import os
import uuid
import time

from dotenv import load_dotenv
import razorpay
import streamlit as st


# ============================================================
# LOAD LOCAL ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# RAZORPAY CREDENTIALS
# Supports:
# 1. Local .env
# 2. Streamlit Cloud Secrets
# ============================================================

key_id = os.getenv("RAZORPAY_KEY_ID")
key_secret = os.getenv("RAZORPAY_KEY_SECRET")


# Streamlit Cloud fallback
if not key_id:
    try:
        key_id = st.secrets["RAZORPAY_KEY_ID"]
    except Exception:
        key_id = None


if not key_secret:
    try:
        key_secret = st.secrets["RAZORPAY_KEY_SECRET"]
    except Exception:
        key_secret = None


# ============================================================
# VALIDATE RAZORPAY CREDENTIALS
# ============================================================

if not key_id or not key_secret:
    raise ValueError(
        "Razorpay credentials are not configured."
    )


# ============================================================
# RAZORPAY CLIENT
# ============================================================

client = razorpay.Client(
    auth=(key_id, key_secret)
)


# ============================================================
# CREATE RAZORPAY TEST PAYMENT LINK
# ============================================================

def create_test_payment_link(customer_id, product):

    reference_id = (
        f"RGAI_{uuid.uuid4().hex[:10]}"
    )

    payment_data = {
        "amount": 1000,
        "currency": "INR",
        "accept_partial": False,
        "description": (
            f"RazorGrowth AI Test Offer - {product}"
        ),
        "reference_id": reference_id,
        "customer": {
            "name": f"Customer {customer_id}",
            "email": "test@example.com",
            "contact": "+919876543210",
        },
        "notify": {
            "sms": False,
            "email": False,
            "whatsapp": False,
        },
        "reminder_enable": False,
    }

    payment_link = client.payment_link.create(
        data=payment_data
    )

    return payment_link