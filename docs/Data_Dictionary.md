# Data Dictionary — Crime Analysis Dataset

> **Project:** AI-Powered Crime Hotspot Analysis and Proximity Alert System  
> **Version:** 1.0  
> **Last Updated:** 2026-07-28  
> **Author:** Data Engineering Team

---

## 1. Project Overview

The Crime Analysis project aims to build a machine learning-driven system that identifies crime hotspots, predicts high-risk zones, and sends real-time proximity alerts to users. The dataset is the foundational layer of this system — it aggregates crime incident records from multiple sources (government records, police reports, news articles) into a single, clean, geocoded, and feature-engineered dataset suitable for training predictive models.

---

## 2. Dataset Purpose

The primary objectives of this dataset are:

| Objective | Description |
|---|---|
| Hotspot Identification | Identify geographic areas with statistically elevated crime rates |
| Temporal Pattern Analysis | Detect daily, weekly, seasonal, and annual crime trends |
| Risk Scoring | Assign risk scores to geographic zones (grid cells or administrative wards) |
| Model Training | Serve as the labelled dataset for supervised and unsupervised ML models |
| Alert Triggering | Enable real-time proximity checks between user GPS locations and known hotspots |

---

## 3. Dataset Structure

The dataset pipeline follows a three-stage architecture:

| Stage | Directory | Description |
|---|---|---|
| **Raw** | `data/raw/` | Immutable source data ingested from external sources. Subdirectories: `government/`, `news/`, `police/`, `archived/` |
| **Processed** | `data/processed/` | Cleaned, deduplicated, and standardised data with validated schema |
| **Final** | `data/final/` | Geocoded, feature-engineered dataset ready for ML consumption |

### File Naming Convention

| Convention | Example |
|---|---|
| `{source}_{city}_{date_range}.csv` | `ncrb_vellore_2024_q1.csv` |
| `{source}_{city}_clean.csv` | `vellore_crime_clean.csv` |
| `{source}_{city}_final.csv` | `vellore_crime_final.csv` |

---

## 4. Column Definitions

### 4.1 Final Dataset Schema (`vellore_crime_final.csv`)

| # | Column Name | Data Type | Description | Required |
|---|---|---|---|---|
| 1 | `incident_id` | `STRING (UUID)` | Globally unique identifier for the crime incident | Yes |
| 2 | `source` | `STRING` | Origin of the record (`ncrb`, `police`, `news`, `government`) | Yes |
| 3 | `crime_category` | `STRING` | High-level category from standardised taxonomy | Yes |
| 4 | `crime_subcategory` | `STRING` | Specific crime type within the category | Yes |
| 5 | `incident_date` | `DATE (YYYY-MM-DD)` | Date when the incident occurred | Yes |
| 6 | `incident_time` | `TIME (HH:MM:SS)` | Time of the incident (if available, else `00:00:00`) | No |
| 7 | `latitude` | `FLOAT (8 bytes)` | Geocoded latitude in WGS84 coordinate system | Yes |
| 8 | `longitude` | `FLOAT (8 bytes)` | Geocoded longitude in WGS84 coordinate system | Yes |
| 9 | `address` | `STRING` | Street address or location description | No |
| 10 | `city` | `STRING` | City or town where the incident occurred | Yes |
| 11 | `district` | `STRING` | Administrative district | Yes |
| 12 | `state` | `STRING` | State or union territory | Yes |
| 13 | `pincode` | `STRING (6 digits)` | Postal code of the incident location | No |
| 14 | `landmark` | `STRING` | Nearby landmark for spatial reference | No |
| 15 | `victim_count` | `INTEGER` | Number of victims involved | No |
| 16 | `suspect_count` | `INTEGER` | Number of suspects involved | No |
| 17 | `weapon_used` | `BOOLEAN` | Whether a weapon was used (`TRUE`/`FALSE`) | No |
| 18 | `property_value_loss` | `FLOAT` | Estimated value of property lost in INR | No |
| 19 | `day_of_week` | `STRING` | Derived: day name (Monday–Sunday) | Yes |
| 20 | `hour_of_day` | `INTEGER (0–23)` | Derived: hour when the incident occurred | Yes |
| 21 | `month` | `INTEGER (1–12)` | Derived: month of the incident | Yes |
| 22 | `season` | `STRING` | Derived: `Summer`, `Monsoon`, `Post-Monsoon`, `Winter` | Yes |
| 23 | `is_weekend` | `BOOLEAN` | Derived: `TRUE` if Saturday or Sunday | Yes |
| 24 | `geo_cluster_id` | `INTEGER` | Derived: cluster/zone identifier from spatial clustering | No |
| 25 | `crime_density_score` | `FLOAT (0.0–1.0)` | Derived: normalised crime density for the zone | No |
| 26 | `ingestion_timestamp` | `DATETIME` | When the record was ingested into the system | Yes |

