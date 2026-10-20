"""
Central configuration for the IoT PDF Collector.

All knobs live here so you can tune behavior without touching crawler code.
Every value can be overridden from the command line (see main.py --help).
"""

# ----------------------------------------------------------------------
# General behavior
# ----------------------------------------------------------------------
OUTPUT_DIR = "pdfs"              # folder where PDFs are stored (flat, one folder)
PER_SOURCE_LIMIT = 60            # max PDFs discovered per source (user choice: 50+)
MIN_YEAR = 2020                  # publication year filter for paper-like sources
MIN_PDF_SIZE = 20_000            # bytes; smaller files are treated as error pages
MAX_PDF_SIZE = 200_000_000       # bytes; safety cap (200 MB)
MAX_TITLE_LEN_IN_FILENAME = 48   # keep filenames readable

REQUEST_TIMEOUT = 30             # seconds per HTTP request
MAX_RETRIES = 3                  # retries per request (429/5xx/connection errors)
RETRY_BACKOFF = 2.0              # exponential backoff factor (2 -> 2s, 4s, 8s...)

# Politeness: seconds to sleep between consecutive requests to a source.
# arXiv explicitly asks for >= 3s between API calls; Semantic Scholar is 1 rps
# without a key; datatracker / mdpi get moderate values.
SOURCE_DELAYS = {
    "arxiv": 3.0,
    "rfc_editor": 1.0,
    "ietf_datatracker": 2.0,
    "nist": 1.0,
    "mdpi": 2.0,
    "semantic_scholar": 6.0,
    "oasis": 1.0,
    "lora_alliance": 1.0,
}

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 IoT-PDF-Collector/1.0"
)

# Optional: request a free key at https://www.semanticscholar.org/product/api
# and put it here (or export S2_API_KEY) to raise Semantic Scholar rate limits.
S2_API_KEY = ""

# ----------------------------------------------------------------------
# Topic focus: ALL IoT protocol families (user choice)
# ----------------------------------------------------------------------
IOT_KEYWORDS = [
    "MQTT", "CoAP", "AMQP", "6LoWPAN", "RPL", "LoRaWAN", "LoRa", "NB-IoT",
    "Sigfox", "Zigbee", "Thread", "Matter", "BLE", "Bluetooth Low Energy",
    "LPWAN", "SCHC", "wireless sensor network", "IoT security", "IIoT",
    "industrial IoT", "IoT protocol", "802.15.4", "OPC UA", "XMPP",
    "WebSocket", "M2M", "IoT interoperability",
]

# arXiv: keywords that are already IoT-specific (no extra "IoT" AND needed).
ARXIV_STANDALONE = {
    "MQTT", "CoAP", "AMQP", "6LoWPAN", "RPL", "LoRaWAN", "LoRa", "NB-IoT",
    "Sigfox", "Zigbee", "LPWAN", "SCHC", "wireless sensor network",
    "industrial IoT", "IIoT",
}
ARXIV_MAX_RESULTS_PER_QUERY = 60

# Semantic Scholar: paper-search queries (kept small due to rate limits).
S2_QUERIES = [
    "IoT protocol", "MQTT IoT", "CoAP IoT", "LoRaWAN performance",
    "6LoWPAN", "NB-IoT", "IoT security protocol", "wireless sensor network",
]
S2_PDF_HOST_WHITELIST = (
    "arxiv.org",
    "springer.com", "nature.com", "ieee.org", "acm.org",
    "frontiersin.org", "plos.org", "techrxiv.org", "preprints.org",
    "mdpi.com", "semanticscholar.org", "wiley.com", "tandfonline.com",
    "sciencedirect.com", "spiedigitallibrary.org", "iopscience.iop.org",
    "aps.org", "acs.org", "doi.org",
)

# DOAJ -> MDPI journals (by exact journal title as returned by DOAJ).
MDPI_JOURNAL_TITLES = {
    "Sensors", "Electronics", "Applied Sciences", "Future Internet", "IoT",
    "Journal of Sensor and Actuator Networks", "Computers", "Smart Cities",
    "Network", "Cryptography",
}
DOAJ_QUERIES = [
    "IoT protocol", "MQTT", "CoAP", "LoRaWAN", "6LoWPAN", "NB-IoT",
    "wireless sensor network", "IoT security", "Zigbee",
]
OPENALEX_MAILTO = "iot.pdf.collector.research@gmail.com"  # polite pool

# IETF Datatracker working groups with strong IoT-protocol relevance.
IETF_WG_LIST = [
    "lpwan", "core", "ace", "roll", "6lo", "lwig", "asdf",
    "6tisch", "iotops", "suit", "mud",
]

