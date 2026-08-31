# -*- coding: utf-8 -*-

"""
RazorGrowth AI - Agent 1 Tests

Tests for deterministic opportunity detection,
cross-sell logic, ranking and qualification.
"""

from pathlib import Path

import pandas as pd

from agent.growth_agent import (
    analyze_growth_opportunities,
    already_purchased,
    calculate_opportunity_score,
    deduplicate_opportunities,
    generate_candidates,
    is_qualified,
    limit_opportunities_per_customer,
    rank_opportunities,
)


# ============================================================
# HELPERS
# ============================================================

def make_profile(
    customer_id="C001",
    products=None,
    total_spend=50000,
    order_count=1,
):
    """
    Create a minimal customer profile for testing.
    """

    products = products or ["Laptop"]

    return {
        "customer_id": customer_id,
        "products": products,
        "products_normalized": {
            str(product).strip().lower()
            for product in products
        },
        "categories": ["Electronics"],
        "total_spend": total_spend,
        "order_count": order_count,
    }


# ============================================================
# TEST 1
# ============================================================

def test_already_purchased_product_is_detected():

    profile = make_profile(
        products=[
            "Laptop",
            "Wireless Mouse",
        ]
    )

    assert already_purchased(
        profile,
        "Wireless Mouse"
    ) is True


# ============================================================
# TEST 2
# ============================================================

def test_unpurchased_product_is_not_marked_as_purchased():

    profile = make_profile(
        products=[
            "Laptop",
        ]
    )

    assert already_purchased(
        profile,
        "Laptop Bag"
    ) is False


# ============================================================
# TEST 3
# ============================================================

def test_purchased_products_are_not_generated_as_candidates():

    profile = make_profile(
        products=[
            "Laptop",
            "Wireless Mouse",
        ]
    )

    candidates = generate_candidates(
        profile
    )

    products = {
        candidate["recommendation"]
        for candidate in candidates
    }

    assert "Wireless Mouse" not in products


# ============================================================
# TEST 4
# ============================================================

def test_same_customer_can_have_multiple_products():

    profile = make_profile(
        customer_id="C003",
        products=[
            "Laptop",
        ]
    )

    candidates = generate_candidates(
        profile
    )

    products = {
        candidate["recommendation"]
        for candidate in candidates
    }

    assert "Laptop Bag" in products
    assert "Wireless Mouse" in products

    assert len(products) >= 2


# ============================================================
# TEST 5
# ============================================================

def test_duplicate_customer_product_is_removed():

    opportunities = [

        {
            "customer_id": "C001",
            "recommendation": "Laptop Bag",
            "confidence": 0.80,
            "potential_revenue": 2200,
        },

        {
            "customer_id": "C001",
            "recommendation": "Laptop Bag",
            "confidence": 0.75,
            "potential_revenue": 2200,
        },

        {
            "customer_id": "C001",
            "recommendation": "Wireless Mouse",
            "confidence": 0.70,
            "potential_revenue": 1200,
        },
    ]

    result = deduplicate_opportunities(
        opportunities
    )

    keys = {
        (
            item["customer_id"],
            item["recommendation"],
        )
        for item in result
    }

    assert len(keys) == 2

    assert (
        "C001",
        "Laptop Bag",
    ) in keys

    assert (
        "C001",
        "Wireless Mouse",
    ) in keys


# ============================================================
# TEST 6
# ============================================================

def test_duplicate_keeps_stronger_opportunity():

    opportunities = [

        {
            "customer_id": "C001",
            "recommendation": "Laptop Bag",
            "confidence": 0.70,
            "potential_revenue": 2200,
        },

        {
            "customer_id": "C001",
            "recommendation": "Laptop Bag",
            "confidence": 0.90,
            "potential_revenue": 2200,
        },
    ]

    result = deduplicate_opportunities(
        opportunities
    )

    assert len(result) == 1

    assert result[0]["confidence"] == 0.90


# ============================================================
# TEST 7
# ============================================================

def test_maximum_opportunities_per_customer():

    opportunities = [

        {
            "customer_id": "C001",
            "recommendation": "Product A",
            "opportunity_score": 0.90,
            "confidence": 0.90,
            "potential_revenue": 2000,
        },

        {
            "customer_id": "C001",
            "recommendation": "Product B",
            "opportunity_score": 0.85,
            "confidence": 0.85,
            "potential_revenue": 1800,
        },

        {
            "customer_id": "C001",
            "recommendation": "Product C",
            "opportunity_score": 0.80,
            "confidence": 0.80,
            "potential_revenue": 1500,
        },

        {
            "customer_id": "C001",
            "recommendation": "Product D",
            "opportunity_score": 0.70,
            "confidence": 0.70,
            "potential_revenue": 1000,
        },
    ]

    result = limit_opportunities_per_customer(
        opportunities,
        maximum=3
    )

    assert len(result) == 3


# ============================================================
# TEST 8
# ============================================================

