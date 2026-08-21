# Crime Categories — Standardised Taxonomy

> **Project:** AI-Powered Crime Hotspot Analysis and Proximity Alert System  
> **Version:** 1.0  
> **Last Updated:** 2026-07-28

---

## Overview

This document defines the standardised crime category taxonomy used across the Crime Analysis project. Every crime incident in the dataset is classified into exactly one category and one subcategory. This taxonomy ensures consistency across data sources, enables accurate aggregation, and provides meaningful labels for machine learning models.

---

## Category Definitions

### 1. Theft

| Attribute | Value |
|---|---|
| **Category ID** | `theft` |
| **Severity** | Medium |
| **Common Subcategories** | Pickpocketing, Shoplifting, Bicycle Theft, General Theft, Luggage Theft |
| **Description** | The unlawful taking of property without force or threat against the victim. Theft does not involve direct confrontation. It is a crime of opportunity where the victim is often unaware at the time of the incident. |
| **Example** | A mobile phone is stolen from an unattended bag at a bus stop. |
| **Typical Locations** | Markets, bus stands, railway stations, crowded public areas |

---

### 2. Robbery

| Attribute | Value |
|---|---|
| **Category ID** | `robbery` |
| **Severity** | High |
| **Common Subcategories** | Armed Robbery, Street Robbery, Carjacking, Bank Robbery |
| **Description** | The unlawful taking of property from a person through force, threat, or intimidation. Unlike theft, robbery involves direct confrontation with the victim. When a weapon is involved, it is classified as armed robbery. |
| **Example** | A person is threatened at knifepoint and forced to hand over their wallet. |
| **Typical Locations** | Streets, ATMs, parking lots, isolated pathways |

---

### 3. Burglary

| Attribute | Value |
|---|---|
| **Category ID** | `burglary` |
| **Severity** | Medium–High |
| **Common Subcategories** | Home Burglary, Commercial Burglary, Attempted Burglary, Night-time Burglary |
| **Description** | The unlawful entry into a building or structure with the intent to commit theft or another crime. Burglary does not require confrontation — the property is typically unoccupied when the crime occurs. |
| **Example** | A house is broken into during the day while the residents are at work. |
| **Typical Locations** | Residential areas, commercial districts, standalone houses |

---

### 4. Assault

| Attribute | Value |
|---|---|
| **Category ID** | `assault` |
| **Severity** | High |
| **Common Subcategories** | Simple Assault, Aggravated Assault, Assault on Women, Assault on Public Servant |
| **Description** | An intentional act that causes physical harm or the reasonable apprehension of immediate harm to another person. Aggravated assault involves a weapon or results in serious bodily injury. |
| **Example** | A person is physically attacked and beaten during a road rage incident. |
| **Typical Locations** | Streets, public spaces, entertainment venues, residential areas |

---

### 5. Murder

| Attribute | Value |
|---|---|
| **Category ID** | `murder` |
| **Severity** | Critical |
| **Common Subcategories** | Premeditated Murder, Culpable Homicide, Honour Killing, Dowry Death |
| **Description** | The unlawful and intentional killing of one person by another. Premeditated murder involves planning and intent, while culpable homicide may occur without premeditation but with the intent to cause harm. |
| **Example** | A person is fatally stabbed during a property dispute. |
| **Typical Locations** | Residential areas, isolated locations, conflict-prone zones |

---

### 6. Kidnapping

| Attribute | Value |
|---|---|
| **Category ID** | `kidnapping` |
| **Severity** | Critical |
| **Common Subcategories** | Kidnapping for Ransom, Abduction, Missing Person, Child Abduction |
| **Description** | The unlawful seizure, confinement, or transportation of a person against their will. Kidnapping may be motivated by ransom, political demands, or personal vendettas. |
| **Example** | A child is abducted from a school playground. |
| **Typical Locations** | School zones, playgrounds, residential areas, transit hubs |

---

### 7. Fraud

| Attribute | Value |
|---|---|
| **Category ID** | `fraud` |
| **Severity** | Medium |
| **Common Subcategories** | Financial Fraud, Insurance Fraud, Impersonation, Cheating, Online Scam |
| **Description** | Wrongful or criminal deception intended to result in financial or personal gain. Fraud involves misrepresentation, concealment, or breach of trust. |
| **Example** | A person receives a phone call from someone impersonating a bank official and is tricked into sharing OTP details. |
| **Typical Locations** | Banks, financial institutions, online platforms, phone networks |

---

### 8. Cyber Crime

