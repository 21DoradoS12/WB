from typing import List

from src.database.repositories import SupplyRepository
from src.domain.models.supply import Supply


class GetActiveSuppliesUseCase:
    def __init__(self, supply_repository: SupplyRepository):
        self.supply_repository = supply_repository

    async def execute(self) -> List[Supply]:
        return await self.supply_repository.get_active_supplies()
