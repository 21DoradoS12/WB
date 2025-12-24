from pydantic import BaseModel, ConfigDict


class BaseModelWithConfig(BaseModel):
    """Базовая модель для DTO и Domain моделей"""

    model_config = ConfigDict(
        from_attributes=True,
    )
