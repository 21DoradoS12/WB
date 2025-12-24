from src.application.dto.material.material_info_dto import MaterialInfoDTO
from src.application.dto.template_dto import TemplateDTO
from src.application.dto.user.user_dto import UserDTO
from src.application.dto.wb_order.supply import SupplyDTO
from src.application.dto.wb_order.wb_assembly_task_dto import WbAssemblyTaskDTO
from src.application.dto.wb_order.wb_order_dto import WbOrderDTO

from src.database.repositories import (
    MaterialRepository,
    UserRepository,
    TemplateRepository,
    WbAssemblyTaskRepository,
    WbOrderRepository,
    SupplyRepository,
)


class GetMaterialInfoByAssemblyTaskUseCase:
    def __init__(
        self,
        material_repo: MaterialRepository,
        user_repo: UserRepository,
        template_repo: TemplateRepository,
        wb_assembly_task_repo: WbAssemblyTaskRepository,
        wb_order_repo: WbOrderRepository,
        supply_repo: SupplyRepository,
    ):
        self.material_repo = material_repo
        self.user_repo = user_repo
        self.template_repo = template_repo
        self.wb_assembly_task_repo = wb_assembly_task_repo
        self.wb_order_repo = wb_order_repo
        self.supply_repo = supply_repo

    async def execute(self, assembly_task_id: int) -> MaterialInfoDTO | None:
        # Находим сборочное задание
        assembly_task = await self.wb_assembly_task_repo.get_by_id(assembly_task_id)
        if not assembly_task or not assembly_task.wb_order_id:
            return None

        # Находим заказ
        wb_order = await self.wb_order_repo.get_by_id(assembly_task.wb_order_id)
        if not wb_order or not wb_order.material_id:
            return None

        # Находим материал
        material = await self.material_repo.get_by_id(wb_order.material_id)
        if not material:
            return None

        # Находим шаблон материала
        template = await self.template_repo.get_by_id(material.template_id)
        template_dto = (
            TemplateDTO(id=template.id, name=template.name) if template else None
        )

        # Находим пользователя
        user = await self.user_repo.get_by_id(material.user_id)
        user_dto = (
            UserDTO(
                id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                username=user.username,
            )
            if user
            else None
        )

        # Строим supply DTO
        supply_dto = None
        if assembly_task.supply_id:
            supply = await self.supply_repo.get_by_id(assembly_task.supply_id)
            if supply:
                supply_dto = SupplyDTO(id=supply.id, name=supply.name)

        # Строим assembly task DTO
        assembly_task_dto = WbAssemblyTaskDTO(id=assembly_task.id, supply=supply_dto)

        # Строим заказ DTO
        wb_order_dto = WbOrderDTO(
            id=wb_order.id,
            region_name=wb_order.region_name,
            is_cancel=wb_order.is_cancel,
            assembly_task=assembly_task_dto,
        )

        # Возвращаем DTO материала
        return MaterialInfoDTO(
            id=material.id,
            status=material.status,
            data=material.data,
            order=wb_order_dto,
            user=user_dto,
            template=template_dto,
        )