---

## 5. Data Types Summary

| Type | Usage |
|---|---|
| `STRING` | Text fields (addresses, categories, names) |
| `STRING (UUID)` | Unique identifiers following RFC 4122 format |
| `DATE` | Calendar date in ISO 8601 format (`YYYY-MM-DD`) |
| `TIME` | Time of day in 24-hour format (`HH:MM:SS`) |
| `DATETIME` | Combined date and timestamp (`YYYY-MM-DD HH:MM:SS`) |
| `FLOAT` | 64-bit floating point for coordinates and numeric measures |
| `INTEGER` | 32-bit signed integer for counts and indices |
| `BOOLEAN` | Logical `TRUE`/`FALSE` values |

---

## 6. Allowed Values

### 6.1 Crime Categories

| Category | Subcategories |
|---|---|
| `Theft` | Pickpocketing, Shoplifting, Bicycle Theft, General Theft |
| `Robbery` | Armed Robbery, Street Robbery, Carjacking |
| `Burglary` | Home Burglary, Commercial Burglary, Attempted Burglary |
| `Assault` | Simple Assault, Aggravated Assault, Assault on Women |
| `Murder` | Premeditated Murder, Culpable Homicide |
| `Kidnapping` | Kidnapping for Ransom, Abduction, Missing Person |
| `Fraud` | Financial Fraud, Insurance Fraud, Impersonation |
| `Cyber Crime` | Hacking, Phishing, Identity Theft, Online Harassment |
| `Vehicle Theft` | Two-wheeler Theft, Four-wheeler Theft, Auto Theft |
| `Drug Offence` | Possession, Trafficking, Manufacturing |
| `Domestic Violence` | Physical Abuse, Emotional Abuse, Dowry Harassment |
| `Harassment` | Street Harassment, Stalking, Threats |
| `Chain Snatching` | Gold Chain Snatching, Purse Snatching |
| `Vandalism` | Property Damage, Graffiti, Public Property Damage |

### 6.2 Geographical Values

| Field | Values |
|---|---|
| `city` | Vellore, Chennai, Bangalore, Hyderabad |
| `state` | Tamil Nadu, Karnataka, Telangana |
| `latitude` | 8.0°N – 18.0°N (South India bounding box) |
| `longitude` | 76.0°E – 81.0°E (South India bounding box) |

### 6.3 Derived Values

| Field | Allowed Values |
|---|---|
| `day_of_week` | Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday |
| `hour_of_day` | 0–23 (integer) |
| `month` | 1–12 (integer, January = 1) |
| `season` | Summer (Mar–May), Monsoon (Jun–Sep), Post-Monsoon (Oct–Nov), Winter (Dec–Feb) |
| `is_weekend` | TRUE, FALSE |

---

## 7. Example Records

