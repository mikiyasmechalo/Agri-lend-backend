# AgriLend Backend

Agricultural Credit Intelligence Platform — backend API server built with FastAPI.

AgriLend transforms raw farm data into reliable agricultural credit scores, bridging the gap between smallholder farmers and financial institutions.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Server                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Auth    │  │  Farmer  │  │  Loan    │  │  Bank    │       │
│  │  Router  │  │  Router  │  │  Router  │  │  Router  │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       │              │              │              │            │
│  ┌────┴──────────────┴──────────────┴──────────────┴─────────┐ │
│  │                    Service Layer                           │ │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐  │ │
│  │  │ Auth │ │Farm  │ │Credit│ │ Loan │ │Brain │ │Admin │  │ │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘  │ │
│  │  ┌──────────────────┐ ┌──────────────────┐               │ │
│  │  │  Geospatial      │ │   Scoring        │  ← Internal   │ │
│  │  │  (Eyosiyas)      │ │  (Amanuel)       │    API calls  │ │
│  │  └──────────────────┘ └──────────────────┘               │ │
│  └───────────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │          SQLAlchemy 2.0 Async ORM                          │ │
│  │          PostgreSQL (prod) / SQLite (dev)                  │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │                                        │
         ▼                                        ▼
  Eyosiyas's Pipeline              Amanuel's ML Service
  (NDVI, climate data)             (credit scores, heatmaps)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI (Python 3.11+) |
| Database | PostgreSQL + asyncpg (prod) / SQLite + aiosqlite (dev) |
| ORM | SQLAlchemy 2.0 (async) |
| Auth | OAuth2 JWT (python-jose) + bcrypt (passlib) |
| Validation | Pydantic v2 |
| Rate Limiting | slowapi (10 req/min on auth, 30 req/min default) |
| Testing | pytest + pytest-asyncio + httpx |

## Roles (RBAC)

| Role | Permissions |
|------|------------|
| Farmer | Own profile, parcels, consent, credit, loans |
| Bank Viewer | Read-only loan & credit data |
| Bank Analyst | Dashboard reports, heatmap, risk warnings |
| Bank Administrator | Bank settings, loan review |
| Loan Officer | Loan review (approve/reject/disburse) |
| Risk Analyst | Trigger score calculations |
| Platform Admin | Full access: users, banks, reports, ML ops |

## Project Structure

```
app/
├── main.py                 # FastAPI entry, CORS, slowapi limiter, lifespan
├── seed.py                 # Seeds 7 default roles on startup
├── core/
│   ├── config.py           # Environment settings (16 vars)
│   ├── security.py         # bcrypt hashing, JWT create/decode
│   ├── dependencies.py     # get_current_user, require_roles guard
│   └── logging.py          # Audit logger
├── db/
│   ├── base.py             # DeclarativeBase + TimestampMixin
│   └── session.py          # Async engine + session factory
├── models/                 # 10 SQLAlchemy ORM models
│   ├── auth.py             # Role, User
│   ├── farmer.py           # FarmerProfile, FarmParcel
│   ├── credit.py           # CreditScoreRecord (RiskTier enum)
│   ├── loan.py             # LoanApplication (LoanStatus enum)
│   ├── bank.py             # BankPartner
│   ├── satellite.py        # SatelliteObservation
│   └── audit.py            # AuditLog, ModelVersion
├── schemas/                # Pydantic v2 request/response models
│   ├── __init__.py         # PaginatedResponse[T] generic
│   ├── auth.py
│   ├── farmer.py
│   ├── credit.py
│   ├── loan.py
│   ├── bank.py
│   └── admin.py            # Reports, ML metrics, Pipeline status
├── routers/v1/             # 6 routers, 58 endpoints under /api/v1/
│   ├── auth.py             # Register, login, refresh, me, update me
│   ├── farmers.py          # Registration hub, parcels, consent, credit, farm status
│   ├── loans.py            # Create, list (filtered/paginated), reports, review
│   ├── banks.py            # CRUD + settings
│   ├── admin.py            # User mgmt, 4 reports, 6 ML endpoints, pipelines
│   └── brain.py            # Score trigger, risk tier, webhook, yield stub
├── services/               # Business logic layer
│   ├── auth.py
│   ├── farmer.py
│   ├── credit.py
│   ├── loan.py
│   ├── admin.py            # Reports, ML metrics, model rollback
│   ├── brain.py            # Score trigger, fallback NDVI scoring
│   ├── scoring.py          # HTTP client → Amanuel ML service
│   └── geospatial.py       # HTTP client → Eyosiyas pipeline
tests/
├── conftest.py             # Async fixtures: engine, session, admin_user, farmer_user
├── test_auth.py            # 6 tests: register, duplicate, invalid role, auth
├── test_credit.py          # 14 tests: risk tier classification, loan ranges
├── test_loan.py            # 4 tests: create, review, not found, high-risk warning
└── test_brain.py           # 8 tests: risk tier detail, tier determination, confidence
```

