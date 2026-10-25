# CrimeSense — Backend API Documentation

This document details the complete, verified REST API surface of the CrimeSense backend implemented in Python and Flask, including request parameters, authentication constraints, and example JSON payloads and responses.

---

## Base URL & Configuration
- **Local Development**: `http://127.0.0.1:5000`
- **Frontend API Base**: Configured via `VITE_API_URL` or defaulting to `http://localhost:5000`
- **Global Error Format**:
  All errors return structured JSON with uniform envelope semantics:
  ```json
  {
    "error": "ErrorType",
    "message": "Human-readable explanation of the issue.",
    "status_code": 400
  }
  ```

---

## 1. Authentication Endpoints (`/api/auth`)

### 1.1 User Registration
- **Route**: `POST /api/auth/register`
- **Auth**: Public
- **Request Body**:
  ```json
  {
    "name": "Jane Citizen",
    "email": "jane@example.com",
    "password": "SecurePassword123!",
    "role": "user"
  }
  ```
- **Response** (`201 Created`):
  ```json
  {
    "message": "User registered successfully",
    "user": {
      "id": 3,
      "name": "Jane Citizen",
      "email": "jane@example.com",
      "role": "user"
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```

### 1.2 User Login
- **Route**: `POST /api/auth/login`
- **Auth**: Public
- **Request Body**:
  ```json
  {
    "email": "jane@example.com",
    "password": "SecurePassword123!"
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "message": "Login successful",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 3,
      "name": "Jane Citizen",
      "email": "jane@example.com",
      "role": "user"
    }
  }
  ```

### 1.3 Current User Profile
- **Route**: `GET /api/auth/me`
- **Auth**: Bearer Token required (`Authorization: Bearer <token>`)
- **Response** (`200 OK`):
  ```json
  {
    "id": 3,
    "name": "Jane Citizen",
    "email": "jane@example.com",
    "role": "user",
    "is_verified": true,
    "created_at": "2026-10-25T11:00:00"
  }
  ```

### 1.4 Email Verification
- **Route**: `GET /api/auth/verify-email` or `POST /api/auth/verify-email`
- **Auth**: Public (Cryptographic token query param or body)
- **Query Parameter / Body**: `token=<token_string>`
- **Rate Limit**: 20 requests / minute / IP
- **Description**: Validates a single-use SHA-256 hashed verification token with a 24-hour expiration window. Invalidates token upon successful activation.
- **Response** (`200 OK`):
  ```json
  {
    "success": true,
    "message": "Email address verified successfully! You now have full access to CrimeSense.",
    "is_verified": true
  }
  ```

### 1.5 Resend Email Verification Link
- **Route**: `POST /api/auth/resend-verification`
- **Auth**: Public
- **Rate Limit**: 5 requests / 5 minutes / IP
- **Request Body**:
  ```json
  {
    "email": "jane@example.com"
  }
  ```
- **Description**: Sends a fresh single-use verification token if an unverified account matches. Returns a uniform anti-enumeration message.
- **Response** (`200 OK`):
  ```json
  {
    "success": true,
    "message": "If an unverified account exists for this email, a new verification link has been sent."
  }
  ```

### 1.6 Forgot Password (Password Recovery)
- **Route**: `POST /api/auth/forgot-password`
- **Auth**: Public
- **Rate Limit**: 5 requests / 5 minutes / IP
- **Request Body**:
  ```json
  {
    "email": "jane@example.com"
  }
  ```
- **Description**: Generates a cryptographically secure 1-hour expiration reset token and stores its SHA-256 hash. Returns a uniform generic message regardless of email existence to prevent user enumeration.
- **Response** (`200 OK`):
  ```json
  {
    "success": true,
    "message": "If that email address is registered, a password reset link has been sent to your inbox."
  }
  ```

### 1.7 Reset Password
- **Route**: `POST /api/auth/reset-password`
- **Auth**: Public
- **Rate Limit**: 10 requests / 5 minutes / IP
- **Request Body**:
  ```json
  {
    "token": "a1b2c3d4e5...",
    "password": "NewSecurePassword123!"
  }
  ```
- **Description**: Verifies unexpired single-use token hash, enforces minimum 6-character password policy, updates hashed password using Werkzeug bcrypt/pbkdf2, and immediately invalidates the reset token.
- **Response** (`200 OK`):
  ```json
  {
    "success": true,
    "message": "Your password has been successfully reset. You can now log in with your new password."
  }
  ```

---

## 2. Crime Data & Reporting Endpoints (`/api/crimes`)

### 2.1 Query Crime Records
- **Route**: `GET /api/crimes`
- **Auth**: Public / Authenticated
- **Query Parameters**:
  - `page` (integer, default: 1)
  - `per_page` (integer, default: 50, max: 200)
  - `category` (string, optional)
  - `status` (string, default: `APPROVED`)
  - `start_date`, `end_date` (ISO date string, optional)
  - `min_lat`, `max_lat`, `min_lng`, `max_lng` (bounding box floats, optional)
- **Response** (`200 OK`):
  ```json
  {
    "items": [
      {
        "id": 101,
        "category": "THEFT",
        "description": "Bicycle stolen from bike rack",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "severity_score": 0.45,
        "risk_level": "MEDIUM",
        "status": "APPROVED",
        "reported_at": "2026-10-24T18:30:00"
      }
    ],
    "page": 1,
    "per_page": 50,
    "total": 685,
    "pages": 14
  }
  ```

### 2.2 Submit Citizen Crime Report
- **Route**: `POST /api/crimes/report`
- **Auth**: Bearer Token required (`role: user` or `role: admin`)
- **Request Body**:
  ```json
  {
    "category": "ASSAULT",
    "description": "Verbal dispute escalating to physical altercation",
    "latitude": 13.0850,
    "longitude": 80.2750,
    "severity_score": 0.75,
    "reported_at": "2026-10-25T12:00:00"
  }
  ```