def test_limit_preserves_strongest_opportunities():

    opportunities = [

        {
            "customer_id": "C001",
            "recommendation": "Weak",
            "opportunity_score": 0.65,
            "confidence": 0.65,
            "potential_revenue": 500,
        },

        {
            "customer_id": "C001",
            "recommendation": "Strong",
            "opportunity_score": 0.90,
            "confidence": 0.90,
            "potential_revenue": 2200,
        },

        {
            "customer_id": "C001",
            "recommendation": "Medium",
            "opportunity_score": 0.80,
            "confidence": 0.80,
            "potential_revenue": 1500,
        },

        {
            "customer_id": "C001",
            "recommendation": "Another",
            "opportunity_score": 0.75,
            "confidence": 0.75,
            "potential_revenue": 1200,
        },
    ]

    ranked = rank_opportunities(
        opportunities
    )

    result = limit_opportunities_per_customer(
        ranked,
        maximum=3
    )

    products = {
        item["recommendation"]
        for item in result
    }

    assert "Strong" in products
    assert "Medium" in products
    assert "Another" in products

    assert "Weak" not in products


# ============================================================
# TEST 9
# ============================================================

def test_low_confidence_opportunity_is_rejected():

    opportunity = {

        "customer_id": "C001",

        "recommendation":
            "Random Product",

        "confidence":
            0.40,

        "opportunity_score":
            0.45,

        "potential_revenue":
            2000,
    }

    assert is_qualified(
        opportunity
    ) is False


# ============================================================
# TEST 10
# ============================================================

def test_high_quality_opportunity_is_qualified():

    opportunity = {

        "customer_id": "C001",

        "recommendation":
            "Laptop Bag",

        "confidence":
            0.83,

        "opportunity_score":
            0.84,

        "potential_revenue":
            2200,
    }

    assert is_qualified(
        opportunity
    ) is True


# ============================================================
# TEST 11
# ============================================================

def test_zero_revenue_opportunity_is_rejected():

    opportunity = {

        "customer_id":
            "C001",

        "recommendation":
            "Laptop Bag",

        "confidence":
            0.85,

        "opportunity_score":
            0.85,

        "potential_revenue":
            0,
    }

    assert is_qualified(
        opportunity
    ) is False


# ============================================================
# TEST 12
# ============================================================

def test_ranking_puts_stronger_opportunity_first():

    opportunities = [

        {
            "customer_id": "C001",
            "recommendation": "Weak",
            "opportunity_score": 0.65,
            "confidence": 0.65,
            "potential_revenue": 500,
        },

        {
            "customer_id": "C002",
            "recommendation": "Strong",
            "opportunity_score": 0.90,
            "confidence": 0.90,
            "potential_revenue": 2200,
        },
    ]

    ranked = rank_opportunities(
        opportunities
    )

    assert (
        ranked[0]["recommendation"]
        == "Strong"
    )


# ============================================================
# TEST 13
# ============================================================

def test_opportunity_score_is_bounded():

    score = calculate_opportunity_score(
        confidence=1.0,
        revenue=100000
    )

    assert 0.0 <= score <= 1.0


# ============================================================
# TEST 14
# ============================================================

def test_real_transaction_file_generates_opportunities():

    transaction_file = (
        Path(__file__).resolve().parent.parent
        / "data"
        / "transactions.csv"
    )

    assert transaction_file.exists()

    opportunities = (
        analyze_growth_opportunities(
            str(transaction_file)
        )
    )

    assert isinstance(
        opportunities,
        list
    )

    assert len(
        opportunities
    ) > 0


# ============================================================
# TEST 15
# ============================================================

def test_real_opportunities_have_required_fields():

    transaction_file = (
        Path(__file__).resolve().parent.parent
        / "data"
        / "transactions.csv"
    )

    opportunities = (
        analyze_growth_opportunities(
            str(transaction_file)
        )
    )

    required_fields = {
        "customer_id",
        "trigger_product",
        "recommendation",
        "potential_revenue",
        "confidence",
        "opportunity_score",
        "priority",
        "expected_revenue",
    }

    for opportunity in opportunities:

        assert required_fields.issubset(
            opportunity.keys()
        )


# ============================================================
# TEST 16
# ============================================================

def test_real_opportunities_are_ranked():

    transaction_file = (
        Path(__file__).resolve().parent.parent
        / "data"
        / "transactions.csv"
    )

    opportunities = (
        analyze_growth_opportunities(
            str(transaction_file)
        )
    )

    scores = [
        float(
            opportunity[
                "opportunity_score"
            ]
        )
        for opportunity in opportunities
    ]

    assert scores == sorted(
        scores,
        reverse=True
    )


# ============================================================
# TEST 17
# ============================================================

def test_real_data_has_no_duplicate_customer_product():

    transaction_file = (
        Path(__file__).resolve().parent.parent
        / "data"
        / "transactions.csv"
    )

    opportunities = (
        analyze_growth_opportunities(
            str(transaction_file)
        )
    )

    keys = [

        (
            str(
                opportunity[
                    "customer_id"
                ]
            ),
            str(
                opportunity[
                    "recommendation"
                ]
            ),
        )

        for opportunity in opportunities
    ]

    assert len(keys) == len(
        set(keys)
    )