"""LoRa Alliance source: decodes signed Uberflip download tokens (cmd=d).

The resources hub (resources.lora-alliance.org) server-renders item pages.
Each page embeds a cdntwrk.com file token whose base64 payload contains
"cmd=d" (download) for the actual specification PDF.
"""
import base64
import re

import config as cfg
import utils
from models import Document
from sources.base import BaseSource

ITEM_BASE = "https://resources.lora-alliance.org/technical-specifications/"
CDN_HOSTS = ("content.cdntwrk.com", "uberflip.cdntwrk.com")


class LoraAllianceSource(BaseSource):
    name = "lora_alliance"
    label = "lora"
    display = "LoRa Alliance (official LoRaWAN specifications)"

    def discover(self):
        docs = []
        with self.query_progress(list(cfg.LORA_ITEM_SLUGS), "LoRa items"):
            for slug in cfg.LORA_ITEM_SLUGS:
                doc = self._process_item(slug)
                if doc:
                    docs.append(doc)
                self.sleep()
        return docs

    def _process_item(self, slug: str):
        try:
            resp = self.session.get(ITEM_BASE + slug, timeout=cfg.REQUEST_TIMEOUT)
            if not resp.ok:
                return None
            html = resp.text
            title = self._og_title(html) or slug.replace("-", " ").title()

            for token in dict.fromkeys(
                re.findall(r'cdntwrk\.com/files/([A-Za-z0-9=]+)', html)
            ):
                payload = self._decode_token(token)
                if payload and re.search(r"cmd=d(&|$)", payload):
                    host = next(h for h in CDN_HOSTS if h in html) \
                        if any(h in html for h in CDN_HOSTS) else CDN_HOSTS[0]
                    return Document(
                        source=self.label,
                        url=f"https://{host}/files/{token}",
                        title=title,
                        year=utils.extract_year(title),
                        doc_id=slug,
                    )
        except Exception:
            return None
        return None

    @staticmethod
    def _decode_token(token: str):
        try:
            padded = token + "=" * (-len(token) % 4)
            return base64.b64decode(padded).decode("utf-8", "ignore")
        except Exception:
            return None

    @staticmethod
    def _og_title(html: str):
        m = re.search(r'property="og:title" content="([^"]+)"', html)
        return m.group(1).strip() if m else None
