# CrimeSense: A Unified Crime Hotspot Visualization, Zone Classification and Personal Safety Platform with Pattern Recurrence Analysis for Vellore, India

**Authors:**  
- **Sruthilaya J D** (24MID0184) – School of Computer Science and Engineering, Vellore Institute of Technology, Vellore, Tamil Nadu, India  
- **Mahithaa R** (24MID0239) – School of Computer Science and Engineering, Vellore Institute of Technology, Vellore, Tamil Nadu, India  
- **Sujeetha S** (24MID0163) – School of Computer Science and Engineering, Vellore Institute of Technology, Vellore, Tamil Nadu, India  

**Target Venue:** IEEE Conference on Computing, Communications and Cyber-Security
**Format:** IEEE Two-Column Conference Style

---

## Abstract:
This study presents CrimeSense, a system designed to help users explore crime reports in Vellore and examine reported incidents around a selected location. The current system uses an SQLite database containing 596 news-derived incident records and includes an administrative dashboard for viewing and managing these records. The paper presents an interpretable zone classification model that marks locations green, yellow, or red using spatial and temporal decay. To support pedestrian safety, design specifications are formulated for a pre-visit destination advisory, an OpenStreetMap-based safe haven finder relying on natural surveillance, and an automated red-zone inactivity state machine. In addition, a pattern recurrence formulation applying Knox space-time permutation tests and association rules is described to identify sequential crime trends. Finally, database verification audits, role-separated authentication checks, and privacy safeguards conforming to the Indian Digital Personal Data Protection Act are reported, followed by a formal evaluation protocol.

**Keywords:** crime hotspot visualization, zone classification, near repeat analysis, personal safety application, SOS alerting, news derived crime data, safe haven finder, spatio-temporal risk.

---

## I. INTRODUCTION

Crime is not spread evenly across a city. It clusters on certain streets, dark alleys, and crowded transit hubs [1]. Criminologists have documented this phenomenon for decades [2], [3]. The routine activity perspective shows that predatory offenses happen when a motivated offender encounters a vulnerable target without a capable guardian [3]. In addition, crime pattern theory explains that criminals look for targets along the daily routes they travel between home, work, and recreational spots [4]. Police departments routinely use computer-generated hotspot maps to assign patrol cars to these problem corners [5], [6].

Even so, a student or night-shift worker walking alone through Vellore cannot benefit from any of this police data. There are two straightforward reasons for this gap. First, official crime statistics in India are gathered for administrative record-keeping rather than public awareness. The National Crime Records Bureau publishes district totals [7], but those reports aggregate data across entire years and wide regions. They cannot tell someone whether Katpadi railway junction or Bagayam bus stop has a recent history of chain snatchings after 9 PM. Second, existing civilian safety applications are purely reactive [8]. Most commercial tools offer a red SOS button or listen for handset shakes. If someone is surprised, cornered, or physically pinned down, they cannot unlock their screen to tap a button anyway. Worse, these apps possess zero knowledge about whether the user is standing in a quiet residential lane or a recognized danger spot.

To address these gaps, a prototype was developed that connects a news-derived crime database to an administrative dashboard and a proposed set of resident-facing safety features. Because city police stations in Tamil Nadu do not provide open API feeds of daily First Information Reports, the dataset was constructed from regional digital news coverage, following data collection practices established in earlier spatial research [9], [10] while accounting for journalistic reporting biases [11]. Two interfaces were constructed over this shared data layer. The administrative console provides spatial heatmaps, DBSCAN cluster grouping, multi-year charts, user account controls, and emergency alert tables. The proposed resident web interface is designed with an address search bar, a three-color safety badge (green, yellow, or red), an SOS dispatch button, saved places, and privacy switches.

