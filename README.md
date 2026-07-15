# AgriLend Backend

Agricultural Credit Intelligence Platform — backend API server built with FastAPI.

AgriLend transforms raw farm data into reliable agricultural credit scores, bridging the gap between smallholder farmers and financial institutions.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI Server                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │  Auth    │  │  Farmer  │  │  Bank    │  │  Admin     │  │
│  │  Router  │  │  Router  │  │  Router  │  │  Router    │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬──────┘  │
│       │              │              │               │        │
│  ┌────┴──────────────┴──────────────┴───────────────┴────┐  │
│  │                    Service Layer                       │  │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │  │
│  │  │  Auth   │ │  Farmer  │ │  Credit  │ │  Loan    │  │  │
│  │  └─────────┘ └──────────┘ └──────────┘ └──────────┘  │  │
│  │  ┌──────────────┐ ┌──────────────┐                    │  │
│  │  │ Geospatial   │ │   Scoring    │  ← Internal APIs   │  │
│  │  │ (Eyosiyas)   │ │  (Amanuel)   │                    │  │
│  │  └──────────────┘ └──────────────┘                    │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │            SQLAlchemy ORM + PostgreSQL                 │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │                                        │
         ▼                                        ▼
  Eyosiyas's Pipeline              Amanuel's ML Service
  (NDVI, climate data)             (credit scores, heatmaps)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI (Python 3.11+) |
| Database | PostgreSQL + PostGIS / SQLite (dev) |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Auth | OAuth2 / JWT (python-jose) + bcrypt |
| Validation | Pydantic v2 |
| Geospatial | GeoJSON via PostGIS |

## Project Structure

```
app/
├── main.py                 # FastAPI entry point, CORS, lifespan
├── seed.py                 # Seeds default roles on startup
├── core/
│   ├── config.py           # Environment-based settings
│   ├── security.py         # bcrypt hashing, JWT create/decode
│   ├── dependencies.py     # Auth & RBAC middleware
│   └── logging.py          # Audit logger (PII access tracking)
├── db/
│   ├── base.py             # DeclarativeBase + TimestampMixin
│   └── session.py          # Async engine + session factory
├── models/                 # SQLAlchemy ORM models
│   ├── auth.py             # User, Role
│   ├── farmer.py           # FarmerProfile, FarmParcel
│   ├── credit.py           # CreditScoreRecord
│   ├── satellite.py        # SatelliteObservation
│   ├── loan.py             # LoanApplication
│   ├── bank.py             # BankPartner
│   └── audit.py            # AuditLog, ModelVersion
├── schemas/                # Pydantic request/response models
│   ├── auth.py
│   ├── farmer.py
│   ├── credit.py
│   ├── loan.py
│   └── bank.py
├── routers/v1/             # API endpoints under /api/v1/
│   ├── auth.py             # Register, login, refresh, profile
│   ├── farmers.py          # Registration hub, parcels, consent, credit, farm status
│   ├── loans.py            # Create, list, review, status check
│   ├── banks.py            # Bank partner CRUD
│   └── admin.py            # User management, audit, bank activation
└── services/               # Business logic layer
    ├── auth.py
    ├── farmer.py
    ├── credit.py
    ├── loan.py
    ├── geospatial.py       # Internal API client for Eyosiyas
    └── scoring.py          # Internal API client for Amanuel
```

## API Endpoints

### Authentication (`/api/v1/auth`)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/register` | Create new user account | No |
| POST | `/login` | Login, returns JWT tokens | No |
| POST | `/refresh` | Refresh access token | No |
| GET | `/me` | Get current user profile | JWT |
| PATCH | `/me` | Update own profile | JWT |

