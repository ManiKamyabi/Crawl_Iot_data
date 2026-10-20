"""Base class shared by every source crawler."""
import time
from typing import List

from tqdm import tqdm

import utils
from models import Document


class BaseSource:
    """One crawler per reputable source.

    Subclasses implement discover() and return Document objects. The base
    class provides a polite HTTP session, deduplication and the per-source
    discovery progress bar.
    """

    name = "base"        # unique key used in config dicts
    label = "src"        # filename prefix, e.g. "arxiv_..."
    display = "Base"     # pretty name for console output

    def __init__(self, session, limit: int, min_year: int, verbose: bool = True):
        self.session = session
        self.limit = limit
        self.min_year = min_year
        self.verbose = verbose
        self.delay = self._delay_for()

    # ------------------------------------------------------------------
    def _delay_for(self) -> float:
        try:
            import config as cfg
            return cfg.SOURCE_DELAYS.get(self.name, 1.5)
        except Exception:
            return 1.5

    def sleep(self) -> None:
        utils.polite_sleep(self.delay)

    # ------------------------------------------------------------------
    def discover(self) -> List[Document]:
        raise NotImplementedError

    # ------------------------------------------------------------------
    def collect(self, seen_urls: set) -> List[Document]:
        """Run discovery, dedupe against global seen set, truncate to limit."""
        docs: List[Document] = []
        try:
            raw = self.discover()
        except Exception as exc:  # a broken source never kills the run
            utils.say(f"    !! source '{self.name}' failed: {type(exc).__name__}: {exc}")
            raw = []

        unique = []
        for doc in raw:
            key = doc.url.rstrip("/")
            if key in seen_urls:
                continue
            seen_urls.add(key)
            unique.append(doc)
        return unique[: self.limit]

    # ------------------------------------------------------------------
    def query_progress(self, queries, description: str):
        """Small progress bar over discovery queries."""
        return tqdm(
            queries, desc=f"    {description}", unit="q",
            leave=True, position=0, dynamic_ncols=True,
            bar_format="{desc} {n_fmt}/{total_fmt} [{elapsed}]",
        )
