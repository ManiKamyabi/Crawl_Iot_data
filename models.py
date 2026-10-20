"""Shared data models for the collector pipeline."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Document:
    """A single downloadable PDF candidate discovered from a source."""

    source: str                 # source label, e.g. "arxiv", "rfc", "nist"
    url: str                    # direct PDF URL
    title: str                  # human-readable title
    year: Optional[int] = None  # publication year, if known
    doc_id: str = ""            # native id (arXiv id, RFC number, DOI, ...)
    notes: str = ""             # small notes shown in verbose mode

    def __post_init__(self):
        # Normalize: strip whitespace, force https when the source is https-capable
        self.url = (self.url or "").strip()
        self.title = " ".join((self.title or "").split())
        if self.url.startswith("http://arxiv.org"):
            self.url = self.url.replace("http://arxiv.org", "https://arxiv.org", 1)


@dataclass
class Stats:
    """Aggregated run statistics."""

    downloaded: int = 0
    failed: int = 0
    skipped_existing: int = 0
    invalid_pdf: int = 0
    bytes_downloaded: int = 0
    per_source: dict = field(default_factory=dict)

    def add(self, source: str, outcome: str, nbytes: int = 0) -> None:
        bucket = self.per_source.setdefault(
            source, {"downloaded": 0, "failed": 0, "skipped_existing": 0, "invalid_pdf": 0}
        )
        bucket[outcome] += 1
        if outcome == "downloaded":
            self.downloaded += 1
            self.bytes_downloaded += nbytes
        elif outcome == "failed":
            self.failed += 1
        elif outcome == "skipped_existing":
            self.skipped_existing += 1
        elif outcome == "invalid_pdf":
            self.invalid_pdf += 1
