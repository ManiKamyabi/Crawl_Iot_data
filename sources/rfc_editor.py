"""RFC Editor source: parses rfc-index.txt and downloads official RFC PDFs."""
import re
from typing import List, Optional

import config as cfg
import utils
from models import Document
from sources.base import BaseSource

RFC_INDEX_URL = "https://www.rfc-editor.org/rfc-index.txt"
MONTHS = (
    "January|February|March|April|May|June|July|August|September|"
    "October|November|December"
)


class RfcEditorSource(BaseSource):
    name = "rfc_editor"
    label = "rfc"
    display = "RFC Editor / IETF (official RFC PDFs)"

    def discover(self):
        utils.say("    -> downloading rfc-index.txt (~2 MB) ...")
        resp = self.session.get(RFC_INDEX_URL, timeout=cfg.REQUEST_TIMEOUT * 2)
        resp.raise_for_status()
        entries = self._parse_index(resp.text)
        matched = [e for e in entries if self._matches(e["title"])]
        # newest first, so the per-source limit keeps the most recent RFCs
        matched.sort(key=lambda e: e["year"], reverse=True)
        utils.say(f"    -> matched {len(matched)} IoT-protocol RFCs "
                  f"(year >= {self.min_year})")
        docs: List[Document] = []
        for e in matched:
            docs.append(Document(
                source=self.label,
                url=f"https://www.rfc-editor.org/rfc/rfc{e['num']}.pdf",
                title=f"RFC {e['num']}: {e['title']}",
                year=e["year"],
                doc_id=f"RFC{e['num']}",
            ))
        return docs

    # ------------------------------------------------------------------
    def _parse_index(self, text: str):
        """Entries look like:

        9011 Static Context Header Compression and Fragmentation (SCHC) over
             LoRaWAN. O. Gimenez, Ed., I. Petrov, Ed.. April 2021. (Format:
             HTML, TXT, PDF, XML) (Status: PROPOSED STANDARD) (DOI: ...)
        """
        results = []
        for block in re.split(r"\n(?=\d{4}[\s.])", text):
            m = re.match(r"^(\d{4})[\s.](.*)", block, re.S)
            if not m:
                continue
            num, body = m.group(1), m.group(2)
            flat = re.sub(r"\s+", " ", body).strip()

            date_m = re.search(rf"\.\s+({MONTHS})\s+((?:19|20)\d{{2}})\.", flat)
            if not date_m:
                continue
            year = int(date_m.group(2))

            fmt = re.search(r"\(Format:([^)]*)\)", flat)
            if not fmt or "PDF" not in fmt.group(1).upper():
                continue  # no official PDF for this RFC

            if year < self.min_year:
                continue  # publication year filter

            if re.search(r"\(Obsoleted by", flat):
                continue  # superseded -> skip to avoid duplicates

            title = self._extract_title(flat)
            if not title:
                continue
            results.append({"num": num, "year": year, "title": title})
        return results

    @staticmethod
    def _extract_title(flat: str) -> Optional[str]:
        # Title runs until the first ". " that is followed by an author
        # initial pattern like "R. Fielding".
        m = re.match(r"(?P<title>.*?)\.\s+(?=[A-Z]\.\s)", flat)
        if m and m.group("title").strip():
            return m.group("title").strip()
        return None

    @staticmethod
    def _matches(title: str) -> bool:
        return any(re.search(p, title) for p in cfg.RFC_TITLE_PATTERNS)
