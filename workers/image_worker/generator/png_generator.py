from io import BytesIO

from PIL import Image, ImageFont, ImageDraw, ImageEnhance
from aiogram import Bot


async def process_element_recursive(
    bot,
    canvas,
    draw,
    order_data,
    element,
    base_pos=None,
    scalar: float = 1.0,
):
    """
    Рекурсивная обработка элементов шаблона
    """
    base_pos = base_pos or {"x": 0, "y": 0}
    e_type = element["type"]
    e_name = element.get("name")

    # применяем локальный scalar, если он есть
    element_scalar = element.get("scalar", 1.0)
    scalar *= element_scalar

    if e_type == "group":
        group_items = order_data.get(e_name, [])
        repeat_count = element.get("repeat_count", len(group_items))
        positions = element.get("positions", [])

        for idx in range(min(repeat_count, len(group_items))):
            item_data = group_items[idx]
            group_pos = positions[idx] if idx < len(positions) else {"x": 0, "y": 0}
            new_base = {
                "x": base_pos["x"] + int(group_pos.get("x", 0) * scalar),
                "y": base_pos["y"] + int(group_pos.get("y", 0) * scalar),
            }

            for sub_element in element["elements"]:
                await process_element_recursive(
                    bot,
                    canvas,
                    draw,
                    item_data,
                    sub_element,
                    base_pos=new_base,
                    scalar=scalar,
                )

    elif e_type == "photo":
        source = element.get("source", "user")
        pos = element["position"]
        abs_pos = {
            "x": base_pos["x"] + int(pos["x"] * scalar),
            "y": base_pos["y"] + int(pos["y"] * scalar),
            "width": int(pos["width"] * scalar),
            "height": int(pos["height"] * scalar),
        }

        filters = element.get("filters", [])

        if source == "user":
            file_id = order_data.get(e_name, {}).get("photo_url")
            if file_id:
                await process_photo(bot, canvas, file_id, abs_pos, filters)
        elif source == "static":
            file_path = element.get("path")
            if file_path:
                await process_static_photo(canvas, file_path, abs_pos, filters)

    elif e_type == "text":
        text = order_data.get(e_name, "")
        if text:
            pos = element["position"]
            align = element.get("align", "left")
            abs_pos = {
                "x": base_pos["x"] + int(pos["x"] * scalar),
                "y": base_pos["y"] + int(pos["y"] * scalar),
            }

            # масштабируем шрифт и max_width
            font_info = element["font"].copy()
            font_info["size"] = int(font_info.get("size", 32) * scalar)
            font_info["max_width"] = int(font_info.get("max_width", 100) * scalar)

            await process_text(draw, text, font_info, abs_pos, align, scalar)


async def generate_png_from_template(
    bot: Bot,
    order_data: dict,
    template_json: dict,
    scalar: float = 1.0,
):
    """
    Генерация изображения по JSON-шаблону
    """
    template = template_json

    canvas_w = int(template["canvas"]["width"] * scalar)
    canvas_h = int(template["canvas"]["height"] * scalar)
    bg_color = template["canvas"].get("background_color", "#FFFFFF")

    canvas = Image.new("RGB", (canvas_w, canvas_h), bg_color)
    draw = ImageDraw.Draw(canvas)

    for element in template["elements"]:
        await process_element_recursive(
            bot, canvas, draw, order_data, element, scalar=scalar
        )

    output = BytesIO()
    canvas.save(output, format="PNG")
    output.seek(0)
    return output

def apply_filters(image, filters):
    """Применяет фильтры к изображению"""
    for filter_config in filters:
        filter_type = filter_config["type"]
        value = filter_config["value"]

        if filter_type == "brightness":
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(value)
    return image

async def process_photo(bot, canvas, file_id: str, pos: dict, filters: list = None):
    """
    Обработка фото, загруженного пользователем
    """

    filters = filters or []

    file = await bot.get_file(file_id)
    file_bytes = await bot.download_file(file.file_path)
    img = Image.open(BytesIO(file_bytes.read())).convert("RGBA")
    img = img.resize((pos["width"], pos["height"]))

    img = apply_filters(img, filters)

    canvas.paste(img, (pos["x"], pos["y"]), img)


async def process_static_photo(canvas, path: str, pos: dict, filters: list = None):
    """
    Обработка статичного изображения из файловой системы
    """
    filters = filters or []

    img = Image.open(path).convert("RGBA")
    img = img.resize((pos["width"], pos["height"]))

    img = apply_filters(img, filters)

    canvas.paste(img, (pos["x"], pos["y"]), img)


def get_text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


async def process_text(
    draw: ImageDraw,
    text: str,
    font_info: dict,
    pos: dict,
    align: str = "left",
    scalar: float = 1.0,
):
    """
    Обработка текста + эмодзи (через Pilmoji)
    """
    font_path = font_info["file"]
    color = font_info.get("color", "#000000")
    max_width = font_info.get("max_width", 100)
    font_size = font_info.get("size", 32)
    stroke_fill = font_info.get("stroke_fill", None)
    stroke_width = font_info.get("stroke_width", 0)

    # подбираем размер шрифта
    font = ImageFont.truetype(font_path, font_size)
    min_size = 10
    if max_width:
        while font_size > min_size:
            text_width, _ = get_text_size(draw, text, font)
            if text_width <= max_width:
                break
            font_size -= 1
            font = ImageFont.truetype(font_path, font_size)
    else:
        text_width, _ = get_text_size(draw, text, font)

    # выравнивание
    x = pos.get("x", 0)
    y = pos.get("y", 0)

    if align == "center":
        x -= text_width // 2
    elif align == "right":
        x -= text_width

    # теперь рисуем и текст, и эмодзи через Pilmoji
    from pilmoji import Pilmoji

    image = draw._image  # получаем сам Image из ImageDraw
    with Pilmoji(image) as pilmoji:
        pilmoji.text(
            (x, y),
            text,
            font=font,
            fill=color,
            stroke_fill=stroke_fill,
            stroke_width=stroke_width,
        )
