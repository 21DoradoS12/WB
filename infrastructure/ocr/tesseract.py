import logging
import re
from datetime import datetime
from typing import Optional, Tuple, Union

import cv2
import numpy as np
import pytesseract

from src.core.config.settings import settings

log = logging.getLogger("ocr")

pytesseract.pytesseract.tesseract_cmd = settings.PYTESSERACT_PATH

# Все возможные конфигурации Tesseract с приоритетами
CONFIGS = [
    {
        "name": "PSM 11 + OEM 3",
        "config": "--psm 11 --oem 3 -c tessedit_char_blacklist=®!@#$%^&*()_+=[]{};<>/?~`-/. ",
    },
    {
        "name": "PSM 6 + OEM 3",
        "config": "--psm 6 --oem 3 -c tessedit_char_blacklist=®!@#$%^&*()_+=[]{};<>/?~`-/. ",
    },
    {
        "name": "PSM 4 + OEM 3",
        "config": "--psm 4 --oem 3 -c tessedit_char_blacklist=®!@#$%^&*()_+=[]{};<>/?~`-/. ",
    },
    {
        "name": "PSM 3 + OEM 3",
        "config": "--psm 3 --oem 3 -c tessedit_char_blacklist=®!@#$%^&*()_+=[]{};<>/?~`-/. ",
    },
]

# Паттерны дат с приоритетами
DATE_PATTERNS = [
    {
        "name": "DD Month YYYY, HH:MM AM/PM",
        "pattern": r"\b\d{1,2}\s+[а-яА-Я]+\s+\d{4},\s*\d{1,2}:\d{2}\s*(?:АМ|РМ)?\b",
    },
    {
        "name": "DD Month YYYY, HH:MM",
        "pattern": r"\b\d{1,2}\s+[а-яА-Я]+\s+\d{4},\s*\d{1,2}:\d{2}\b",
    },
    {
        "name": "DD Month, HH:MM AM/PM",
        "pattern": r"\b\d{1,2}\s+[а-яА-Я]+,\s*\d{1,2}:\d{2}\s*(?:АМ|РМ)?\b",
    },
    {"name": "DD Month, HH:MM", "pattern": r"\b\d{1,2}\s+[а-яА-Я]+,\s*\d{1,2}:\d{2}\b"},
]


def normalize_month(date_str: str) -> str:
    ru_to_en = {
        "января": "January",
        "февраля": "February",
        "марта": "March",
        "апреля": "April",
        "мая": "May",
        "июня": "June",
        "июля": "July",
        "августа": "August",
        "сентября": "September",
        "октября": "October",
        "ноября": "November",
        "декабря": "December",
    }
    for ru, en in ru_to_en.items():
        if ru in date_str.lower():
            return date_str.lower().replace(ru, en)
    return date_str


