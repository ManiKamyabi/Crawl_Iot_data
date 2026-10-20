"""HTTP helpers, filename sanitation and small utilities used everywhere."""
import hashlib
import re
import sys
import time
import unicodedata
from typing import Optional
from urllib.parse import quote, urlparse


def urlencode(text: str) -> str:
    """URL-encode a query string value (safe for path segments too)."""
    return quote(text, safe="")


try:
    import config as cfg
except ImportError:  # when imported as package member
    from . import config as cfg  # type: ignore

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def build_session(with_retries: bool = True) -> requests.Session:
    """HTTP session.

    with_retries=True  -> download session: retries 429/5xx with backoff.
    with_retries=False -> discovery session: fails fast. Sources implement
        their own pacing (urllib3's Retry-After waiting can stall a run for
        minutes when a server sends a large Retry-After header).
    """
    session = requests.Session()
    retry_kwargs = dict(
        backoff_factor=cfg.RETRY_BACKOFF,
        allowed_methods=("GET", "HEAD"),
    )
    if with_retries:
        retry = Retry(
            total=cfg.MAX_RETRIES,
            status_forcelist=(429, 500, 502, 503, 504),
            respect_retry_after_header=True,
            **retry_kwargs,
        )
    else:
        retry = Retry(total=0, status_forcelist=None, **retry_kwargs)
    adapter = HTTPAdapter(max_retries=retry, pool_connections=4, pool_maxsize=4)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({
        "User-Agent": cfg.USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/pdf,application/json;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    return session


def polite_sleep(seconds: float) -> None:
    if seconds and seconds > 0:
        time.sleep(seconds)


def sha1_8(text: str) -> str:
    """Stable 8-hex id for a URL -> deterministic filenames + resume support."""
    return hashlib.sha1(text.encode("utf-8", "ignore")).hexdigest()[:8]


def _ascii_fold(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return normalized.encode("ascii", "ignore").decode("ascii")


def sanitize_title(title: str, max_len: int = cfg.MAX_TITLE_LEN_IN_FILENAME) -> str:
    """ASCII, filesystem-safe, readable slug from a document title."""
    text = _ascii_fold(title)
    text = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
    text = re.sub(r"_+", "_", text)
    if len(text) > max_len:
        text = text[:max_len].rstrip("_")
    return text.lower()


def target_filename(doc, used_names: set) -> str:
    """Deterministic filename: <source>_<slug>_<hash8>.pdf (resume-friendly)."""
    slug = sanitize_title(doc.title) or "document"
    base = f"{doc.source}_{slug}_{sha1_8(doc.url)}.pdf"
    name, counter = base, 1
    while name in used_names:  # same URL twice -> keep a single file
        name = base.replace(".pdf", f"_{counter}.pdf")
        counter += 1
    used_names.add(name)
    return name


def url_host(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def host_allowed(url: str, whitelist) -> bool:
    host = url_host(url)
    return any(host == w or host.endswith("." + w) for w in whitelist)


def looks_like_pdf(first_chunk: bytes) -> bool:
    """Real PDFs start with the %PDF- magic marker."""
    return first_chunk[:5] == b"%PDF-"


def extract_year(text: str) -> Optional[int]:
    m = re.search(r"\b(19|20)\d{2}\b", text or "")
    if m:
        year = int(m.group(0))
        if 1990 <= year <= 2035:
            return year
    return None


def say(message: str = "") -> None:
    """Console print that always flushes (progress bars interleave safely)."""
    print(message, flush=True)
