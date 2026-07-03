# AgriLend Backend Implementation Task List
**Owner:** Mikiyas Mechalo — Backend Logic Development
**Scope basis:** Team Roles Doc + MVP Specification + SRS v1.0 + System Architecture

Mikiyas's mandate is "The Brain's" delivery layer: server-side business logic, dashboard data, and system workflows, ensuring every backend endpoint satisfies what Eyob's React frontend needs. He consumes structured data from Eyosiyas (geospatial pipeline) and Amanuel (credit scoring model) rather than building either himself. National Digital ID integration is **explicitly deferred** per the Team Roles doc — MVP only needs a simulated verification step.

---

## Phase 0 — Foundations & Setup

- [ ] Scaffold FastAPI project (routers, services, schemas, dependency-injection structure)
- [ ] Configure environments: Development / Staging / Production (SRS 3.2)
- [ ] Set up PostgreSQL + PostGIS, connection pooling, Alembic migrations
- [ ] Implement core data models (SRS 7.1): `FarmerProfile`, `FarmParcel`, `CreditScoreRecord`, `SatelliteObservation`, `LoanApplication`, `BankPartner`
- [ ] Add supporting tables not explicit in SRS but required by MVP: `User`/`Role` (for RBAC across Farmer/Bank/Admin), `AuditLog`, `ModelVersion`
- [ ] Stand up OAuth2 / JWT auth scaffolding (NFR-SEC003)
- [ ] Build RBAC dependency/middleware — roles: Farmer, Bank Viewer/Analyst/Admin, Platform Admin, Risk Analyst, Loan Officer (MVP 1.3)
- [ ] Version all routes under `/api/v1/` (SRS 6.2)
- [ ] Wire up OpenAPI/Swagger auto-docs (NFR-M001)
- [ ] Define the internal API contract with **Eyosiyas** for consuming structured geospatial data (NDVI, climate layers)
- [ ] Define the internal API contract with **Amanuel** for consuming credit score, risk tier, and explainability output
- [ ] Set up PII access audit logging (NFR-SEC007)

---

## Phase 1 — Authentication & User Management
*(Shared backbone for all three "Marketplace" surfaces)*

- [ ] Farmer / Bank / Admin registration endpoints (Sign Up) — MVP 1.2, 1.3
- [ ] Login endpoint with JWT issuance + refresh token flow (Sign In)
- [ ] Password hashing via bcrypt (NFR-SEC006)
- [ ] Admin: create user endpoint (farmer, bank officer, risk analyst, admin) — MVP 1.3
- [ ] Admin: role assignment endpoint
- [ ] Admin: access-control endpoint to grant/restrict access to sensitive modules (credit scoring, loan approvals, portfolio monitoring)
- [ ] Admin: bank activation endpoint ("allow banks to use the AgriLend system") + grant bank-officer dashboard access
- [ ] Profile update endpoint (contact details, linked mobile money placeholder, farm info)
- [ ] Deactivate / delete user endpoint
- [ ] Audit trail capture on all user-management actions

---

## Phase 2 — Farmer Mobile Backend

- [ ] **Registration Hub** endpoint (FR-M-001): full name, phone, national ID *(stored only — not live-verified)*, GPS coordinates, crop type(s), farm size
- [ ] Land ownership verification field/upload placeholder — input method still TBD per MVP doc; build a generic document/attestation field so it's swappable later
- [ ] **Consent Authorization** endpoint (FR-X-002): consent checkbox → `consent_status`, `consent_date`; revoke-consent endpoint; simulate the National ID verification loading step (mock async delay + success response, since the real integration is deferred)
- [ ] Locale field on farmer profile to support the language switcher (English / Amharic / Afaan Oromo) — translation itself lives in frontend, but backend should persist and return the preference
- [ ] **Credit Score Dashboard** endpoint (FR-M-002): current score + Low/Medium/High banding, score history/trend
- [ ] Simplified explainability endpoint: reformats Amanuel's feature-importance output into farmer-readable "why this score" text
- [ ] **Farm Status** endpoint (FR-M-003): pulls NDVI time-series from Eyosiyas's pipeline, shapes it for the circular score display + chart component
- [ ] **Loan Application** endpoint (FR-M-005): amount, purpose, snapshots credit score at time of submission, sets `status = PENDING`
- [ ] Loan status-check endpoint for the farmer
- [ ] *Backlog (SRS Phase 2/3, not in MVP layout doc):* SMS alerts (FR-M-004), yield insights (FR-M-006), crop calendar (FR-M-007) — flag with team for prioritization