### Farmers (`/api/v1/farmers`)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/register` | Registration hub — creates user + profile + parcel | No |
| GET | `/me` | Get own farmer profile | JWT |
| GET | `/profile/{id}` | Get farmer profile by ID | JWT |
| POST | `/consent` | Set data sharing consent | JWT |
| POST | `/consent/revoke` | Revoke consent | JWT |
| POST | `/parcels` | Add farm parcel | Farmer/Admin |
| GET | `/{id}/parcels` | List farmer's parcels | JWT |
| GET | `/{id}/credit-score` | Current credit score | JWT |
| GET | `/{id}/credit-history` | Score history + trend | JWT |
| GET | `/{id}/explain` | "Why this score" explanation | JWT |
| GET | `/{id}/farm-status` | NDVI crop health + chart data | JWT |

### Loans (`/api/v1/loans`)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/` | Submit loan application | Farmer/Admin |
| GET | `/` | List loans (filterable) | JWT |
| GET | `/{id}` | Loan status check | JWT |
| PATCH | `/{id}/review` | Approve/reject loan | Loan Officer/Analyst/Admin |

### Banks (`/api/v1/banks`)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/` | Register bank partner | Platform Admin |
| GET | `/` | List bank partners | JWT |

### Admin (`/api/v1/admin`)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/users` | List all users | Platform Admin |
| POST | `/users` | Create any user | Platform Admin |
| PATCH | `/users/{id}/role` | Assign role | Platform Admin |
| PATCH | `/users/{id}` | Update any user | Platform Admin |
| DELETE | `/users/{id}` | Delete user | Platform Admin |
| PATCH | `/users/{id}/deactivate` | Soft-deactivate user | Platform Admin |
| POST | `/banks/{id}/activate` | Activate bank partner | Platform Admin |

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

The app defaults to SQLite — no external database needed.

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
| `DATABASE_URL` | `sqlite+aiosqlite:///./agrilend_dev.db` | Async database URL |
| `DATABASE_SYNC_URL` | `sqlite:///./agrilend_dev.db` | Sync database URL |
| `JWT_SECRET_KEY` | `change-me-to-a-long-random-string` | JWT signing key |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | Allowed CORS origins |
| `EYOSIYAS_SERVICE_URL` | `http://geospatial-service:8001` | Geospatial pipeline URL |
| `AMANUEL_SERVICE_URL` | `http://scoring-service:8002` | ML scoring service URL |
| `LOG_LEVEL` | `INFO` | Logging level |
| `AUDIT_LOG_ENABLED` | `true` | Enable PII audit logging |

## Database Models

```
User ──> Role
  │
  └──> FarmerProfile ──> FarmParcel ──> SatelliteObservation
         │                  │
         │                  └──> CreditScoreRecord
         │
         └──> LoanApplication ──> BankPartner
                                    │
                              User (reviewed_by)
```

Additional tables: `AuditLog` (PII access tracking), `ModelVersion` (ML model versioning).

## Internal API Contracts

### Eyosiyas (Geospatial Pipeline)

Service stubbed in `app/services/geospatial.py`:
- `GET /api/v1/ndvi/{parcel_id}?days=90` — NDVI time-series
- `GET /api/v1/climate/{parcel_id}` — Climate data

### Amanuel (ML Scoring Service)

Service stubbed in `app/services/scoring.py`:
- `GET /api/v1/score/{farmer_id}` — Credit score
- `GET /api/v1/explain/{farmer_id}` — Feature importance
- `GET /api/v1/heatmap` — Risk heatmap data
- `GET /api/v1/metrics` — Model performance metrics

## Development

### Onboarding Checklist

- [ ] Phase 0 — Foundations & Setup ✓
- [ ] Phase 1 — Authentication & User Management ✓
- [ ] Phase 2 — Farmer Mobile Backend ✓
- [ ] Phase 3 — Bank Web Dashboard Backend
- [ ] Phase 4 — Admin Portal Backend
- [ ] Phase 5 — "The Brain" Integration Layer
- [ ] Phase 6 — Cross-Cutting / Non-Functional

### Testing

```bash
# Run tests (when implemented)
pytest
```

### Migrations

```bash
# Generate a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## License

Internal project — AgriLend