## API Endpoints

### Health

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/health` | Server health check | No |

### Authentication (`/api/v1/auth`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|-----------|
| POST | `/auth/register` | Create new user account | No | 10/min |
| POST | `/auth/login` | Login, returns JWT tokens | No | 10/min |
| POST | `/auth/refresh` | Refresh access token | No |
| GET | `/auth/me` | Get current user profile | JWT |
| PATCH | `/auth/me` | Update own profile | JWT |

### Farmers (`/api/v1/farmers`)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/farmers/register` | Registration hub — creates user + profile + parcel (single transaction) | No |
| GET | `/farmers/` | List all farmers (paginated, filterable by region) | Platform Admin |
| GET | `/farmers/me` | Get own farmer profile | JWT |
| GET | `/farmers/profile/{id}` | Get farmer profile by ID | JWT |
| POST | `/farmers/consent` | Set data sharing consent | JWT |
| POST | `/farmers/consent/revoke` | Revoke consent | JWT |
| POST | `/farmers/parcels` | Add farm parcel | Farmer/Admin |
| GET | `/farmers/{id}/parcels` | List farmer's parcels | JWT |
| GET | `/farmers/{id}/credit-score` | Current credit score | JWT |
| GET | `/farmers/{id}/credit-history` | Score history + trend (paginated) | JWT |
| GET | `/farmers/{id}/explain` | "Why this score" explanation | JWT |
| GET | `/farmers/{id}/farm-status` | NDVI crop health + chart data | JWT |

### Loans (`/api/v1/loans`)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/loans/` | Submit loan application (snapshots credit score) | Farmer/Admin |
| GET | `/loans/` | List loans (filtered by status/region/crop/amount, paginated) | JWT |
| GET | `/loans/reports/dashboard` | Aggregated loan counts by status | Bank Analyst+ |
| GET | `/loans/reports/high-risk` | Pending loans with score < 500 | Bank Analyst+ |
| GET | `/loans/reports/heatmap` | GeoJSON risk heatmap by region/crop | Bank Analyst+ |
| GET | `/loans/{id}` | Loan status check | JWT |
| GET | `/loans/{id}/detail` | Full credit report for applicant | JWT |
| PATCH | `/loans/{id}/review` | Approve/reject/disburse loan | Loan Officer/Analyst/Admin |

### Banks (`/api/v1/banks`)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/banks/` | Register bank partner | Platform Admin |
| GET | `/banks/` | List bank partners (paginated) | JWT |
| GET | `/banks/{id}` | Get bank details | Bank Admin/Platform Admin |
| PATCH | `/banks/{id}/settings` | Update bank name/tier | Bank Admin/Platform Admin |

### Admin (`/api/v1/admin`)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/admin/roles` | List all roles | JWT |
| GET | `/admin/users` | List users (paginated, filter by role/search) | Platform Admin |
| POST | `/admin/users` | Create any user | Platform Admin |
| PATCH | `/admin/users/{id}/role` | Assign role | Platform Admin |
| PATCH | `/admin/users/{id}` | Update any user | Platform Admin |
| DELETE | `/admin/users/{id}` | Delete user (permanent) | Platform Admin |
| PATCH | `/admin/users/{id}/deactivate` | Soft-deactivate user | Platform Admin |
| POST | `/admin/banks/{id}/activate` | Activate bank partner | Platform Admin |

**Reports:**

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/admin/reports/farmers` | Farmer onboarding stats | Platform Admin |
| GET | `/admin/reports/loans` | Loan activity breakdown | Platform Admin |
| GET | `/admin/reports/credit-scores` | Credit score distribution | Platform Admin |
| GET | `/admin/reports/risk` | Risk & portfolio report | Platform Admin |

**ML Monitoring:**

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/admin/ml/metrics` | Accuracy, precision, recall, F1 | Platform Admin |
| GET | `/admin/ml/error-analysis` | Misclassification by region/crop | Platform Admin |
| GET | `/admin/ml/bias` | Bias & fairness indicators | Platform Admin |
| GET | `/admin/ml/drift` | Feature & score drift detection | Platform Admin |
| GET | `/admin/ml/versions` | Model version history (paginated) | Platform Admin |
| POST | `/admin/ml/versions/{id}/rollback` | Rollback to specified version | Platform Admin |
| GET | `/admin/pipelines` | Satellite, climate, scoring pipeline health | Platform Admin |

