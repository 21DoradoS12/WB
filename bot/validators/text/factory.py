from typing import List

from src.bot.validators.text import MaxLinesValidator, MaxLengthValidator
from src.bot.validators.text.base import TextValidator


class TextValidatorFactory:
    """
    Фабрика для создания валидаторов текста на основе конфигурации.
    """

    # Сопоставление типа валидатора и класса
    _validator_classes = {
        "max_lines": MaxLinesValidator,
        "max_length": MaxLengthValidator,
    }

    @classmethod
    def create_validators(cls, config_list: list | None) -> List[TextValidator]:
        """
        Создаёт список валидаторов на основе списка конфигураций.

        :param config_list: Список валидаторов
        """
        validators = []

        for item in config_list or []:
            v_type = item.get("type")
            if not v_type:
                continue

            validator_class = cls._validator_classes.get(v_type)
            if not validator_class:
                continue

            params = item.copy()
            params.pop("type")
            error_message = params.pop("error_message", "Некорректный ввод.")

            validator = validator_class(error_message=error_message, **params)
            validators.append(validator)

        return validators
