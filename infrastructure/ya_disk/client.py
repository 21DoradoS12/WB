import asyncio
import logging
from io import BytesIO

import aiohttp
import yadisk_async

logger = logging.getLogger(__name__)


class YandexDiskService:
    def __init__(self, token: str, retries: int = 3, delay: float = 1.0):
        self.disk = yadisk_async.YaDisk(token=token)
        self.retries = retries
        self.delay = delay
        self._token = token

    async def create_folder(self, path: str) -> None:
        """
        Создать папку с повторными попытками.
        """
        for attempt in range(1, self.retries + 1):
            try:
                if not await self.disk.exists(path):
                    await self.disk.mkdir(path)
                    logger.info(f"Папка создана: {path}")
                else:
                    logger.debug(f"Папка уже существует: {path}")
                return
            except Exception as e:
                logger.warning(
                    f"Ошибка при создании {path}, попытка {attempt}/{self.retries}: {e}"
                )
                if attempt < self.retries:
                    await asyncio.sleep(self.delay)
        logger.error(f"Не удалось создать папку {path} после {self.retries} попыток")
        raise Exception(f"Не удалось создать папку {path}")

    async def create_nested_folders(self, path: str) -> None:
        """
        Рекурсивно создает папки

        Пример: order/19.08.2025/12345
        """
        parts = [p for p in path.strip("/").split("/") if p]
        current = ""
        for part in parts:
            current += f"/{part}"
            await self.create_folder(current)

    async def upload_file(self, local_path: str, yandex_path: str) -> None:
        """
        Загружает файл потоково через Yandex Disk API.
        """
        # 1. Создаём папки
        folder_path = "/".join(yandex_path.split("/")[:-1])
        if folder_path:
            await self.create_nested_folders(folder_path)

        # 2. Получаем URL для загрузки
        url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        headers = {
            "Authorization": f"OAuth {self._token}"
        }  # ← убедитесь, что у вас есть self.token
        params = {"path": yandex_path, "overwrite": "true"}

        async with aiohttp.ClientSession() as session:
            # Запрос на получение upload URL
            async with session.get(url, headers=headers, params=params) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(
                        f"Не удалось получить URL загрузки: {resp.status} - {error_text}"
                    )
                data = await resp.json()
                upload_href = data.get("href")
                if not upload_href:
                    raise Exception(f"Ответ не содержит href: {data}")

            # 3. Потоковая загрузка файла
            logger.info(f"Начинаем потоковую загрузку {local_path} → {yandex_path}")
            with open(local_path, "rb") as f:
                async with session.put(
                    upload_href, data=f, timeout=aiohttp.ClientTimeout(total=3600)
                ) as resp:
                    if resp.status == 201:
                        logger.info(f"Файл успешно загружен: {yandex_path}")
                    else:
                        error_text = await resp.text()
                        raise Exception(
                            f"Ошибка загрузки: {resp.status} - {error_text}"
                        )

    # async def upload_file(self, local_path: str, yandex_path: str) -> None:
    #     """
    #     Загружает файл с созданием папок.
    #     """
    #     folder_path = "/".join(yandex_path.split("/")[:-1])
    #     if folder_path:
    #         await self.create_nested_folders(folder_path)
    #     try:
    #         await self.disk.upload(local_path, yandex_path, overwrite=True, timeout=300)
    #         logger.info(f"Файл загружен: {yandex_path}")
    #     except Exception as e:
    #         logger.error(
    #             f"Ошибка загрузки файла {local_path} → {yandex_path}: {e}", exc_info=e
    #         )
    #         raise

    async def upload_bytes(self, data: bytes, yandex_path: str) -> None:
        if isinstance(data, bytes):
            data = BytesIO(data)

        folder_path = "/".join(yandex_path.split("/")[:-1])
        if folder_path:
            await self.create_nested_folders(folder_path)
        try:
            await self.disk.upload(data, yandex_path, overwrite=True)
            logger.info(f"Файл загружен (из памяти): {yandex_path}")
        except Exception as e:
            logger.error(
                f"Ошибка загрузки файла из памяти→ {yandex_path}: {e}", exc_info=e
            )
            raise