---

## Phase 3 — Bank Web Dashboard Backend

- [ ] Loan applicant list endpoint with filters (status, region, crop type)
- [ ] Applicant detail endpoint (FR-B-D-002): full credit report — score, risk tier, land status, contributing data sources, trend
- [ ] Approve / reject loan application endpoint — status transition, `reviewed_by`, `reviewed_at`
- [ ] Report dashboard endpoint: counts by Approved / Rejected / Pending, row-click detail payload
- [ ] Risk heatmap data endpoint (FR-B-D-003): aggregates Amanuel's heatmap generator output + Eyosiyas's geospatial layers into GeoJSON, filterable by crop/risk tier/time period
- [ ] High-risk loan warning-flag logic (threshold-based, surfaced on portfolio views)
- [ ] Bank RBAC enforcement (Viewer / Analyst / Administrator) — MVP 1.2, FR-B-D-001
- [ ] Bank settings endpoint (profile customization, permission management)
- [ ] *Backlog:* Credit Scoring API for external bank system integration (FR-B-D-005) — build once a bank partner needs programmatic access; MVP only needs the dashboard-facing version

---

## Phase 4 — Admin Portal Backend

- [ ] Farmer onboarding report endpoint (registered / verified / mobile-money-linked counts)
- [ ] Loan report endpoint (submitted / approved / rejected / disbursed counts)
- [ ] Credit scoring report endpoint (average score, regional distribution, trend over time)
- [ ] Risk & portfolio report endpoint (default rates, repayment performance, geo risk clusters) — *repayment data depends on loan lifecycle being live; stub with placeholder data until disbursement tracking exists*
- [ ] ML Performance page endpoints:
  - [ ] Model accuracy / precision / recall metrics — surfaces Amanuel's evaluation output
  - [ ] Error analysis endpoint (misclassification breakdown)
  - [ ] Bias & fairness indicator endpoint (by region / crop type)
  - [ ] Drift-detection status endpoint
  - [ ] Model version display + rollback trigger endpoint (NFR-M003: rollback within 1 hour — backend owns the versioning table and rollback API call; actual model artifact swap is Amanuel's)
- [ ] Data pipeline monitoring endpoint (FR-A-002) — surfaces Eyosiyas's ingestion job status, success/failure rates, last-run timestamps

---

## Phase 5 — "The Brain" Integration Layer

- [ ] Internal service client to call Amanuel's scoring model service
- [ ] Score-calculation trigger + persistence logic (`CreditScoreRecord`) on new satellite data ingestion events (FR-B-001)
- [ ] Risk tier classification exposure (FR-B-003): tier label, contributing factors, recommended loan range
- [ ] *Flag with team:* SRS marks yield prediction (FR-B-002) as HIGH priority, but it's absent from the MVP layout doc — confirm whether it's in scope for this sprint or backlog

---

## Phase 6 — Cross-Cutting / Non-Functional

- [ ] Keep credit-score endpoint under 3s response time under normal load (NFR-P001)
- [ ] Pagination + filtering on all list endpoints (supports scaling toward 10k+ farmers — NFR-P002)
- [ ] Rate limiting middleware on public-facing endpoints (NFR-SEC005)
- [ ] Coordinate TLS-in-transit and AES-256-at-rest with infra/deploy (NFR-SEC001/002)
- [ ] Coordinate automated DB backup cadence with infra (RPO 24h / RTO 4h — NFR-R002)
- [ ] Unit test coverage ≥ 80% on core business logic (NFR-M002)
- [ ] Complete OpenAPI/Swagger documentation for all endpoints (NFR-M001, SRS 6.2)

---

## Explicitly Out of Scope for MVP (per Team Roles Doc)

- Full National Digital ID API integration (simulate only)
- Traditional banking / alternative financial history integration
- Live mobile money integration (SRS Phase 3) — stub/mock if a frontend dependency needs it, coordinate with Eyosiyas's mock-data fallback strategy
- Native mobile app backend concerns (mobile stack undecided; MVP targets the responsive web app)
- Agricultural Input Marketplace (FR-X-004, Phase 4)

---

## Suggested Sprint Order

1. **Foundations + Auth/RBAC** — Phase 0 & 1
2. **Farmer backend** — Phase 2
3. **Bank dashboard backend** — Phase 3
4. **Admin backend** — Phase 4
5. **Brain integration + hardening** — Phase 5 & 6
