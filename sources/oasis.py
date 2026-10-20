"""OASIS source: official MQTT / AMQP / MQTT-SN / Sparkplug specification PDFs."""
import config as cfg
from models import Document
from sources.base import BaseSource


class OasisSource(BaseSource):
    name = "oasis"
    label = "oasis"
    display = "OASIS (MQTT, AMQP, MQTT-SN, Sparkplug standards)"

    def discover(self):
        docs = []
        with self.query_progress(list(cfg.OASIS_SPECS), "OASIS specs"):
            for spec in cfg.OASIS_SPECS:
                for url in spec["urls"]:
                    if self._url_serves_pdf(url):
                        docs.append(Document(
                            source=self.label,
                            url=url,
                            title=spec["title"],
                            year=spec.get("year"),
                            doc_id="",
                        ))
                        break
                self.sleep()
        return docs

    def _url_serves_pdf(self, url: str) -> bool:
        """Light HEAD-style probe; falls back to GET-stream when HEAD fails."""
        import requests
        try:
            resp = self.session.head(url, timeout=cfg.REQUEST_TIMEOUT,
                                     allow_redirects=True)
            if resp.ok and "pdf" in resp.headers.get("Content-Type", "").lower():
                return True
        except Exception:
            pass
        try:
            with self.session.get(url, timeout=cfg.REQUEST_TIMEOUT,
                                  stream=True, allow_redirects=True) as resp:
                if resp.ok:
                    chunk = next(resp.iter_content(64), b"")
                    return chunk.startswith(b"%PDF-")
        except Exception:
            pass
        return False