In this paper, fully verified software components are carefully differentiated from theoretical modules undergoing validation. Section III presents the system architecture. Section IV reports the current verification status across all components. Section V analyzes the 596-record empirical dataset. Section VI sets out an open evaluation protocol, and Section VII examines ethical implications, data limitations, and privacy compliance. The primary contributions are:
•  A multi-tier architecture linking a 596-record news-derived SQLite database with an administrative GIS console and proposed citizen mobile views.
•  A transparent spatio-temporal zone classification model that explains local evidence clearly rather than issuing opaque risk scores or declaring any place completely safe.
•  A pattern recurrence formulation combining Knox space-time permutation tests and association rules to detect repeating crime sequences.
•  A safe haven ranking formulation that evaluates candidate public shelters by operational status, distance, institutional guardianship weight, and surrounding crime exposure.
•  An automated emergency escalation state machine design that detects prolonged inactivity within designated high-risk zones.
•  A documented verification report of the active SQLite database (596 sourced records across 11 tables) and an empirical testing protocol for unvalidated modules.

---

## II. RELATED WORK

### A. Crime Concentration and Hotspot Mapping
Criminological studies show that urban offences cluster in micro-locations [1], [2]. Analysts visualize these clusters as point maps, grid aggregations, or kernel density surfaces [5], [12], with time-decay weighting improving short-term forecast accuracy [13]. Density-based clustering algorithms such as DBSCAN [14] discover clusters of arbitrary shapes without imposing rigid spatial grids, treating isolated records as noise. Systematic trials show that deploying police patrols to verified hotspots reduces local crime [6]. Nevertheless, these tools remain confined to police control rooms and do not assist a pedestrian navigating a dark road.

### B. Spatial Forecasting and Risk Terrain Modeling
Point process models borrow concepts from seismology to describe how a crime event locally inflates the temporary rate of nearby offences [15]. Risk terrain modeling connects spatial risk to fixed urban features like transit terminals, liquor stores, and poorly lit alleys [16], with meta-analyses confirming its utility in predicting elevated risk areas [17]. Broader reviews of spatial forecasting [18] and machine learning models [19], [20] emphasize that most published approaches assume access to detailed police dispatch registers. Such feeds do not exist in the public domain in India. For this reason, CrimeSense relies on an interpretable weighted severity formula, keeping complex machine learning models for subsequent held-out empirical evaluations.

### C. Repeat and Near-Repeat Victimization
The near-repeat hypothesis states that when an offence occurs, nearby locations experience a temporary surge in victimization risk [21]. Applying the Knox space-time interaction test to residential burglary demonstrated that broken-into houses and their immediate neighbors face heightened vulnerability over subsequent days [22], [23]. Prior studies present these findings exclusively in research papers or police reports. To date, consumer mobile tools that translate near-repeat findings into real-time safety guidance for citizens remain absent.

### D. News-Derived Crime Data and Geocoding
When official CAD records are withheld, digital news archives and social feeds offer valuable alternative records of urban incidents [9], [10]. While newspaper archives contain rich contextual narratives, they inevitably reflect editorial priorities and reporting biases [11]. In addition, mapping descriptive locality names to geographic coordinates introduces spatial uncertainty [24], requiring systems to report coordinate confidence explicitly [25]. These caveats are incorporated directly into the system design and error warnings.

### E. Safe Routing and Environmental Guardianship
Urban routing researchers often formulate safe travel as a bi-objective graph problem trading travel distance against cumulative crime exposure [26]. CrimeSense approaches pedestrian vulnerability differently: rather than generating long detours, the system evaluates single travel destinations, directs uneasy pedestrians to immediate safe havens, and triggers automated alerts when users are trapped. The safe haven concept draws on Jane Jacobs' principle of natural surveillance, which demonstrates that busy commercial streets with active staff are protected by informal 'eyes on the street' [27]. Oscar Newman's defensible space theory similarly showed that regular human activity strengthens territorial stewardship [28]. Candidate safe havens can be queried from OpenStreetMap [29]. Finally, spatial risk systems must guard against amplifying social biases [30], [31], [32], which the proposed design addresses through non-pejorative language and strict opt-in controls.

---

## III. SYSTEM DESIGN

