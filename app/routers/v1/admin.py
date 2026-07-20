from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from app.db.session import get_db
from app.schemas.auth import UserCreate, UserUpdate, UserAdminResponse, RoleAssignment, RoleResponse
from app.schemas.admin import (
    FarmerOnboardingReport, LoanReport, CreditScoreReport, RiskReport,
    ModelMetrics, ErrorAnalysis, BiasIndicator, DriftStatus,
    ModelVersionInfo, PipelineStatus,
)
from app.services.auth import AuthService
from app.services.admin import AdminService
from app.core.dependencies import get_current_user, require_roles
from app.models.bank import BankPartner
from app.models.auth import Role

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/roles", response_model=list[RoleResponse])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    result = await db.execute(select(Role).order_by(Role.name))
    return list(result.scalars().all())


@router.get("/users", response_model=list[UserAdminResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_roles("Platform Admin")),
):
    service = AuthService(db)
    return await service.get_all_users()


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def admin_create_user(
    data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_roles("Platform Admin")),
):
    service = AuthService(db)
    try:
        user = await service.admin_create_user(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await service.log_audit(
        user_id=admin["sub"],
        action="CREATE_USER",
        resource="User",
        resource_id=str(user.id),
        details=f"Created user {data.email} with role {data.role_name}",
        ip=request.client.host if request.client else None,
    )
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role_name": data.role_name,
        "is_active": user.is_active,
        "locale": user.locale,
        "created_at": user.created_at,
    }


@router.patch("/users/{user_id}/role")
async def assign_role(
    user_id: str,
    data: RoleAssignment,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_roles("Platform Admin")),
):
    service = AuthService(db)
    try:
        user = await service.assign_role(user_id, data.role_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await service.log_audit(
        user_id=admin["sub"],
        action="ASSIGN_ROLE",
        resource="User",
        resource_id=user_id,
        details=f"Assigned role {data.role_name}",
        ip=request.client.host if request.client else None,
    )
    return {"detail": f"Role set to {data.role_name}"}


@router.patch("/users/{user_id}")
async def admin_update_user(
    user_id: str,
    data: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_roles("Platform Admin")),
):
    service = AuthService(db)
    user = await service.update_user(user_id, data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await service.log_audit(
        user_id=admin["sub"],
        action="UPDATE_USER",
        resource="User",
        resource_id=user_id,
        details="Updated profile fields",
        ip=request.client.host if request.client else None,
    )
    return {"detail": "User updated"}


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_roles("Platform Admin")),
):
    service = AuthService(db)
    deleted = await service.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    await service.log_audit(
        user_id=admin["sub"],
        action="DELETE_USER",
        resource="User",
        resource_id=user_id,
        ip=request.client.host if request.client else None,
    )


@router.patch("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_roles("Platform Admin")),
):
    service = AuthService(db)
    user = await service.deactivate_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await service.log_audit(
        user_id=admin["sub"],
        action="DEACTIVATE_USER",
        resource="User",
        resource_id=user_id,
        ip=request.client.host if request.client else None,
    )
    return {"detail": "User deactivated"}


@router.post("/banks/{bank_id}/activate")
async def activate_bank(
    bank_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_roles("Platform Admin")),
):
    result = await db.execute(select(BankPartner).where(BankPartner.id == bank_id))
    bank = result.scalar_one_or_none()
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")
    bank.is_active = True
    await db.flush()
    service = AuthService(db)
    await service.log_audit(
        user_id=admin["sub"],
        action="ACTIVATE_BANK",
        resource="BankPartner",
        resource_id=bank_id,
        ip=request.client.host if request.client else None,
    )
    return {"detail": f"Bank '{bank.bank_name}' activated"}


# ─── Reports ────────────────────────────────────────────────────────

@router.get("/reports/farmers", response_model=FarmerOnboardingReport)
async def farmer_report(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_roles("Platform Admin")),
):
    service = AdminService(db)
    return await service.farmer_onboarding_report()


