"""Semantic Scholar source: open-access PDFs via the free Graph API.

Handles aggressive shared-pool rate limiting (HTTP 429) with patient
exponential backoff and keeps only PDF URLs hosted on reputable domains.
"""
import time

import config as cfg
import utils
from models import Document
from sources.base import BaseSource

S2_API = "https://api.semanticscholar.org/graph/v1/paper/search"


class SemanticScholarSource(BaseSource):
    name = "semantic_scholar"
    label = "s2"
    display = "Semantic Scholar (open-access papers, reputable hosts only)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._rate_limited = 0
        self._pool_exhausted = False

    def _search(self, query: str, limit: int = 100):
        params = {
            "query": query,
            "limit": limit,
            "fields": "title,year,openAccessPdf,externalIds,venue",
            "year": f"{self.min_year}-",
        }
        headers = {}
        api_key = cfg.S2_API_KEY
        if not api_key:
            import os
            api_key = os.environ.get("S2_API_KEY", "")
        if api_key:
            headers["x-api-key"] = api_key

        for attempt in range(1, 4):  # patient but bounded: 3 tries per query
            try:
                resp = self.session.get(S2_API, params=params,
                                        headers=headers, timeout=cfg.REQUEST_TIMEOUT)
                if resp.status_code == 429:
                    self._rate_limited += 1
                    time.sleep(5 * attempt + 3)
                    continue
                if resp.ok:
                    return resp.json().get("data", []), True
                return [], True
            except Exception:
                time.sleep(3 * attempt)
        return [], False  # still rate-limited after all tries

    def discover(self):
        docs = []
        with self.query_progress(list(cfg.S2_QUERIES), "S2 queries"):
            for query in cfg.S2_QUERIES:
                if self._pool_exhausted:
                    break  # shared pool drained -> stop hammering the API
                papers, ok = self._search(query)
                if not ok and self._rate_limited >= 6:
                    self._pool_exhausted = True
                    utils.say("    !! Semantic Scholar rate limit exhausted - "
                              "continuing with other sources")
                    break
                for paper in papers:
                    oa = paper.get("openAccessPdf") or {}
                    url = (oa.get("url") or "").strip()
                    year = paper.get("year")
                    title = (paper.get("title") or "").strip()
                    if not url or not title:
                        continue
                    if year is not None and year < self.min_year:
                        continue
                    if not utils.host_allowed(url, cfg.S2_PDF_HOST_WHITELIST):
                        continue  # reputable hosts only
                    docs.append(Document(
                        source=self.label,
                        url=url,
                        title=title,
                        year=year if isinstance(year, int) else None,
                        doc_id=(paper.get("externalIds") or {}).get("DOI", ""),
                        notes=paper.get("venue", "") or "",
                    ))
                self.sleep()
        return docs
