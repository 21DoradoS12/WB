from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: str

    DB_HOST: str
    DB_PORT: str
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_ECHO: bool = False

    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str
    RABBITMQ_HOST: str
    RABBITMQ_PORT: str
    RABBITMQ_MANAGER_PORT: str

    REDIS_HOST: str
    REDIS_PORT: str

    YANDEX_TOKEN: str

    PYTESSERACT_PATH: str

    WB_NOTIFICATION_THREAD: int
    MEDIA_NOTIFICATION_THREAD: int
    ADMIN_CHAT_ID: int

    WB_TOKEN: str

    ADMIN_ID: int

    API_ID: int
    API_HASH: str

    @property
    def db_url_async(self):
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def rabbitmq_url(self):
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/"

    class Config:
        env_file = ".env"


settings = Settings()
