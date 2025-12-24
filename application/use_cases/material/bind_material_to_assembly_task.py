from src.application.exceptions.material_exceptions import MaterialBindingError
from src.database.repositories import (
    MaterialRepository,
    WbOrderRepository,
    WbAssemblyTaskRepository,
)
from src.database.repositories.wb_article import WbArticleRepository
from src.infrastructure.rabbitmq.producer import send_to_queue


class BindMaterialToAssemblyTaskUseCase:
    def __init__(
        self,
        material_repo: MaterialRepository,
        wb_order_repo: WbOrderRepository,
        wb_assembly_task_repo: WbAssemblyTaskRepository,
        wb_article_repo: WbArticleRepository,
    ):
        self.material_repo = material_repo
        self.wb_order_repo = wb_order_repo
        self.wb_assembly_task_repo = wb_assembly_task_repo
        self.wb_article_repo = wb_article_repo

    async def execute(self, material_id: int, assembly_task_id: int):
        material = await self.material_repo.get_by_id(material_id)

        if not material:
            raise MaterialBindingError(f"Материал #{material_id} не найден")

        assembly_task = await self.wb_assembly_task_repo.get_by_id(assembly_task_id)

        if not assembly_task:
            raise MaterialBindingError(
                f"Сборочное задание с #{assembly_task_id} не найден"
            )

        existing_wb_order = await self.wb_order_repo.get_by_material_id(material_id)

        if existing_wb_order:
            raise MaterialBindingError(
                f"Материал #{material_id} уже связан с заказом #{existing_wb_order.id}"
            )

        wb_order = await self.wb_order_repo.get_by_id(assembly_task.wb_order_id)

        if wb_order.material_id:
            raise MaterialBindingError(
                f"Сборочное задание #{assembly_task_id} уже связан с материалом #{wb_order.material_id}"
            )

        wb_articles = await self.wb_article_repo.get_list_by_template_id(
            template_id=material.template_id
        )

        is_match = any(
            wb_article.wb_article == wb_order.nm_id for wb_article in wb_articles
        )

        if not is_match:
            raise MaterialBindingError(
                f"Сборочное задание #{assembly_task_id} не подходит под артикул {wb_order.nm_id}"
            )

        wb_order.material_id = material_id

        await self.wb_order_repo.update(wb_order)

        await send_to_queue(
            queue_name="processing_supply",
            data={
                "assembly_task_id": assembly_task.id,
            },
        )

        return True
