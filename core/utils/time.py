from datetime import datetime, timezone


def now_utc() -> datetime:
    """
    Возвращает текущее время в UTC+0 без tzinfo.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
