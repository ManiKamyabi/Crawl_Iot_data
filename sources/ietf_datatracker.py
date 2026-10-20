"""IETF Datatracker source: active Internet-Drafts of IoT working groups.

Uses the official Datatracker REST API. PDFs are served from
https://datatracker.ietf.org/doc/pdf/<draft-name>. Some hosting networks
receive 403 from datatracker's bot protection - in that case the source
reports the problem and returns an empty list (the RFC Editor source
already covers IETF standards documents).
"""
import re

import config as cfg
import utils
from models import Document
from sources.base import BaseSource

API = "https://datatracker.ietf.org/api/v1/doc/document/"
PDF_BASE = "https://datatracker.ietf.org/doc/pdf/"


class IetfDatatrackerSource(BaseSource):
    name = "ietf_datatracker"
    label = "ietf"
    display = "IETF Datatracker (IoT working-group Internet-Drafts)"

    def discover(self):
        docs = []
        wgs = list(cfg.IETF_WG_LIST)
        with self.query_progress(wgs, "IETF WGs"):
            for wg in wgs:
                if self._blocked:
                    break
                docs.extend(self._wg_drafts(wg))
                self.sleep()
        return self._year_filter(docs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._blocked = False

    def _wg_drafts(self, wg: str):
        docs = []
        offset = 0
        page_size = 100
        for _ in range(4):  # up to 400 drafts per WG
            params = {
                "format": "json",
                "doctype": "draft",
                "group__acronym": wg,
                "limit": page_size,
                "offset": offset,
            }
            try:
                resp = self.session.get(API, params=params, timeout=cfg.REQUEST_TIMEOUT)
                if resp.status_code == 403:
                    self._blocked = True
                    utils.say("    !! datatracker blocked this IP (403) - "
                              "skipping IETF drafts (RFC source still covers IETF)")
                    return []
                if not resp.ok:
                    return docs
                payload = resp.json()
            except Exception:
                return docs

            objects = payload.get("objects", [])
            for obj in objects:
                doc = self._to_document(obj)
                if doc:
                    docs.append(doc)
            total = (payload.get("meta") or {}).get("total_count", 0)
            offset += page_size
            if offset >= total or not objects:
                break
        return docs

    def _to_document(self, obj):
        name = (obj.get("name") or "").strip()
        title = (obj.get("title") or "").strip()
        if not name or not title:
            return None
        if not name.startswith("draft-"):
            return None
        updated = obj.get("time") or ""
        year = int(updated[:4]) if re.match(r"^\d{4}", updated) else None
        return Document(
            source=self.label,
            url=PDF_BASE + name,
            title=title,
            year=year,
            doc_id=name,
            notes=name,
        )

    def _year_filter(self, docs):
        kept = [d for d in docs if d.year is None or d.year >= self.min_year]
        # dedupe by draft name (revisions repeat across WGs listings)
        unique, seen = [], set()
        for d in kept:
            key = d.doc_id
            if key in seen:
                continue
            seen.add(key)
            unique.append(d)
        return unique
