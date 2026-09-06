# Data Sources — Crime Analysis

> **Project:** AI-Powered Crime Hotspot Analysis and Proximity Alert System  
> **Version:** 1.0  
> **Last Updated:** 2026-07-28

---

## Overview

This document catalogues all data sources used to build the crime analysis dataset. Sources are classified by type (government, police, news, open data) and evaluated for their purpose, data type, advantages, and limitations. Understanding each source's strengths and weaknesses is essential for data quality assessment and model reliability.

---

## Section 1: Government Datasets

### 1.1 National Crime Records Bureau (NCRB)

| Attribute | Description |
|---|---|
| **Purpose** | Primary source of official crime statistics in India. NCRB publishes annual "Crime in India" reports with state-wise and district-wise crime data. |
| **Data Type** | Aggregated statistical tables (CSV/PDF). Incident counts by crime category, city, and time period. |
| **Advantages** | Authoritative and government-verified data. Consistent reporting methodology across years. Covers all 36 states and union territories. Includes detailed classification across IPC and SLL sections. |
| **Limitations** | Published annually with a 1–2 year lag. Data is aggregated at the district level — no precise geocodes or timestamps for individual incidents. Under-reporting is a known issue. Does not capture incidents that go unreported to police. |

### 1.2 Tamil Nadu Police Department

| Attribute | Description |
|---|---|
| **Purpose** | State-level crime records with FIR-level detail for Tamil Nadu districts, including Vellore. |
| **Data Type** | FIR records, incident logs, and monthly crime statistics (structured CSV/JSON). |
| **Advantages** | More granular than NCRB data. Includes specific location descriptions, time of incident, and case status. Shorter publication lag (quarterly updates). |
| **Limitations** | Coverage limited to Tamil Nadu. Data format may vary between districts. FIR text is in Tamil and English — requires bilingual processing. Manual data entry can introduce typographical errors. |

### 1.3 Vellore District Administration

| Attribute | Description |
|---|---|
| **Purpose** | Local government records specific to Vellore district, including municipal corporation crime data and ward-level incident summaries. |
| **Data Type** | Ward-level crime logs, monthly reports, and administrative records (PDF/Excel). |
| **Advantages** | Highest geographic granularity at the ward/zone level. Includes local context such as festival seasons and market days. |
| **Limitations** | Not consistently digitised. Some records are in scanned PDF format requiring OCR. No standardised schema across different administrative units. |

---

## Section 2: Open Data Portals

### 2.1 Data.gov.in (Open Government Data Platform India)

| Attribute | Description |
|---|---|
| **Purpose** | Central repository for open government datasets published by Indian ministries and departments. |
| **Data Type** | Structured datasets (CSV, JSON, XML) covering crime statistics, census data, and demographic information. |
| **Advantages** | Centralised access to hundreds of datasets. Machine-readable formats. API access available. Creative Commons licensing for non-commercial use. |
| **Limitations** | Variable data quality and update frequency. Some datasets are incomplete or contain missing values. API rate limits apply. Requires registration for bulk downloads. |

### 2.2 Tamil Nadu Open Data Portal

| Attribute | Description |
|---|---|
| **Purpose** | State-level open data initiative publishing datasets from Tamil Nadu government departments. |
| **Data Type** | District-wise crime statistics, police station boundaries, demographic data (CSV, GeoJSON). |
| **Advantages** | State-specific data with higher resolution than national datasets. Includes GIS boundary files for spatial analysis. Regularly updated. |
| **Limitations** | Smaller catalogue compared to the national portal. Historical data may be limited. Some datasets require manual download. |

### 2.3 India Census Data (Office of the Registrar General)

| Attribute | Description |
|---|---|
| **Purpose** | Population and demographic data used for normalising crime rates per capita. |
| **Data Type** | Census tables (CSV) with population, literacy, employment, and housing data at the district and town level. |
| **Advantages** | Comprehensive and reliable. Conducted decennially with full enumeration. Essential for rate-based analysis (crimes per 100,000 population). |
| **Limitations** | Updated only once every 10 years (latest: 2011, next: 2021 delayed). Does not reflect rapid urbanisation changes within the decade. |

---

## Section 3: News Sources

### 3.1 The Hindu — Tamil Nadu Edition

