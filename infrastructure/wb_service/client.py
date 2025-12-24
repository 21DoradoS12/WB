import logging
from typing import List

import httpx

from src.infrastructure.wb_service.models import (
    CreateSupplyResponse,
    AssemblyTaskStickersResponse,
)

log = logging.getLogger(__name__)


class WBApiService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient()

    async def _make_request(
        self,
        url: str,
        method: str = "GET",
        params: dict = None,
        json: dict = None,
    ):
        headers = {"Authorization": f"Bearer {self.api_key}"}

        params = params or {}
        json = json or {}

        log.info(
            "Запрос к WB API: %s %s | params=%s | json=%s", method, url, params, json
        )

        try:
            response = await self.client.request(
                method, url, params=params, headers=headers, json=json
            )

            log.info(
                "Ответ WB API: %s %s | status=%s", method, url, response.status_code
            )

            response.raise_for_status()

            if response.status_code == 204 or not response.text.strip():
                log.info(
                    "WB API вернул пустой ответ (204 No Content) для %s %s", method, url
                )
                return None
            else:
                try:
                    data = response.json()
                    log.debug("JSON ответ WB API: %s", data)
                    return data
                except Exception as e:
                    log.error("Не удалось распарсить JSON: %s", e, exc_info=True)
                    return {"error": "Invalid JSON"}

        except httpx.RequestError as e:
            log.error(
                "Ошибка запроса WB API: %s %s | %s", method, url, e, exc_info=True
            )
            return {"error": "Request failed"}
        except Exception as e:
            log.error(
                "Произошла ошибка при вызове WB API: %s %s | %s",
                method,
                url,
                e,
                exc_info=True,
            )
            return {"error": "Unexpected error"}

    async def create_supply(self, name: str):
        url = "https://marketplace-api.wildberries.ru/api/v3/supplies"
        json = {"name": name}
        response = await self._make_request(url=url, json=json, method="POST")
        log.info("Создана поставка: %s", response)
        return CreateSupplyResponse.model_validate(response)

    async def add_assembly_task_to_supply(self, supply_id: str, assembly_task_id: int):
        url = f"https://marketplace-api.wildberries.ru/api/v3/supplies/{supply_id}/orders/{assembly_task_id}"
        params = {"supplyId": supply_id, "orderId": assembly_task_id}
        response = await self._make_request(url=url, params=params, method="PATCH")
        log.info(
            "Добавлено сборочное задание %s в поставку %s", assembly_task_id, supply_id
        )
        return True

    async def get_assembly_task_stickers(
        self,
        assembly_task_ids: List[int],
        sticker_type: str = "png",
        width: int = 58,
        height: int = 40,
    ):
        url = "https://marketplace-api.wildberries.ru/api/v3/orders/stickers"
        params = {"type": sticker_type, "width": width, "height": height}
        json = {"orders": assembly_task_ids}

        response = await self._make_request(
            url=url, params=params, json=json, method="POST"
        )

        if not response.get("stickers"):
            log.warning("Нет стикеров для assembly_task_ids=%s", assembly_task_ids)

        log.info("Получены стикеры для assembly_task_ids=%s", assembly_task_ids)
        return AssemblyTaskStickersResponse.model_validate(response)