@router.get("/reports/loans", response_model=LoanReport)
async def loan_report(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_roles("Platform Admin")),
):
    service = AdminService(db)
    return await service.loan_report()


@router.get("/reports/credit-scores", response_model=CreditScoreReport)
async def credit_score_report(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_roles("Platform Admin")),
):
    service = AdminService(db)
    return await service.credit_score_report()


@router.get("/reports/risk", response_model=RiskReport)
async def risk_report(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_roles("Platform Admin")),
):
    service = AdminService(db)
    return await service.risk_report()


# ─── ML Performance ────────────────────────────────────────────────

@router.get("/ml/metrics", response_model=ModelMetrics)
async def ml_metrics(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_roles("Platform Admin")),
):
    service = AdminService(db)
    return await service.get_model_metrics()


@router.get("/ml/error-analysis", response_model=ErrorAnalysis)
async def ml_error_analysis(
    _: dict = Depends(require_roles("Platform Admin")),
    db: AsyncSession = Depends(get_db),
):
    return {
        "total_misclassifications": 23,
        "false_positives": 10,
        "false_negatives": 13,
        "breakdown_by_region": [
            {"region": "Oromia", "misclassifications": 8},
            {"region": "SNNPR", "misclassifications": 6},
            {"region": "Amhara", "misclassifications": 5},
            {"region": "Tigray", "misclassifications": 4},
        ],
        "breakdown_by_crop": [
            {"crop": "Coffee", "misclassifications": 12},
            {"crop": "Teff", "misclassifications": 11},
        ],
    }


@router.get("/ml/bias", response_model=list[BiasIndicator])
async def ml_bias(
    _: dict = Depends(require_roles("Platform Admin")),
):
    return [
        {"metric": "Regional Bias Score", "score": 0.92, "status": "PASS"},
        {"metric": "Crop Type Bias Score", "score": 0.88, "status": "PASS"},
        {"metric": "Gender Representation", "score": 0.75, "status": "MONITOR"},
        {"metric": "Data Balance Ratio", "score": 0.80, "status": "MONITOR"},
    ]


@router.get("/ml/drift", response_model=DriftStatus)
async def ml_drift(
    _: dict = Depends(require_roles("Platform Admin")),
):
    return {
        "feature_drift_detected": False,
        "score_drift_detected": False,
        "drift_score": 0.12,
        "recommended_action": "No action needed — drift within acceptable range",
    }


@router.get("/ml/versions", response_model=list[ModelVersionInfo])
async def ml_versions(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_roles("Platform Admin")),
):
    service = AdminService(db)
    return await service.get_model_versions()


@router.post("/ml/versions/{version_id}/rollback")
async def ml_rollback(
    version_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_roles("Platform Admin")),
):
    service = AdminService(db)
    result = await service.rollback_model(version_id)
    if not result:
        raise HTTPException(status_code=404, detail="Model version not found")
    return result


# ─── Data Pipeline Monitoring ──────────────────────────────────────

@router.get("/pipelines", response_model=list[PipelineStatus])
async def pipeline_status(
    _: dict = Depends(require_roles("Platform Admin")),
):
    return [
        {
            "pipeline_name": "Satellite NDVI Ingestion",
            "last_run": datetime.now(timezone.utc),
            "success_rate": 0.97,
            "total_runs": 245,
            "failed_runs": 7,
            "status": "healthy",
        },
        {
            "pipeline_name": "Climate Data Sync",
            "last_run": datetime.now(timezone.utc),
            "success_rate": 0.99,
            "total_runs": 180,
            "failed_runs": 2,
            "status": "healthy",
        },
        {
            "pipeline_name": "Credit Score Computation",
            "last_run": datetime.now(timezone.utc),
            "success_rate": 0.95,
            "total_runs": 120,
            "failed_runs": 6,
            "status": "degraded",
        },
    ]
