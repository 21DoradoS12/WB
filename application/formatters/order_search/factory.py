from src.application.formatters.order_search import (
    RegionSearchFormatter,
    ReceiptSearchFormatter,
)

SEARCH_FORMATTER_MAP = {
    "REGION": RegionSearchFormatter,
    "RECEIPT_NUMBER": ReceiptSearchFormatter,
}


def build_search_message(search_type: str, filters: dict, status: str, search_id: int):
    cls = SEARCH_FORMATTER_MAP.get(search_type)
    if not cls:
        raise ValueError(f"Unknown search type {search_type}")
    return cls(
        **filters, status=status, search_id=search_id, search_type=search_type
    ).to_message()
