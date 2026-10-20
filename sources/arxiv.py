"""arXiv source: official export.arxiv.org Atom API (free, no key needed)."""
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote

import config as cfg
import utils
from models import Document
from sources.base import BaseSource

ATOM_NS = {"a": "http://www.w3.org/2005/Atom"}
ARXIV_API = "http://export.arxiv.org/api/query"


class ArxivSource(BaseSource):
    name = "arxiv"
    label = "arxiv"
    display = "arXiv (open-access preprints)"

    QUERIES = [
        q for q in [
            *cfg.IOT_KEYWORDS,
        ]
    ]

    def _build_query(self, keyword: str) -> str:
        if keyword in cfg.ARXIV_STANDALONE:
            return f'abs:"{keyword}"'
        return f'abs:"{keyword}" AND (abs:"IoT" OR abs:"Internet of Things")'

    def discover(self):
        docs = []
        queries = self.QUERIES[:10]  # keep API load reasonable
        with self.query_progress(queries, "arXiv queries"):
            for keyword in queries:
                url = (
                    f"{ARXIV_API}?search_query={quote(self._build_query(keyword))}"
                    f"&start=0&max_results={cfg.ARXIV_MAX_RESULTS_PER_QUERY}"
                    "&sortBy=submittedDate&sortOrder=descending"
                )
                try:
                    resp = self.session.get(url, timeout=cfg.REQUEST_TIMEOUT)
                    if resp.ok:
                        docs.extend(self._parse_atom(resp.text))
                except Exception:
                    pass
                self.sleep()

        return self._year_filter(docs)

    def _parse_atom(self, xml_text: str):
        docs = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return docs
        for entry in root.findall("a:entry", ATOM_NS):
            eid = (entry.findtext("a:id", "", ATOM_NS) or "").strip()
            title = (entry.findtext("a:title", "", ATOM_NS) or "").strip()
            published = (entry.findtext("a:published", "", ATOM_NS) or "").strip()
            if not eid or not title:
                continue
            arxiv_id = eid.rsplit("/abs/", 1)[-1]
            year = int(published[:4]) if re.match(r"^\d{4}", published) else None
            docs.append(Document(
                source=self.label,
                url=f"https://arxiv.org/pdf/{arxiv_id}",
                title=title,
                year=year,
                doc_id=arxiv_id,
            ))
        return docs

    def _year_filter(self, docs):
        kept = [d for d in docs if d.year is None or d.year >= self.min_year]
        return kept
