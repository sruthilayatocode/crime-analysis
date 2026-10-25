import re, shutil

html_repo = r"c:\Users\sruth\crime analysis\research_paper\CrimeSense_Research_Paper.html"
html_desk = r"c:\Users\sruth\Desktop\CrimeSense_Research_Paper.html"

with open(html_repo, "r", encoding="utf-8") as f:
    html = f.read()

# Update title to remove hyphens
html = html.replace(
    "CrimeSense: A Unified Crime-Hotspot Visualization, Dynamic Zone-Classification, and Personal-Safety Platform with Pattern-Recurrence Analysis for Tier-II Urban Environments",
    "CrimeSense: A Unified Crime Hotspot Visualization, Zone Classification and Personal Safety Platform with Pattern Recurrence Analysis for Vellore, India"
)

# Update Abstract
new_abs_html = """<span class="abstract-title">Abstract—</span>
      <span class="abstract-text">We developed CrimeSense to help users explore crime reports in Vellore and examine reported incidents around a selected location. The current system uses an SQLite database containing 596 news-derived incident records and includes an administrative dashboard for viewing and managing these records. We present an interpretable zone classification model that marks locations green, yellow, or red using spatial and temporal decay. To support pedestrian safety, we formulate design specifications for a pre-visit destination advisory, an OpenStreetMap-based safe haven finder relying on natural surveillance, and an automated red-zone inactivity state machine. In addition, we describe a pattern recurrence formulation applying Knox space-time permutation tests and association rules to identify sequential crime trends. Finally, we report database verification audits, role-separated authentication checks, and privacy safeguards conforming to the Indian Digital Personal Data Protection Act, followed by a formal evaluation protocol.</span>"""

html = re.sub(r'<div class="abstract-box">\s*<span class="abstract-title">.*?</span>\s*<span class="abstract-text">.*?</span>\s*</div>', f'<div class="abstract-box">\n      {new_abs_html}\n    </div>', html, flags=re.DOTALL)

with open(html_repo, "w", encoding="utf-8") as f:
    f.write(html)

shutil.copy2(html_repo, html_desk)
print("Updated HTML paper successfully on Repo and Desktop!")
