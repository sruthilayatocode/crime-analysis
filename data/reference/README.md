# Reference Data

This directory contains reference datasets used by the Crime Analysis system. These datasets provide standardized mappings, categories, and structural templates for the application.

---

## Datasets

### 1. `crime_categories.csv`

**Purpose:** Defines standard crime categories with their associated severity levels and risk scores. Used by the ML pipeline and backend to classify and score crime incidents.

**Columns:**

| Column        | Type   | Description                                                        |
|---------------|--------|--------------------------------------------------------------------|
| `crime_type`  | String | Name of the crime category (e.g., Theft, Robbery, Murder)         |
| `severity`    | String | Severity level: `Low`, `Medium`, `High`, or `Critical`            |
| `risk_score`  | Integer | Numeric risk score (2–10) corresponding to the severity level    |

**Populated:** Yes — 15 standard crime categories included (14 core + fallback `Other`).
**Populated:** Yes — 14 standard crime categories included.

**Sample Rows:**

```csv
crime_type,severity,risk_score
Theft,Low,2
Robbery,High,8
Murder,Critical,10
```
```csv
crime_type,severity,risk_score
Theft,Low,2
Robbery,High,8
Assault,High,8
Sexual Assault,Critical,10
Murder,Critical,10
Kidnapping,Critical,10
Fraud,Medium,5
Cyber Crime,Medium,5
Vehicle Theft,Medium,5
Domestic Violence,High,8
Harassment,Medium,5
Drug Offence,High,8
Chain Snatching,Medium,5
Vandalism,Low,2
Other,Medium,5
```

**Note on `Other`:** The `Other` category serves as a fallback for incidents that were not classified into any standard crime type by the upstream classifier or by `scripts/classify_crimes.py`.  Run `scripts/classify_crimes.py` first to re-classify `Other` records via keyword rules before scoring.  Any `Other` records that remain after classification (e.g. wildlife seizures, non-crime news) receive Medium / score 5 as a safe default.

---

### 2. `severity_mapping.csv`

**Purpose:** Maps severity levels to numeric risk scores and display colors. Used by the dashboard and alert system for visual representation of crime severity.

**Columns:**

| Column       | Type    | Description                                              |
|--------------|---------|----------------------------------------------------------|
| `severity`   | String  | Severity level: `Low`, `Medium`, `High`, `Critical`     |
| `risk_score` | Integer | Numeric risk score (2, 5, 8, 10)                        |
| `color`      | String  | Display color for UI/dashboard (Green, Yellow, Orange, Red) |

**Populated:** Yes — 4 severity levels included.

**Full Contents:**

```csv
severity,risk_score,color
Low,2,Green
Medium,5,Yellow
High,8,Orange
Critical,10,Red
```

---

### 3. `vellore_localities.csv`

**Purpose:** Reference template for Vellore city localities/neighborhoods. Used for geospatial analysis, crime hotspot mapping, and locality-based crime statistics.

**Columns:**

| Column              | Type    | Description                                                        |
|---------------------|---------|--------------------------------------------------------------------|
| `locality_id`       | String  | Unique identifier for the locality                                 |
| `locality_name`     | String  | Name of the locality/neighborhood                                 |
| `zone`              | String  | Zone/region within the city (e.g., North, South, Central)         |
| `latitude`          | Float   | Geographic latitude coordinate                                    |
| `longitude`         | Float   | Geographic longitude coordinate                                   |
| `population_density`| Integer | Population density of the locality (people per sq. km)           |

**Populated:** No — structure only with 3 example rows (clearly marked with `EXAMPLE_` prefix).

> ⚠️ **Note:** Example rows contain placeholder data. Replace with real locality data sourced from official government records or verified geocoding services. Do not use fabricated location coordinates.

**Sample Rows:**

```csv
locality_id,locality_name,zone,latitude,longitude,population_density
EXAMPLE_001,Example Locality 1 (Replace with Real Data),North,,,,
EXAMPLE_002,Example Locality 2 (Replace with Real Data),South,,,,
EXAMPLE_003,Example Locality 3 (Replace with Real Data),Central,,,,
```

---

### 4. `vellore_police_stations.csv`

**Purpose:** Reference template for Vellore police stations. Used for proximity alerts, jurisdiction mapping, and nearest-station calculations in the IoT and backend modules.

**Columns:**

| Column         | Type   | Description                                                        |
|----------------|--------|--------------------------------------------------------------------|
| `station_id`   | String | Unique identifier for the police station                           |
| `station_name` | String | Name of the police station                                         |
| `address`      | String | Physical address of the station                                   |
| `latitude`     | Float  | Geographic latitude coordinate                                    |
| `longitude`    | Float  | Geographic longitude coordinate                                    |
| `jurisdiction` | String | Area/zone under the station's jurisdiction                         |

**Populated:** No — structure only with 2 example rows (clearly marked with `EXAMPLE_` prefix).

> ⚠️ **Note:** Example rows contain placeholder data. Replace with real police station data sourced from official law enforcement records or verified government sources. Do not use fabricated location coordinates.

**Sample Rows:**

```csv
station_id,station_name,address,latitude,longitude,jurisdiction
EXAMPLE_001,Example Police Station 1 (Replace with Real Data),,,,Example Zone 1
EXAMPLE_002,Example Police Station 2 (Replace with Real Data),,,,Example Zone 2
```

---

## Usage Guidelines

1. **Do not fabricate location data.** All latitude/longitude values must come from verified sources (e.g., Google Maps Geocoding API, OpenStreetMap Nominatim, or official government GIS data).

2. **Maintain consistency.** The `severity` and `risk_score` values in `crime_categories.csv` must align with the mappings defined in `severity_mapping.csv`.

3. **Example rows are placeholders.** Rows prefixed with `EXAMPLE_` in `vellore_localities.csv` and `vellore_police_stations.csv` should be replaced with real data before use in production.

4. **Encoding:** All CSV files use UTF-8 encoding with comma (`,`) as the delimiter.

5. **Updates:** When updating reference data, ensure downstream consumers (ML pipeline, backend API, dashboard) are tested for compatibility.

---

## Data Sources (Recommended)

For populating real data in the locality and police station files, consider:

- **Vellore City Municipal Corporation** — official locality/ward boundaries
- **Tamil Nadu Police** — official police station directory
- **Google Maps Geocoding API** — for latitude/longitude coordinates
- **OpenStreetMap Nominatim** — free/open geocoding alternative
- **Census of India** — for population density data