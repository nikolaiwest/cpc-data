# Placeholder registry - populate as you implement functions
# TODO: implement
EXTRACTION_REGISTRY = {
    "raw": lambda data, **kwargs: data,  # passthrough
    "paa": lambda data, **kwargs: {"method": "paa", "data": "placeholder"},
    "tsfresh": lambda data, **kwargs: {"method": "tsfresh", "data": "placeholder"},
    "catch22": lambda data, **kwargs: {"method": "catch22", "data": "placeholder"},
}
