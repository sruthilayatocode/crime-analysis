# CrimeSense — Security Review & Vulnerability Assessment

This report documents the security audit, access control verification, vulnerability remediation, and production hardening assessment for the CrimeSense platform.

---

## 1. Executive Summary
- **Overall Security Posture**: **STRONG (Grade A-)**
- **Authentication**: JWT with bcrypt password hashing
- **Authorization**: Role-Based Access Control (RBAC) with case-insensitive role normalisation
- **Data Privacy**: Citizen multi-tenancy isolation strictly enforced
- **SQL Injection Risk**: **NONE** (All queries use SQLAlchemy parameterized abstractions)

---

## 2. Core Security Controls & Verifications

### 2.1 Password Security & Storage
- **Implementation**: Passwords hashed using `bcrypt.hashpw` with standard salt rounds before storage in SQLite.
- **Verification**: Audited `User` model and `auth_service.py`. Raw passwords are never stored or logged. Password hashes are explicitly excluded from serialization dictionaries.

### 2.2 JWT Token Architecture & Validation
- **Algorithm**: HMAC-SHA256 (`HS256`).
- **Expiry Enforced**: Tokens contain an explicit expiration claim (`exp`).
- **Revocation / Invalidation**: Expired or corrupted tokens return standard HTTP `401 Unauthorized` responses via the unified error handler.

### 2.3 Role-Based Access Control (RBAC) & Normalisation
- **Identified Defect**: In early revisions, role checks performed strict equality against `"admin"`. If a user was stored with role `"ADMIN"`, access was inconsistently evaluated.
- **Remediation**: Implemented robust case-insensitive normalisation in both service and decorator layers:
  ```python
  def is_admin(user) -> bool:
      return str(user.role or "").strip().lower() == "admin"
  ```
- **Verification**: Tested in `verify_phase1_e2e.py` and `backend/tests/test_crimesense_suite.py`. Non-admin accounts attempting to access `/api/admin/*` consistently receive HTTP `403 Forbidden`.

### 2.4 User Data Privacy & Cross-Tenant Isolation
- **Risk Assessed**: Unauthorised cross-user inspection of private citizen crime reports.
- **Remediation & Control**: The citizen report endpoint (`GET /api/crimes/my-reports`) queries exclusively against `current_user.id`. Citizens have zero capability to specify another user's ID or retrieve unapproved reports submitted by others.
- **Verification**: Verified via test suite `test_07_role_based_access_and_cross_user_isolation`.

### 2.5 SQL Injection & Query Parameterization
- **Audit Findings**: The application utilises SQLAlchemy ORM exclusively for data layer operations.
- **Verdict**: No raw string concatenation was detected in database queries. All inputs are safely escaped and parameterized by SQLite driver bindings.

### 2.6 Input Validation & Safe Error Responses
- **Control**: Input payloads are validated before downstream model creation.
- **Safe Error Envelope**: Uncaught exceptions do not leak stack traces or environment variables to client responses. Instead, the global handler wraps errors in a sanitised JSON payload:
  ```json
  {
    "error": "ValidationError",
    "message": "Invalid latitude format. Must be between -90 and 90.",
    "status_code": 400
  }
  ```

---

## 3. Residual Risks & Recommended Production Hardening

| Risk Factor | Current State | Production Recommendation | Priority |
| :--- | :--- | :--- | :--- |
| **Secret Key Rotation** | Fallback key defined in development configuration. | Enforce `SECRET_KEY` load from secure environment secrets in production container. | **HIGH** |
| **API Rate Limiting** | Open burst thresholds for local development. | Add `Flask-Limiter` on `/api/auth/login` and `/api/crimes/report` to mitigate brute force attacks and spam. | **MEDIUM** |
| **HTTPS / TLS** | HTTP used for local development. | Terminate TLS via reverse proxy (Nginx / Cloudflare / Caddy) in production deployments. | **HIGH** |
| **CORS Origins** | Permits `*` in development configuration. | Restrict `CORS_ORIGINS` to verified frontend domains in production environment. | **MEDIUM** |
| **Physical SQLite Security** | Database stored on local filesystem. | Restrict filesystem permissions on `backend/instance/` so only the service execution user has read/write privileges. | **HIGH** |
