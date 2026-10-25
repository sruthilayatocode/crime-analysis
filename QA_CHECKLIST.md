# CrimeSense — Manual QA & Verification Checklist

This document contains a manual Quality Assurance checklist for verifying all user, safety, sharing, and administrative workflows in the CrimeSense application.

---

## Table of Contents
1. [Onboarding & Profile Setup](#1-first-time-onboarding--contacts)
2. [Location Permissions & Fallback Handling](#2-location-permissions--fallback)
3. [Location Access Master Toggle & Privacy Controls](#3-location-toggle-off--privacy)
4. [Coordinate & Street Address Search](#4-search-by-latlng-and-street)
5. [Zone Badge & Risk Level Calculation](#5-redyellowgreen-zone-classification)
6. [Manual SOS Trigger & All-Clear Resolution](#6-sos-manual-trigger--cancellation)
7. [Automated Red-Zone Inactivity Alert](#7-automated-red-zone-state-machine)
8. [WhatsApp, Web Share API & Shareable Token Links](#8-whatsapp--public-share-links)
9. [Authentication & Google OAuth](#9-authentication-flow--google-oauth)
10. [Admin Portal & Role-Based Access Control](#10-admin-views--role-based-access)

---

## 1. First-Time Onboarding & Contacts
- [ ] **Account Creation**: Register a new user account via `/signup`. Verify redirection directly to `/onboarding`.
- [ ] **Enforced Navigation Guard**: Try navigating to `/`, `/map`, or `/settings` while onboarding is incomplete. Verify the app redirects back to `/onboarding`.
- [ ] **Contact Validation**:
  - [ ] Attempt saving with 0 contacts -> Verify submission is blocked with an error prompt.
  - [ ] Add a contact with invalid phone format (e.g., `12345`) -> Verify Indian standard / E.164 phone validation error (`+91XXXXXXXXXX` or 10-digit format).
  - [ ] Add 1 contact and mark as Primary -> Verify save button enables.
  - [ ] Add up to 5 contacts -> Verify the "Add Contact" button disables when 5 contacts are reached.
  - [ ] Attempt saving without designating a Primary contact -> Verify auto-designation or validation error.
- [ ] **Completion**: Click "Complete Setup & Continue". Verify redirection to main app (`/`) and unlock of navigation tabs.

---

## 2. Location Permissions & Fallback
- [ ] **Permission Prompt**: On first load, browser asks for geolocation permission.
- [ ] **Location Denied Path**:
  - [ ] Click "Block" or "Deny" in browser prompt.
  - [ ] Verify banner/notification appears informing the user that live tracking is disabled.
  - [ ] Verify default fallback location (e.g., city center / Bangalore coordinates `12.9716, 77.5946`) renders on the map without crashing.
  - [ ] Verify manual search bar remains fully interactive and functional.

---

## 3. Location Toggle OFF & Privacy
- [ ] **Master Toggle in Settings**:
  - [ ] Navigate to Settings -> **Location & Privacy**.
  - [ ] Toggle **Location Access** to OFF.
  - [ ] Verify warning dialog appears explaining that live tracking, heartbeats, and automatic red-zone alerts are paused.
  - [ ] Verify background heartbeat requests stop (`POST /api/users/heartbeat`).
  - [ ] Verify manual search and static place views continue working.
- [ ] **Admin Visibility Toggle**:
  - [ ] Toggle "Allow admins to see my live location" to OFF.
  - [ ] Login as admin in an incognito window -> Navigate to Admin Live Map -> Verify this user is hidden from the live tracking map.
- [ ] **Delete Location History**:
  - [ ] Click "Delete my location history".
  - [ ] Confirm deletion in modal.
  - [ ] Verify historical location breadcrumbs are cleared from backend database (`user_locations` table).
- [ ] **Delete Account Flow**:
  - [ ] Navigate to Settings -> Account -> Click "Delete My Data & Account".
  - [ ] Confirm password/action -> Verify user is logged out, JWT cleared, and all associated personal records (contacts, saved places, breadcrumbs, audit logs) are permanently purged.

---

## 4. Search by Lat/Lng and Street
- [ ] **Street Geocoding Search**:
  - [ ] Type a landmark or street name (e.g., `"MG Road, Bangalore"` or `"Indiranagar"`).
  - [ ] Verify dropdown suggestions appear from OpenStreetMap Nominatim / geocoder.
  - [ ] Select a result -> Verify map pans smoothly and renders a marker at the chosen location.
- [ ] **Direct Lat/Lng Search**:
  - [ ] Enter raw coordinates in search (e.g., `12.9716, 77.5946`).
  - [ ] Verify search parses numeric values and centers map directly on the coordinates.
- [ ] **Current Location Pin**:
  - [ ] Click the "My Location" crosshair button.
  - [ ] Verify map pans back to device GPS coordinates with accuracy circle.

---

## 5. RED / YELLOW / GREEN Zone Classification
- [ ] **Zone Evaluation**:
  - [ ] Pan or click on a high-density crime area -> Verify badge displays **RED ZONE (High Risk)** with calculated crime score and distance.
  - [ ] Pan to a moderate crime density area -> Verify badge displays **YELLOW ZONE (Moderate Risk)** with safety guidelines.
  - [ ] Pan to a low/zero crime incident area -> Verify badge displays **GREEN ZONE (Low Risk / Safe)**.
- [ ] **Decay & Radius Check**:
  - [ ] Verify crime incidents farther than the search radius (1 km) are decayed or excluded using Haversine distance.

---

## 6. SOS Manual Trigger & Cancellation
- [ ] **Press-and-Hold Mechanism**:
  - [ ] Quick tap on SOS button -> Verify trigger does NOT fire (prevents accidental trigger).
  - [ ] Press and hold for 2 seconds -> Verify animated progress circle fills and triggers the 5-second cancel countdown.
- [ ] **5-Second Countdown Cancellation**:
  - [ ] Click "Cancel Distress Alert" during countdown -> Verify countdown halts and NO SOS event or SMS notification is dispatched.
- [ ] **Emergency Dispatch & Notifications**:
  - [ ] Allow 5-second countdown to complete.
  - [ ] Verify dispatch modal opens showing "Distress Alert Active".
  - [ ] Verify backend creates an `sos_events` record with timestamp, coordinates, and zone badge.
  - [ ] Verify simulated Twilio SMS / WhatsApp message is dispatched to all configured SOS contacts containing user name, live Google Maps link, and zone info.
- [ ] **"I'm Safe" Resolution**:
  - [ ] Click "I'm Safe" in the distress screen.
  - [ ] Verify event status is updated to `resolved` in backend.
  - [ ] Verify all-clear notification is sent to SOS contacts.

---

## 7. Automated Red-Zone State Machine
- [ ] **Heartbeat Streaming**:
  - [ ] Ensure app is active with location enabled. Verify network tab sends `POST /api/users/heartbeat` every 30 seconds with coordinates and interaction flag.
- [ ] **Inactivity in Red Zone**:
  - [ ] Simulate user stationary inside a RED zone for `inactivity_minutes` (configured in Settings: 5, 10, 15, or 30 min).
  - [ ] Verify state transitions from `SAFE` -> `IN_RED` -> `WARNING`.
  - [ ] Verify interactive modal popup appears: **"Are you safe? We noticed you've been stationary in a high-risk zone."** with a 60-second timer.
- [ ] **User Check-in**:
  - [ ] Tap "I'm Safe" within 60 seconds -> Verify state resets to `SAFE` and no emergency alert is triggered.
- [ ] **Timeout Auto-Trigger**:
  - [ ] Let 60-second timer expire without input.
  - [ ] Verify auto-distress trigger (`sos_events` of type `auto_red_zone`) dispatches to contacts.
  - [ ] Verify 30-minute cooldown prevents duplicate spamming.

---

## 8. WhatsApp & Public Share Links
- [ ] **WhatsApp One-Click Sharing**:
  - [ ] From Saved Places or Map View, click "Share via WhatsApp".
  - [ ] Verify URL opens `https://wa.me/?text=...` with pre-filled message, place title, zone safety status, and Google Maps coordinate link.
- [ ] **Public Shareable Token Link (`/s/:token`)**:
  - [ ] In Share modal, select expiry: **1 Hour**, **8 Hours**, or **24 Hours**.
  - [ ] Choose **Static Location** or **Live Tracking**.
  - [ ] Click "Generate Share Link" -> Copy link `/s/<random-token>`.
  - [ ] Open generated link in a completely separate browser or incognito window without logging in.
  - [ ] Verify mobile-friendly read-only view displays the map, zone badge, and shared coordinates without leaking any private user data.
- [ ] **Revocation & Expiry**:
  - [ ] Click "Stop Sharing" from the user's dashboard.
  - [ ] Refresh the `/s/<token>` page in the incognito window.
  - [ ] Verify it displays an "Expired or Revoked Link" state.

---

## 9. Authentication Flow & Google OAuth
- [ ] **Standard Auth**:
  - [ ] Test Signup, Login, Password validation (min 6 chars), and Token Refresh.
  - [ ] Verify JWT stored securely with `Authorization: Bearer <token>`.
- [ ] **Google One-Tap / OAuth Login**:
  - [ ] Click "Continue with Google".
  - [ ] Select Google account -> Verify token verification on backend (`POST /api/auth/google`).
  - [ ] Verify automatic account creation / login and redirection.
- [ ] **Cross-User Data Isolation**:
  - [ ] Log in as User A -> Save a place "My Home".
  - [ ] Log in as User B -> Verify User A's saved places and SOS contacts are NOT visible.
  - [ ] Attempt direct API request `GET /api/users/saved-locations/<id_of_user_a>` with User B's token -> Verify backend returns `404 Not Found` or `403 Forbidden`.

---

## 10. Admin Views & Role-Based Access
- [ ] **RBAC Protection**:
  - [ ] Attempt accessing `/admin` as a standard user -> Verify frontend redirects or shows Access Denied.
  - [ ] Send direct API request `GET /api/admin/overview` with standard user JWT -> Verify backend returns HTTP `403 Forbidden`.
- [ ] **Admin Overview Dashboard**:
  - [ ] Login as `admin@crimesense.org`.
  - [ ] Verify KPI metric cards (Total Crimes, High Severity, Active Hotspots, Total Users, Active SOS Distress Events).
  - [ ] Verify interactive charts for Crime Trends and Category Distribution.
- [ ] **Crime Data Management (CRUD)**:
  - [ ] View paginated crime incident table with search and filters (category, severity, date range).
  - [ ] Click "Add Incident" -> Fill form with lat, lng, category, severity -> Save -> Verify added to map and table.
  - [ ] Edit existing incident -> Verify updates reflect immediately.
  - [ ] Delete incident -> Verify incident is removed.
  - [ ] Export CSV -> Verify CSV file downloads with complete dataset.
- [ ] **Historical Trends & Analytics**:
  - [ ] Switch year filters (2020 - present) -> Verify charts update dynamically.
  - [ ] Check breakdown by category, severity distribution, and monthly heat.
- [ ] **User Management**:
  - [ ] View registered user list with roles, contact counts, and sharing status.
  - [ ] Change user role (User <-> Admin) -> Verify role updates in database.
  - [ ] View User Details modal -> Verify location history breadcrumbs and SOS logs.
- [ ] **Admin Live Map**:
  - [ ] Open Live Map -> Verify pins for all active users who have location sharing enabled and have consented to admin visibility.
- [ ] **Emergency Distress Feed (Alerts & SOS)**:
  - [ ] View active SOS alarms -> Click "Resolve Event" -> Verify status updates to resolved in real-time.
- [ ] **Audit Trail**:
  - [ ] Navigate to **Admin Audit Log**.
  - [ ] Verify timestamped entries for all administrative actions (`CRIME_CREATE`, `USER_ROLE_CHANGE`, `LOCATION_HISTORY_VIEW`, `SOS_RESOLVE`) with Admin ID and IP address.
