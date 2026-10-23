import re, os

md_path = r"c:\Users\sruth\crime analysis\research_paper\CRIMESENSE_RESEARCH_PAPER.md"
tex_path = r"c:\Users\sruth\crime analysis\research_paper\crimesense_ieee_conference.tex"

with open(md_path, "r", encoding="utf-8") as f:
    text = f.read()

new_disc_concl = """## VII. DISCUSSION, ETHICS, AND THREATS TO VALIDITY

### A. What Is New
Core elements of spatial crime analysis, near repeat testing, safe routing, and emergency alerting possess established research literatures. CrimeSense organizes these concepts around a single shared evidence base. The current database supports the administrative dashboard. The proposed resident advisory, safe-haven finder, and automated red-zone escalation would use the same incident records if implemented and validated. The haven finder and pre-visit advisory are designed to convert spatial data into immediate pedestrian guidance, while dwell escalation aims to address scenarios where victims are physically incapacitated.

### B. Ethics and Non-Stigmatizing Design
Assigning risk labels to urban sectors risks stigmatizing communities and amplifying data biases [30], [31], [32]. CrimeSense mitigates these harms by framing zones objectively as "reported incidents", displaying report counts and source links transparently, avoiding pejorative terms like "unsafe", stating clearly that green zones do not guarantee absolute safety, and excluding automated outputs from punitive policing loops [32]. Confirmation challenges and cooldown timers prevent alert fatigue.

### C. Limitations and Threats to Validity
News sourced datasets reflect journalistic coverage choices, which over represent unusual or severe offenses relative to minor infractions [11]. Locality centroid coordinates limit spatial precision [24], [25]. The severity score table is expert assigned rather than calibrated on longitudinal outcome metrics. OpenStreetMap haven records inherit volunteer mapping variations, and automated browser push notifications depend upon active browser lifecycles and mobile connectivity.

---

## VIII. CONCLUSION AND FUTURE WORK

This study presents CrimeSense, a prototype for visualizing news-reported crime incidents in Vellore. We verified the database structure and selected application functions using 596 records. The resident safety modules and pattern-recurrence methods remain to be evaluated as described in the implementation-status and evaluation sections. Database integrity, authentication, and persistence have been verified, while role enforcement remains partially active. Future work will execute rolling temporal evaluations, refine geocoding resolution, conduct physical safe haven audits, and evaluate user cognitive load through structured field usability trials.

---
"""

pattern = r"## VII\. DISCUSSION.*?(?=## REFERENCES)"
text_updated = re.sub(pattern, new_disc_concl + "\n", text, flags=re.DOTALL)

with open(md_path, "w", encoding="utf-8") as f:
    f.write(text_updated)

print("Updated CRIMESENSE_RESEARCH_PAPER.md successfully!")
