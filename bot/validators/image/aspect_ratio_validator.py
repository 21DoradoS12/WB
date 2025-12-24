from src.application.dto.photo_validation import ImageInfo
from src.bot.validators.image import ImageValidator
from src.bot.validators.validation_result import ValidationResult


class AspectRatioValidator(ImageValidator):
    """
    Универсальный валидатор для проверки соотношения сторон изображения
    (например: 1:1, 3:4, 9:16 и т.д.).
    """

    def __init__(
        self,
        target_ratio: tuple[int, int],
        tolerance: float = 0.1,
        error_message: str | None = None,
        error_media_id: str | None = None,
        error_media_type: str | None = None,
    ):
        """
        :param target_ratio: кортеж (ширина, высота), например (3, 4) для 3:4
        :param error_message: сообщение об ошибке
        :param tolerance: допустимая погрешность (0.1 = 10%)
        """
        super().__init__(
            error_message=error_message,
            error_media_id=error_media_id,
            error_media_type=error_media_type,
        )

        self.tolerance = tolerance
        self.target_ratio = target_ratio[0] / target_ratio[1]

    async def validate(self, image_info: ImageInfo) -> ValidationResult:
        ratio = image_info.width / image_info.height
        if abs(ratio - self.target_ratio) > self.tolerance:
            return ValidationResult(
                is_valid=False,
                error_text=self.error_message,
                error_media_id=self.error_media_id,
                error_media_type=self.error_media_type,
            )
        return ValidationResult(is_valid=True)
