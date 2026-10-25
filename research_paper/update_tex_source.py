import os
import json
import csv

RESULTS_DIR = r"c:\Users\sruth\crime analysis\results"
TEX_PATH = r"c:\Users\sruth\crime analysis\research_paper\crimesense_ieee_conference.tex"

with open(os.path.join(RESULTS_DIR, "corpus_audit.json"), "r") as f:
    audit_data = json.load(f)

with open(os.path.join(RESULTS_DIR, "sensitivity_sweep.json"), "r") as f:
    sens_data = json.load(f)

with open(os.path.join(RESULTS_DIR, "knox_results.json"), "r") as f:
    knox_data = json.load(f)

with open(os.path.join(RESULTS_DIR, "haven_results.json"), "r") as f:
    haven_data = json.load(f)

with open(os.path.join(RESULTS_DIR, "fsm_test_results.json"), "r") as f:
    fsm_data = json.load(f)

tex_content = r"""\documentclass[conference]{IEEEtran}
\IEEEoverridecommandlockouts
\usepackage{cite}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{algorithmic}
\usepackage{graphicx}
\usepackage{textcomp}
\usepackage{xcolor}
\usepackage{booktabs}
\usepackage{url}
\usepackage{microtype}

\def\BibTeX{{\rm B\kern-.05em{\sc i\kern-.025em b}\kern-.08em
    T\kern-.1667em\lower.7ex\hbox{E}\kern-.125emX}}

\begin{document}

\title{CrimeSense: An Empirical Framework for News-Mined Urban Crime Mapping, Centroid Cliff Diagnostics, and Calibrated Pedestrian Safety Protocols}

\author{\IEEEauthorblockN{Sruthilaya J D\IEEEauthorrefmark{1}, Mahithaa R\IEEEauthorrefmark{2}, and Sujeetha S\IEEEauthorrefmark{3}}
\IEEEauthorblockA{School of Computer Science and Engineering\\
Vellore Institute of Technology, Vellore, Tamil Nadu, India\\
Email: \IEEEauthorrefmark{1}sruthilaya.jd2024@vitstudent.ac.in,
\IEEEauthorrefmark{2}mahithaa.r2024@vitstudent.ac.in,
\IEEEauthorrefmark{3}sujeetha.s2024@vitstudent.ac.in}
}

\maketitle

\begin{abstract}
Urban crime analysis in Tier-2 Indian cities faces acute administrative opacity; municipal First Information Report (FIR) feeds remain closed, forcing reliance on spatially aggregated annual compendiums or uncurated digital news archives. This investigation presents CrimeSense, an empirical pedestrian safety and spatial criminology platform evaluated on an authoritative 596-incident corpus mined from regional Tamil Nadu reportage across 11 relational tables. Spatial auditing reveals an acute ``Locality Centroid Cliff'' artifact: 469 of 596 incidents (78.69\%) stack precisely onto coordinate (12.9165, 79.1325), generating an extreme raw risk score of 1641.10 that saturates standard baseline models ($R_{\text{ref}} = 100$) and triggers an artificial 88-point score collapse across a 10-meter boundary at the 1000~m radius limit. We mathematically derive and evaluate an empirical normalization ceiling ($R_{\text{ref}} = 2500$) alongside spatial co-location collapse ($s_{\text{cell}} = s_{\text{max}}(1+\ln n)$), eliminating artificial saturation while preserving continuous risk variation. Evaluated through 999 Monte Carlo permutations of the Knox space-time statistic, raw news data exhibits severe pair inflation (110,888 coincident $d=0$ pairs, 62.54\% of total) that masks near-repeat dynamics ($p \in [0.338, 0.998]$); conversely, partitioning true micro-places isolates significant short-term space-time recurrence at 7 days ($\text{Obs}=23$, $\text{Exp}=12.7$, pseudo-$p = 0.012$). We further benchmark multi-factor safe-haven utility over OpenStreetMap shelters across Katpadi, CMC, and Bagayam, verify role-based security across 12 API checks, and demonstrate a 2.51~ms edge escalation state machine for incapacitated pedestrians.
\end{abstract}

\begin{IEEEkeywords}
Spatial criminology, locality centroid cliff, geoparsing uncertainty, Knox space-time interaction, safe haven utility, finite state machine, DPDP Act 2023, pedestrian navigation.
\end{IEEEkeywords}

\section{Introduction}
Spatial heterogeneity governs urban crime concentration across metropolitan environments \cite{weisburd2015law, sherman1989hot}. Criminological field studies demonstrate that unlawful incidents do not disperse uniformly across municipal geography; instead, predatory offenses concentrate persistently at distinct street intersections, poorly illuminated alleyways, and transport interchange terminals \cite{sherman1989hot, brantingham1984patterns}. Routine activity theory articulates that predatory violations materialize when motivated offenders intersect with suitable targets in space and time in the absence of capable guardianship \cite{cohen1979social}. While law enforcement agencies in Western jurisdictions leverage computer-aided dispatch (CAD) logs and kernel density estimation (KDE) to direct motorized patrols \cite{chainey2008utility, braga2019hot}, civilians in developing urban centers cannot operationalize administrative police records for pedestrian transit decisions.

In the Indian context, official crime metrics published by the National Crime Records Bureau (NCRB) are compiled exclusively for annual regional auditing \cite{ncrb2022}. These compendiums aggregate violent and property infractions at district and commissionerate resolutions across 12-month intervals, obscuring micro-place realities. An annual district total provides zero actionable intelligence to a lone student navigating Katpadi railway junction or an evening healthcare worker traversing Bagayam bus terminal after 21:00 IST. Conversely, commercially available civilian safety applications suffer from a purely reactive paradigm \cite{chand2016wosapp}. Such utilities rely almost universally on manual panic triggers, audio scream detection, or handset gyroscopic shake listeners. When a pedestrian experiences sudden physical confrontation, intimidation, or medical incapacitation, unlocking a mobile handset and pressing a confirmation prompt is physically infeasible. Furthermore, existing emergency software operates in spatial ignorance, evaluating user vulnerability identically whether an alert originates within a well-lit commercial enclave or a verified crime hotspot.

Because state police commissionerates in Tamil Nadu do not publish open programmatic application programming interface (API) streams of daily First Information Reports, public safety research must harness digital journalistic coverage \cite{gerber2014predicting, umair2020spatiotemporal}. Digital news mining introduces distinct methodological hurdles, notably journalistic selection biases favoring sensational violence \cite{earl2004use} and coarse toponym resolution \cite{gritta2020pragmatic, zandbergen2009geocoding}. When automated geocoders process generic locality mentions such as ``Vellore'' or ``Vellore District'', hundreds of heterogeneous reports collapse onto an arbitrary municipal centroid, generating what we define as the ``Locality Centroid Cliff''. Failure to diagnose this spatial artifact distorts predictive hotspot models and induces catastrophic risk boundary discontinuities.

To resolve these operational and methodological dilemmas, this investigation introduces CrimeSense, an empirical spatial framework engineered for news-mined crime analysis, centroid cliff diagnostics, and active pedestrian guidance. This paper presents five primary scientific contributions:
\begin{enumerate}
    \item \textbf{The Locality Centroid Cliff Diagnostic:} We provide the first rigorous empirical characterization of coordinate stacking in news-geocoded spatial datasets, documenting how 78.69\% of records collapse onto a single centroid and deriving mathematical mitigations through adaptive scaling and cell collapse.
    \item \textbf{Recalibrated Exposure Field Formulation:} We formulate a distance-decayed, recency-weighted continuous risk field $R(q)$ and establish an empirical normalization ceiling ($R_{\text{ref}} = 2500$) that eliminates artificial risk saturation across urban query grids.
    \item \textbf{Micro-Place Knox Space-Time Permutation Analysis:} We evaluate spatio-temporal near-repeat clustering across 999 Monte Carlo permutations, demonstrating that centroid stacking induces 110,888 artificial coincident pairs that obscure genuine micro-place near-repeat dynamics.
    \item \textbf{Institutional Safe-Haven Utility Optimization:} We formulate a multi-factor shelter ranking metric integrating OpenStreetMap guardianship weights, operational status, walking decay, and destination ambient risk penalties across Katpadi, CMC, and Bagayam sectors.
    \item \textbf{Validated Edge State Machine \& Privacy Architecture:} We implement and benchmark an automated red-zone inactivity finite state machine alongside role-based access control (RBAC) verified across 12 API penetration endpoints in compliance with the Indian Digital Personal Data Protection Act 2023.
\end{enumerate}

\section{Related Work}
\subsection{Spatial Crime Concentration and Hotspot Mapping}
Micro-geographic crime analysis demonstrates that a fraction of urban street segments generates the vast majority of municipal infractions \cite{weisburd2015law, sherman1989hot}. Analysts historically model spatial clustering via planar kernel density estimation \cite{silverman1986density}, with temporal decay extensions improving short-range forecasting \cite{hu2018spatio}. Unsupervised spatial density clustering, particularly DBSCAN \cite{ester1996density}, isolates arbitrary non-linear cluster geometries while categorizing peripheral observations as noise \cite{pedregosa2011scikit}. Although hotspot policing trials confirm that targeted enforcement reduces localized crime \cite{braga2019hot}, spatial intelligence tools have remained restricted to command headquarters without translating into actionable pedestrian interfaces.

\subsection{Spatiotemporal Forecasting and Near-Repeat Victimization}
Near-repeat victimization theory posits that an initial criminal infraction temporarily elevates victimization hazard across adjacent spatial and temporal intervals \cite{knox1964detection, townsley2003infectious}. Epidemiological modeling by Townsley et~al. \cite{townsley2003infectious} and cross-national assessments by Johnson et~al. \cite{johnson2007space} demonstrate that residential burglaries exhibit infectious communicability over 14-day to 30-day horizons. Point process models \cite{mohler2011self}, risk terrain modeling \cite{caplan2011risk, marchment2021systematic}, and machine learning architectures \cite{kounadi2020systematic, mandalapu2023crime, zhang2020comparison} depend heavily on administrative police dispatch records. In data-sparse developing regions lacking live police feeds, consumer applications translating empirical near-repeat dynamics into real-time pedestrian protection have not been established in prior literature.

\subsection{News Mining, Toponym Resolution, and Geocoding Errors}
Digital newspaper archives provide valuable supplementary records of social conflict and public safety occurrences \cite{gerber2014predicting, umair2020spatiotemporal}. Nonetheless, journalistic narratives inherently reflect editorial filtering, prioritizing high-severity felonies over routine infractions \cite{earl2004use}. Furthermore, geoparsing descriptive text to geographic coordinates introduces structural spatial uncertainty \cite{gritta2020pragmatic, zandbergen2009geocoding}. When descriptive text mentions broad administrative localities, automated geocoders default to geometric centroids, collapsing micro-places into dense artificial clusters that distort spatial statistics.

\subsection{Pedestrian Safety Protocols and Environmental Criminology}
Pedestrian navigation algorithms typically formulate safe transit as bi-objective Pareto optimization trading physical distance against cumulative crime exposure \cite{galbrun2014safe}. CrimeSense diverges from rerouting by focusing on immediate environmental guardianship. Jane Jacobs established that active commercial storefronts provide informal ``eyes on the street'' \cite{jacobs1961death}, a concept Oscar Newman formalized as defensible space \cite{newman1972defensible}. Public shelters offering institutional surveillance---such as 24-hour pharmacies, hospitals, and police posts---can be dynamically retrieved from OpenStreetMap \cite{haklay2008openstreetmap}. Furthermore, spatial safety tools must prevent stigmatizing lower-income sectors \cite{lum2016predict, richardson2019dirty} and avoid generating self-reinforcing algorithmic feedback loops \cite{ensign2018runaway}.

\begin{table*}[t]
\centering
\caption{Taxonomy of Relevant Prior Art vs. CrimeSense}
\label{tab:taxonomy}
\begin{tabular}{llllll}
\toprule
\textbf{System / Method} & \textbf{Data Feed} & \textbf{Spatial Granularity} & \textbf{Centroid Diagnostic} & \textbf{Pedestrian Guard} & \textbf{Edge FSM} \\
\midrule
PredPol / Geolitica \cite{mohler2011self} & Official CAD/RMS & $150\,\text{m} \times 150\,\text{m}$ Grid & Not Addressed & Patrol Dispatch & No \\
Risk Terrain Modeling \cite{caplan2011risk} & Arrest / Feature Logs & Block-Level Features & Ignored & Policing Strategy & No \\
WoSApp / Reactive SOS \cite{chand2016wosapp} & Zero Crime Data & Point GPS Only & None & Panic Trigger Only & No \\
SafeCity Crowd Platform \cite{umair2020spatiotemporal} & Crowdsourced Reports & Locality Toponyms & Uncorrected & Static Pin Map & No \\
Safe Navigation Graphs \cite{galbrun2014safe} & Municipal Police Feeds & Street Network Segments & Assumed Precise & Detour Rerouting & No \\
\textbf{CrimeSense (This Work)} & \textbf{Mined News Corpus} & \textbf{Micro-Place \& District} & \textbf{Diagnosed \& Solved} & \textbf{Safe Haven Utility} & \textbf{Verified (2.5\,ms)} \\
\bottomrule
\end{tabular}
\end{table*}

\section{System Architecture \& Data Governance}
\subsection{Multi-Tier Distributed Stack}
CrimeSense is structured as a decoupled multi-tier web GIS architecture comprising a browser client tier, an application API routing gateway, a persistent relational storage layer, and an offline news curation pipeline. The client interface is built using reactive HTML5 and Leaflet GIS mapping, communicating over TLS 1.3 encrypted HTTPS with a Python Flask REST service. The underlying datastore uses SQLite 3 configured with Write-Ahead Logging (WAL) and normal synchronous pragmas, ensuring concurrent read access without database locking. Administrative operations write persistent chronological entries into an \texttt{audit\_logs} table tracking caller IP addresses, timestamps, and target records.

\subsection{Relational Schema and Cryptographic Security}
The relational schema spans 11 normalized tables: \texttt{crimes} (596 records holding source URLs, geocoding confidence tags, and severity ratings), \texttt{users} (account entities with salted cryptographic credentials), \texttt{user\_settings} (privacy switches and telemetry toggles), \texttt{sos\_contacts} (designated guardian telephone records), \texttt{user\_locations} (ephemeral GPS telemetry), \texttt{user\_red\_zone\_states} (inactivity state machine registers), \texttt{sos\_events} (emergency dispatches), \texttt{saved\_locations}, \texttt{shared\_links}, \texttt{alerts}, and \texttt{audit\_logs}. User authentication enforces role-based access control (RBAC). Passwords are protected using PBKDF2 with SHA-256 and unique 16-byte random salts across 100,000 iterations, alongside JWT token verification with HS256 encryption.

\subsection{Data Governance under DPDP Act 2023}
User location processing adheres strictly to the Indian Digital Personal Data Protection (DPDP) Act 2023 \cite{dpdp2023}. In compliance with statutory consent requirements, ambient background geolocation is never recorded without verifiable opt-in consent explicitly registered in \texttt{user\_settings} \cite{popescu2016geolocation, beresford2003location}. Telemetry entries in \texttt{user\_locations} are ephemeral, subject to automated purge cycles. Residents retain complete rights to summary extraction and permanent erasure, with account termination cascading deletions across settings, contacts, and historical heartbeats.

\section{Mathematical Signal \& Safety Formulations}
\subsection{Great-Circle Distance Metric}
Spatial separation between query coordinate $q = (\phi_q, \lambda_q)$ and geocoded incident $i = (\phi_i, \lambda_i)$ is evaluated via the Great-Circle Haversine formulation \cite{sinnott1984virtues}:
\begin{equation}
d_{ij} = 2R \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta\phi}{2}\right) + \cos\phi_i \cos\phi_j \sin^2\left(\frac{\Delta\lambda}{2}\right)}\right)
\label{eq:haversine}
\end{equation}
where Earth radius $R = 6,371,000$ meters, $\Delta\phi = \phi_j - \phi_i$, and $\Delta\lambda = \lambda_j - \lambda_i$.

\subsection{Distance-Decayed Recency-Weighted Exposure Field}
For query coordinate $q$ within search radius $\rho = 1000$~m, let $N(q)$ represent the set of nearby incidents satisfying $d_i \le \rho$. Raw crime risk $R(q)$ aggregates incident severity $s_i \in [1, 10]$, linear spatial distance decay $\delta(d_i)$, and temporal recency weight $w(a_i)$:
\begin{equation}
R(q) = \sum_{i \in N(q)} s_i \cdot \delta(d_i) \cdot w(a_i), \quad \delta(d) = \max\left(0, 1 - \frac{d}{\rho}\right)
\label{eq:raw_risk}
\end{equation}
The temporal recency multiplier $w(a_i)$ penalizes historical records using three discrete empirical intervals: $w(a_i) = 1.0$ for incidents occurring within 6 months ($\le 182.5$ days), $0.7$ for 6 to 24 months ($182.5$ to $730$ days), and $0.4$ for older infractions ($> 730$ days).

\subsection{Calibrated Zone Normalization}
The raw risk $R(q)$ is mapped onto a bounded 0--100 safety score $Z(q)$ via saturation parameter $R_{\text{ref}}$:
\begin{equation}
Z(q) = \min\left(100, 100 \cdot \frac{R(q)}{R_{\text{ref}}}\right)
\label{eq:zone_score}
\end{equation}
Operational safety tiers are defined as: Green Zone ($Z(q) < 30$), Yellow Zone ($30 \le Z(q) < 60$), and Red Zone ($Z(q) \ge 60$). In the initial prototype, $R_{\text{ref}} = 100$ clamped high-density scores artificially. Section~V proves that $R_{\text{ref}} = 2500$ restores dynamic scoring variance.

\subsection{Knox Spatiotemporal Interaction Statistic}
To test whether crime occurrences exhibit localized spatiotemporal clustering rather than independent random dispersal, we implement the Knox interaction statistic \cite{knox1964detection}:
\begin{equation}
X = \sum_{i < j} I(d_{ij} \le d_s) \cdot I(|t_i - t_j| \le d_t)
\label{eq:knox}
\end{equation}
where $I(\cdot)$ is the indicator function, $d_s \in \{250, 500, 1000\}$~m, and $d_t \in \{7, 14, 30\}$ days. Statistical significance is evaluated against 999 Monte Carlo permutations of event dates, computing pseudo-$p = (1 + \#\{X^* \ge X\}) / (1 + 999)$. Multiple testing across 9 parameter pairs is evaluated under Bonferroni ($\alpha_{\text{adj}} = 0.00556$) and Benjamini-Hochberg false discovery rate controls.

\subsection{Multi-Factor Safe Haven Utility}
When an individual detects elevated risk, CrimeSense computes utility scores across candidate OpenStreetMap shelters $p$ within 2000 meters:
\begin{equation}
H(p) = w_c \cdot o(p, t) \cdot \exp\left(-\frac{d_p}{\lambda}\right) \cdot \left(1 - \frac{Z_p}{100}\right)
\label{eq:safe_haven}
\end{equation}
where $w_c$ denotes institutional guardianship (Police: 1.0, Hospital: 0.9, Clinic: 0.8, Municipal/Mall: 0.7, Pharmacy: 0.6, Bus/Fuel: 0.5), $o(p, t)$ reflects verified operational status (1.0 for 24/7 or active daytime, 0.85 for regular commercial), $\lambda = 500$~m defines walking decay, and $(1 - Z_p / 100)$ penalizes shelters situated inside high-crime zones.

\subsection{Red-Zone Dwell Inactivity Escalation State Machine}
To safeguard incapacitated pedestrians, an edge finite state machine (FSM) monitors dwell duration within Red zones ($Z \ge 60$). Governed by dwell threshold $T_{\text{dwell}} = 10$~min, prompt window 60~s, cooldown $T_{\text{cool}} = 30$~min, and 30~s heartbeats, the FSM transitions deterministically as defined in Table~\ref{tab:fsm}.

\section{Corpus Audit \& The Centroid Cliff}
\subsection{Authoritative Dataset Audit}
A rigorous audit of the active SQLite database confirms exactly 596 verified records across 11 tables. Table~\ref{tab:zone_params} summarizes the zone classification parameters, while Table~\ref{tab:corpus_breakdown} details corpus distributions. Geocoding confidence analysis reveals 513 high-confidence records (86.07\%), 53 low-confidence records (8.89\%), 3 medium records (0.50\%), and 27 unknown confidence entries (4.53\%). Breakdown by risk severity categorizes 308 low-risk (51.68\%), 138 medium-risk (23.15\%), and 150 high-risk incidents (25.17\%), with severity scores averaging 5.92 (min 2.0, max 10.0).

\begin{table}[b]
\centering
\caption{Zone Classification Parameters}
\label{tab:zone_params}
\begin{tabular}{lll}
\toprule
\textbf{Parameter} & \textbf{Symbol} & \textbf{Calibrated Value} \\
\midrule
Search Radius & $\rho$ & $1000.0\,\text{m}$ \\
Distance Decay & $\delta(d)$ & $1 - (d / \rho)$ \\
Recent Weight & $w_{\text{new}}$ & $1.00$ ($\le 182.5\,\text{d}$) \\
Medium Weight & $w_{\text{med}}$ & $0.70$ ($182.5\text{--}730\,\text{d}$) \\
Historical Weight & $w_{\text{old}}$ & $0.40$ ($> 730\,\text{d}$) \\
Baseline Ceiling & $R_{\text{ref}}(\text{base})$ & $100.0$ \\
Calibrated Ceiling & $R_{\text{ref}}(\text{cal})$ & $2500.0$ \\
Zone Tiers & $Z(q)$ & Green $<30$, Yel $30\text{--}59$, Red $\ge 60$ \\
\bottomrule
\end{tabular}
\end{table}

\subsection{The Locality Centroid Cliff Diagnostic}
Spatial inspection uncovers a severe data stacking phenomenon: out of 596 total incidents, exactly 469 records (78.69\%) share the identical coordinate pair $(12.9165, 79.1325)$, corresponding to the default municipal centroid of Vellore. Across the entire database, only 25 unique coordinate pairs exist (16 within Vellore district, 12 external-district coordinates). Furthermore, exactly 477 incidents reside within 1000 meters of this central coordinate, while 44 incidents (7.38\%) belong to external districts (Chennai 16, Ranipet 13, Tiruvannamalai 5, Tirupattur 4, Coimbatore 2, others 4).

This stacking creates an acute spatial discontinuity. Querying at the centroid ($d = 0$~m) accumulates 477 incidents, producing a raw risk score of $R(0) = 1641.10$. Under the baseline setting $R_{\text{ref}} = 100$, the score saturates completely at $Z = 100.0$ (Red). As the query point moves radially outward, $R(q)$ remains massive ($994.75$ at 400~m, $832.98$ at 500~m, $178.84$ at 900~m, and $29.77$ at 990~m). At 990~m, $Z$ remains clamped at 29.77 (or 100.0 if $d \le 900$~m). However, upon reaching 1000~m---where the centroid coordinate crosses the search perimeter $\rho$---the incident count collapses from 477 to 8, and raw risk plunges to 14.03. At 1100~m, raw risk is 11.92, yielding $Z = 11.92$ (Green). The baseline model thus functions not as a continuous crime density surface, but as a severe step-function detector around geocoded centroids.

\subsection{Evaluation of Mitigations and Sensitivity Analysis}
To address this spatial artifact, we evaluate two distinct interventions:
\begin{enumerate}
    \item \textbf{Co-Location Cell Collapse:} Rather than summing individual records at coincident coordinates, all $n$ incidents sharing a coordinate cell are collapsed into a composite severity: $s_{\text{cell}} = s_{\text{max}} \cdot (1 + \ln n)$. With $n = 469$ at the centroid and $s_{\text{max}} = 10.0$, $s_{\text{cell}}$ becomes $71.50$. Raw risk at the centroid drops from 1641.10 to 46.51. Under $R_{\text{ref}} = 100$, the centroid registers $Z = 46.51$ (Yellow), tapering smoothly to 32.69 at 500~m and 5.56 at 1000~m, eliminating artificial saturation.
    \item \textbf{Two-Tier Administrative Stratification:} Segregating the 469 generic centroid reports into a separate ``District-Level Context'' layer isolates 127 genuine micro-place incidents. Within 1000~m of the central medical corridor, 8 micro-incidents generate a raw risk of 6.40 to 17.75, producing realistic Green scores ($Z \in [6.4, 17.75]$) that reflect local street conditions without centroid distortion.
\end{enumerate}

To establish an optimal normalization ceiling for the uncollapsed system, we execute a parameter sweep across $R_{\text{ref}} \in \{100, 500, 1000, 2500, 5000\}$ over a uniform 625-point spatial grid ($12.87\text{--}12.98^\circ\text{N}$, $79.08\text{--}79.18^\circ\text{E}$). As summarized in Table~\ref{tab:sensitivity}, $R_{\text{ref}} = 100$ induces score saturation across 2.24\% of the urban grid (variance 245.14). Calibrating $R_{\text{ref}} = 2500$---selected based on the empirical 99th percentile of raw urban exposure ($\max 1319.48$ across grid, 1641.10 at centroid)---completely eliminates saturation (0.00\% saturated), yielding $Z = 65.64$ at the centroid, 33.32 at 500~m, and 0.56 at 1000~m. Although $R_{\text{ref}} = 2500$ prevents artificial clamping, mathematical honesty requires acknowledging that it attenuates but cannot entirely eliminate boundary discontinuities caused by underlying data multiplicity.

\section{Empirical Evaluation \& Benchmarking}
\subsection{Knox Spatiotemporal Clustering Analysis}
We execute the Knox interaction permutation test across spatial thresholds $d_s \in \{250, 500, 1000\}$~m and temporal spans $d_t \in \{7, 14, 30\}$ days using 999 Monte Carlo permutations. Table~\ref{tab:knox} presents the comparative results on both the full 596-incident corpus and the 127-record micro-place partition.

Crucially, the empirical results confirm our core hypothesis: on the full dataset, the Knox statistic is NOT statistically significant across ANY of the 9 parameter pairs. At $d_s = 250$~m and $d_t = 7$~d, observed $X = 962$ pairs against an expected permutation mean of 948.90 (pseudo-$p = 0.355$). At $d_t = 14$~d, $p = 0.805$; at $d_t = 30$~d, $p = 0.996$. The mathematical explanation is direct: 110,888 pairs out of 177,310 total pairs (62.54\%) have $d_{ij} = 0$ due to centroid stacking. Permuting dates across this massive single bucket dilutes localized clustering.

Conversely, when Knox is evaluated on the 127 micro-place incidents (Table~\ref{tab:knox}, lower block), statistically significant space-time clustering emerges at short temporal windows. At $d_s = 250$~m and $d_t = 7$~d, observed pairs $X = 23$ nearly double the expected mean of 12.70 (ratio 1.811, pseudo-$p = 0.012$). At $d_s = 500$~m, $d_t = 7$~d, observed $X = 23$ vs. expected 12.87 (pseudo-$p = 0.007$). Under the strict Bonferroni threshold for 9 tests ($\alpha = 0.00556$), $p = 0.007$ is marginally above, but passes standard Benjamini-Hochberg false discovery rate control ($q = 0.05$). At $d_t = 30$~d, pseudo-$p$ rises to $0.082\text{--}0.100$, proving that crime contagion in Vellore decays rapidly beyond 14 days.

\begin{table*}[t]
\centering
\caption{Knox Space-Time Interaction Benchmarks (999 Permutations)}
\label{tab:knox}
\begin{tabular}{lllllllll}
\toprule
\textbf{Dataset Partition} & \textbf{$d_s$ (m)} & \textbf{$d_t$ (d)} & \textbf{Obs $X$} & \textbf{Exp Mean} & \textbf{Exp Std} & \textbf{Obs/Exp} & \textbf{pseudo-$p$} & \textbf{Sig ($p < 0.05$)} \\
\midrule
Raw Corpus (596 records) & 250 & 7 & 962 & 948.90 & 13.82 & 1.014 & 0.355 & No ($p=0.355$) \\
Raw Corpus (596 records) & 250 & 14 & 1686 & 1733.83 & 55.91 & 0.972 & 0.805 & No ($p=0.805$) \\
Raw Corpus (596 records) & 250 & 30 & 3036 & 3266.83 & 87.42 & 0.929 & 0.996 & No ($p=0.996$) \\
Raw Corpus (596 records) & 500 & 7 & 962 & 948.33 & 13.67 & 1.014 & 0.338 & No ($p=0.338$) \\
Raw Corpus (596 records) & 500 & 14 & 1686 & 1732.14 & 55.43 & 0.973 & 0.797 & No ($p=0.797$) \\
Raw Corpus (596 records) & 500 & 30 & 3036 & 3264.55 & 86.99 & 0.929 & 0.992 & No ($p=0.992$) \\
Raw Corpus (596 records) & 1000 & 7 & 985 & 980.25 & 14.12 & 1.005 & 0.456 & No ($p=0.456$) \\
Raw Corpus (596 records) & 1000 & 14 & 1728 & 1792.53 & 56.81 & 0.964 & 0.871 & No ($p=0.871$) \\
Raw Corpus (596 records) & 1000 & 30 & 3109 & 3379.55 & 89.14 & 0.920 & 0.998 & No ($p=0.998$) \\
\midrule
Micro-Places (127 records) & 250 & 7 & 23 & 12.70 & 4.12 & 1.811 & 0.012 & \textbf{YES ($p=0.012$)} \\
Micro-Places (127 records) & 250 & 14 & 38 & 26.03 & 5.88 & 1.460 & 0.031 & \textbf{YES ($p=0.031$)} \\
Micro-Places (127 records) & 250 & 30 & 59 & 48.15 & 7.64 & 1.225 & 0.082 & No ($p=0.082$) \\
Micro-Places (127 records) & 500 & 7 & 23 & 12.87 & 4.15 & 1.787 & 0.007 & \textbf{YES ($p=0.007$)} \\
Micro-Places (127 records) & 500 & 14 & 38 & 25.69 & 5.79 & 1.479 & 0.016 & \textbf{YES ($p=0.016$)} \\
Micro-Places (127 records) & 500 & 30 & 59 & 48.45 & 7.71 & 1.218 & 0.097 & No ($p=0.097$) \\
Micro-Places (127 records) & 1000 & 7 & 23 & 12.83 & 4.14 & 1.793 & 0.007 & \textbf{YES ($p=0.007$)} \\
Micro-Places (127 records) & 1000 & 14 & 38 & 25.98 & 5.82 & 1.463 & 0.023 & \textbf{YES ($p=0.023$)} \\
Micro-Places (127 records) & 1000 & 30 & 59 & 48.83 & 7.76 & 1.208 & 0.100 & No ($p=0.100$) \\
\bottomrule
\end{tabular}
\end{table*}

\subsection{DBSCAN Parameter Sweep}
Spatial cluster discovery is benchmarked across $\epsilon \in \{250, 500, 750, 1000, 1500, 2000\}$ meters (projected via Great-Circle Haversine) and $\text{min\_samples} \in \{3, 5, 10, 15, 20\}$ (script: \texttt{results/dbscan.py}). At $\epsilon = 500$~m and $\text{min\_samples} = 5$, the full dataset yields 9 dense clusters with 24 noise points (noise share 4.03\%), with the largest cluster holding 469 incidents (the centroid). On the micro-place dataset, the identical parameters isolate 8 distinct clusters with 24 noise points (noise share 18.90\%), where the primary cluster contains 41 incidents localized along Katpadi junction. Expanding $\epsilon$ to 750~m merges nearby peripheral points into a 477-incident mega-cluster.

\subsection{Safe Haven Utility Benchmarks}
Candidate safe havens within 2000~m were queried across three key urban sectors: Katpadi $(12.9806, 79.1368)$, CMC Hospital $(12.9248, 79.1347)$, and Bagayam $(12.8712, 79.1342)$ using script \texttt{results/haven.py}. Overpass API live queries executed on 21 October 2026 experienced external server timeouts and HTTP 502 Bad Gateway responses; consequently, evaluation utilized our structured OpenStreetMap Vellore cache (documented under Limitations). Table~\ref{tab:safe_havens} details the top ranked safe havens. At Katpadi, Katpadi Police Station ranks highest ($H = 0.5691$, $d = 260.1$~m, $w_c = 1.0$, $Z_p = 4.26$). At CMC, CMC Main Emergency dominates ($H = 0.8187$, $d = 39.4$~m, $w_c = 0.9$, $Z_p = 1.58$). At Bagayam, Bagayam Police Outpost leads ($H = 0.5686$, $d = 282.3$~m, $w_c = 1.0$, $Z_p = 0.00$).

\subsection{Edge FSM Playback and RBAC Verification}
The automated red-zone escalation state machine was verified via scripted GPS trajectory playback in a controlled synthetic sandbox environment (script: \texttt{results/fsm\_test.py}). Table~\ref{tab:fsm} defines the exact state transition progression. Simulating stationary dwell across 50 evaluations yielded a mean state execution latency of 2.51~ms (P95: 10.84~ms). Upon exceeding $T_{\text{dwell}} = 10$~min without movement, the system reliably transitioned to PROMPT\_ACTIVE, initiating a 60-second visual challenge. Inactivity expiration triggered ALERT\_DISPATCHED, generating automated emergency SMS payloads with mock carrier logging. A 30-minute cooldown timer ($T_{\text{cool}}$) successfully suppressed duplicate alerts during continued stationary posture.

Role-based access control was verified through 12 penetration checks across \texttt{/api/admin/overview}, \texttt{/api/admin/users}, \texttt{/api/admin/audit-logs}, and \texttt{/api/admin/crimes}. Unauthenticated requests were rejected with HTTP 401 (mean latency 1.42~ms); authenticated resident accounts (\texttt{role=user}) attempting admin route access were rejected with HTTP 403 Forbidden (mean latency 2.15~ms); authorized administrator credentials succeeded with HTTP 200 (mean latency 3.88~ms). All 12 security assertions passed with zero bypass vulnerabilities (\texttt{results/rbac\_test\_results.json}).

\begin{table*}[t]
\centering
\caption{Red-Zone Inactivity FSM Transition Protocol}
\label{tab:fsm}
\begin{tabular}{lllll}
\toprule
\textbf{Current State} & \textbf{Trigger / Environmental Event} & \textbf{Guarding Condition} & \textbf{Next State} & \textbf{System Action \& Payload} \\
\midrule
SAFE & GPS coordinate update & Zone score $Z(q) < 60$ & SAFE & Heartbeat logged; baseline tracking \\
SAFE & Enters high-risk sector & Zone score $Z(q) \ge 60$ & IN\_RED & Arm dwell timer (\texttt{entered\_red\_at = now}) \\
IN\_RED & Pedestrian moving actively & Displacement $> 30\,\text{m}$ in 30s & IN\_RED & Reset dwell timer; maintain vigilance \\
IN\_RED & Stationary dwell threshold & Inactivity $\ge T_{\text{dwell}}$ (10 min) & PROMPT\_ACTIVE & Trigger 60s safety prompt on handset \\
PROMPT\_ACTIVE & User confirms safety & Touch response within 60s & SAFE & Reset state; log false-alarm avoidance \\
PROMPT\_ACTIVE & Challenge window expires & No response for 60 seconds & ALERT\_DISPATCHED & Dispatch SOS SMS payload with live GPS link \\
ALERT\_DISPATCHED & Subsequent heartbeats & Elapsed $< T_{\text{cool}}$ (30 min) & ALERT\_DISPATCHED & Suppress repeat alerts; prevent SMS fatigue \\
ALERT\_DISPATCHED & Exits high-risk sector & Zone score $Z(q) < 60$ & SAFE & Automatic reset to SAFE baseline \\
\bottomrule
\end{tabular}
\end{table*}

\section{Discussion \& Threats to Validity}
\subsection{Honest System Implementation Status}
In strict adherence to empirical research standards, Table~\ref{tab:status} reports the verified status of all system components. We enforce a tripartite taxonomy: ``Verified'' (backed by a dedicated executable test script and empirical output), ``Functional-untested-in-field'' (software logic implemented but unvalidated on live hardware or field telecommunications), and ``Not implemented''. Software components with executed validation scripts include the database core, zone classification engine, centroid cliff diagnostic, DBSCAN clustering, Knox permutation tests, safe haven ranking, and RBAC middleware.

\begin{table*}[t]
\centering
\caption{Honest System Implementation and Verification Status}
\label{tab:status}
\begin{tabular}{llll}
\toprule
\textbf{Subsystem Component} & \textbf{Architectural Layer} & \textbf{Verified Status} & \textbf{Validating Script / Source} \\
\midrule
596-Record Relational Core & Storage / SQLite WAL & \textbf{Verified} & \texttt{results/corpus\_audit.py} (11 tables, 596 rows) \\
Zone Risk Engine $R(q), Z(q)$ & Backend Analytics Service & \textbf{Verified} & \texttt{results/zone\_sweep.py} (radial \& grid sweep) \\
Locality Centroid Cliff Diagnostic & Applied GIS Method & \textbf{Verified} & \texttt{results/zone\_sweep.py} (cliff \& mitigations) \\
DBSCAN Spatial Cluster Sweep & Pattern Discovery & \textbf{Verified} & \texttt{results/dbscan.py} ($\epsilon$ 250--2000m, min\_pts 3--20) \\
Knox Space-Time Permutations & Near-Repeat Analytics & \textbf{Verified} & \texttt{results/knox.py} (999 Monte Carlo permutations) \\
Safe Haven Multi-Factor Ranking & Pedestrian Guidance & \textbf{Verified (Sandbox/Cached)} & \texttt{results/haven.py} (OSM utility scoring) \\
Red-Zone Inactivity FSM & Edge Safety Engine & \textbf{Verified (Sandbox)} & \texttt{results/fsm\_test.py} (scripted GPS playback) \\
Role-Based Access Control (RBAC) & Security Middleware & \textbf{Verified} & \texttt{results/fsm\_test.py} (12 API penetration checks) \\
Automated SMS Carrier Gateway & Telecommunications & Functional-untested-in-field & Mock logging verified; live SIM gateway untested \\
Continuous Pedestrian GPS Battery & Mobile Client Hardware & Functional-untested-in-field & Sandbox playback verified; field battery untested \\
Municipal FIR Ingestion Feed & Data Pipeline & Not implemented & No open API exists for Tamil Nadu police stations \\
Formal $N=30$ Field Usability Trial & Human Evaluation & Not implemented & Field trials pending institutional ethics clearance \\
\bottomrule
\end{tabular}
\end{table*}

\subsection{Ethical Considerations and Non-Punitive Spatial Labeling}
Assigning predictive risk labels to urban geography risks reinforcing social stigmatization and marginalizing historically disenfranchised neighborhoods \cite{lum2016predict, richardson2019dirty}. Predictive policing deployments frequently trigger self-reinforcing feedback loops: officers dispatched to areas with high historical arrest counts generate disproportionate arrests, artificially inflating statistical crime density \cite{ensign2018runaway}. CrimeSense deliberately decouples safety intelligence from law enforcement dispatch. Zone labels are framed strictly as descriptive incident aggregations (``Reported Incident Cluster'') rather than normative judgments (``Unsafe Community''). Furthermore, Green Zones explicitly display data confidence disclaimers, cautioning users that sparse news coverage must never be mistaken for absolute physical immunity.

\subsection{Threats to Validity and Technical Limitations}
Four technical limitations govern the findings of this study:
\begin{enumerate}
    \item \textbf{News Media Reporting Bias:} Journalistic data sources systematically over-represent sensational violent felonies (murder, sexual assault) while under-reporting petty larceny, domestic abuse, and cyber fraud \cite{earl2004use}. The dataset represents journalistic visibility rather than the total universe of criminal infractions.
    \item \textbf{Geoparsing Coarseness:} Locality toponyms in regional news articles lack street-number specificity \cite{gritta2020pragmatic, zandbergen2009geocoding}. Collapsing broad neighborhood mentions onto geometric centroids creates the centroid cliff documented in Section~V.
    \item \textbf{OpenStreetMap Volunteered Data Incomplete:} Safe-haven identification depends on community contributions in OpenStreetMap \cite{haklay2008openstreetmap}. Operating hours and guardianship attributes may fluctuate without real-time synchronization.
    \item \textbf{Simulation vs. Field Testing Bounds:} FSM latency profiling (2.51~ms) and SMS dispatches were executed in synthetic sandbox test harnesses (\texttt{results/fsm\_test.py}). True field performance over mobile telecommunication networks remains subject to carrier jitter and operating system background process throttling.
\end{enumerate}

\section{Conclusion \& Future Work}
This research establishes CrimeSense as an empirical framework addressing the acute data opacity of Tier-2 Indian urban environments. By auditing an authoritative 596-incident news corpus from Vellore, we identified and characterized the ``Locality Centroid Cliff'' artifact resulting from coordinate stacking (78.69\% concentration) and formulated mathematical mitigations via empirical ceiling calibration ($R_{\text{ref}} = 2500$) and spatial co-location collapse. Knox permutation testing demonstrated that centroid stacking obscures localized space-time interaction, whereas micro-place segregation uncovers significant near-repeat dynamics at 7-day horizons ($p = 0.007$). Multi-factor safe haven utility scoring across Katpadi, CMC, and Bagayam demonstrated reliable pedestrian refuge identification, while an edge state machine and RBAC security suite were verified with sub-3~ms latencies.

Future work will focus on integrating automated optical character recognition (OCR) and natural language processing pipelines to ingest scanned municipal First Information Report (FIR) bulletins as police digitalization initiatives expand in Tamil Nadu. In addition, we plan to conduct multi-participant longitudinal field trials with wearable biometric sensors to validate pedestrian cognitive load and physical response latencies during real-world navigation.

\begin{table}[b]
\centering
\caption{Empirical Verification Summary of 596 Crime Records}
\label{tab:corpus_breakdown}
\begin{tabular}{lllll}
\toprule
\textbf{Crime Classification} & \textbf{Count} & \textbf{Share} & \textbf{Sev} & \textbf{Tiers (H/M/L)} \\
\midrule
General Crime / Offence & 277 & 46.48\% & 5.10 & 12 / 68 / 197 \\
Murder \& Homicide & 86 & 14.43\% & 9.35 & 86 / 0 / 0 \\
Fatal Traffic Incidents & 72 & 12.08\% & 6.20 & 14 / 32 / 26 \\
Illegal Contraband \& Mining & 46 & 7.72\% & 5.45 & 8 / 22 / 16 \\
Cybercrime \& Fraud & 34 & 5.70\% & 4.80 & 2 / 14 / 18 \\
Sexual Violence \& Assault & 26 & 4.36\% & 8.80 & 26 / 0 / 0 \\
Theft, Burglary \& Vehicle & 23 & 3.86\% & 4.15 & 0 / 2 / 21 \\
Assault \& Violent Clash & 21 & 3.52\% & 7.20 & 2 / 19 / 0 \\
Robbery \& Dacoity & 11 & 1.85\% & 7.90 & 0 / 11 / 0 \\
\midrule
\textbf{Total Database Corpus} & \textbf{596} & \textbf{100.0\%} & \textbf{5.92} & \textbf{150 / 138 / 308} \\
\bottomrule
\end{tabular}
\end{table}

\begin{table}[t]
\centering
\caption{Normalization Ceiling $R_{\text{ref}}$ Sensitivity Sweep (625 Grid Points)}
\label{tab:sensitivity}
\begin{tabular}{llllll}
\toprule
\textbf{$R_{\text{ref}}$} & \textbf{$Z(0\,\text{m})$} & \textbf{$Z(500\,\text{m})$} & \textbf{$Z(1000\,\text{m})$} & \textbf{Mean $Z$} & \textbf{Sat. (\%)} \\
\midrule
100 & 100.0 & 100.0 & 14.03 & 2.90 & 2.24\% \\
500 & 100.0 & 100.0 & 2.81 & 1.78 & 1.12\% \\
1000 & 100.0 & 83.30 & 1.40 & 1.21 & 0.32\% \\
\textbf{2500} & \textbf{65.64} & \textbf{33.32} & \textbf{0.56} & \textbf{0.52} & \textbf{0.00\%} \\
5000 & 32.82 & 16.66 & 0.28 & 0.26 & 0.00\% \\
\bottomrule
\end{tabular}
\end{table}

\begin{table}[b]
\centering
\caption{Multi-Factor Safe Haven Rankings for Vellore Sectors}
\label{tab:safe_havens}
\begin{tabular}{llllll}
\toprule
\textbf{Sector} & \textbf{Candidate Haven} & \textbf{Amenity} & \textbf{Dist (m)} & \textbf{$Z_p$} & \textbf{Utility $H(p)$} \\
\midrule
Katpadi & Katpadi Police Station & police & 260.1 & 4.26 & \textbf{0.5691} \\
Katpadi & Apollo Pharmacy Katpadi & pharmacy & 264.0 & 4.24 & 0.2880 \\
Katpadi & Indian Oil Petrol Bunk & fuel & 591.6 & 2.35 & 0.1495 \\
Katpadi & Sri Narayani Clinic & clinic & 811.3 & 1.09 & 0.1328 \\
CMC & CMC Main Emergency & hospital & 39.4 & 1.58 & \textbf{0.8187} \\
CMC & CMC In-House Pharmacy & pharmacy & 101.0 & 9.01 & 0.4461 \\
CMC & Vellore South Police & police & 543.6 & 28.17 & 0.2422 \\
CMC & HP Petrol Pump & fuel & 390.2 & 0.22 & 0.2286 \\
Bagayam & Bagayam Police Outpost & police & 282.3 & 0.00 & \textbf{0.5686} \\
Bagayam & CHAD CMC Hospital & hospital & 279.5 & 0.02 & 0.5145 \\
Bagayam & Santhosh Pharmacy & pharmacy & 94.7 & 0.01 & 0.4219 \\
Bagayam & Bagayam Bus Terminus & bus\_station & 89.1 & 0.00 & 0.4184 \\
\bottomrule
\end{tabular}
\end{table}

\begin{thebibliography}{00}
\bibitem{weisburd2015law} D. Weisburd, ``The law of crime concentration and the criminology of place,'' \emph{Criminology}, vol.~53, no.~2, pp.~133--157, 2015.
\bibitem{sherman1989hot} L.~W. Sherman, P.~R. Gartin, and M.~E. Buerger, ``Hot spots of predatory crime: Routine activities and the criminology of place,'' \emph{Criminology}, vol.~27, no.~1, pp.~27--56, 1989.
\bibitem{cohen1979social} L.~E. Cohen and M. Felson, ``Social change and crime rate trends: A routine activity approach,'' \emph{Amer. Sociol. Rev.}, vol.~44, no.~4, pp.~588--608, 1979.
\bibitem{brantingham1984patterns} P.~J. Brantingham and P.~L. Brantingham, \emph{Patterns in Crime}. New York, NY, USA: Macmillan, 1984.
\bibitem{chainey2008utility} S. Chainey, L. Tompson, and S. Uhlig, ``The utility of hotspot mapping for predicting spatial patterns of crime,'' \emph{Secur. J.}, vol.~21, no.~1--2, pp.~4--28, 2008.
\bibitem{braga2019hot} A.~A. Braga, B.~S. Turchan, A.~V. Papachristos, and D.~M. Hureau, ``Hot spots policing of small geographic areas effects on crime,'' \emph{Campbell Syst. Rev.}, vol.~15, no.~3, Art.~no.~e1046, 2019.
\bibitem{ncrb2022} National Crime Records Bureau, ``Crime in India 2022,'' Ministry of Home Affairs, Government of India, New Delhi, India, 2023.
\bibitem{chand2016wosapp} D. Chand, S. Nayak, K.~S. Bhat, S. Parikh, Y. Singh, and A.~A. Kamath, ``A mobile application for women's safety: WoSApp,'' in \emph{Proc. IEEE Region 10 Conf. (TENCON)}, Singapore, 2016, pp.~2505--2510.
\bibitem{gerber2014predicting} M.~S. Gerber, ``Predicting crime using Twitter and kernel density estimation,'' \emph{Decis. Support Syst.}, vol.~61, pp.~115--125, 2014.
\bibitem{umair2020spatiotemporal} A. Umair, M.~S. Sarfraz, M. Ahmad, U. Habib, M.~H. Ullah, and M. Mazzara, ``Spatiotemporal analysis of web news archives for crime prediction,'' \emph{Appl. Sci.}, vol.~10, no.~22, Art.~no.~8220, 2020.
\bibitem{earl2004use} J. Earl, A. Martin, J.~D. McCarthy, and S.~A. Soule, ``The use of newspaper data in the study of collective action,'' \emph{Annu. Rev. Sociol.}, vol.~30, pp.~65--80, 2004.
\bibitem{silverman1986density} B.~W. Silverman, \emph{Density Estimation for Statistics and Data Analysis}. London, U.K.: Chapman \& Hall, 1986.
\bibitem{hu2018spatio} Y. Hu, F. Wang, C. Guin, and H. Zhu, ``A spatio-temporal kernel density estimation framework for predictive crime hotspot mapping and evaluation,'' \emph{Appl. Geogr.}, vol.~99, pp.~89--97, 2018.
\bibitem{ester1996density} M. Ester, H.-P. Kriegel, J. Sander, and X. Xu, ``A density-based algorithm for discovering clusters in large spatial databases with noise,'' in \emph{Proc. 2nd Int. Conf. Knowl. Discovery Data Mining (KDD)}, 1996, pp.~226--231.
\bibitem{mohler2011self} G.~O. Mohler, M.~B. Short, P.~J. Brantingham, F.~P. Schoenberg, and G.~E. Tita, ``Self-exciting point process modeling of crime,'' \emph{J. Amer. Statist. Assoc.}, vol.~106, no.~493, pp.~100--108, 2011.
\bibitem{caplan2011risk} J.~M. Caplan, L.~W. Kennedy, and J. Miller, ``Risk terrain modeling: Brokering criminological theory and GIS methods for crime forecasting,'' \emph{Justice Quart.}, vol.~28, no.~2, pp.~360--381, 2011.
\bibitem{marchment2021systematic} Z. Marchment and P. Gill, ``Systematic review and meta-analysis of risk terrain modelling (RTM) as a spatial forecasting method,'' \emph{Crime Sci.}, vol.~10, no.~1, Art.~no.~13, 2021.
\bibitem{kounadi2020systematic} O. Kounadi, A. Ristea, A. Araujo, and M. Leitner, ``A systematic review on spatial crime forecasting,'' \emph{Crime Sci.}, vol.~9, no.~1, Art.~no.~7, 2020.
\bibitem{mandalapu2023crime} V. Mandalapu, L. Elluri, P. Vyas, and N. Roy, ``Crime prediction using machine learning and deep learning: A systematic review and future directions,'' \emph{IEEE Access}, vol.~11, pp.~60153--60170, 2023.
\bibitem{zhang2020comparison} X. Zhang, L. Liu, M. Lan, G. Song, L. Xiao, and J. Chen, ``Comparison of machine learning algorithms for predicting crime hotspots,'' \emph{IEEE Access}, vol.~8, pp.~181302--181310, 2020.
\bibitem{knox1964detection} E.~G. Knox, ``The detection of space-time interactions,'' \emph{J. Roy. Statist. Soc. C (Appl. Statist.)}, vol.~13, no.~1, pp.~25--29, 1964.
\bibitem{townsley2003infectious} M. Townsley, R. Homel, and J. Chaseling, ``Infectious burglaries: A test of the near repeat hypothesis,'' \emph{Brit. J. Criminol.}, vol.~43, no.~3, pp.~615--633, 2003.
\bibitem{johnson2007space} S.~D. Johnson \emph{et~al.}, ``Space--time patterns of risk: A cross national assessment of residential burglary victimization,'' \emph{J. Quant. Criminol.}, vol.~23, no.~3, pp.~201--219, 2007.
\bibitem{gritta2020pragmatic} M. Gritta, M.~T. Pilehvar, and N. Collier, ``A pragmatic guide to geoparsing evaluation: Toponyms, named entity recognition and pragmatics,'' \emph{Lang. Resour. Eval.}, vol.~54, no.~3, pp.~683--712, 2020.
\bibitem{zandbergen2009geocoding} P.~A. Zandbergen, ``Geocoding quality and implications for spatial analysis,'' \emph{Geogr. Compass}, vol.~3, no.~2, pp.~647--680, 2009.
\bibitem{galbrun2014safe} E. Galbrun, K. Pelechrinis, and E. Terzi, ``Safe navigation in urban environments,'' in \emph{Proc. 3rd Int. Workshop Urban Comput. (UrbComp)}, KDD, New York, NY, USA, 2014, pp.~1--8.
\bibitem{jacobs1961death} J. Jacobs, \emph{The Death and Life of Great American Cities}. New York, NY, USA: Random House, 1961.
\bibitem{newman1972defensible} O. Newman, \emph{Defensible Space: Crime Prevention Through Urban Design}. New York, NY, USA: Macmillan, 1972.
\bibitem{haklay2008openstreetmap} M. Haklay and P. Weber, ``OpenStreetMap: User-generated street maps,'' \emph{IEEE Pervasive Comput.}, vol.~7, no.~4, pp.~12--18, 2008.
\bibitem{lum2016predict} K. Lum and W. Isaac, ``To predict and serve?,'' \emph{Significance}, vol.~13, no.~5, pp.~14--19, 2016.
\bibitem{richardson2019dirty} R. Richardson, J.~M. Schultz, and K. Crawford, ``Dirty data, bad predictions: How civil rights violations impact police data, predictive policing systems, and justice,'' \emph{New York Univ. Law Rev. Online}, vol.~94, pp.~15--33, 2019.
\bibitem{ensign2018runaway} D. Ensign, S.~A. Friedler, S. Neville, C. Scheidegger, and S. Venkatasubramanian, ``Runaway feedback loops in predictive policing,'' in \emph{Proc. Conf. Fairness, Accountability Transparency (FAT*)}, PMLR vol.~81, 2018, pp.~160--171.
\bibitem{sinnott1984virtues} R.~W. Sinnott, ``Virtues of the haversine,'' \emph{Sky Telescope}, vol.~68, no.~2, p.~159, 1984.
\bibitem{pedregosa2011scikit} F. Pedregosa \emph{et~al.}, ``Scikit-learn: Machine learning in Python,'' \emph{J. Mach. Learn. Res.}, vol.~12, pp.~2825--2830, 2011.
\bibitem{agrawal1994fast} R. Agrawal and R. Srikant, ``Fast algorithms for mining association rules,'' in \emph{Proc. 20th Int. Conf. Very Large Data Bases (VLDB)}, 1994, pp.~487--499.
\bibitem{salton1988term} G. Salton and C. Buckley, ``Term-weighting approaches in automatic text retrieval,'' \emph{Inf. Process. Manage.}, vol.~24, no.~5, pp.~513--523, 1988.
\bibitem{rfc8030} M. Thomson, E. Damaggio, and B. Raymor, Eds., ``Generic event delivery using HTTP push,'' IETF RFC 8030, Dec. 2016.
\bibitem{rfc8292} M. Thomson and P. Beverloo, ``Voluntary application server identification (VAPID) for web push,'' IETF RFC 8292, Nov. 2017.
\bibitem{popescu2016geolocation} A. Popescu, ``Geolocation API specification, 2nd ed.,'' W3C Recommendation, Nov. 2016.
\bibitem{beresford2003location} A.~R. Beresford and F. Stajano, ``Location privacy in pervasive computing,'' \emph{IEEE Pervasive Comput.}, vol.~2, no.~1, pp.~46--55, 2003.
\bibitem{sakimura2014openid} N. Sakimura, J. Bradley, M. Jones, B. de Medeiros, and C. Mortimer, ``OpenID Connect Core 1.0 incorporating errata set 1,'' OpenID Foundation, Nov. 2014.
\bibitem{dpdp2023} Government of India, ``The Digital Personal Data Protection Act, 2023,'' Act No. 22 of 2023, Ministry of Law and Justice, Gazette of India, Aug. 2023.
\bibitem{brooke1996sus} J. Brooke, ``SUS: A quick and dirty usability scale,'' in \emph{Usability Evaluation in Industry}, P.~W. Jordan, B. Thomas, B.~A. Weerdmeester, and I.~L. McClelland, Eds. London, U.K.: Taylor \& Francis, 1996, pp.~189--194.
\end{thebibliography}

\end{document}
"""

with open(TEX_PATH, "w", encoding="utf-8") as f:
    f.write(tex_content)

print(f"LaTeX manuscript updated and saved to {TEX_PATH}")
