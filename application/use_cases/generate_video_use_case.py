from typing import List

from src.application.dto.generate_video_result import GenerateVideoResult
from src.infrastructure.telegram.telegram_media_service import TelegramMediaService
from src.infrastructure.video.moviepy_video_service import MoviePyVideoService
from src.infrastructure.ya_disk.client import YandexDiskService


class GenerateAndUploadVideoUseCase:
    def __init__(
        self,
        telegram_service: TelegramMediaService,
        video_service: MoviePyVideoService,
        storage_service: YandexDiskService,
    ):
        self._telegram_service = telegram_service
        self._video_service = video_service
        self._storage_service = storage_service

    async def execute(
        self,
        order_id: int,
        file_ids: List[str],
        output_path: str,
    ) -> GenerateVideoResult:
        try:
            image_paths = await self._telegram_service.download_images(file_ids)
            if not image_paths:
                return GenerateVideoResult(
                    success=False, message="❌ Нет изображений для генерации видео"
                )

            video_path = await self._video_service.generate(image_paths, order_id)
            if not video_path:
                return GenerateVideoResult(
                    success=False, message="❌ Ошибка при создании видео"
                )

            video_name = video_path.split("/")[-1]

            await self._storage_service.upload_file(
                video_path, f"{output_path}{video_name}"
            )

            return GenerateVideoResult(
                success=True,
                message="Видео успешно сгенерировано!",
                video_path=video_path,
            )

        except Exception as e:
            return GenerateVideoResult(success=False, message=f"❌ Ошибка: {str(e)}")
