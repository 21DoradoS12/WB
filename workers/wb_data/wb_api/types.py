from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field


class WildberriesOrders(BaseModel):
    orders: list["WildberriesOrder"] = []


class WildberriesOrder(BaseModel):
    id: str = Field(alias="srid")
    created_at: datetime = Field(alias="date")
    country_name: str = Field(alias="countryName")
    region_name: str = Field(alias="regionName")
    supplier_article: str = Field(alias="supplierArticle")
    nm_id: int = Field(alias="nmId")
    is_cancel: bool = Field(alias="isCancel")
    cancel_date: datetime = Field(alias="cancelDate")
    warehouse_name: str = Field(alias="warehouseName")
    warehouse_type: str = Field(alias="warehouseType")


class WildberriesNewAssemblyTasks(BaseModel):
    orders: list["WildberriesAssemblyTask"] = []


class WildberriesAssemblyTask(BaseModel):
    id: int = Field(alias="id")
    wb_order_id: str = Field(alias="rid")
    created_at: datetime = Field(default=datetime.now())


class WildberriesAssemblyOrderStatus(BaseModel):
    """
    https://dev.wildberries.ru/openapi/orders-fbs#tag/Sborochnye-zadaniya/paths/~1api~1v3~1orders/get

    Возможные значения supplierStatus:
        new — новое сборочное задание
        confirm — на сборке для доставки силами Wildberries fbs
        complete — в доставке для доставки силами Wildberries fbs и курьером WB wbgo
        cancel — отменено продавцом

    Возможные значения wbStatus:
        waiting — сборочное задание в работе
        sorted — сборочное задание отсортировано
        sold — сборочное задание получено покупателем
        canceled — отмена сборочного задания
        canceled_by_client — покупатель отменил заказ при получении
        declined_by_client — покупатель отменил заказ. Отмена доступна покупателю в первый час с момента заказа, если заказ не переведён на сборку
        defect — отмена сборочного задания по причине брака
        ready_for_pickup — сборочное задание прибыло на пункт выдачи заказов (ПВЗ)
        postponed_delivery — курьерская доставка отложена


    """
    id: int
    supplier_status: Literal[
        "new",
        "confirm",
        "complete",
        "cancel"
    ] = Field(alias="supplierStatus")
    wb_status: Literal[
        "waiting",
        "sorted",
        "sold",
        "canceled",
        "canceled_by_client",
        "declined_by_client",
        "defect",
        "ready_for_pickup",
        "postponed_delivery",
    ] = Field(alias="wbStatus")


class WildberriesAssemblyOrdersStatusResponse(BaseModel):
    orders: List[WildberriesAssemblyOrderStatus]