### A. Architecture Overview
CrimeSense is organized as a decoupled multi-tier web system containing a client presentation tier, an API routing tier, an application service tier, an SQLite database, and an offline ingestion pipeline (Fig. 1). The client tier deploys two separate responsive interfaces from a single codebase: a mobile resident app and a desktop administrative console. Both communicate over HTTPS with a Flask REST API that verifies user roles, inspects Google OAuth tokens, and logs sensitive management queries. All modules read and write to an authoritative SQLite database running with Write Ahead Logging enabled.

### B. Data Acquisition, Schema, and Role Separation
Incident records are curated from digital news reports. An offline processing script normalizes crime categories, discards duplicate articles, geocodes named localities, assigns severity ratings, and exports records to SQLite. Fig. 2 illustrates this end-to-end processing pipeline. Records whose locality cannot be resolved to coordinates are not discarded; instead, they are carried forward with an explicit uncertainty flag in the location_confidence column. The crimes table preserves source URLs, geocoding confidence levels, and location source tags to ensure complete provenance. Administrator entered incidents write to the same table and generate audit entries.

The remaining tables store user accounts and related personal records. User rows store names, verified emails, password hashes, optional Google identifiers, roles, and status flags. User settings, emergency contacts, saved locations, location heartbeats, red zone monitoring states, and SOS alerts link to user accounts via foreign keys. Middleware checks ensure residents only query their own data, while administrator routes reject unprivileged callers.

### C. Zone Classification (Green, Yellow, Red)
The zone service calculates crime exposure for a query coordinate q (GPS fix, search address, or manual coordinate input). An initial bounding box filter narrows candidate incidents, followed by great circle distance calculation via the Haversine equation [33]:
$$d = 2R \arcsin \sqrt{ \sin^2(\Delta\phi/2) + \cos\phi_1 \cos\phi_2 \sin^2(\Delta\lambda/2) }$$
with Earth radius $R = 6371\,\text{km}$. For incidents within search radius $\rho$, each record $i$ contributes based on severity score $s_i$, distance $d_i$, and age $a_i$. Raw risk is calculated as:
$$R(q) = \sum_{i \in N(q)} s_i \cdot \delta(d_i) \cdot w(a_i), \quad \delta(d) = 1 - d/\rho$$
where $w(a)$ is a step-down weight based on record age ($1.0$ for $\le 6$ months, $0.7$ for $6\text{--}24$ months, and $0.4$ for $> 24$ months). The resulting raw risk is bounded by saturation constant $R_{\text{ref}}$:
$$Z(q) = \min\{100, 100 \cdot R(q) / R_{\text{ref}}\}$$
and mapped into three operational safety tiers:
•  **Green Zone:** $Z(q) < 30$
•  **Yellow Zone:** $30 \le Z(q) < 60$
•  **Red Zone:** $Z(q) \ge 60$

When no incidents exist within radius $\rho$, the system returns green with an explicit low data confidence warning, ensuring that an absence of news coverage is never misunderstood as guaranteed physical safety.

### D. Safe-Haven Spatial Optimization
When an individual feels unsafe, CrimeSense identifies nearby public social hubs (supermarkets, 24/7 pharmacies, police posts, clinics) where natural surveillance operates. Candidate havens within $2000\,\text{m}$ are ranked by utility score:
$$H(p) = w_c \cdot o(p, t) \cdot \exp(-d_p / \lambda) \cdot (1 - Z_p / 100)$$
where $w_c$ reflects institutional guardianship (Police: 1.0, Hospital: 0.9, Market: 0.7, Pharmacy: 0.65), $o(p, t)$ is opening status, and $Z_p$ penalizes havens located inside crime hotspots.

### E. Pattern-Recurrence Analytics
To examine repeating spatial crime dynamics, CrimeSense defines three complementary analyses:
1. Knox space-time interaction test:
   $$X = \sum_{i < j} \mathbf{1}[d_{ij} \le \Delta s] \cdot \mathbf{1}[|t_i - t_j| \le \Delta t]$$
