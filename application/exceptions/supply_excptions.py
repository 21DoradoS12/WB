class SupplyError(Exception):
    """Базовое исключение для операций с поставками"""

    pass


class SupplyNotFoundError(SupplyError):
    """Поставка не найдена"""

    pass


class SupplyAlreadyClosedError(SupplyError):
    """Поставка уже закрыта"""

    pass