- **Response** (`201 Created`):
  ```json
  {
    "message": "Crime report submitted successfully for administrative review",
    "report": {
      "id": 686,
      "category": "ASSAULT",
      "status": "PENDING_REVIEW",
      "reported_by_id": 3,
      "latitude": 13.0850,
      "longitude": 80.2750
    }
  }
  ```

### 2.3 Citizen Submitted Reports
- **Route**: `GET /api/crimes/my-reports`
- **Auth**: Bearer Token required (Citizen isolation enforced)
- **Response** (`200 OK`):
  ```json
  {
    "reports": [
      {
        "id": 686,
        "category": "ASSAULT",
        "description": "Verbal dispute escalating to physical altercation",
        "status": "PENDING_REVIEW",
        "reviewer_notes": null,
        "created_at": "2026-10-25T12:00:00"
      }
    ]
  }
  ```

### 2.4 Crime Aggregation Statistics
- **Route**: `GET /api/crimes/statistics`
- **Auth**: Public
- **Response** (`200 OK`):
  ```json
  {
    "total_crimes": 685,
    "by_category": {
      "THEFT": 210,
      "BURGLARY": 145,
      "ASSAULT": 120,
      "ROBBERY": 95,
      "VANDALISM": 115
    },
    "by_risk_level": {
      "LOW": 180,
      "MEDIUM": 320,
      "HIGH": 185
    }
  }
  ```

---

## 3. Machine Learning & Spatial Hotspots (`/api/ml`)

### 3.1 Spatial Hotspot Density Clustering
- **Route**: `GET /api/ml/hotspots`
- **Auth**: Public
- **Query Parameters**:
  - `eps_km` (float, default: 1.0): DBSCAN neighborhood distance in kilometers
  - `min_samples` (integer, default: 5): Minimum crime density threshold
- **Response** (`200 OK`):
  ```json
  {
    "hotspots": [
      {
        "cluster_id": 0,
        "centroid_lat": 13.0827,
        "centroid_lng": 80.2707,
        "incident_count": 42,
        "risk_level": "HIGH",
        "top_categories": ["THEFT", "ROBBERY"]
      }
    ],
    "total_clusters": 4,
    "noise_points": 18
  }
  ```

### 3.2 Supervised Crime Risk Prediction
- **Route**: `POST /api/ml/predict-risk`
- **Auth**: Public / Authenticated
- **Request Body**:
  ```json
  {
    "category": "ROBBERY",
    "latitude": 13.0827,
    "longitude": 80.2707,
    "hour": 23,
    "day_of_week": 5,
    "month": 10
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "status": "success",
    "prediction": {
      "risk_level": "HIGH",
      "risk_score": 0.88,
      "confidence": 0.9042,
      "class_probabilities": {
        "LOW": 0.012,
        "MEDIUM": 0.0838,
        "HIGH": 0.9042
      },
      "model_version": "1.0.0"
    }
  }
  ```

### 3.3 Model Metadata & Provenance
- **Route**: `GET /api/ml/model-info`
- **Auth**: Public
- **Response** (`200 OK`):
  ```json
  {
    "model_name": "CrimeSense_Risk_Classifier",
    "model_type": "RandomForestClassifier",
    "version": "1.0.0",
    "trained_at": "2026-10-25T11:45:00",
    "training_records": 685,
    "target_variable": "risk_level (LOW, MEDIUM, HIGH)",
    "baseline_dummy_accuracy": 0.4672,
    "test_accuracy": 0.9927,
    "macro_f1": 0.993
  }
  ```

---

## 4. Administrative Triage Endpoints (`/api/admin`)
*All administrative endpoints require `Authorization: Bearer <token>` where user role is `admin` (case-insensitive).*

### 4.1 Pending Crime Reports
- **Route**: `GET /api/admin/crimes/pending`
- **Auth**: Admin only
- **Response** (`200 OK`):
  ```json
  {
    "pending_crimes": [
      {
        "id": 686,
        "category": "ASSAULT",
        "description": "Verbal dispute escalating to physical altercation",
        "latitude": 13.0850,
        "longitude": 80.2750,
        "severity_score": 0.75,
        "reported_by": {
          "id": 3,
          "name": "Jane Citizen",
          "email": "jane@example.com"
        },
        "created_at": "2026-10-25T12:00:00"
      }
    ]
  }
  ```

### 4.2 Approve Crime Report
- **Route**: `POST/PATCH/PUT /api/admin/crimes/<id>/approve`
- **Auth**: Admin only
- **Request Body** (optional):
  ```json
  {
    "notes": "Verified against local precinct incident log #4928"
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "message": "Crime report 686 approved successfully",
    "crime_id": 686,
    "status": "APPROVED"
  }
  ```

### 4.3 Reject Crime Report
- **Route**: `POST/PATCH/PUT /api/admin/crimes/<id>/reject`
- **Auth**: Admin only
- **Request Body** (optional):
  ```json
  {
    "notes": "Duplicate entry of previously recorded incident #682"
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "message": "Crime report 686 rejected",
    "crime_id": 686,
    "status": "REJECTED"
  }
  ```

---

## 5. System Health & Metadata (`/api/system`)

### 5.1 System Environment Info
- **Route**: `GET /api/system/info`
- **Auth**: Public
- **Response** (`200 OK`):
  ```json
  {
    "status": "online",
    "application": "CrimeSense API",
    "version": "1.0.0",
    "database": "sqlite",
    "auth_type": "jwt",
    "total_crimes_loaded": 685
  }
  ```
