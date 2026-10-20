"""Source registry - add new reputable sources here."""
from sources.arxiv import ArxivSource
from sources.rfc_editor import RfcEditorSource
from sources.ietf_datatracker import IetfDatatrackerSource
from sources.nist import NistSource
from sources.mdpi import MdpiSource
from sources.semantic_scholar import SemanticScholarSource
from sources.oasis import OasisSource
from sources.lora_alliance import LoraAllianceSource

SOURCE_REGISTRY = [
    ArxivSource,
    RfcEditorSource,
    NistSource,
    OasisSource,
    LoraAllianceSource,
    SemanticScholarSource,
    MdpiSource,
    IetfDatatrackerSource,
]

SOURCE_NAMES = [cls.name for cls in SOURCE_REGISTRY]
