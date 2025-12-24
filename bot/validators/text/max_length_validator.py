from src.bot.validators.text import TextValidator
from src.bot.validators.validation_result import ValidationResult


class MaxLengthValidator(TextValidator):
    def __init__(
        self,
        limit: int,
        error_message: str | None = None,
        error_media_id: str | None = None,
        error_media_type: str | None = None,
    ):
        super().__init__(
            error_message=error_message,
            error_media_id=error_media_id,
            error_media_type=error_media_type,
        )
        self.limit = limit

    async def validate(self, text: str) -> ValidationResult:
        if len(text) > self.limit:
            return ValidationResult(
                is_valid=False,
                error_text=self.error_message.format(limit=self.limit, count=len(text)),
                error_media_id=self.error_media_id,
                error_media_type=self.error_media_type,
            )
        return ValidationResult(is_valid=True)
