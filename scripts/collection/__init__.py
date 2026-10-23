"""CrimeSense scalable, incident-level collection pipeline.

Design goals (see collection/README.md):
  * resumable, paginated, rate-limited, cache-aware, source-aware, failure-tolerant
  * incident-level (NOT article-level) deduplication
  * mandatory provenance for every accepted record
  * zero fabrication: unknown fields stay NULL
  * additive: never modifies the protected 89-record validated dataset
"""