```csv
incident_id,source,crime_category,crime_subcategory,incident_date,incident_time,latitude,longitude,address,city,district,state,pincode,landmark,victim_count,suspect_count,weapon_used,property_value_loss,day_of_week,hour_of_day,month,season,is_weekend,geo_cluster_id,crime_density_score,ingestion_timestamp
a1b2c3d4-1234-5678-9abc-def012345678,police,Theft,Pickpocketing,2024-03-15,14:30:00,12.9165,79.1325,Gandhi Nagar Main Road,Vellore,Vellore,Tamil Nadu,632006,Gandhi Statue,1,1,FALSE,5000.0,Friday,14,3,Summer,FALSE,5,0.73,2024-03-15 18:00:00
e5f6g7h8-9012-3456-789a-bcdef0123456,ncrb,Robbery,Armed Robbery,2024-06-22,21:15:00,12.9200,79.1450,Kosappet Road,Vellore,Vellore,Tamil Nadu,632004,Old Bus Stand,2,3,TRUE,25000.0,Saturday,21,6,Monsoon,TRUE,3,0.89,2024-06-22 23:45:00
i9j0k1l2-3456-789a-bcde-f0123456789a,news,Assault,Aggravated Assault,2024-09-10,19:45:00,12.9100,79.1200,Katpadi Junction,Vellore,Vellore,Tamil Nadu,632007,Railway Station,1,2,TRUE,0.0,Tuesday,19,9,Post-Monsoon,FALSE,2,0.65,2024-09-11 08:30:00
```

---

## 8. Data Validation Rules

### 8.1 Field-Level Rules

| Field | Validation Rule |
|---|---|
| `incident_id` | Must be a valid UUID v4 string; must be unique across the dataset |
| `latitude` | Range: 8.0 to 18.0 (decimal degrees) |
| `longitude` | Range: 76.0 to 81.0 (decimal degrees) |
| `incident_date` | Must not be a future date; format must be `YYYY-MM-DD` |
| `incident_time` | Must be in `HH:MM:SS` 24-hour format (or `00:00:00` if unknown) |
| `pincode` | Exactly 6 digits; must match Indian postal code format |
| `victim_count` | Must be >= 0 |
| `suspect_count` | Must be >= 0 |
| `property_value_loss` | Must be >= 0 (0 if not applicable) |
| `crime_density_score` | Must be between 0.0 and 1.0 inclusive |
| `city` | Must belong to the predefined list of supported cities |
| `state` | Must belong to recognised Indian states/UTs |
| `day_of_week` | Must match the actual day computed from `incident_date` |

### 8.2 Cross-Field Rules

| Rule | Description |
|---|---|
| Date-Day Consistency | `day_of_week` must match the actual day computed from `incident_date` |
| Geo Boundaries | `latitude` and `longitude` must fall within the bounding box of the declared `city` and `state` |
| Source Integrity | Records from `ncrb` source must not appear in `news` source partition |

### 8.3 Record-Level Rules

| Rule | Description |
|---|---|
| Completeness | `incident_id`, `source`, `crime_category`, `incident_date`, `latitude`, `longitude`, `city`, `state`, `day_of_week`, `hour_of_day`, `month`, `season`, `is_weekend` must never be null |
| Uniqueness | No two records may share the same `incident_id` |

---

## 9. Naming Conventions

| Artifact | Convention | Example |
|---|---|---|
| Column names | `snake_case` (lowercase with underscores) | `incident_date`, `crime_category` |
| CSV files | `{stage}_{city}_{descriptor}.csv` | `raw_vellore_2024.csv` |
| Directories | Lowercase, single word | `government/`, `processed/` |
| Crime categories | `Pascal Case` with spaces | `Cyber Crime`, `Drug Offence` |
| Derived features | Prefix `is_` for booleans, descriptive name for others | `is_weekend`, `crime_density_score` |

---

## 10. Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-07-28 | Data Engineering Team | Initial release. Defines schema for Vellore dataset with 26 columns. Includes raw → processed → final pipeline stages. |

---

*End of Data Dictionary*