| Attribute | Description |
|---|---|
| **Purpose** | English-language newspaper with dedicated coverage of crime incidents in Vellore and surrounding districts. |
| **Data Type** | News articles (HTML/text) containing descriptions of crime incidents, locations, and outcomes. |
| **Advantages** | Daily publication — near-real-time incident reporting. Includes location descriptions and context not found in official records. Covers incidents that may not be in police data. |
| **Limitations** | Unstructured text requires NLP extraction. Potential editorial bias — not all incidents are reported. Limited detail for minor crimes. Paywall may restrict archival access. |

### 3.2 Dinamani — Tamil Daily

| Attribute | Description |
|---|---|
| **Purpose** | Tamil-language newspaper with extensive local crime reporting across Tamil Nadu. |
| **Data Type** | News articles (HTML/text) in Tamil language. |
| **Advantages** | Broader coverage of local incidents compared to English newspapers. Includes rural and semi-urban crime reports. Detailed community-level reporting. |
| **Limitations** | Tamil language requires translation and NLP processing. Limited digital archive for older articles. No structured data format. |

### 3.3 Times of India — Vellore/Chennai Edition

| Attribute | Description |
|---|---|
| **Purpose** | Major English-language daily with crime reporting for Tamil Nadu cities. |
| **Data Type** | Online news articles (HTML/text) covering urban crime incidents. |
| **Advantages** | High readership and consistent publishing. Covers a wide range of crime types. Includes follow-up reporting on case outcomes. |
| **Limitations** | Focus on urban areas — rural coverage is sparse. Sensationalism may skew incident reporting. Article volume varies significantly by day. |

### 3.4 The News Minute

| Attribute | Description |
|---|---|
| **Purpose** | Digital news platform with focused reporting on crime, justice, and human rights in South India. |
| **Data Type** | Online articles (HTML/text) with in-depth crime analysis and investigative reports. |
| **Advantages** | Independent journalism with detailed investigative pieces. Covers under-reported crime categories (cyber crime, hate crimes). |
| **Limitations** | Smaller volume of articles. Niche readership — may not cover routine crime incidents. Limited geographic scope. |

---

## Section 4: Current Sources Summary

| Source | Type | Coverage | Update Frequency | Format | Reliability |
|---|---|---|---|---|---|
| NCRB | Government | National | Annual | CSV/PDF | High (official) |
| TN Police | Government | Tamil Nadu | Quarterly | CSV/JSON | High (official) |
| Vellore Admin | Government | Vellore | Monthly | PDF/Excel | Medium |
| Data.gov.in | Open Data | National | Variable | CSV/JSON | Medium |
| TN Open Data | Open Data | Tamil Nadu | Variable | CSV/GeoJSON | Medium |
| Census India | Open Data | National | Decennial | CSV | High |
| The Hindu | News | Tamil Nadu | Daily | HTML/Text | Medium |
| Dinamani | News | Tamil Nadu | Daily | HTML/Text | Medium |
| Times of India | News | Major Cities | Daily | HTML/Text | Medium |
| The News Minute | News | South India | Daily | HTML/Text | Medium |

---

## Section 5: Future Sources (Planned)

### 5.1 Police Station FIR Databases

Direct integration with police station record management systems would provide the most granular and authoritative data. This requires formal Memoranda of Understanding (MoUs) with the Tamil Nadu Police Department.

### 5.2 Community Crime Reporting Platforms

Platforms such as SafeCity and HarassMap allow crowdsourced reporting of incidents. These can complement official data by capturing unreported crimes, particularly gender-based violence and harassment.

### 5.3 Social Media Monitoring

Twitter, Facebook, and local community forums (e.g., Vellore community WhatsApp groups) can provide real-time incident reports. Requires careful ethical consideration, anonymisation, and compliance with data privacy regulations.

### 5.4 RTI (Right to Information) Responses

Formal RTI applications to police stations and government departments can yield specific datasets not available through public channels. This is a manual but legally guaranteed method to access undisclosed crime data.

### 5.5 Satellite Imagery and GIS Layers

Night-time light intensity, land use classification, and road network density from satellite sources (ISRO Bhuvan, NASA VIIRS) can serve as proxy features for urbanisation and crime risk modelling.

---

## Section 6: Data Quality Considerations by Source

| Source | Completeness | Accuracy | Timeliness | Consistency |
|---|---|---|---|---|
| Government | High | High | Low (annual) | High |
| Police | Medium | High | Medium (quarterly) | Medium |
| News | Low | Medium | High (daily) | Low |
| Open Data | Medium | Medium | Variable | Medium |

---

## Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-07-28 | Data Engineering Team | Initial documentation of all data sources |

---

*End of Data Sources*