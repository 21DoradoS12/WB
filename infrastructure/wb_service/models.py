from typing import List

from pydantic import BaseModel, Field


class CreateSupplyResponse(BaseModel):
    id: str


class AssemblyTaskSticker(BaseModel):
    order_id: int = Field(alias="orderId")
    part_a: str = Field(alias="partA")
    part_b: str = Field(alias="partB")
    barcode: str = Field(alias="barcode")
    file: str = Field(alias="file")


class AssemblyTaskStickersResponse(BaseModel):
    stickers: List[AssemblyTaskSticker] = []
