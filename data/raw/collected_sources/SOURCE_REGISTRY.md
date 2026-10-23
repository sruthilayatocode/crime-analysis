# CrimeSense — Acceptable Source Registry

This document defines which source types and domains are acceptable for future
Vellore-region incident collection. It exists to keep provenance verifiable and
consistent. **No incidents may be added unless they cite one of these acceptable
source types with a real, verifiable URL.**

> Current dataset status: **89 validated records** (unchanged). This file creates
> no records — it only documents the source policy.

---

## Source priority & types

### 1. Reputable Tamil Nadu news outlets
Prefer outlets with an editorial desk and a stable article URL.

| Outlet | Base domain (canonical) | Notes |
|---|---|---|
| The Hindu – Tamil Nadu | `thehindu.com` | Preferred; TN desk |
| The New Indian Express | `newindianexpress.com` | TN bureau; has `states/tamil-nadu`, `cities/vellore` |
| The Times of India | `timesofindia.indiatimes.com` | City/Vellore section |
| DT Next | `dtnext.in` | Tamil Nadu daily |
| The News Minute | `thenewsminute.com` | TN-focused (verified source in existing 89) |
| Maalai Malar | `maalaimalar.com` | Tamil-language |
| Daily Thanthi | `dailythanthi.com` | Tamil-language |
| Dinamalar | `dinamalar.com` | Tamil-language |
| Dinamani | `dinamani.com` | Tamil-language |
| Vikatan | `vikatan.com` | Tamil-language magazine |

### 2. Reputable Indian newspapers / national press
`thehindubusinessline.com` (Business Line), `indianexpress.com`, `indiatoday.in`,
`ndtv.com`, `news18.com`, `deccanherald.com`, `thewire.in`, `timesnownews.com`,
`etvbharat.com`, `keralakaumudi.com`, `hansindia.com`, `afternoonnews.in`,
`medicaldialogues.in` (health cases), `Press Trust of India`, `Khmer Times`
(only for international-nexus Vellore cases already used in the 89).

### 3. Official police / government sources (publicly accessible only)
| Domain | Type | Policy |
|---|---|---|
| `tnpolice.gov.in` | Tamil Nadu Police | Use only publicly published pages / press notes; never logged-in or CAPTCHA-gated data |
| `vellore.nic.in` | Vellore District Government | Publicly posted district notices/awards |
| `eservices.tnpolice.gov.in` | TN e-services portal | **FIR/CSR lookups require authentication** — do NOT bypass; do NOT use |
| `data.gov.in` | Open Government Data | Only downloadable, license-permitted crime datasets |
| `scrbidia.com` / SCRB TN | Crime statistics | **Statistics only for validation, never to invent rows** |

### 4. Publicly accessible district-level crime reports
- District crime statistics published by TN Police / CPIR (Crime in India reports).
- Used for **validation only** — never converted into individual incident rows.

---

## Acceptable / unacceptable URL patterns

- **Accepted:** a direct, working article URL (HTTP 200) that describes the individual incident.
  > e.g. `thehindu.com/.../article-slug` , `newindianexpress.com/.../article-slug`
- **Rejected:** `news.google.com/articles/...` (licence-restricted & session-locked),
  search-result pages, snippet-only links, fabrication helper redirects, bare
  domain names with no article, or any URL that cannot be fetched/verified.

---

## Import rules
1. One incident = one record.
2. Every record uses a URL from the acceptable set above that is fetched and confirmed.
3. Missing latitude/longitude remain `NULL`; never derive coordinates from a locality.
4. `state` default `Tamil Nadu`; district `Vellore`; locality one of the scoped Vellore-region places (Vellore, Katpadi, Gudiyatham, Pernambut, Ambur, Arcot, Ranipet, Sripuranthapuram, etc.).
5. No records are created from search snippets, aggregates, or statistics.

## How to add a source
Paste the candidate URL + headline into a new row in `batch_001.json`, then a human/web verifier confirms the article exists and describes the incident. Only after verification does the pipeline accept it.

---

## Permitted discovery channels (verified)

