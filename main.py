#!/usr/bin/env python3
"""
IoT PDF Collector
=================
Downloads open-access PDFs about IoT protocols from reputable sources only:

  * arXiv            - official Atom API
  * RFC Editor       - official RFC PDFs (parsed from rfc-index.txt)
  * NIST             - CSRC publications (server-rendered pages)
  * OASIS            - MQTT / AMQP / MQTT-SN / Sparkplug standards
  * LoRa Alliance    - official LoRaWAN specifications
  * Semantic Scholar - open-access papers (reputable hosts whitelist)
  * MDPI             - Sensors / Electronics / IoT journals via DOAJ + OpenAlex
  * IETF Datatracker - IoT working-group Internet-Drafts

Features: nested tqdm progress bars, resume (existing valid PDFs are kept),
PDF magic-byte validation, polite per-source rate limiting, per-source
failure isolation (one broken source never stops the run).

Usage:
    python main.py                         # all sources, defaults
    python main.py --limit 30              # fewer files per source
    python main.py --sources arxiv rfc_editor nist
    python main.py --out /path/to/pdfs
    python main.py --list-sources
"""
import argparse
import sys
import time
from pathlib import Path

import config as cfg
import utils
from downloader import download_all
from models import Stats
from sources import SOURCE_NAMES, SOURCE_REGISTRY


BANNER = """
=========================================================================
   IoT PDF Collector - reputable open-access sources only
   Focus: MQTT | CoAP | LoRaWAN | 6LoWPAN | Zigbee | BLE | NB-IoT | ...
=========================================================================
"""


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Download IoT-protocol PDFs from reputable sources.")
    parser.add_argument("--limit", type=int, default=cfg.PER_SOURCE_LIMIT,
                        help=f"max PDFs per source (default {cfg.PER_SOURCE_LIMIT})")
    parser.add_argument("--out", type=str, default=cfg.OUTPUT_DIR,
                        help=f"output folder (default ./{cfg.OUTPUT_DIR})")
    parser.add_argument("--min-year", type=int, default=cfg.MIN_YEAR,
                        help=f"publication year filter for papers (default {cfg.MIN_YEAR})")
    parser.add_argument("--sources", nargs="+", choices=SOURCE_NAMES,
                        default=None, metavar="SOURCE",
                        help="subset of sources to run (default: all)")
    parser.add_argument("--delay-factor", type=float, default=1.0,
                        help="multiply all politeness delays (use 2.0 if rate-limited)")
    parser.add_argument("--list-sources", action="store_true",
                        help="print available sources and exit")
    return parser.parse_args(argv)


def list_sources():
    utils.say("Available sources:")
    for cls in SOURCE_REGISTRY:
        utils.say(f"  {cls.name:<18} {cls.display}")


def run_discovery(session, selected, limit, min_year, delay_factor):
    """Phase 1: crawl every source's catalog and build the download queue."""
    all_docs, seen_urls = [], set()
    total = len(selected)
    for idx, cls in enumerate(selected, 1):
        source = cls(session, limit=limit, min_year=min_year)
        utils.say(f"\n[{idx}/{total}] {source.display}")
        t0 = time.time()
        docs = source.collect(seen_urls)
        dt = time.time() - t0
        if docs:
            all_docs.extend(docs)
            preview = docs[0].title[:58] if docs[0].title else docs[0].url[:58]
            utils.say(f"    -> {len(docs)} PDFs queued (took {dt:.0f}s)")
            utils.say(f"       sample: {preview}")
        else:
            utils.say("    -> 0 PDFs found (source blocked, empty, or offline)")
    return all_docs


def main(argv=None):
    args = parse_args(argv)
    if args.list_sources:
        list_sources()
        return 0

    selected = SOURCE_REGISTRY
    if args.sources:
        wanted = set(args.sources)
        selected = [cls for cls in SOURCE_REGISTRY if cls.name in wanted]

    out_dir = Path(args.out).expanduser().resolve()
    utils.say(BANNER)
    utils.say(f"  Sources      : {', '.join(cls.name for cls in selected)}")
    utils.say(f"  Keywords     : {', '.join(cfg.IOT_KEYWORDS[:8])} ...")
    utils.say(f"  Output folder: {out_dir}")
    utils.say(f"  Per-source limit: {args.limit} | min year: {args.min_year} "
              f"(canonical specs exempt) | delay factor: {args.delay_factor}")

    session = utils.build_session(with_retries=False)      # discovery: fail fast
    download_session = utils.build_session(with_retries=True)  # downloads: patient

    # ---------------- Phase 1: discovery ----------------
    t0 = time.time()
    documents = run_discovery(session, selected, args.limit,
                              args.min_year, args.delay_factor)
    utils.say(f"\nDiscovery finished: {len(documents)} unique PDFs queued "
              f"in {time.time() - t0:.0f}s")

    if not documents:
        utils.say("\nNothing to download. Possible causes: no internet access, "
                  "or every source blocked this network. Try again later or "
                  "from a different network.")
        return 1

    # ---------------- Phase 2: download ----------------
    exempt = cfg.SOURCES_EXEMPT_FROM_YEAR_FILTER
    stats = Stats()
    utils.say(f"\nDownloading into: {out_dir}\n")
    t0 = time.time()

    def delay_for(source_name: str) -> float:
        base = cfg.SOURCE_DELAYS.get(source_name, 1.5)
        return base * args.delay_factor

    try:
        download_all(
            session=download_session,
            documents=documents,
            out_dir=out_dir,
            stats=stats,
            delay_for_source=delay_for,
            min_size=cfg.MIN_PDF_SIZE,
            max_size=cfg.MAX_PDF_SIZE,
        )
    except KeyboardInterrupt:
        pass

    # ---------------- Summary ----------------
    dt = time.time() - t0
    utils.say("\n" + "=" * 73)
    utils.say("SUMMARY" + " " * 66)
    utils.say("-" * 73)
    for source_name, bucket in stats.per_source.items():
        note = " (canonical specs)" if source_name in exempt else ""
        utils.say(f"  {source_name:<18} downloaded {bucket['downloaded']:<4} "
                  f"failed {bucket['failed']:<3} "
                  f"skipped-existing {bucket['skipped_existing']:<3} "
                  f"invalid {bucket['invalid_pdf']}{note}")
    mb = stats.bytes_downloaded / (1024 * 1024)
    utils.say("-" * 73)
    utils.say(f"  TOTAL downloaded: {stats.downloaded}  |  failed: {stats.failed}  "
              f"|  skipped (already existed): {stats.skipped_existing}  "
              f"|  invalid: {stats.invalid_pdf}")
    utils.say(f"  Elapsed: {dt / 60:.1f} min | Volume: {mb:.1f} MB")
    utils.say(f"  Output folder: {out_dir}")
    if stats.failed:
        utils.say("  Tip: some 403/429 responses are normal on shared networks - "
                  "re-running keeps everything already downloaded (resume) "
                  "and retries only the missing files.")
    utils.say("=" * 73)
    return 0


if __name__ == "__main__":
    sys.exit(main())