| Attribute | Value |
|---|---|
| **Category ID** | `cyber_crime` |
| **Severity** | Medium–High |
| **Common Subcategories** | Hacking, Phishing, Identity Theft, Online Harassment, Cyber Stalking, Data Breach |
| **Description** | Criminal activities carried out using computers, networks, or the internet. Cyber crime ranges from financial fraud to harassment and data theft. |
| **Example** | A hacker gains unauthorised access to a social media account and posts malicious content. |
| **Typical Locations** | Online platforms, social media, email, banking portals |

---

### 9. Vehicle Theft

| Attribute | Value |
|---|---|
| **Category ID** | `vehicle_theft` |
| **Severity** | Medium |
| **Common Subcategories** | Two-wheeler Theft, Four-wheeler Theft, Auto Rickshaw Theft, Bicycle Theft |
| **Description** | The theft or attempted theft of a motor vehicle, motorcycle, or bicycle. Vehicle theft is often linked to organised crime and cross-border smuggling. |
| **Example** | A motorcycle parked outside a shopping mall is stolen. |
| **Typical Locations** | Parking lots, streets, residential areas, commercial zones |

---

### 10. Drug Offence

| Attribute | Value |
|---|---|
| **Category ID** | `drug_offence` |
| **Severity** | High |
| **Common Subcategories** | Drug Possession, Drug Trafficking, Drug Manufacturing, Consumption |
| **Description** | Offences related to the possession, sale, transportation, or manufacture of controlled substances. Severity depends on the quantity and type of substance involved. |
| **Example** | A person is found in possession of 100 grams of cannabis during a routine vehicle check. |
| **Typical Locations** | Nightlife districts, border areas, college zones, transit points |

---

### 11. Domestic Violence

| Attribute | Value |
|---|---|
| **Category ID** | `domestic_violence` |
| **Severity** | High |
| **Common Subcategories** | Physical Abuse, Emotional Abuse, Dowry Harassment, Marital Rape |
| **Description** | Violent or aggressive behaviour within a domestic setting, typically involving family members or intimate partners. Includes physical, emotional, sexual, and economic abuse. |
| **Example** | A spouse is physically assaulted and verbally threatened at home. |
| **Typical Locations** | Private residences |

---

### 12. Harassment

| Attribute | Value |
|---|---|
| **Category ID** | `harassment` |
| **Severity** | Medium |
| **Common Subcategories** | Street Harassment, Stalking, Threats, Intimidation, Workplace Harassment |
| **Description** | Unwanted behaviour that annoys, threatens, or intimidates a person. Harassment may be verbal, physical, or digital and often targets individuals based on gender, caste, or religion. |
| **Example** | A woman is repeatedly followed and verbally harassed on her way to work. |
| **Typical Locations** | Streets, public transport, workplaces, online platforms |

---

### 13. Chain Snatching

| Attribute | Value |
|---|---|
| **Category ID** | `chain_snatching` |
| **Severity** | Medium–High |
| **Common Subcategories** | Gold Chain Snatching, Purse Snatching, Necklace Snatching |
| **Description** | A specific form of street robbery where valuables (especially gold jewellery) are snatched from the victim, often by perpetrators on motorcycles. Common in Indian cities. |
| **Example** | Two men on a motorcycle snatch a gold chain from a woman walking on the roadside and flee. |
| **Typical Locations** | Roadsides, market areas, residential streets, temple premises |

---

### 14. Vandalism

| Attribute | Value |
|---|---|
| **Category ID** | `vandalism` |
| **Severity** | Low–Medium |
| **Common Subcategories** | Property Damage, Graffiti, Public Property Damage, Vehicle Vandalism |
| **Description** | The deliberate destruction or damage of public or private property. Vandalism is often motivated by protest, mischief, or gang activity. |
| **Example** | Windows of a government building are smashed during a protest. |
| **Typical Locations** | Public buildings, parks, streets, schools, transit stations |

---

## Category Hierarchy

```
All Crimes
├── Violent Crimes
│   ├── Murder
│   ├── Assault
│   ├── Robbery
│   ├── Kidnapping
│   └── Domestic Violence
├── Property Crimes
│   ├── Theft
│   ├── Burglary
│   ├── Vehicle Theft
│   ├── Chain Snatching
│   └── Vandalism
├── Cyber Crimes
│   └── Cyber Crime
├── White Collar Crimes
│   └── Fraud
├── Drug Related
│   └── Drug Offence
└── Public Order
    └── Harassment
```

---

## Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-07-28 | Data Engineering Team | Initial taxonomy with 14 categories and hierarchy |

---

*End of Crime Categories*