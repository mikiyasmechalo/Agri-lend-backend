# AgriLend Backend — Implementation Report

**Project:** Agricultural Credit Intelligence Platform  
**Owner:** Mikiyas Mechalo — Backend Logic Development  
**Repository:** `Agri-lend-backend`  
**Status:** Phases 0–6 Complete | 32/32 tests passing | 58 API routes  

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Technology Stack](#2-technology-stack)
3. [Database Schema](#3-database-schema)
4. [API Endpoints](#4-api-endpoints)
5. [Authentication & Authorization](#5-authentication--authorization)
6. [Phase-by-Phase Implementation](#6-phase-by-phase-implementation)
7. [Business Logic Details](#7-business-logic-details)
8. [Testing](#8-testing)
9. [Security Measures](#9-security-measures)
10. [Known Gaps & Next Steps](#10-known-gaps--next-steps)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                          │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐  │
│  │  Auth  │ │Farmers │ │ Loans  │ │ Banks  │ │ Admin  │ │ Brain  │  │
│  │ Router │ │ Router │ │ Router │ │ Router │ │ Router │ │ Router │  │
│  └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘  │
│      │          │          │          │          │          │       │
│  ┌───┴──────────┴──────────┴──────────┴──────────┴──────────┴────┐  │
│  │                     Service Layer                             │  │
│  │  Auth  │  Farmer  │  Loan  │  Credit  │  Admin  │  Brain      │  │
│  │  ──────┴──────────┴────────┴──────────┴─────────┴────────     │  │
│  │  ┌──────────────────────┐  ┌────────────────────────────┐     │  │
│  │  │ ScoringService (HTTP)│  │  GeospatialService (HTTP)  │     │  │
│  │  │ → Amanuel's ML API   │  │   → Eyosiyas's NDVI API    │     │  │
│  │  └──────────────────────┘  └────────────────────────────┘     │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                         │                                           │
│  ┌──────────────────────┴──────────────────────────────────────────┐│
│  │                   SQLAlchemy Async ORM                          ││
│  │                SQLite (dev) / PostgreSQL (prod)                 ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| SQLite for dev, PostgreSQL for prod | No local PostGIS required; auto-detected via `DATABASE_URL` prefix |
| PostGIS Geometry → Text (GeoJSON) | Cross-DB compatibility; avoids PostGIS dependency in dev |
| bcrypt < 5.0.0 | bcrypt 5.x incompatible with passlib 1.7.4 (causes login errors) |
| `/reports/*` before `/{app_id}` | Prevents path-parameter capture conflicts in loans router |
| All routes under `/api/v1/` | SRS 6.2 versioning requirement |
| Rate limit on auth endpoints only | Public-facing endpoints need protection; internal routes have JWT guard |
| PaginatedResponse[T] generic schema | Consistent pagination shape across all list endpoints |

---

## 2. Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | FastAPI | ≥0.115.0 |
| ASGI Server | Uvicorn | ≥0.34.0 |
| ORM | SQLAlchemy (async) | ≥2.0.0 |
| Migrations | Alembic | ≥1.14.0 |
| Validation | Pydantic v2 | ≥2.10.0 |
| Auth | python-jose (JWT) + passlib (bcrypt) | — |
| HTTP Client | httpx | ≥0.28.0 |
| Rate Limiting | slowapi | ≥0.1.9 |
| Testing | pytest + pytest-asyncio | ≥8.0.0 |
| Dev DB | SQLite + aiosqlite | ≥0.20.0 |
| Prod DB | PostgreSQL + asyncpg | ≥0.30.0 |

### Requirements

```
fastapi>=0.115.0
uvicorn[standard]>=0.34.0
sqlalchemy[asyncio]>=2.0.0
alembic>=1.14.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.18
pydantic>=2.10.0
pydantic-settings>=2.7.0
python-dotenv>=1.0.0
httpx>=0.28.0
aiosqlite>=0.20.0
asyncpg>=0.30.0
geoalchemy2>=0.15.0
slowapi>=0.1.9
pytest>=8.0.0
pytest-asyncio>=0.25.0
```

---

## 3. Database Schema

### 3.1 Entity-Relationship Diagram (Text)

```
roles ──1:N── users ──1:1── farmer_profiles ──1:N── farm_parcels ──1:N── satellite_observations
                │                                 │
                │                                 ├──1:N── credit_score_records
                │                                 │
                │                                 └──1:N── loan_applications ──N:1── bank_partners
                │
                └──N:1── model_versions (audit)

audit_logs (standalone, references user_id as plain UUID)
```

### 3.2 Table: `roles`

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default uuid4 |
| name | VARCHAR(50) | UNIQUE, NOT NULL |
| description | VARCHAR(255) | NULLABLE |
| created_at | TIMESTAMPTZ | NOT NULL, default now() |

**Seeded values:** Farmer, Bank Viewer, Bank Analyst, Bank Administrator, Platform Admin, Risk Analyst, Loan Officer

### 3.3 Table: `users`

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default uuid4 |
| email | VARCHAR(255) | UNIQUE, NOT NULL, indexed |
| phone_number | VARCHAR(20) | UNIQUE, NULLABLE |
| hashed_password | VARCHAR(255) | NOT NULL |
| full_name | VARCHAR(255) | NOT NULL |
| role_id | UUID | FK → roles.id, NOT NULL |
| is_active | BOOLEAN | default true |
| locale | VARCHAR(10) | default 'en' |
| last_login | TIMESTAMPTZ | NULLABLE |
| created_at | TIMESTAMPTZ | NOT NULL (TimestampMixin) |
| updated_at | TIMESTAMPTZ | NOT NULL (TimestampMixin) |

### 3.4 Table: `farmer_profiles`

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default uuid4 |
| user_id | UUID | FK → users.id, UNIQUE, NOT NULL |
| full_name | VARCHAR(255) | NOT NULL |
| national_id | VARCHAR(100) | UNIQUE, NOT NULL |
| phone_number | VARCHAR(20) | UNIQUE, NOT NULL |
| mobile_money_id | VARCHAR(100) | NULLABLE |
| gps_coordinates | VARCHAR(100) | NULLABLE |
| land_proof_document | VARCHAR(500) | NULLABLE |
| consent_status | BOOLEAN | default false |
| consent_date | TIMESTAMPTZ | NULLABLE |
| locale | VARCHAR(10) | default 'en' |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

### 3.5 Table: `farm_parcels`

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default uuid4 |
| farmer_id | UUID | FK → farmer_profiles.id, NOT NULL |
| parcel_name | VARCHAR(255) | NOT NULL |
| location_polygon | TEXT | NULLABLE (GeoJSON string) |
| size_hectares | NUMERIC(10,4) | NOT NULL |
| primary_crop | VARCHAR(100) | NOT NULL |
| region | VARCHAR(100) | NOT NULL |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

### 3.6 Table: `credit_score_records`

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default uuid4 |
| farmer_id | UUID | FK → farmer_profiles.id, NOT NULL, indexed |
| score_value | INTEGER | NOT NULL |
| risk_tier | ENUM(LOW, MEDIUM, HIGH) | NOT NULL |
| geospatial_score | NUMERIC(5,2) | default 0 |
| transactional_score | NUMERIC(5,2) | default 0 |
| alternative_score | NUMERIC(5,2) | default 0 |
| model_version | VARCHAR(20) | NOT NULL |
| confidence_rating | NUMERIC(3,2) | default 0 |
| calculated_at | TIMESTAMPTZ | NOT NULL, default now() |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

**Risk Tier Thresholds:**
- LOW: score ≥ 650 (recommended loan: ETB 50,000 – 200,000)
- MEDIUM: 500 ≤ score < 650 (recommended loan: ETB 10,000 – 50,000)
- HIGH: score < 500 (recommended loan: ETB 0 – 10,000)

### 3.7 Table: `loan_applications`

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default uuid4 |
| farmer_id | UUID | FK → farmer_profiles.id, NOT NULL, indexed |
| bank_id | UUID | FK → bank_partners.id, NOT NULL |
| requested_amount | NUMERIC(12,2) | NOT NULL |
| loan_purpose | VARCHAR(500) | NOT NULL |
| credit_score_at_application | INTEGER | NOT NULL |
| status | ENUM(PENDING, APPROVED, REJECTED, DISBURSED) | default PENDING |
| submitted_at | TIMESTAMPTZ | NOT NULL, default now() |
| reviewed_at | TIMESTAMPTZ | NULLABLE |
| reviewed_by | UUID | FK → users.id, NULLABLE |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

### 3.8 Table: `satellite_observations`

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default uuid4 |
| parcel_id | UUID | FK → farm_parcels.id, NOT NULL, indexed |
| observation_date | DATE | NOT NULL |
| ndvi_value | NUMERIC(5,4) | NOT NULL |
| cloud_cover_pct | NUMERIC(5,2) | default 0 |
| data_source | VARCHAR(50) | default 'Sentinel-2' |
| processed_at | TIMESTAMPTZ | NOT NULL, default now() |

### 3.9 Table: `bank_partners`

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default uuid4 |
| bank_name | VARCHAR(255) | NOT NULL |
| api_key_hash | VARCHAR(255) | NOT NULL |
| subscription_tier | VARCHAR(50) | default 'standard' |
| is_active | BOOLEAN | default true |
| onboarding_date | TIMESTAMPTZ | NOT NULL, default now() |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

### 3.10 Table: `audit_logs`

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default uuid4 |
| user_id | UUID | NOT NULL, indexed |
| action | VARCHAR(100) | NOT NULL |
| resource | VARCHAR(100) | NOT NULL |
| resource_id | VARCHAR(100) | NOT NULL |
| details | TEXT | NULLABLE |
| ip_address | VARCHAR(45) | NULLABLE |
| timestamp | TIMESTAMPTZ | NOT NULL, default now() |

**Audited actions:** CREATE_USER, ASSIGN_ROLE, UPDATE_USER, DELETE_USER, DEACTIVATE_USER, ACTIVATE_BANK, UPDATE_BANK_SETTINGS

### 3.11 Table: `model_versions`

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default uuid4 |
| version | VARCHAR(20) | UNIQUE, NOT NULL |
| is_active | BOOLEAN | default false |
| accuracy | FLOAT | NULLABLE |
| precision | FLOAT | NULLABLE |
| recall | FLOAT | NULLABLE |
| deployed_at | TIMESTAMPTZ | NULLABLE |
| rolled_back_at | TIMESTAMPTZ | NULLABLE |
| created_at | TIMESTAMPTZ | NOT NULL, default now() |

---

## 4. API Endpoints

### 4.1 Authentication (`/api/v1/auth`)

| Method | Path | Role | Rate Limited | Description |
|--------|------|------|-------------|-------------|
| POST | /register | Public | Yes (10/min) | Create user account |
| POST | /login | Public | Yes (10/min) | Authenticate, get JWT pair |
| POST | /refresh | Any authenticated | No | Exchange refresh token |
| GET | /me | Any authenticated | No | Get current user profile |
| PATCH | /me | Any authenticated | No | Update own profile |

### 4.2 Farmers (`/api/v1/farmers`)

| Method | Path | Role | Description |
|--------|------|------|-------------|
| POST | /register | Public | Register farmer + profile + optional parcel |
| GET | / | Platform Admin | List all farmers (paginated, filterable by region) |
| GET | /profile/{farmer_id} | Any authenticated | Get farmer profile by ID |
| GET | /me | Any authenticated | Get own farmer profile |
| POST | /consent | Any authenticated | Grant/update consent |
| POST | /consent/revoke | Any authenticated | Revoke consent |
| POST | /parcels | Farmer, Platform Admin | Add farm parcel |
| GET | /{farmer_id}/parcels | Any authenticated | List farmer's parcels |
| GET | /{farmer_id}/credit-score | Any authenticated | Get latest credit score |
| GET | /{farmer_id}/credit-history | Any authenticated | Get paginated score history |
| GET | /{farmer_id}/explain | Any authenticated | Get score explanation |
| GET | /{farmer_id}/farm-status | Any authenticated | Get NDVI farm status |

### 4.3 Loans (`/api/v1/loans`)

| Method | Path | Role | Description |
|--------|------|------|-------------|
| POST | / | Farmer, Platform Admin | Create loan application |
| GET | / | Any authenticated | List loans (paginated, filterable) |
| GET | /reports/dashboard | Bank Analyst+ | Dashboard counts |
| GET | /reports/high-risk | Bank Analyst+ | High-risk warnings (<500 score) |
| GET | /reports/heatmap | Bank Analyst+ | Risk heatmap GeoJSON |
| GET | /{app_id} | Any authenticated | Get single loan |
| GET | /{app_id}/detail | Any authenticated | Full applicant credit report |
| PATCH | /{app_id}/review | Loan Officer+ | Approve/reject loan |

### 4.4 Banks (`/api/v1/banks`)

| Method | Path | Role | Description |
|--------|------|------|-------------|
| POST | / | Platform Admin | Register bank |
| GET | / | Any authenticated | List banks (paginated) |
| GET | /{bank_id} | Bank Administrator+ | Get bank details |
| PATCH | /{bank_id}/settings | Bank Administrator+ | Update bank settings |

### 4.5 Admin (`/api/v1/admin`)

| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | /roles | Any authenticated | List all roles |
| GET | /users | Platform Admin | List users (paginated, filterable) |
| POST | /users | Platform Admin | Create any user |
| PATCH | /users/{user_id}/role | Platform Admin | Assign role |
| PATCH | /users/{user_id} | Platform Admin | Update user |
| DELETE | /users/{user_id} | Platform Admin | Delete user |
| PATCH | /users/{user_id}/deactivate | Platform Admin | Deactivate user |
| POST | /banks/{bank_id}/activate | Platform Admin | Activate bank |
| GET | /reports/farmers | Platform Admin | Farmer onboarding report |
| GET | /reports/loans | Platform Admin | Loan activity report |
| GET | /reports/credit-scores | Platform Admin | Credit score stats |
| GET | /reports/risk | Platform Admin | Risk & portfolio report |
| GET | /ml/metrics | Platform Admin | Model accuracy/precision/recall |
| GET | /ml/error-analysis | Platform Admin | Misclassification breakdown |
| GET | /ml/bias | Platform Admin | Bias & fairness indicators |
| GET | /ml/drift | Platform Admin | Drift detection status |
| GET | /ml/versions | Platform Admin | List model versions (paginated) |
| POST | /ml/versions/{version_id}/rollback | Platform Admin | Rollback model |
| GET | /pipelines | Platform Admin | Data pipeline monitoring |

### 4.6 Brain Integration (`/api/v1/brain`)

| Method | Path | Role | Description |
|--------|------|------|-------------|
| POST | /trigger-score/{farmer_id} | Platform Admin, Risk Analyst | Trigger score calculation |
| POST | /trigger-all | Platform Admin | Recalculate all scores |
| GET | /risk-tier/{farmer_id} | Any authenticated | Risk tier + loan range |
| POST | /webhook/satellite-ingestion | Public (no auth) | Eyosiyas satellite webhook |
| GET | /yield-prediction/{farmer_id} | Any authenticated | **STUB** — FR-B-002 flagged |

### 4.7 System

| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | /api/v1/health | Public | Health check |
| GET | /api/v1/docs | Public | Swagger UI |
| GET | /api/v1/redoc | Public | ReDoc UI |
| GET | /api/v1/openapi.json | Public | OpenAPI spec |

---

## 5. Authentication & Authorization

### 5.1 JWT Token Flow

```
Registration → Login → { access_token (30min), refresh_token (7d) }
                              │
                              ├──→ Bearer Authorization header
                              │       │
                              │       └──→ decode_token → payload { sub, role, exp, type }
                              │
                              └──→ /auth/refresh → new access_token
```

### 5.2 RBAC Role Hierarchy

```
Platform Admin (highest)
├── Bank Administrator
│   ├── Bank Analyst
│   │   └── Bank Viewer
│   └── Loan Officer
├── Risk Analyst
└── Farmer (lowest, self-scoped)
```

### 5.3 Guard Functions

- `get_current_user` — extracts JWT payload, validates signature + expiry
- `require_roles("RoleA", "RoleB")` — checks `current_user["role"]` is in allowed set; raises 403 otherwise

---

## 6. Phase-by-Phase Implementation

### Phase 0 — Foundations & Setup

- FastAPI scaffold with `app/` package structure (routers, services, schemas, models, core, db)
- 10 SQLAlchemy async models covering all entities
- Alembic migration configuration
- Auto-seed of 7 roles on startup via lifespan
- Environment config via pydantic-settings (.env file)
- PostGIS → Text fallback for SQLite compatibility
- CORS configured from settings
- Logging setup with Python logging

### Phase 1 — Authentication & User Management

- 5 auth endpoints (register, login, refresh, /me, PATCH /me)
- 8 admin endpoints (CRUD on users, role assignment, bank activation, deactivation)
- JWT access + refresh token implementation
- bcrypt password hashing
- Audit log capture on all admin actions

### Phase 2 — Farmer Mobile Backend

- Registration Hub: creates User + FarmerProfile + optional FarmParcel in single transaction
- Consent set/revoke endpoints
- Credit score dashboard (GET /credit-score)
- Score history (GET /credit-history) with pagination
- Explainability endpoint with AI fallback
- Farm status endpoint (NDVI trend via GeospatialService)
- Loan application submission + status check

### Phase 3 — Bank Web Dashboard

- Filtered + paginated loan list (region, crop, amount, status)
- Applicant detail with full credit report
- Dashboard report (counts by status)
- Risk heatmap (Amanuel integration + mock fallback)
- High-risk warning flags (<500 score)
- Bank RBAC enforcement (Viewer/Analyst/Admin)
- Bank settings update

### Phase 4 — Admin Portal

- 4 report endpoints (farmers, loans, credit scores, risk)
- 6 ML monitoring endpoints (metrics, error analysis, bias, drift, versions, rollback)
- Data pipeline monitoring (satellite, climate, scoring)

### Phase 5 — Brain Integration Layer

- BrainService orchestrator for score calculation
- Trigger single farmer score (POST /trigger-score/{farmer_id})
- Trigger all farmers (POST /trigger-all)
- Risk tier detail with loan range (GET /risk-tier/{farmer_id})
- Satellite ingestion webhook (POST /webhook/satellite-ingestion)
- Fallback to NDVI-based scoring when Amanuel unreachable

### Phase 6 — Cross-Cutting / Non-Functional

| Item | Status |
|------|--------|
| Rate limiting on public auth endpoints | Implemented (10 req/min) |
| Pagination on all list endpoints | Implemented (admin users, credit history, banks, ML versions, farmers list) |
| Missing GET /farmers/ list endpoint | Added (Platform Admin only) |
| OpenAPI docs on all endpoints | All 38 endpoints have summary, description, responses |
| Unit test suite | 32 tests passing (auth, credit, loan, brain) |
| Yield prediction stub | Added with FR-B-002 flag |
| Input validation (email, phone, password) | Pydantic field validators on all schemas |
| UUID→string conversion safety | Fixed in loan service |
| Authentication endpoint rate limit | Implemented with slowapi |

---

## 7. Business Logic Details

### 7.1 Credit Score Calculation Flow

```
trigger_score(farmer_id)
  │
  ├──→ Try Amanuel ScoringService.get_score(farmer_id)
  │       │
  │       ├──→ Success: persist score, update model info
  │       │
  │       └──→ Failure: fall back to NDVI-based scoring
  │               │
  │               └──→ GeospatialService.get_ndvi_timeseries(parcel_id)
  │                       │
  │                       └──→ avg_ndvi → score (0–1000 scale)
  │
  └──→ Create + persist CreditScoreRecord
```

### 7.2 Risk Tier Classification

```python
def classify_risk_tier(score: int) -> RiskTier:
    if score >= 650:
        return RiskTier.LOW      # ETB 50,000 – 200,000
    elif score >= 500:
        return RiskTier.MEDIUM   # ETB 10,000 – 50,000
    else:
        return RiskTier.HIGH     # ETB 0 – 10,000
```

### 7.3 Loan Review Workflow

```
PENDING ──→ APPROVED ──→ DISBURSED
  │                        
  └──→ REJECTED
```

- High-risk warning: any PENDING loan with `credit_score_at_application < 500`
- Score is snapshotted at application time; current score may differ

### 7.4 Explainability Fallback

When Amanuel's service is unreachable, local factors are used:
- Satellite crop health (35%)
- Sales & payment history (35%)
- Mobile money activity (20%)
- Climate resilience (10%)

---

## 8. Testing

### Test Framework

- **pytest** + **pytest-asyncio** + **SQLite in-memory database**
- Async fixtures with auto table creation and role seeding
- Config file: `pytest.ini` (`asyncio_mode = auto`)

### Test Coverage (32 tests)

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `tests/test_auth.py` | 6 | Registration (success, duplicate, invalid role), authentication (success, wrong password, inactive user) |
| `tests/test_credit.py` | 14 | Risk tier boundaries (650/500), recommended loan ranges, contributing factors |
| `tests/test_loan.py` | 4 | Create application, review (approve/not-found), high-risk threshold |
| `tests/test_brain.py` | 8 | Risk tier detail, score→tier mapping, confidence labels |

### Running Tests

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

---

## 9. Security Measures

### Implemented

| Measure | Implementation |
|---------|---------------|
| Password hashing | bcrypt via passlib (NFR-SEC006) |
| JWT authentication | Access (30min) + refresh (7d) tokens (NFR-SEC003) |
| RBAC enforcement | `require_roles()` decorator on all protected endpoints |
| Rate limiting | slowapi on /auth/register and /auth/login (10/min) |
| Input validation | Pydantic field validators: email regex, phone regex, password min_length=6 |
| UUID safety | String-to-UUID conversion before SQL queries |
| Audit logging | All admin actions logged to audit_logs table with user, IP, timestamp |
| CORS | Configured from settings, restricted to known frontend origins |

### Deferred (Infra/Team)

| Measure | Reason |
|---------|--------|
| TLS-in-transit (NFR-SEC001) | Requires infrastructure/load balancer configuration |
| AES-256-at-rest (NFR-SEC002) | Database-level encryption, infra decision |
| Automated DB backups (RPO 24h, RTO 4h) | Requires PostgreSQL + backup tooling |
| Credit-score endpoint <3s monitoring (NFR-P001) | Requires APM tooling decision |
| National Digital ID integration | Explicitly deferred per Team Roles doc; mock verification only |

---

## 10. Known Gaps & Next Steps

### FR-B-002: Yield Prediction
**Status:** Stub endpoint exists at `GET /brain/yield-prediction/{farmer_id}`  
**Action needed:** Confirm scope with team. If in scope, requires integration with Eyosiyas's crop yield model.

### NFR-P001: Credit Score Endpoint Performance
**Status:** Not instrumented  
**Action:** Needs APM tool selection (e.g., Prometheus, Datadog, Sentry) before implementation.

### NFR-R002: Disaster Recovery
**Status:** Deferred to infra team  
**Action:** Coordinate PostgreSQL backup cadence (RPO 24h, RTO 4h).

### Deferred Features (per Team Roles Doc)

- Phone-based OTP login for farmers
- Full National Digital ID API integration
- Traditional banking / alternative financial history integration
- Live mobile money integration
- Native mobile app backend
- Agricultural Input Marketplace (FR-X-004)

---

## Appendix: Project Structure

```
Agri-lend-backend/
├── app/
│   ├── core/
│   │   ├── config.py          # Environment settings
│   │   ├── dependencies.py    # get_current_user, require_roles
│   │   ├── logging.py         # Logger setup
│   │   └── security.py        # bcrypt, JWT helpers
│   ├── db/
│   │   ├── base.py            # DeclarativeBase + TimestampMixin
│   │   └── session.py         # Async engine + session factory
│   ├── models/
│   │   ├── auth.py            # User, Role
│   │   ├── farmer.py          # FarmerProfile, FarmParcel
│   │   ├── credit.py          # CreditScoreRecord, RiskTier
│   │   ├── loan.py            # LoanApplication, LoanStatus
│   │   ├── satellite.py       # SatelliteObservation
│   │   ├── bank.py            # BankPartner
│   │   └── audit.py           # AuditLog, ModelVersion
│   ├── schemas/
│   │   ├── __init__.py        # PaginatedResponse[T]
│   │   ├── auth.py            # Request/response models
│   │   ├── farmer.py
│   │   ├── credit.py
│   │   ├── loan.py
│   │   ├── bank.py
│   │   └── admin.py
│   ├── routers/v1/
│   │   ├── auth.py            # 5 endpoints
│   │   ├── farmers.py         # 12 endpoints
│   │   ├── loans.py           # 8 endpoints
│   │   ├── banks.py           # 4 endpoints
│   │   ├── admin.py           # 19 endpoints
│   │   └── brain.py           # 5 endpoints
│   ├── services/
│   │   ├── auth.py            # AuthService
│   │   ├── farmer.py          # FarmerService
│   │   ├── credit.py          # CreditService
│   │   ├── loan.py            # LoanService
│   │   ├── admin.py           # AdminService
│   │   ├── brain.py           # BrainService (orchestrator)
│   │   ├── scoring.py         # HTTP client → Amanuel
│   │   └── geospatial.py      # HTTP client → Eyosiyas
│   ├── main.py                # FastAPI app, lifespan, CORS, rate limit
│   └── seed.py                # Role seeder (7 roles)
├── alembic/                   # Migration config
├── tests/
│   ├── conftest.py            # Async fixtures
│   ├── test_auth.py           # 6 tests
│   ├── test_credit.py         # 14 tests
│   ├── test_loan.py           # 4 tests
│   └── test_brain.py          # 8 tests
├── pytest.ini                 # asyncio_mode = auto
├── requirements.txt
├── .env.example
├── agrilend_dev.db            # SQLite dev database (auto-created)
└── AGRILEND_BACKEND_REPORT.md # This document
```

---

**Document generated:** 2026-07-20  
**Total API routes:** 58 (including health check and doc endpoints)  
**Database tables:** 10  
**Test count:** 32 (all passing)  
**Latest commit:** Phase 5 — brain integration layer
