"""
Streaming PDF downloader with nested tqdm progress bars.

Layout of the bars while running:

  Overall  35%|######        | 105/300 [01:40<03:06,  1.05file/s]
  RFC 9011 (SCHC over LoRaWAN).pdf  78%|#######  | 402k/515k [00:01<00:00, 392kB/s]
"""
import os
import time
from pathlib import Path
from typing import List

from tqdm import tqdm

import config as cfg
import utils
from models import Document, Stats


def _is_resume_complete(path: Path) -> bool:
    """A previously downloaded file counts as complete if it is a real PDF."""
    try:
        if not path.exists() or path.stat().st_size < cfg.MIN_PDF_SIZE:
            return False
        with open(path, "rb") as fh:
            head = fh.read(5)
        return head == b"%PDF-"
    except OSError:
        return False


def download_pdf(session, doc: Document, dest: Path, stats: Stats,
                 file_bar_desc: str, max_size: int) -> None:
    """Download one document into dest, validating the PDF magic bytes."""
    outcome, nbytes = "failed", 0
    try:
        with session.get(doc.url, stream=True, timeout=30, allow_redirects=True) as resp:
            if resp.status_code != 200:
                resp.close()
                stats.add(doc.source, "failed")
                return

            total = int(resp.headers.get("Content-Length") or 0)
            if total > max_size:
                resp.close()
                stats.add(doc.source, "failed")
                return

            bar = tqdm(
                total=total or None,
                unit="B", unit_scale=True, unit_divisor=1024,
                desc=file_bar_desc, leave=False, position=1,
                bar_format="{desc:.42} {percentage:3.0f}%|{bar:20}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
            )
            first_chunk = True
            tmp = dest.with_suffix(".part")
            try:
                with open(tmp, "wb") as fh:
                    for chunk in resp.iter_content(chunk_size=64 * 1024):
                        if not chunk:
                            continue
                        if first_chunk:
                            if not utils.looks_like_pdf(chunk):
                                # Not a real PDF (HTML login page, Cloudflare, ...)
                                bar.close()
                                stats.add(doc.source, "invalid_pdf")
                                return
                            first_chunk = False
                        fh.write(chunk)
                        nbytes += len(chunk)
                        bar.update(len(chunk))
            finally:
                try:
                    bar.close()
                except Exception:
                    pass

            if nbytes < cfg.MIN_PDF_SIZE:
                tmp.unlink(missing_ok=True)
                stats.add(doc.source, "invalid_pdf")
                return

            tmp.replace(dest)
            outcome = "downloaded"
            stats.add(doc.source, "downloaded", nbytes)

    except Exception:
        outcome = "failed"
        stats.add(doc.source, "failed")
    finally:
        if outcome != "downloaded":
            part = dest.with_suffix(".part")
            if part.exists():
                try:
                    part.unlink()
                except OSError:
                    pass


def download_all(session, documents: List[Document], out_dir: Path,
                 stats: Stats, delay_for_source, min_size: int, max_size: int) -> None:
    """Sequential, polite, resume-capable download of the whole queue."""
    out_dir.mkdir(parents=True, exist_ok=True)
    used_names: set = set()
    last_source = None

    overall = tqdm(
        total=len(documents), unit="file", position=0,
        desc="Overall", dynamic_ncols=True,
        bar_format="{desc} {percentage:3.0f}%|{bar:28}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
    )
    try:
        for doc in documents:
            if last_source is not None and doc.source != last_source:
                time.sleep(0.5)  # small pause when switching sources
            last_source = doc.source

            fname = utils.target_filename(doc, used_names)
            dest = out_dir / fname

            if dest.exists():
                if _is_resume_complete(dest):
                    stats.add(doc.source, "skipped_existing")
                else:
                    # Broken leftover file -> re-download
                    try:
                        dest.unlink()
                    except OSError:
                        pass
                    desc = f"{fname[:44]}"
                    download_pdf(session, doc, dest, stats, desc, max_size)
                    utils.polite_sleep(delay_for_source(doc.source))
            else:
                desc = f"{fname[:44]}"
                download_pdf(session, doc, dest, stats, desc, max_size)
                utils.polite_sleep(delay_for_source(doc.source))

            overall.update(1)
    except KeyboardInterrupt:
        tqdm.write("Interrupted by user - partial downloads kept.")
        raise
    finally:
        overall.close()
