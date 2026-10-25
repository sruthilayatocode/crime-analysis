"""Resumable orchestrator: DISCOVERY -> FETCH -> EXTRACT -> VALIDATE ->
DEDUP -> GEOCODE -> CONFIDENCE -> INCIDENTS -> REPORT.

Usage:
  python -m scripts.collection.run_collect --pilot
  python -m scripts.collection.run_collect --sources dinamalar,dinamani \
      --sitemaps 60 --fetches 120

Pilot mode uses 2-3 sources with small budgets (per requirement: pilot before
scaling). The protected 89-record dataset is never modified. All state is
resumable: discovery ledger, fetch ledger, and candidate store.
"""
from __future__ import annotations
import argparse, time
from concurrent.futures import ThreadPoolExecutor, as_completed

from scripts.collection import config as CFG
from scripts.collection import discover as DISC
from scripts.collection import sources as SRC
from scripts.collection import store as STORE
from scripts.collection.extract import fetch_article
from scripts.collection.classify import validate as classify_validate
from scripts.collection.dedupe import deduplicate
from scripts.collection.geo import geocode_incidents
from scripts.collection.confidence import score_all, admissible
from scripts.collection import report as REPORT


def phase_fetch(pending, workers):
    """Fetch + extract pending article pages (failure-tolerant)."""
    articles, failed = [], 0
    done_urls = []

    def work(item):
        url, source_key = item
        art, st = fetch_article(url)
        return url, art, st

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(work, it) for it in pending]
        for i, fut in enumerate(as_completed(futs), 1):
            try:
                url, art, st = fut.result()
            except Exception:
                continue
            if art:
                articles.append(art)
            else:
                failed += 1
            done_urls.append(url)
            if i % 25 == 0:
                print(f"    fetched {i}/{len(pending)} "
                      f"(ok={len(articles)}, fail={failed})")
    STORE.mark_fetched(done_urls)
    return articles, failed


def phase_validate(articles):
    """Scope + crime-relevance + typing for each extracted article."""
    cands, rejected = [], 0
    for art in articles:
        try:
            rec = classify_validate(art)
        except Exception:
            rec = None
        if rec is None:
            rejected += 1
        else:
            cands.append(rec)
    return cands, rejected


def phase_incidents(cands):
    """Dedup -> geocode -> confidence -> acceptance gates."""
    main_scope = [c for c in cands if c.get("scope_class") in CFG.ACCEPT_SCOPES]
    side_scope = [c for c in cands
                  if c.get("scope_class") in CFG.SIDE_TABLE_SCOPES]
    incidents, prov, n_dup = deduplicate(main_scope)
    geocode_incidents(incidents)
    score_all(incidents)
    keep = [i for i in incidents if admissible(i)]
    return keep, prov, n_dup, side_scope


def run(sources_keys=None, max_sitemaps=None, fetches=None, workers=None):
    workers = workers or CFG.CONCURRENCY
    stats = {"discovered": 0, "fetched": 0, "fetch_failed": 0,
             "rejected": 0, "accepted": 0, "duplicates": 0}

    print("[1/6] DISCOVERY (sitemap index -> daily sitemaps, resumable)")
    disc = DISC.discover(sources_keys)
    stats["discovered"] = disc["new_urls"]
    for k, v in disc["summary"].items():
        print(f"    {k}: {v}")

    budget = fetches or CFG.MAX_ARTICLE_FETCHES_PER_RUN
    pending = DISC.pending_urls(limit=budget)
    print(f"[2/6] FETCH+EXTRACT: {len(pending)} pending articles "
          f"(budget {budget}, workers {workers})")
    articles, failed = phase_fetch(pending, workers)
    stats["fetched"], stats["fetch_failed"] = len(articles), failed

    print("[3/6] VALIDATE (scope -> crime relevance -> typing)")
    cands, rejected = phase_validate(articles)
    stats["rejected"] = rejected
    stats["accepted"] = len(cands)
    print(f"    candidates: {len(cands)} | rejected: {rejected}")
    if cands:
        STORE.add_candidates(cands)

    # Re-validate the FULL accumulated candidate store each run (idempotent):
    # classifier/scoper improvements apply retroactively, and incident building
    # is resumable — nothing validated is ever lost.
    all_cands = STORE.load_candidates()
    fresh = [c for c in all_cands if not c.get("side_table")]
    print(f"[4/6] DEDUP over full candidate store ({len(fresh)} candidates)")
    keep, prov, n_dup, side = phase_incidents(fresh)
    stats["duplicates"] = n_dup
    print(f"    incidents kept: {len(keep)} | dup collapsed: {n_dup} | "
          f"historic-side: {len(side)}")

    print("[5/6] PERSIST (incidents + provenance, resumable upsert)")
    res = STORE.upsert_incidents(keep)
    np = STORE.add_provenance(prov)
    print(f"    incidents added={res['added']} updated={res['updated']} "
          f"| provenance rows={np}")
    if side:
        STORE.add_candidates([{**c, "side_table": True} for c in side])

    print("[6/6] EXPORT + REPORT")
    all_inc = STORE.load_incidents()
    all_prov = STORE.load_provenance()
    REPORT.export_csvs(all_inc, all_prov)
    REPORT.print_report(stats, all_inc)
    return stats


def _apply_budgets(sitemaps=None, fetches=None):
    """Runtime overrides so budgets are configurable from ONE place (config.py)
    with optional CLI refinement — no hard-coded run limits."""
    if sitemaps is not None:
        CFG.MAX_SITEMAPS_PER_SOURCE_PER_RUN = sitemaps
        DISC.MAX_SITEMAPS_PER_SOURCE_PER_RUN = sitemaps
    if fetches is not None:
        CFG.MAX_ARTICLE_FETCHES_PER_RUN = fetches


def main(argv=None):
    ap = argparse.ArgumentParser(description="CrimeSense incident collector")
    ap.add_argument("--pilot", action="store_true",
                    help="small controlled run: 3 sources, reduced budgets")
    ap.add_argument("--sources", default=None,
                    help="comma-separated source keys (default: all approved)")
    ap.add_argument("--sitemaps", type=int, default=None,
                    help="max sitemaps per source this run")
    ap.add_argument("--fetches", type=int, default=None,
                    help="max article fetches this run")
    ap.add_argument("--workers", type=int, default=None,
                    help="concurrent fetch workers")
    ap.add_argument("--report-only", action="store_true",
                    help="re-export CSVs + print audit report, no fetching")
    args = ap.parse_args(argv)

    if args.pilot:
        keys = (args.sources or "dinamalar,dinamani,dailythanthi").split(",")
        _apply_budgets(sitemaps=args.sitemaps or 6,
                       fetches=args.fetches or 60)
    else:
        keys = args.sources.split(",") if args.sources else None
        _apply_budgets(sitemaps=args.sitemaps, fetches=args.fetches)

    if args.report_only:
        all_inc = STORE.load_incidents()
        all_prov = STORE.load_provenance()
        REPORT.export_csvs(all_inc, all_prov)
        REPORT.print_report({}, all_inc)
        return 0

    t0 = time.time()
    stats = run(sources_keys=keys, workers=args.workers)
    print(f"\n    run wall time: {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