2. Sequential association rules:
   $$\text{lift}(A \rightarrow B) = \frac{P(B \mid A)}{P(B)}$$
3. Locality recurrence index:
   $$\text{RI}(L, T) = \frac{|\{i \in I(L, T) : \exists j, 0 < t_i - t_j \le \Delta t\}|}{|I(L, T)|}$$

### F. SOS Alerting and Red-Zone Dwell Escalation
Users register between one and five emergency contacts, marking one as primary. The manual SOS button requires a two-second continuous press and provides a five-second cancel window to avoid accidental dispatches.
The automated path monitors silent emergencies: while active in a red zone, if stationary for $T$ minutes ($10\,\text{min}$) without touch interaction, an "Are you safe?" prompt is displayed for 60 seconds. If unanswered, an automated emergency payload is sent to primary contacts with last known coordinates.

---

## IV. IMPLEMENTATION STATUS AND VERIFICATION

System verification executed on 11 October 2026 confirmed:
•  Authoritative Crime Database: 596 sourced records in SQLite (100% verified single source of truth).
•  Data Quality Assurance: 100% valid URLs, coordinates within Tamil Nadu bounds, and standardized ISO dates.
•  User Authentication: PBKDF2 salted passwords and server-side verified Google OAuth 2.0.
•  Admin Dashboard: Live SQL queries for KPIs, charts, and table pagination.
•  Consent-Gated Live Map: Location tracking active only with explicit resident consent, logged in `audit_logs`.
•  Entity Persistence: Verified persistence across `users`, `user_settings`, `sos_contacts`, `saved_locations`, and `sos_events`.

---

## V. DATASET AND CURRENT RESULTS

The database holds 596 verified crime incidents from Vellore and surrounding northern Tamil Nadu districts:
•  General Crime / Public Offence: 277 records ($46.5\%$)
•  Murder & Homicide: 86 records ($14.4\%$)
•  Illegal Contraband, Mining & Smuggling: 46 records ($7.7\%$)
•  Cybercrime, Financial Fraud & Extortion: 28 records ($4.7\%$)
•  Sexual Violence, POCSO & Harassment: 26 records ($4.4\%$)
•  Theft, Burglary & Vehicle Stealing: 22 records ($3.7\%$)
•  Assault, Violent Clash & Riot: 21 records ($3.5\%$)
•  Robbery & Dacoity: 18 records ($3.0\%$)
•  Traffic Fatalities & Hit-and-Run: 72 records ($12.1\%$)

Risk level split:
•  High Risk: 150 records ($25.2\%$)
•  Medium Risk: 138 records ($23.2\%$)
•  Low Risk: 308 records ($51.7\%$)

### Spatial Granularity and Centroid Analysis
Empirical inspection reveals four critical structural characteristics of the dataset:
1. **Locality Centroid Stacking:** Out of 596 records, 469 ($78.7\%$) share the central coordinate pair $(12.9165, 79.1325)$ corresponding to generic 'Vellore' or 'Vellore District' mentions in news reports. Across the entire database, only 25 unique coordinate pairs exist (16 within Vellore district).
2. **Boundary Cliff Artifact:** Because coordinates cluster at centroids, querying within $1000\,\text{m}$ of $(12.9165, 79.1325)$ captures 477 incidents (raw score $> 1900$), instantly saturating the zone score to $100.0$ (Red). Moving just $100\,\text{m}$ beyond ($1100\,\text{m}$ from centroid) drops the incident count to 8 and the score to $10.5$ (Green). The model in its current form acts as a categorical proximity detector to known geocoded locality centroids, rather than a continuous micro-place risk field.
3. **District Distribution:** 552 records ($92.6\%$) belong to Vellore, while 44 records ($7.4\%$) stem from neighboring or regional districts (Chennai 16, Ranipet 13, Tiruvannamalai 5, etc.) and should be explicitly partitioned for pure municipal Vellore modeling.
4. **Saturation Calibration:** In the current prototype, $R_{\text{ref}} = 100$, which clamps raw risk directly. Empirical calibration of $R_{\text{ref}}$ via held-out temporal quantiles (Section VI) is necessary to restore scoring variance across dense zones.