### Brain Integration (`/api/v1/brain`)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/brain/trigger-score/{farmer_id}` | Trigger score calculation for a farmer | Platform Admin/Risk Analyst |
| POST | `/brain/trigger-all` | Trigger scores for all farmers | Platform Admin |
| GET | `/brain/risk-tier/{farmer_id}` | Risk tier + recommended loan range | JWT |
| POST | `/brain/webhook/satellite-ingestion` | Eyosiyas satellite data webhook (auto-recalculates score) | No |
| GET | `/brain/yield-prediction/{farmer_id}` | Yield prediction [STUB — FR-B-002 flagged] | JWT |

## Getting Started

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/mikiyasmechalo/Agri-lend-backend.git
cd Agri-lend-backend

# Install dependencies
pip install -r requirements.txt
```

### Running Locally (SQLite)

The app defaults to SQLite — no external database needed. Tables are created automatically on startup.

```bash
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/api/v1/docs for the Swagger UI.

### Running with PostgreSQL

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/agrilend
DATABASE_SYNC_URL=postgresql://postgres:postgres@localhost:5432/agrilend
```

Then start the server — tables are created automatically on startup.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | Runtime environment |
| `DEBUG` | `true` | Enable debug mode |
| `DATABASE_URL` | `sqlite+aiosqlite:///./agrilend_dev.db` | Async database URL (auto-detects postgresql prefix) |
| `DATABASE_SYNC_URL` | `sqlite:///./agrilend_dev.db` | Sync database URL for scripts |
| `JWT_SECRET_KEY` | `change-me-to-a-long-random-string` | JWT signing key (change in production) |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |
| `CORS_ORIGINS` | `["http://localhost:5173","http://localhost:3000"]` | Allowed CORS origins |
| `EYOSIYAS_SERVICE_URL` | `http://geospatial-service:8001` | Geospatial pipeline URL |
| `AMANUEL_SERVICE_URL` | `http://scoring-service:8002` | ML scoring service URL |
| `RATE_LIMIT_PER_MINUTE` | `30` | Default rate limit (requests/min) |
| `RATE_LIMIT_AUTH_PER_MINUTE` | `10` | Auth endpoints rate limit |
| `LOG_LEVEL` | `INFO` | Logging level |
| `AUDIT_LOG_ENABLED` | `true` | Enable PII audit logging |

## Database Models

```
User ──> Role (7 roles)
  │
  └──> FarmerProfile ──> FarmParcel ──> SatelliteObservation
         │                  │
         │                  └──> CreditScoreRecord (RiskTier: LOW/MEDIUM/HIGH)
         │
         └──> LoanApplication (Status: PENDING/APPROVED/REJECTED/DISBURSED)
                │
                └──> BankPartner
                        │
                  User (reviewed_by)
```

Additional tables: `AuditLog` (PII access tracking), `ModelVersion` (ML model versioning).

## Internal API Contracts

### Eyosiyas (Geospatial Pipeline)

Service client in `app/services/geospatial.py`:
- `GET /api/v1/ndvi/{parcel_id}?days=90` — NDVI time-series
- `GET /api/v1/climate/{parcel_id}` — Climate data

Both fall back to hardcoded mock data on connection failure.

### Amanuel (ML Scoring Service)

Service client in `app/services/scoring.py`:
- `GET /api/v1/score/{farmer_id}` — Credit score
- `GET /api/v1/explain/{farmer_id}` — Feature importance / explainability
- `GET /api/v1/heatmap` — Risk heatmap data
- `GET /api/v1/metrics` — Model performance metrics

BrainService falls back to NDVI-based scoring (satellite-only) if Amanuel is unreachable.

## Development

### Onboarding Checklist

- [x] Phase 0 — Foundations & Setup
- [x] Phase 1 — Authentication & User Management
- [x] Phase 2 — Farmer Mobile Backend
- [x] Phase 3 — Bank Web Dashboard Backend
- [x] Phase 4 — Admin Portal Backend
- [x] Phase 5 — "The Brain" Integration Layer
- [x] Phase 6 — Cross-Cutting / Non-Functional

### Testing

32 tests across 4 test files:

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_auth.py -v
```

### OpenAPI Documentation

- Swagger UI: http://127.0.0.1:8000/api/v1/docs
- ReDoc: http://127.0.0.1:8000/api/v1/redoc
- OpenAPI JSON: http://127.0.0.1:8000/api/v1/openapi.json

### Migrations

Alembic is configured but currently inactive — the app uses `Base.metadata.create_all` on startup. Switch to migrations for production schema control:

```bash
# Generate a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Known Limitations

| Item | Status | Notes |
|------|--------|-------|
| FR-B-002: Yield Prediction | Stub | `GET /brain/yield-prediction/{farmer_id}` — needs Eyosiyas model integration |
| Alembic migrations | Configured | App uses `create_all()` — switch for production |
| Credit-score endpoint <3s | Not instrumented | Needs APM tool decision |
| National Digital ID | Mock only | Deferred per Team Roles doc |
| TLS / AES-256 / DB backups | Deferred | Coordinated with infra team |

## License

Internal project — AgriLend