# RFC Editor: word-boundary keyword patterns applied to RFC titles.
RFC_TITLE_PATTERNS = [
    r"\bIoT\b", r"\bMQTT\b", r"\bCoAP\b", r"6LoWPAN", r"\bRPL\b",
    r"\bLoRa\b", r"\bLoRaWAN\b", r"\bNB-IoT\b", r"\bSCHC\b", r"\bLPWAN\b",
    r"\bCoRE\b", r"\bOSCORE\b", r"\bACE\b", r"\bDTLS\b", r"\bSDF\b",
    r"\bLWIG\b", r"\bM2M\b", r"\bBLE\b", r"Bluetooth", r"Zigbee",
    r"\bThread\b", r"\bMatter\b", r"wireless sensor", r"sensor network",
    r"machine-to-machine", r"Internet of Things", r"\bMesh\b",
    r"constrained", r"\b802\.11\b", r"\b802\.15\.4\b",
]

# NIST CSRC detail paths for IoT / IoT-protocol-adjacent publications.
# Titles + PDF URLs are scraped live from these server-rendered pages.
NIST_CSRC_PATHS = [
    "/pubs/ir/8228/final",        # IoT Cybersecurity & Privacy Considerations
    "/pubs/ir/8259/final",        # Foundational Cybersecurity Activities for IoT
    "/pubs/ir/8259/a/final",      # IoT Core Capability Baseline
    "/pubs/ir/8259/b/final",      # IoT Non-Technical Supporting Capabilities
    "/pubs/ir/8425/final",        # Consumer IoT Core Baseline Profile
    "/pubs/sp/800/213/final",     # IoT for Federal Agencies
    "/pubs/sp/1800/8/final",      # Wireless Infusion Pumps (NCCoE)
    "/pubs/sp/1800/30/final",     # Telehealth Remote Patient Monitoring (NCCoE)
    "/pubs/sp/1800/24/final",     # PACS Security (NCCoE)
    "/pubs/sp/800/121/r2/final",  # Guide to Bluetooth Security
    "/pubs/sp/800/94/final",      # Wireless IDS/IPS Guide
    "/pubs/sp/800/48/r1/final",   # Legacy IEEE 802.11 Wireless Security
    "/pubs/sp/800/193/final",     # Platform Firmware Resiliency
    "/pubs/sp/800/187/final",     # Guide to LTE Security
    "/pubs/sp/800/163/r1/final",  # Mobile Application Vetting
    "/pubs/sp/800/52/r2/final",   # TLS Guidelines
    "/pubs/sp/800/207/final",     # Zero Trust Architecture
    "/pubs/sp/800/77/r1/final",   # Guide to IPsec
]

# OASIS official standards (direct PDFs). Each entry may carry several
# candidate URLs; the first one that returns a real PDF wins.
OASIS_SPECS = [
    {
        "title": "MQTT Version 5.0 - OASIS Standard",
        "year": 2019,
        "urls": ["https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.pdf"],
    },
    {
        "title": "MQTT Version 3.1.1 - OASIS Standard",
        "year": 2014,
        "urls": ["https://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.pdf"],
    },
    {
        "title": "MQTT-SN Protocol Specification v1.2",
        "year": 2013,
        "urls": ["https://www.oasis-open.org/committees/download.php/66091/MQTT-SN_spec_v1.2.pdf"],
    },
    {
        "title": "OASIS Advanced Message Queuing Protocol (AMQP) Core v1.0",
        "year": 2014,
        "urls": ["https://docs.oasis-open.org/amqp/core/v1.0/os/amqp-core-complete-v1.0-os.pdf"],
    },
    {
        "title": "Sparkplug Specification v3.0.0 - MQTT data in Industrial IoT",
        "year": 2022,
        "urls": [
            "https://docs.oasis-open.org/sparkplug/sparkplug/v3.0.0/os/sparkplug-v3.0.0-os.pdf",
            "https://github.com/sparkplug/sparkplug/releases/download/v3.0.0/sparkplug-v3.0.0-os.pdf",
        ],
    },
]

# LoRa Alliance (resources hub = Uberflip). Item pages are server-rendered
# and embed a signed download token (cmd=d) that we decode and follow.
# Only slugs verified live are listed first; extra candidates are attempted
# but failures are silently skipped.
LORA_ITEM_SLUGS = [
    "ts001-1-0-4-lorawan-l2-1-0-4-specification",
    "rp002-1-0-4-regional-parameters",
    "ts002-1-0-4-lorawan-architecture",
    "ts003-1-1-0-lorawan-backend-interfaces",
    "rp002-1-0-3-regional-parameters",
]

# Sources whose content is "canonical specs" (OASIS/LoRa/NIST); their
# publication years may predate MIN_YEAR without violating the topic choice.
SOURCES_EXEMPT_FROM_YEAR_FILTER = {"oasis", "lora_alliance", "nist"}
