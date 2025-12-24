from src.application.dto.photo_validation import ImageInfo
from src.bot.validators.image import ImageValidator
from src.bot.validators.validation_result import ValidationResult


class SquareValidator(ImageValidator):
    """
    Проверяет, что изображение квадратное с допустимой погрешностью.
    """

    def __init__(
        self,
        tolerance: float = 0.1,
        error_message: str | None = None,
        error_media_id: str | None = None,
        error_media_type: str | None = None,
    ):
        """
        tolerance: допустимая погрешность соотношения сторон (например, 0.1 = 10)
        """
        super().__init__(
            error_message=error_message,
            error_media_id=error_media_id,
            error_media_type=error_media_type,
        )

        self.tolerance = tolerance

    async def validate(self, image_info: ImageInfo) -> ValidationResult:
        ratio = image_info.width / image_info.height
        if abs(ratio - 1) > self.tolerance:
            return ValidationResult(
                is_valid=False,
                error_text=self.error_message,
                error_media_id=self.error_media_id,
                error_media_type=self.error_media_type,
            )
        return ValidationResult(is_valid=True)