| Source | Method | Coverage | Status |
|---|---|---|---|
| `newindianexpress.com` | Daily sitemaps `/sitemap/sitemap-daily-YYYY-MM-DD.xml` | robots `Allow: /`; verified working back to **2018** | ✅ ACTIVE |
| `dtnext.in` | Daily sitemaps `/sitemap/sitemap-daily-YYYY-MM-DD.xml` (index: `/sitemap.xml`) | robots `Allow: /`; verified working back to **2016-10-17** | ✅ ACTIVE |
| `thehindu.com` | Topic page `/topic/vellore/` returns 200 but article lists are JS-rendered (only 15 unrelated `.ece` links). Archive sitemaps `/sitemap/archive*` and `/search/` are **robots-Disallowed**; only recent update feeds permitted | limited to recent items | ⚠️ LIMITED |
| `timesofindia.indiatimes.com` | robots mostly allows, but Akamai bot-block in practice (`failed_pages.log`) | — | ❌ BLOCKED |
| TN Police e-services (FIR/CSR) | Auth/CAPTCHA gated | — | ❌ OFF-LIMITS |

Collector: `scripts/collect_news.py` (env: `CS_START_YEAR`, `CS_END_YEAR`,
`CS_SITEMAPS`, `CS_MAX_FETCH`, `CS_RATE_LIMIT`, `CS_SOURCE=nie|dtnext|both`).

---

## Historical Vellore region rule (2019 district reorganization)

Vellore district was split in 2019; historical-region incidents may now fall in
**Ranipet** or **Tirupattur**. Rules:

1. The collector searches the full historical region: Vellore, Katpadi,
   Gudiyatham, Pernambut, Ambur, Vaniyambadi, Tirupattur, Jolarpet,
   Natrampalli, Sholingur, Walajapet, Arcot, Ranipet, Melvisharam,
   Arakkonam, Anaicut, Alangayam.
2. **The SOURCE's own district/locality wording is preserved** — a Ranipet-era
   Sholingur report is NOT relabelled as present-day Vellore.
3. Records whose locality maps to Ranipet/Tirupattur carry
   `historical_region: "Ranipet"|"Tirupattur"` in the candidate pool for review.
4. Pipeline scope check (`is_vellore`) accepts current-Vellore-district places
   (incl. Katpadi, Gudiyatham, Anaicut); post-2019-moved places are staged by
   the collector but must be explicitly reviewed before acceptance.

---

## Automated collection status (BLOCKED — read this)

**No machine-readable source is currently configured in this repository** — there
is no news API key, no permitted RSS/sitemap ingest, and no archive/export file.
That is the reason the expansion pipeline holds `0` accepted records: it is not a
code limitation, it is an absence of a *legitimate, verifiable input source*.

Automated collection was tested against the permitted public outlets and could
not legitimately obtain individual Vellore incident articles:

| Channel | Outcome |
|---|---|
| Google News / Google RSS | **Not permitted** — licence restricts use to personal reading; also the "do not scrape" rule |
| The Hindu – TN section | Accessible page but contained no Vellore individual-crime articles |
| New Indian Express – TN | Accessible; no Vellore-region crime items on the listing page |
| DT Next TN | HTTP 404 |
| The Hindu Vellore city page | HTTP 404 |
| TOI / Deccan Chronicle | Bot-blocked (see `data/raw/news/failed_pages.log`) |
| TN Police e-services (FIR/CSR) | Authentication/CAPTCHA gated — off-limits by rule |

### To unblock collection (any ONE of these suffices)
1. **Researcher-supplied batches** (recommended): put real verified rows into
   `batches/batch_NNN.json` or `.csv`, then run the pipeline.
2. A licensed/paid news-archive API key with permission for bulk retrieval.
3. An officially published, licence-permitted crime dataset export
   (`data.gov.in`-style) containing incident-level records.
4. An outlet-provided sitemap/export that explicitly permits ingestion.

Until one of those exists, the honest count remains **89 validated records** and
the pipeline will keep reporting `0` newly accepted records rather than fabricate
anything.