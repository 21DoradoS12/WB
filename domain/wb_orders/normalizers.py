def normalize_region(region: str) -> str:
    """Приводит название региона к стандартному виду."""
    return region.lower().replace("республика", "").strip()
