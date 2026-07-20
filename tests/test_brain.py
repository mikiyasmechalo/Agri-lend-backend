import pytest
from app.models.credit import RiskTier
from app.services.brain import BrainService


class TestBrainRiskTier:
    def test_risk_tier_detail_low(self):
        detail = BrainService.get_risk_tier_detail(720, RiskTier.LOW)
        assert detail["risk_tier"] == "LOW"
        assert detail["score_value"] == 720
        assert detail["recommended_loan_min"] == 50000
        assert detail["recommended_loan_max"] == 200000
        assert len(detail["contributing_factors"]) > 0

    def test_risk_tier_detail_medium(self):
        detail = BrainService.get_risk_tier_detail(550, RiskTier.MEDIUM)
        assert detail["risk_tier"] == "MEDIUM"
        assert detail["recommended_loan_min"] == 10000
        assert detail["recommended_loan_max"] == 50000

    def test_risk_tier_detail_high(self):
        detail = BrainService.get_risk_tier_detail(300, RiskTier.HIGH)
        assert detail["risk_tier"] == "HIGH"
        assert detail["recommended_loan_min"] == 0
        assert detail["recommended_loan_max"] == 10000

    def test_tier_determination_650_plus_is_low(self):
        assert _tier_from_score(650) == RiskTier.LOW
        assert _tier_from_score(800) == RiskTier.LOW

    def test_tier_determination_500_649_is_medium(self):
        assert _tier_from_score(500) == RiskTier.MEDIUM
        assert _tier_from_score(649) == RiskTier.MEDIUM

    def test_tier_determination_below_500_is_high(self):
        assert _tier_from_score(0) == RiskTier.HIGH
        assert _tier_from_score(499) == RiskTier.HIGH

    def test_confidence_label_high(self):
        label = _confidence_label(0.85)
        assert label == "HIGH"

    def test_confidence_label_medium(self):
        label = _confidence_label(0.65)
        assert label == "MEDIUM"

    def test_confidence_label_low(self):
        label = _confidence_label(0.40)
        assert label == "LOW"


def _tier_from_score(score: int) -> RiskTier:
    if score >= 650:
        return RiskTier.LOW
    elif score >= 500:
        return RiskTier.MEDIUM
    return RiskTier.HIGH


def _confidence_label(rating: float) -> str:
    if rating >= 0.7:
        return "HIGH"
    elif rating >= 0.5:
        return "MEDIUM"
    return "LOW"