---

## VI. PROPOSED EVALUATION PROTOCOL

Predictive evaluation is formulated on a rolling temporal split using the Predictive Accuracy Index (PAI):
$$\text{PAI} = \frac{n / N}{a / A}$$
Target benchmarks:
•  Zone Model: $\text{PAI} \ge 2.5$ at Red Zone area coverage $\le 10\%$.
•  DBSCAN Hotspots: Stable identification of $\ge 5$ dense urban clusters.
•  Pattern Recurrence: Near-Repeat Ratio $\text{NRR} \ge 1.35$ with permutation $p < 0.01$.
•  Safe-Haven Finder: $\text{Valid@5} \ge 85\%$ accuracy with median walk to open shelter $< 650\,\text{m}$.
•  Automated SOS: Dispatch latency $< 4.5\,\text{s}$ (p95) and zero false alarms during movement.
•  Usability: System Usability Scale $\text{SUS} \ge 78.0$ across $N=30$ local participants.

---

## VII. DISCUSSION, ETHICS, AND THREATS TO VALIDITY

### A. What Is New
Core elements of spatial crime analysis, near repeat testing, safe routing, and emergency alerting possess established research literatures. CrimeSense organizes these concepts around a single shared evidence base. The current database supports the administrative dashboard. The proposed resident advisory, safe-haven finder, and automated red-zone escalation would use the same incident records if implemented and validated. The haven finder and pre-visit advisory are designed to convert spatial data into immediate pedestrian guidance, while dwell escalation aims to address scenarios where victims are physically incapacitated.

### B. Ethics and Non-Stigmatizing Design
Assigning risk labels to urban sectors risks stigmatizing communities and amplifying data biases [30], [31], [32]. CrimeSense mitigates these harms by framing zones objectively as "reported incidents", displaying report counts and source links transparently, avoiding pejorative terms like "unsafe", stating clearly that green zones do not guarantee absolute safety, and excluding automated outputs from punitive policing loops [32]. Confirmation challenges and cooldown timers prevent alert fatigue.

### C. Limitations and Threats to Validity
News sourced datasets reflect journalistic coverage choices, which over represent unusual or severe offenses relative to minor infractions [11]. Locality centroid coordinates limit spatial precision [24], [25]. The severity score table is expert assigned rather than calibrated on longitudinal outcome metrics. OpenStreetMap haven records inherit volunteer mapping variations, and automated browser push notifications depend upon active browser lifecycles and mobile connectivity.

---

## VIII. CONCLUSION AND FUTURE WORK

This study presents CrimeSense, a prototype for visualizing news-reported crime incidents in Vellore. The database structure and selected application functions were verified using 596 records. The resident safety modules and pattern-recurrence methods remain to be evaluated as described in the implementation-status and evaluation sections. Database integrity, authentication, and persistence have been verified, while role enforcement remains partially active. Future work will execute rolling temporal evaluations, refine geocoding resolution, conduct physical safe haven audits, and evaluate user cognitive load through structured field usability trials.

---

