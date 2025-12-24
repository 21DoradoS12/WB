from abc import abstractmethod, ABC

from src.bot.validators.validation_result import ValidationResult


class TextValidator(ABC):
    def __init__(
        self,
        error_message: str | None = None,
        error_media_id: str | None = None,
        error_media_type: str | None = None,
    ):
        self.error_message = error_message
        self.error_media_id = error_media_id
        self.error_media_type = error_media_type

    @abstractmethod
    async def validate(self, text: str) -> ValidationResult:
        """
        Возвращает:
            (успех: bool, сообщение об ошибке: str или None)
        """
        pass
