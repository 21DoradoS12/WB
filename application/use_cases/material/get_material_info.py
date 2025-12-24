from src.application.dto.material.material_info_dto import MaterialInfoDTO
from src.application.dto.template_dto import TemplateDTO
from src.application.dto.user.user_dto import UserDTO
from src.application.dto.wb_order.supply import SupplyDTO
from src.application.dto.wb_order.wb_assembly_task_dto import WbAssemblyTaskDTO
from src.application.dto.wb_order.wb_order_dto import WbOrderDTO
from src.database.repositories import (
    WbOrderRepository,
    MaterialRepository,
    UserRepository,
    WbAssemblyTaskRepository,
    SupplyRepository,
    TemplateRepository,
)


class GetMaterialInfoUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        material_repo: MaterialRepository,
        wb_order_repo: WbOrderRepository,
        wb_assembly_task_repo: WbAssemblyTaskRepository,
        supply: SupplyRepository,
        template_repo: TemplateRepository,
    ):
        self.user_repo = user_repo
        self.material_repo = material_repo
        self.wb_order_repo = wb_order_repo
        self.wb_assembly_task_repo = wb_assembly_task_repo
        self.supply_repo = supply
        self.template_repo = template_repo

    async def execute(self, material_id: int) -> MaterialInfoDTO | None:
        material = await self.material_repo.get_by_id(material_id)
        if not material:
            return None

        template = await self.template_repo.get_by_id(material.template_id)

        template_dto = None

        if template:
            template_dto = TemplateDTO(id=template.id, name=template.name)

        user = await self.user_repo.get_by_id(material.user_id)

        user_dto = (
            UserDTO(
                id=getattr(user, "id", None),
                first_name=getattr(user, "first_name", None),
                last_name=getattr(user, "last_name", None),
                username=getattr(user, "username", None),
            )
            if user
            else None
        )

        wb_order = await self.wb_order_repo.get_by_material_id(material.id)

        assembly_task_dto = None
        wb_order_dto = None

        if wb_order:
            assembly_task = await self.wb_assembly_task_repo.get_by_wb_order_id(
                wb_order_id=wb_order.id
            )

            supply_dto = None
            if assembly_task and assembly_task.supply_id:
                supply = await self.supply_repo.get_by_id(assembly_task.supply_id)
                if supply:
                    supply_dto = SupplyDTO(
                        id=supply.id,
                        name=supply.name,
                    )

            if assembly_task:
                assembly_task_dto = WbAssemblyTaskDTO(
                    id=assembly_task.id, supply=supply_dto
                )

            wb_order_dto = WbOrderDTO(
                id=wb_order.id,
                region_name=wb_order.region_name,
                is_cancel=wb_order.is_cancel,
                assembly_task=assembly_task_dto,
            )

        return MaterialInfoDTO(
            id=material.id,
            status=material.status,
            data=material.data,
            order=wb_order_dto,
            user=user_dto,
            template=template_dto,
        )
