from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FarmerOnboardingReport(BaseModel):
    total_registered: int
    consented: int
    with_land_proof: int
    with_mobile_money: int


class LoanReport(BaseModel):
    total: int
    approved: int
    rejected: int
    pending: int
    disbursed: int


class CreditScoreReport(BaseModel):
    average_score: float
    min_score: int
    max_score: int
    total_farmers_scored: int
    regional_distribution: list[dict]
    trend: list[dict]


class RiskReport(BaseModel):
    default_rate: float
    total_active_loans: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    geo_risk_clusters: list[dict]


class ModelMetrics(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    model_version: str
    last_trained: Optional[str]


class ErrorAnalysis(BaseModel):
    total_misclassifications: int
    false_positives: int
    false_negatives: int
    breakdown_by_region: list[dict]
    breakdown_by_crop: list[dict]


class BiasIndicator(BaseModel):
    metric: str
    score: float
    status: str


class DriftStatus(BaseModel):
    feature_drift_detected: bool
    score_drift_detected: bool
    drift_score: float
    recommended_action: str


class ModelVersionInfo(BaseModel):
    id: str
    version: str
    is_active: bool
    accuracy: Optional[float]
    precision: Optional[float]
    recall: Optional[float]
    deployed_at: Optional[datetime]
    rolled_back_at: Optional[datetime]
    created_at: datetime


class PipelineStatus(BaseModel):
    pipeline_name: str
    last_run: Optional[datetime]
    success_rate: float
    total_runs: int
    failed_runs: int
    status: str
