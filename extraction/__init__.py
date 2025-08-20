from .extract_cache22 import extract_catch22
from .extract_paa import extract_paa
from .extract_pca import extract_pca
from .extract_statistical import extract_statistical
from .extract_tsfresh import extract_tsfresh

EXTRACTION_REGISTRY = {
    "raw": lambda data, **kwargs: data.copy() if data else [],
    "paa": extract_paa,
    "pca": extract_pca,
    "tsfresh": extract_tsfresh,
    "statistics": extract_statistical,
    "catch22": extract_catch22,
}
