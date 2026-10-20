"""MDPI source: DOAJ API (primary) + OpenAlex (secondary).

DOAJ reliably exposes MDPI journal articles (Sensors, Electronics, ...).
Their fulltext links are article pages on mdpi.com; the PDF lives at
<url>/pdf, which is what we hand to the downloader (validated there).
Some networks get challenged by mdpi.com - those downloads are skipped
gracefully and the OpenAlex fallback provides extra candidates.
"""
import time

import config as cfg
import utils
from models import Document
from sources.base import BaseSource

DOAJ_API = "https://doaj.org/api/search/articles/{query}"
OPENALEX_API = "https://api.openalex.org/works"


class MdpiSource(BaseSource):
    name = "mdpi"
    label = "mdpi"
    display = "MDPI (Sensors/Electronics/IoT journals, open access)"

    def discover(self):
        docs = self._from_doaj()
        if len(docs) < self.limit:
            docs.extend(self._from_openalex(existing={d.url for d in docs}))
        return docs[: self.limit]

    # ------------------------------------------------------------------
    def _from_doaj(self):
        docs = []
        with self.query_progress(list(cfg.DOAJ_QUERIES), "DOAJ queries"):
            for query in cfg.DOAJ_QUERIES:
                try:
                    resp = self.session.get(
                        DOAJ_API.format(query=utils.urlencode(query)),
                        params={"pageSize": 100, "page": 1},
                        timeout=cfg.REQUEST_TIMEOUT,
                    )
                    if resp.ok:
                        docs.extend(self._parse_doaj(resp.json()))
                except Exception:
                    pass
                self.sleep()
        return docs

    def _parse_doaj(self, payload):
        docs = []
        for rec in payload.get("results", []):
            bib = rec.get("bibjson", {}) or {}
            journal = (bib.get("journal") or {}).get("title", "").strip()
            if journal not in cfg.MDPI_JOURNAL_TITLES:
                continue
            try:
                year = int(bib.get("year") or 0)
            except (TypeError, ValueError):
                year = None
            if year is not None and year < self.min_year:
                continue
            for link in bib.get("link", []):
                url = (link.get("url") or "").strip()
                if "mdpi.com" not in url:
                    continue
                if not url.lower().endswith("/pdf"):
                    url = url.rstrip("/") + "/pdf"
                docs.append(Document(
                    source=self.label,
                    url=url,
                    title=bib.get("title", "") or journal,
                    year=year,
                    doc_id=bib.get("id", ""),
                    notes=journal,
                ))
                break
        return docs

    # ------------------------------------------------------------------
    def _from_openalex(self, existing):
        docs = []
        issns = "|".join([
            "1424-8220",  # Sensors
            "2079-9292",  # Electronics
            "2076-3417",  # Applied Sciences
            "1999-5903",  # Future Internet
            "2673-8116",  # IoT
            "2224-2708",  # JSAN
        ])
        queries = ["IoT protocol", "MQTT", "LoRaWAN", "CoAP", "6LoWPAN"]
        with self.query_progress(queries, "OpenAlex queries"):
            for query in queries:
                try:
                    resp = self.session.get(
                        OPENALEX_API,
                        params={
                            "search": query,
                            "per-page": 100,
                            "mailto": cfg.OPENALEX_MAILTO,
                            "filter": (
                                "open_access.is_oa:true,"
                                f"from_publication_date:{self.min_year}-01-01,"
                                f"primary_location.source.issn:{issns}"
                            ),
                        },
                        timeout=cfg.REQUEST_TIMEOUT,
                    )
                    if resp.ok:
                        for work in resp.json().get("results", []):
                            doc = self._parse_openalex(work)
                            if doc and doc.url not in existing:
                                docs.append(doc)
                    elif resp.status_code == 429:
                        time.sleep(8)
                except Exception:
                    pass
                self.sleep()
        return docs

    def _parse_openalex(self, work):
        year = work.get("publication_year")
        title = (work.get("title") or "").strip()
        oa = work.get("best_oa_location") or {}
        url = (oa.get("pdf_url") or "").strip()
        if not url or not title:
            return None
        if "mdpi.com" not in url:
            return None
        if url.endswith(".pdf"):
            url = url[:-4]
        if not url.lower().endswith("/pdf"):
            url = url.rstrip("/") + "/pdf"
        return Document(
            source=self.label, url=url, title=title,
            year=year if isinstance(year, int) else None,
            doc_id=work.get("doi", "") or "",
        )
