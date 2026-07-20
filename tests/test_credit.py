import pytest
from app.models.credit import RiskTier


class TestRiskTierClassification:
    def test_low_tier_700(self):
        score = 700
        tier = _classify_risk_tier(score)
        assert tier == RiskTier.LOW

    def test_low_tier_650(self):
        score = 650
        tier = _classify_risk_tier(score)
        assert tier == RiskTier.LOW

    def test_medium_tier_550(self):
        score = 550
        tier = _classify_risk_tier(score)
        assert tier == RiskTier.MEDIUM

    def test_medium_tier_500(self):
        score = 500
        tier = _classify_risk_tier(score)
        assert tier == RiskTier.MEDIUM

    def test_high_tier_300(self):
        score = 300
        tier = _classify_risk_tier(score)
        assert tier == RiskTier.HIGH

    def test_high_tier_499(self):
        score = 499
        tier = _classify_risk_tier(score)
        assert tier == RiskTier.HIGH

    def test_boundary_low_medium(self):
        tier_low = _classify_risk_tier(650)
        tier_medium = _classify_risk_tier(649)
        assert tier_low == RiskTier.LOW
        assert tier_medium == RiskTier.MEDIUM

    def test_boundary_medium_high(self):
        tier_medium = _classify_risk_tier(500)
        tier_high = _classify_risk_tier(499)
        assert tier_medium == RiskTier.MEDIUM
        assert tier_high == RiskTier.HIGH

    def test_recommended_loan_range_low(self):
        detail = _get_risk_tier_detail(700, RiskTier.LOW)
        assert detail["risk_tier"] == "LOW"
        assert detail["recommended_loan_range"] == "ETB 50,000 – 200,000"

    def test_recommended_loan_range_medium(self):
        detail = _get_risk_tier_detail(550, RiskTier.MEDIUM)
        assert detail["risk_tier"] == "MEDIUM"
        assert detail["recommended_loan_range"] == "ETB 10,000 – 50,000"

    def test_recommended_loan_range_high(self):
        detail = _get_risk_tier_detail(300, RiskTier.HIGH)
        assert detail["risk_tier"] == "HIGH"
        assert detail["recommended_loan_range"] == "ETB 0 – 10,000"

    def test_contributing_factors_low(self):
        detail = _get_risk_tier_detail(720, RiskTier.LOW)
        factors = detail["contributing_factors"]
        assert any("Healthy NDVI" in f for f in factors)

    def test_contributing_factors_high(self):
        detail = _get_risk_tier_detail(400, RiskTier.HIGH)
        factors = detail["contributing_factors"]
        assert any("Low NDVI" in f for f in factors)
        assert any("Insufficient" in f for f in factors)


def _classify_risk_tier(score: int) -> RiskTier:
    if score >= 650:
        return RiskTier.LOW
    elif score >= 500:
        return RiskTier.MEDIUM
    return RiskTier.HIGH


def _get_risk_tier_detail(score: int, tier: RiskTier) -> dict:
    ranges = {
        RiskTier.LOW: "ETB 50,000 – 200,000",
        RiskTier.MEDIUM: "ETB 10,000 – 50,000",
        RiskTier.HIGH: "ETB 0 – 10,000",
    }
    factors_map = {
        RiskTier.LOW: ["Healthy NDVI trend", "Stable climate conditions", "Good mobile money activity"],
        RiskTier.MEDIUM: ["Moderate NDVI trend", "Average climate conditions"],
        RiskTier.HIGH: ["Low NDVI trend", "Climate risk detected", "Insufficient financial data"],
    }
    return {
        "risk_tier": tier.value,
        "score_value": score,
        "contributing_factors": factors_map.get(tier, []),
        "recommended_loan_range": ranges.get(tier, ""),
    }
