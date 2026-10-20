"""NIST source: crawls CSRC publication detail pages (server-rendered).

Each curated CSRC page exposes the official PDF link on nvlpubs.nist.gov
plus the exact title. nvlpubs returns 404 for HEAD requests, therefore the
downloader uses GET (streaming) - which is what downloader.py does anyway.
"""
import re

import config as cfg
import utils
from models import Document
from sources.base import BaseSource

CSRC_BASE = "https://csrc.nist.gov"


class NistSource(BaseSource):
    name = "nist"
    label = "nist"
    display = "NIST (CSRC publications, official PDFs)"

    def discover(self):
        docs = []
        with self.query_progress(list(cfg.NIST_CSRC_PATHS), "NIST pages"):
            for path in cfg.NIST_CSRC_PATHS:
                try:
                    resp = self.session.get(CSRC_BASE + path, timeout=cfg.REQUEST_TIMEOUT)
                    if resp.ok:
                        doc = self._parse_detail(resp.text, path)
                        if doc:
                            docs.append(doc)
                except Exception:
                    pass
                self.sleep()
        return docs

    def _parse_detail(self, html: str, path: str):
        pdf = self._first_nvlpubs_pdf(html)
        if not pdf:
            return None
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
        title = utils._ascii_fold(re.sub(r"\s+", " ", h1.group(1))).strip() if h1 else ""
        title = re.sub(r"\s+", " ", title)
        if not title:
            # fallback: derive from the nvlpubs filename, e.g. NIST.IR.8228.pdf
            title = pdf.rsplit("/", 1)[-1].replace(".pdf", "")

        doc_id = ""
        doi = re.search(r"10\.6028/(NIST\.[A-Za-z0-9.\-]+)", html)
        if doi:
            doc_id = doi.group(1)

        # Year from nvlpubs path (/ir/2019/) or DOI metadata on the page
        year = utils.extract_year(pdf.split("/nistpubs/", 1)[-1])
        if year is None:
            meta_date = re.search(
                r'citation_publication_date" content="([^"]+)"', html)
            if meta_date:
                year = utils.extract_year(meta_date.group(1))

        return Document(
            source=self.label,
            url=pdf,
            title=title,
            year=year,
            doc_id=doc_id or path,
        )

    @staticmethod
    def _first_nvlpubs_pdf(html: str):
        links = re.findall(r'href="(https?://nvlpubs\.nist\.gov/[^"]+\.pdf)"', html)
        return links[0] if links else None