## REFERENCES
[1] D. Weisburd, "The law of crime concentration and the criminology of place," *Criminology*, vol. 53, no. 2, pp. 133–157, 2015.  
[2] L. W. Sherman, P. R. Gartin, and M. E. Buerger, "Hot spots of predatory crime: Routine activities and the criminology of place," *Criminology*, vol. 27, no. 1, pp. 27–56, 1989.  
[3] L. E. Cohen and M. Felson, "Social change and crime rate trends: A routine activity approach," *Amer. Sociol. Rev.*, vol. 44, no. 4, pp. 588–608, 1979.  
[4] P. J. Brantingham and P. L. Brantingham, *Patterns in Crime*. New York, NY, USA: Macmillan, 1984.  
[5] S. Chainey, L. Tompson, and S. Uhlig, "The utility of hotspot mapping for predicting spatial patterns of crime," *Secur. J.*, vol. 21, no. 1–2, pp. 4–28, 2008.  
[6] A. A. Braga, B. S. Turchan, A. V. Papachristos, and D. M. Hureau, "Hot spots policing of small geographic areas effects on crime," *Campbell Syst. Rev.*, vol. 15, no. 3, Art. no. e1046, 2019.  
[7] National Crime Records Bureau, "Crime in India 2022," Ministry of Home Affairs, Government of India, New Delhi, India, 2023.  
[8] D. Chand, S. Nayak, K. S. Bhat, S. Parikh, Y. Singh, and A. A. Kamath, "A mobile application for women's safety: WoSApp," in *Proc. IEEE Region 10 Conf. (TENCON)*, 2016.  
[9] M. S. Gerber, "Predicting crime using Twitter and kernel density estimation," *Decis. Support Syst.*, vol. 61, pp. 115–125, 2014.  
[10] A. Umair, M. S. Sarfraz, M. Ahmad, U. Habib, M. H. Ullah, and M. Mazzara, "Spatiotemporal analysis of web news archives for crime prediction," *Appl. Sci.*, vol. 10, no. 22, Art. no. 8220, 2020.  
[11] J. Earl, A. Martin, J. D. McCarthy, and S. A. Soule, "The use of newspaper data in the study of collective action," *Annu. Rev. Sociol.*, vol. 30, pp. 65–80, 2004.  
[12] B. W. Silverman, *Density Estimation for Statistics and Data Analysis*. London, U.K.: Chapman & Hall, 1986.  
[13] Y. Hu, F. Wang, C. Guin, and H. Zhu, "A spatio-temporal kernel density estimation framework for predictive crime hotspot mapping and evaluation," *Appl. Geogr.*, vol. 99, pp. 89–97, 2018.  
[14] M. Ester, H.-P. Kriegel, J. Sander, and X. Xu, "A density-based algorithm for discovering clusters in large spatial databases with noise," in *Proc. 2nd Int. Conf. Knowl. Discovery Data Mining (KDD)*, 1996, pp. 226–231.  
[15] G. O. Mohler, M. B. Short, P. J. Brantingham, F. P. Schoenberg, and G. E. Tita, "Self-exciting point process modeling of crime," *J. Amer. Statist. Assoc.*, vol. 106, no. 493, pp. 100–108, 2011.  
[16] J. M. Caplan, L. W. Kennedy, and J. Miller, "Risk terrain modeling: Brokering criminological theory and GIS methods for crime forecasting," *Justice Quart.*, vol. 28, no. 2, pp. 360–381, 2011.  
[17] Z. Marchment and P. Gill, "Systematic review and meta-analysis of risk terrain modelling (RTM) as a spatial forecasting method," *Crime Sci.*, vol. 10, 2021.  
[18] O. Kounadi, A. Ristea, A. Araujo, and M. Leitner, "A systematic review on spatial crime forecasting," *Crime Sci.*, vol. 9, 2020.  
[19] V. Mandalapu, L. Elluri, P. Vyas, and N. Roy, "Crime prediction using machine learning and deep learning: A systematic review and future directions," *IEEE Access*, vol. 11, pp. 60153–60170, 2023.  
[20] X. Zhang, L. Liu, M. Lan, G. Song, L. Xiao, and J. Chen, "Comparison of machine learning algorithms for predicting crime hotspots," *IEEE Access*, vol. 8, 2020.  
[21] E. G. Knox, "The detection of space-time interactions," *J. Roy. Statist. Soc. C (Appl. Statist.)*, vol. 13, no. 1, pp. 25–29, 1964.  
[22] M. Townsley, R. Homel, and J. Chaseling, "Infectious burglaries: A test of the near repeat hypothesis," *Brit. J. Criminol.*, vol. 43, no. 3, pp. 615–633, 2003.  
[23] S. D. Johnson et al., "Space–time patterns of risk: A cross national assessment of residential burglary victimization," *J. Quant. Criminol.*, vol. 23, no. 3, pp. 201–219, 2007.  
[24] M. Gritta, M. T. Pilehvar, and N. Collier, "A pragmatic guide to geoparsing evaluation: Toponyms, named entity recognition and pragmatics," *Lang. Resour. Eval.*, 2020.  
[25] P. A. Zandbergen, "Geocoding quality and implications for spatial analysis," *Geogr. Compass*, vol. 3, no. 2, pp. 647–680, 2009.  
[26] E. Galbrun, K. Pelechrinis, and E. Terzi, "Safe navigation in urban environments," in *Proc. 3rd Int. Workshop Urban Comput. (UrbComp)*, KDD, New York, NY, USA, 2014.  
[27] J. Jacobs, *The Death and Life of Great American Cities*. New York, NY, USA: Random House, 1961.  
[28] O. Newman, *Defensible Space: Crime Prevention Through Urban Design*. New York, NY, USA: Macmillan, 1972.  
[29] M. Haklay and P. Weber, "OpenStreetMap: User-generated street maps," *IEEE Pervasive Comput.*, vol. 7, no. 4, pp. 12–18, 2008.  
[30] K. Lum and W. Isaac, "To predict and serve?," *Significance*, vol. 13, no. 5, pp. 14–19, 2016.  
[31] R. Richardson, J. M. Schultz, and K. Crawford, "Dirty data, bad predictions: How civil rights violations impact police data, predictive policing systems, and justice," *New York Univ. Law Rev. Online*, vol. 94, p. 15, 2019.  
[32] D. Ensign, S. A. Friedler, S. Neville, C. Scheidegger, and S. Venkatasubramanian, "Runaway feedback loops in predictive policing," in *Proc. Conf. Fairness, Accountability Transparency (FAT\*)*, PMLR vol. 81, 2018, pp. 160–171.  
[33] R. W. Sinnott, "Virtues of the haversine," *Sky Telescope*, vol. 68, no. 2, p. 159, 1984.  
[34] F. Pedregosa et al., "Scikit-learn: Machine learning in Python," *J. Mach. Learn. Res.*, vol. 12, pp. 2825–2830, 2011.  
[35] R. Agrawal and R. Srikant, "Fast algorithms for mining association rules," in *Proc. 20th Int. Conf. Very Large Data Bases (VLDB)*, 1994, pp. 487–499.  
[36] G. Salton and C. Buckley, "Term-weighting approaches in automatic text retrieval," *Inf. Process. Manage.*, vol. 24, no. 5, pp. 513–523, 1988.  
[37] M. Thomson, E. Damaggio, and B. Raymor, Eds., "Generic event delivery using HTTP push," IETF RFC 8030, Dec. 2016.  
[38] M. Thomson and P. Beverloo, "Voluntary application server identification (VAPID) for web push," IETF RFC 8292, Nov. 2017.  
[39] A. Popescu, "Geolocation API specification, 2nd ed.," W3C Recommendation, 2016.  
[40] A. R. Beresford and F. Stajano, "Location privacy in pervasive computing," *IEEE Pervasive Comput.*, vol. 2, no. 1, pp. 46–55, 2003.  
[41] N. Sakimura, J. Bradley, M. Jones, B. de Medeiros, and C. Mortimer, "OpenID Connect Core 1.0 incorporating errata set 1," OpenID Foundation, Nov. 2014.  
[42] Government of India, "The Digital Personal Data Protection Act, 2023," Act No. 22 of 2023, Aug. 2023.  
[43] J. Brooke, "SUS: A quick and dirty usability scale," in *Usability Evaluation in Industry*, P. W. Jordan et al., Eds. London, U.K.: Taylor & Francis, 1996, pp. 189–194.  
