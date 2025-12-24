from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.async_session import AsyncSessionLocal
from src.database.repositories import (
    CategoryRepository,
    TemplateRepository,
    OrderSearchRepository,
    MaterialRepository,
    CountryRepository,
    CityRepository,
    CategorySettingsRepository,
    UserRepository,
    WbAssemblyTaskRepository,
    SupplyRepository,
)
from src.database.repositories.wb_article import WbArticleRepository
from src.database.repositories.wb_order import WbOrderRepository


class UnitOfWork:
    def __init__(self):
        self.session: AsyncSession | None = None
        self.category: CategoryRepository | None = None
        self.template: TemplateRepository | None = None
        self.material: MaterialRepository | None = None
        self.order_search: OrderSearchRepository | None = None
        self.wb_order: WbOrderRepository | None = None
        self.country: CountryRepository | None = None
        self.city: CityRepository | None = None
        self.category_settings: CategorySettingsRepository | None = None
        self.user: UserRepository | None = None
        self.wb_assembly_task: WbAssemblyTaskRepository | None = None
        self.supply: SupplyRepository | None = None
        self.wb_article: WbArticleRepository | None = None

    async def __aenter__(self):
        self.session = AsyncSessionLocal()
        self.category = CategoryRepository(self.session)
        self.template = TemplateRepository(self.session)
        self.material = MaterialRepository(self.session)
        self.order_search = OrderSearchRepository(self.session)
        self.wb_order = WbOrderRepository(self.session)
        self.country = CountryRepository(self.session)
        self.city = CityRepository(self.session)
        self.category_settings = CategorySettingsRepository(self.session)
        self.user = UserRepository(self.session)
        self.wb_assembly_task = WbAssemblyTaskRepository(self.session)
        self.supply = SupplyRepository(self.session)
        self.wb_article = WbArticleRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
