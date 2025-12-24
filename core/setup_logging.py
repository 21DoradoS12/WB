import logging
import os
from logging.handlers import RotatingFileHandler


class ExtraFormatter(logging.Formatter):
    def format(self, record):
        # Сохраняем оригинальные exc_info и exc_text
        original_exc_text = record.exc_text
        record.exc_text = None  # временно убираем, чтобы не мешал

        # Экранируем \n в основном сообщении (и в args, если нужно)
        if isinstance(record.msg, str):
            record.msg = record.msg.replace("\n", "\\n")
        elif isinstance(record.args, (tuple, list)):
            record.args = tuple(
                arg.replace("\n", "\\n") if isinstance(arg, str) else arg
                for arg in record.args
            )

        # Форматируем основное сообщение (уже без реальных переносов)
        log_message = super().format(record)

        # Возвращаем exc_text обратно
        record.exc_text = original_exc_text

        # Добавляем extra-поля
        standard_attrs = logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys()
        extra_fields = {
            k: v for k, v in record.__dict__.items() if k not in standard_attrs
        }

        if extra_fields:
            # Экранируем \n в значениях extra, если нужно
            safe_extra = {}
            for k, v in extra_fields.items():
                if isinstance(v, str):
                    v = v.replace("\n", "\\n")
                safe_extra[k] = v
            extra_str = " ".join(f"{k}={v}" for k, v in safe_extra.items())
            log_message = f"{log_message} | {extra_str}"

        # Добавляем трейсбэк отдельно (если есть), но он уже не испортит строку
        if record.exc_text:
            log_message = f"{log_message}\n{record.exc_text}"

        return log_message


class NoExcInfoFilter:
    """Убирает exc_info из записи — чтобы traceback не дублировался в общем логе"""

    def filter(self, record):
        record.exc_info = None
        record.exc_text = None
        return True


def setup_logging(
    service_name: str, log_level: int = logging.INFO, logs_dir: str = "logs"
):
    os.makedirs(logs_dir, exist_ok=True)

    formatter = ExtraFormatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    all_file_handler = RotatingFileHandler(
        os.path.join(logs_dir, f"{service_name}.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    all_file_handler.setFormatter(formatter)
    all_file_handler.addFilter(NoExcInfoFilter())  # 🔥 Убираем traceback из общего лога

    error_file_handler = RotatingFileHandler(
        os.path.join(logs_dir, f"{service_name}_error.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    error_file_handler.setFormatter(formatter)
    error_file_handler.setLevel(logging.ERROR)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Настраиваем корневой логгер
    logging.basicConfig(
        level=log_level,
        handlers=[all_file_handler, error_file_handler, console_handler],
        force=True,
    )
