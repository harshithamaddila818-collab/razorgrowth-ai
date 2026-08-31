"""
RazorGrowth AI - Customer Intelligence Layer

Builds customer-level intelligence from transaction history.

This module:
- analyzes customer purchase history
- calculates customer spend
- calculates purchase frequency
- calculates recency
- identifies customer value
- identifies purchased categories/products
- does NOT call Gemini
- does NOT create payment links
- does NOT approve actions
"""

import pandas as pd


# ============================================================
# Configuration
# ============================================================

HIGH_VALUE_SPEND = 50000.0
MEDIUM_VALUE_SPEND = 25000.0


# ============================================================
# Safe Float
# ============================================================

def safe_float(value, default=0.0):

    try:
        return float(value)

    except (
        TypeError,
        ValueError
    ):

        return default


# ============================================================
# Customer Value
# ============================================================

def get_customer_value(total_spend):

    total_spend = safe_float(
        total_spend
    )

    if total_spend >= HIGH_VALUE_SPEND:
        return "HIGH"

    if total_spend >= MEDIUM_VALUE_SPEND:
        return "MEDIUM"

    return "STANDARD"


# ============================================================
# Recency Score
# ============================================================

def calculate_recency_score(
    days_since_purchase
):

    days_since_purchase = max(
        0,
        safe_float(
            days_since_purchase
        )
    )

    # Very recent purchase
    if days_since_purchase <= 7:
        return 1.00

    # Recent purchase
    if days_since_purchase <= 30:
        return 0.85

    # Moderately recent
    if days_since_purchase <= 60:
        return 0.70

    # Older customer activity
    if days_since_purchase <= 90:
        return 0.50

    return 0.30


# ============================================================
# Customer Intelligence
# ============================================================

def build_customer_profiles(
    file_path,
    reference_date=None
):

    df = pd.read_csv(
        file_path
    )

    required_columns = {
        "customer_id",
        "product",
        "category",
        "amount",
        "date"
    }

    missing_columns = (
        required_columns
        - set(df.columns)
    )

    if missing_columns:

        raise ValueError(
            "Missing required columns: "
            + ", ".join(
                sorted(
                    missing_columns
                )
            )
        )

    # --------------------------------------------------------
    # Clean data
    # --------------------------------------------------------

    df = df.copy()

    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="coerce"
    ).fillna(0)

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    df = df.dropna(
        subset=[
            "customer_id",
            "date"
        ]
    )

    # --------------------------------------------------------
    # Reference date
    # --------------------------------------------------------

    if reference_date is None:

        reference_date = df["date"].max()

    else:

        reference_date = pd.to_datetime(
            reference_date
        )

    profiles = {}

    # --------------------------------------------------------
    # Build profile for every customer
    # --------------------------------------------------------

    for customer_id, customer_data in df.groupby(
        "customer_id"
    ):

        total_spend = float(
            customer_data["amount"].sum()
        )

        order_count = int(
            len(customer_data)
        )

        unique_products = sorted(
            {
                str(product).strip()
                for product
                in customer_data["product"]
                if pd.notna(product)
            }
        )

        categories = sorted(
            {
                str(category).strip()
                for category
                in customer_data["category"]
                if pd.notna(category)
            }
        )

        last_purchase_date = (
            customer_data["date"].max()
        )

        days_since_purchase = int(
            (
                reference_date
                - last_purchase_date
            ).days
        )

        recency_score = (
            calculate_recency_score(
                days_since_purchase
            )
        )

        customer_value = (
            get_customer_value(
                total_spend
            )
        )

        profiles[
            customer_id
        ] = {

            "customer_id":
                customer_id,

            "total_spend":
                round(
                    total_spend,
                    2
                ),

            "order_count":
                order_count,

            "unique_products":
                unique_products,

            "categories":
                categories,

            "last_purchase_date":
                last_purchase_date.strftime(
                    "%Y-%m-%d"
                ),

            "days_since_purchase":
                days_since_purchase,

            "recency_score":
                recency_score,

            "customer_value":
                customer_value
        }

    return profiles


# ============================================================
# Get Single Customer Profile
# ============================================================

def get_customer_profile(
    profiles,
    customer_id
):

    return profiles.get(
        customer_id
    )


# ============================================================
# Customer Value Score
# ============================================================

def calculate_customer_value_score(
    profile
):

    if not profile:
        return 0.0

    spend = safe_float(
        profile.get(
            "total_spend",
            0
        )
    )

    # Normalize spend.
    # ₹50,000+ receives maximum contribution.
    spend_score = min(
        spend / HIGH_VALUE_SPEND,
        1.0
    )

    recency_score = safe_float(
        profile.get(
            "recency_score",
            0
        )
    )

    # Combine monetary value and recency.
    score = (
        spend_score * 0.60
        +
        recency_score * 0.40
    )

    return round(
        min(
            max(
                score,
                0.0
            ),
            1.0
        ),
        2
    )


# ============================================================
# Manual Test
# ============================================================

if __name__ == "__main__":

    profiles = build_customer_profiles(
        "data/transactions.csv"
    )

    print(
        "\n================================================="
    )

    print(
        "RazorGrowth AI - Customer Intelligence"
    )

    print(
        "=================================================\n"
    )

    for customer_id, profile in profiles.items():

        value_score = (
            calculate_customer_value_score(
                profile
            )
        )

        print(
            f"Customer: {customer_id}"
        )

        print(
            f"Total Spend: "
            f"Rs. {profile['total_spend']:,.0f}"
        )

        print(
            f"Orders: "
            f"{profile['order_count']}"
        )

        print(
            f"Last Purchase: "
            f"{profile['last_purchase_date']}"
        )

        print(
            f"Days Since Purchase: "
            f"{profile['days_since_purchase']}"
        )

        print(
            f"Customer Value: "
            f"{profile['customer_value']}"
        )

        print(
            f"Customer Value Score: "
            f"{value_score}"
        )

        print(
            f"Products: "
            f"{', '.join(profile['unique_products'])}"
        )

        print(
            f"Categories: "
            f"{', '.join(profile['categories'])}"
        )

        print(
            "-" * 60
        )