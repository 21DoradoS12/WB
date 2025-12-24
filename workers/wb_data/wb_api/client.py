import requests
from pydantic import TypeAdapter

from src.workers.wb_data.wb_api.types import WildberriesOrders, WildberriesNewAssemblyTasks, WildberriesOrder, \
    WildberriesAssemblyOrdersStatusResponse


class WildberriesApi:
    def __init__(self, token: str, timeout: int = 30):
        """
        Инициализация API клиента с токеном авторизации.

        :param token: Токен для авторизации в API
        """
        self._token = token
        self.timeout = timeout

    def fetch_orders_report(self, date_from: str, flag: int = 0) -> WildberriesOrders:
        """
        Получение отчета о заказах за указанный период.

        :param date_from: Дата начала для выборки заказов (например, "2019-06-20" или "2019-06-20T23:59:59")
        :param flag: Параметр фильтрации (0 или 1) для выбора типа данных
        :return: Объект WildberriesOrders, содержащий список заказов
        """
        url = "https://statistics-api.wildberries.ru/api/v1/supplier/orders"

        headers = {
            'Authorization': self._token
        }

        params = {
            "dateFrom": date_from,
            "flag": flag
        }

        response = requests.get(url, params=params, headers=headers, timeout=self.timeout)

        # Проверка успешности запроса
        if response.status_code != 200:
            raise Exception(f"Ошибка при получении данных: {response.status_code}, {response.text}")

        # Адаптация и валидация данных
        adapter = TypeAdapter(WildberriesOrder)
        orders_data = [adapter.validate_python(order) for order in response.json()]

        return WildberriesOrders(orders=orders_data)

    def fetch_new_assembly_tasks(self) -> WildberriesNewAssemblyTasks:
        """
        Метод предоставляет список всех новых сборочных заданий, которые есть у продавца на момент запроса.

        :return: Объект WildberriesNewAssemblyTasks, содержащий список сборочных заданий
        """
        url = "https://marketplace-api.wildberries.ru/api/v3/orders/new"

        headers = {
            'Authorization': self._token
        }

        response = requests.get(url, headers=headers, timeout=self.timeout)

        # Проверка успешности запроса
        if response.status_code != 200:
            raise Exception(f"Ошибка при получении данных: {response.status_code}, {response.text}")

        return WildberriesNewAssemblyTasks.model_validate(response.json())

    def fetch_assembly_task_statuses(self, ids: list[int] = list) -> WildberriesAssemblyOrdersStatusResponse:
        """
        Метод предоставляет статусы сборочных заданий по их идентификаторам.
            ids - Идентификаторы сборочных заданий (Максимальное кол-во идентификаторов — 1000)
        """
        url = "https://marketplace-api.wildberries.ru/api/v3/orders/status"

        headers = {
            'Authorization': self._token
        }

        payload = {
            "orders": ids
        }

        response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)

        # Проверка успешности запроса
        if response.status_code != 200:
            raise Exception(f"Ошибка при получении данных: {response.status_code}, {response.text}")

        return WildberriesAssemblyOrdersStatusResponse.model_validate(response.json())
