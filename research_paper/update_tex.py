import re

tex_path = r"c:\Users\sruth\crime analysis\research_paper\crimesense_ieee_conference.tex"

with open(tex_path, "r", encoding="utf-8") as f:
    tex = f.read()

# 1. Update Abstract
new_abs = r"""\begin{abstract}
We developed CrimeSense to help users explore crime reports in Vellore and examine reported incidents around a selected location. The current system uses an SQLite database containing 596 news-derived incident records and includes an administrative dashboard for viewing and managing these records. We present an interpretable zone classification model that marks locations green, yellow, or red using spatial and temporal decay. To support pedestrian safety, we formulate design specifications for a pre-visit destination advisory, an OpenStreetMap-based safe haven finder relying on natural surveillance, and an automated red-zone inactivity state machine. In addition, we describe a pattern recurrence formulation applying Knox space-time permutation tests and association rules to identify sequential crime trends. Finally, we report database verification audits, role-separated authentication checks, and privacy safeguards conforming to the Indian Digital Personal Data Protection Act, followed by a formal evaluation protocol.
\end{abstract}"""

tex = re.sub(r'\\begin\{abstract\}.*?\\end\{abstract\}', lambda m: new_abs, tex, flags=re.DOTALL)

# 2. Update Intro paragraphs around bridging gaps and contributions
new_intro_p = r"""To address these gaps, we built a prototype that connects a news-derived crime database to an administrative dashboard and a proposed set of resident-facing safety features. Because city police stations in Tamil Nadu do not provide open API feeds of daily First Information Reports, we built our dataset from regional digital news coverage, following data collection practices proven in earlier spatial research \cite{gerber2014, umair2020} while keeping journalistic reporting biases in mind \cite{earl2004}. We constructed two interfaces over this shared data layer: an administrative console providing spatial heatmaps, DBSCAN cluster grouping, multi-year charts, user account controls, and emergency alert tables; and a responsive citizen interface designed for route checks, safe haven searches, and SOS alerts.

In this paper, we carefully differentiate fully verified software components from theoretical modules undergoing validation. Section III presents the system architecture. Section IV reports the current verification status across all components. Section V analyzes our 596-record empirical dataset. Section VI sets out an open evaluation protocol, and Section VII examines ethical implications, data limitations, and privacy compliance. Our primary contributions are:
\begin{itemize}
    \item A multi-tier architecture linking a 596-record news-derived SQLite database with an administrative GIS console and proposed citizen mobile views.
    \item A transparent spatio-temporal zone classification model that explains local evidence clearly rather than issuing opaque risk scores or declaring any place completely safe.
    \item A pattern recurrence formulation combining Knox space-time permutation tests and association rules to detect repeating crime sequences.
    \item A safe haven ranking formulation that evaluates candidate public shelters by operational status, distance, institutional guardianship weight, and surrounding crime exposure.
    \item An automated emergency escalation state machine design that detects prolonged inactivity within designated high-risk zones.
    \item A documented verification report of our active SQLite database (596 sourced records across 11 tables) and an empirical testing protocol for unvalidated modules.
\end{itemize}"""

tex = re.sub(r'To bridge these parallel divides.*?(?=\\section\{Related Work\})', lambda m: new_intro_p + '\n\n', tex, flags=re.DOTALL)

# 3. Update Discussion A. What Is New
new_disc_a = r"""\subsection{What Is New}
Core elements of spatial crime analysis, near repeat testing, safe routing, and emergency alerting possess established research literatures. CrimeSense organizes these concepts around a single shared evidence base. The current database supports the administrative dashboard. The proposed resident advisory, safe-haven finder, and automated red-zone escalation would use the same incident records if implemented and validated. The haven finder and pre-visit advisory are designed to convert spatial data into immediate pedestrian guidance, while dwell escalation aims to address scenarios where victims are physically incapacitated."""

tex = re.sub(r'\\subsection\{Distinction from Prior Art and Integrated Value\}.*?(?=\\subsection\{Ethical Considerations)', lambda m: new_disc_a + '\n\n', tex, flags=re.DOTALL)

# 4. Update Conclusion
new_concl = r"""\section{Conclusion and Future Work}
This study presents CrimeSense, a prototype for visualizing news-reported crime incidents in Vellore. We verified the database structure and selected application functions using 596 records. The resident safety modules and pattern-recurrence methods remain to be evaluated as described in the implementation-status and evaluation sections. Database integrity, authentication, and persistence have been verified, while role enforcement remains partially active. Future work will execute rolling temporal evaluations, refine geocoding resolution, conduct physical safe haven audits, and evaluate user cognitive load through structured field usability trials."""

tex = re.sub(r'\\section\{Conclusion and Future Work\}.*?(?=\\begin\{thebibliography\}|\Z)', lambda m: new_concl + '\n\n', tex, flags=re.DOTALL)

with open(tex_path, "w", encoding="utf-8") as f:
    f.write(tex)

print("Updated crimesense_ieee_conference.tex successfully!")
