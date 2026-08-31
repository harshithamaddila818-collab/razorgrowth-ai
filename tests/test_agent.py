from agent.growth_agent import analyze_growth_opportunities


def test_growth_opportunities_are_detected():
    opportunities = analyze_growth_opportunities(
        "data/transactions.csv"
    )

    assert isinstance(opportunities, list)
    assert len(opportunities) > 0


def test_growth_opportunities_have_required_fields():
    opportunities = analyze_growth_opportunities(
        "data/transactions.csv"
    )

    required_fields = {
        "customer_id",
        "recommendation",
        "potential_revenue",
        "confidence",
        "reason",
    }

    for opportunity in opportunities:
        assert required_fields.issubset(
            opportunity.keys()
        )


def test_revenue_values_are_positive():
    opportunities = analyze_growth_opportunities(
        "data/transactions.csv"
    )

    for opportunity in opportunities:
        assert opportunity["potential_revenue"] > 0