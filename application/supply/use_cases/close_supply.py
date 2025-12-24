from src.application.exceptions.supply_excptions import (
    SupplyNotFoundError,
    SupplyAlreadyClosedError,
)
from src.database.repositories import SupplyRepository


class CloseSupplyUseCase:
    def __init__(self, repo: SupplyRepository):
        self.repo = repo

    async def execute(self, supply_id: str):
        supply = await self.repo.get_by_id(supply_id)
        if not supply:
            raise SupplyNotFoundError()
        if supply.is_inactive():
            raise SupplyAlreadyClosedError()
        supply.close()
        await self.repo.update(supply)
        return supply