def parse_date(date_str: str, pattern_name: str) -> Optional[datetime]:
    date_str = date_str.strip().replace("\n", "")
    date_str = normalize_month(date_str)

    try:
        if pattern_name == "DD Month YYYY, HH:MM AM/PM":
            time_part = re.search(
                r"(\d{1,2}):(\d{2})\s*(AM|PM)", date_str, re.IGNORECASE
            )
            if time_part:
                hour = int(time_part.group(1))
                if hour > 12:
                    clean_date_str = re.sub(
                        r"\s*(AM|PM)", "", date_str, flags=re.IGNORECASE
                    )
                    return datetime.strptime(clean_date_str, "%d %B %Y, %H:%M")
                else:
                    return datetime.strptime(date_str, "%d %B %Y, %I:%M %p")
            else:
                return datetime.strptime(date_str, "%d %B %Y, %H:%M")

        elif pattern_name == "DD Month YYYY, HH:MM":
            return datetime.strptime(date_str, "%d %B %Y, %H:%M")

        elif pattern_name == "DD Month, HH:MM AM/PM":
            current_year = datetime.now().year
            clean_date_str = normalize_month(date_str.strip())

            # Приводим AM/PM к английским
            clean_date_str = re.sub(
                r"\b(ам|aм)\b", "AM", clean_date_str, flags=re.IGNORECASE
            )
            clean_date_str = re.sub(
                r"\b(пм|рм|pm)\b", "PM", clean_date_str, flags=re.IGNORECASE
            )

            # Исправляем возможный формат с запятой между числами
            clean_date_str = re.sub(r"(\d{1,2}),(\d{2})", r"\1:\2", clean_date_str)

            # Ищем время и AM/PM
            time_match = re.search(
                r"(\d{1,2}):(\d{2})\s*(AM|PM)", clean_date_str, re.IGNORECASE
            )

            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                period = time_match.group(3).upper()

                # Перевод в 24-часовой формат
                if period == "PM" and hour < 12:
                    hour += 12

                elif period == "AM" and hour == 12:
                    hour = 0

                # Убираем AM/PM и подставляем 24-часовой формат

                clean_date_str = re.sub(
                    r"\d{1,2}:\d{2}\s*(AM|PM)",
                    f"{hour:02d}:{minute:02d}",
                    clean_date_str,
                    flags=re.IGNORECASE,
                )
                return datetime.strptime(
                    f"{clean_date_str} {current_year}", "%d %B, %H:%M %Y"
                )

            # Если AM/PM не найден, пробуем обычный формат
            return datetime.strptime(
                f"{clean_date_str} {current_year}", "%d %B, %H:%M %Y"
            )

        return None

    except Exception as e:
        print(f"Ошибка парсинга даты: {e}")
        return None


def preprocess_image(image_path: Union[str, bytes]) -> cv2.Mat:
    """Улучшение изображения перед распознаванием"""
    if isinstance(image_path, bytes):
        np_arr = np.frombuffer(image_path, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    elif isinstance(image_path, str):
        img = cv2.imread(image_path)
    else:
        raise TypeError("Аргумент 'img' должен быть типа str или bytes.")

    if img is None:
        raise ValueError(f"Не удалось загрузить изображение: {image_path}")

    # Увеличение размера
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    # Улучшение контраста
    # gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    # Удаление шумов
    # gray = cv2.medianBlur(gray, 3)
    return img


def extract_date_from_text(text: str) -> Optional[Tuple[str, str]]:
    """Поиск даты в тексте с определением формата"""
    for pattern in DATE_PATTERNS:
        match = re.search(pattern["pattern"], text, re.IGNORECASE)
        if match:
            return (match.group(), pattern["name"])
    return None


def validate_date(date_str: str, pattern_name: str) -> bool:
    """Проверка валидности найденной даты"""
    try:
        if pattern_name == "DD Month, HH:MM AM/PM":
            datetime.strptime(date_str, "%d %B, %I:%M %p")
        elif pattern_name == "DD.MM.YY":
            datetime.strptime(date_str, "%d.%m.%y")
        elif pattern_name == "DD Month YYYY":
            datetime.strptime(date_str, "%d %B %Y")
        elif pattern_name == "DD Month":
            # Проверяем что это действительно месяц
            month_part = date_str.split()[1]
            if month_part.lower() in [
                "января",
                "февраля",
                "марта",
                "апреля",
                "мая",
                "июня",
                "июля",
                "августа",
                "сентября",
                "октября",
                "ноября",
                "декабря",
            ]:
                return True
            return False
        return True
    except (ValueError, IndexError):
        return False


def process_image_with_configs(image_path: Union[str, bytes]) -> Optional[datetime]:
    """Обработка изображения со всеми конфигурациями"""
    processed_img = preprocess_image(image_path)
    custom_config = r'--tessdata-dir "./tessdata"'
    for config in CONFIGS:
        try:
            text = pytesseract.image_to_string(
                processed_img, lang="rus", config=config["config"]
            )
            text = text.replace("З", "3").replace("з", "3")
            date_result = extract_date_from_text(text)
            log.debug(f"Результат для конфига: {date_result}")
            if date_result:
                date_str, pattern_name = date_result
                parsed = parse_date(date_str, pattern_name)
                if parsed:
                    return parsed

        except Exception as e:
            log.error(f"Ошибка при обработке с конфигом {config['name']}: {str(e)}")
            continue

    return None
