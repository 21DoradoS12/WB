from io import BytesIO

from PIL import Image, ImageFont, ImageDraw, ImageEnhance, ImageCms
from aiogram import Bot


def mm_to_px(mm: float, dpi: int = 500, scalar: float = 1.0) -> int:
    """Перевод миллиметров в пиксели."""
    return int(mm / 25.4 * dpi * scalar)


async def process_element_recursive(
    bot: Bot,
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    order_data: dict,
    element: dict,
    base_pos=None,
    scalar: float = 1.0,
    dpi: int = 500,
):
    """
    Рекурсивная обработка элементов шаблона
    """
    base_pos = base_pos or {"x": 0, "y": 0}
    e_type = element["type"]
    e_name = element.get("name")

    # применяем локальный scalar
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
                "x": base_pos["x"] + mm_to_px(group_pos.get("x", 0), dpi, scalar),
                "y": base_pos["y"] + mm_to_px(group_pos.get("y", 0), dpi, scalar),
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
                    dpi=dpi,
                )

    elif e_type == "photo":
        source = element.get("source", "user")
        pos = element["position"]
        abs_pos = {
            "x": base_pos["x"] + mm_to_px(int(pos["x"]), dpi, scalar),
            "y": base_pos["y"] + mm_to_px(int(pos["y"]), dpi, scalar),
            "width": mm_to_px(int(pos["width"]), dpi, scalar),
            "height": mm_to_px(int(pos["height"]), dpi, scalar),
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
                "x": base_pos["x"] + mm_to_px(int(pos["x"]), dpi, scalar),
                "y": base_pos["y"] + mm_to_px(int(pos["y"]), dpi, scalar),
            }

            # масштабируем шрифт и max_width
            font_info = element["font"].copy()
            font_info["font_size"] = mm_to_px(font_info.get("size", 5), dpi, scalar)
            font_info["max_width"] = mm_to_px(
                font_info.get("max_width", 50), dpi, scalar
            )

            await process_text(draw, text, font_info, abs_pos, align)


async def generate_output_from_template(
    bot: Bot,
    order_data: dict,
    template_json: dict,
    output_format: str = "pdf",  # pdf | png
    dpi: int = 500,
    scalar: float = 1.0,
):
    """
    Генерация изображения (PDF с ICC или PNG без ICC).
    """
    template = template_json

    # --- 1. Конвертируем мм → пиксели ---
    canvas_w = mm_to_px(template["canvas"]["width"], dpi, scalar)
    canvas_h = mm_to_px(template["canvas"]["height"], dpi, scalar)

    # цвет фона
    bg_color_hex = template["canvas"].get("background_color", "#FFFFFF")
    bg_rgb = tuple(int(bg_color_hex[i : i + 2], 16) for i in (1, 3, 5))

    # --- 2. Создаём холст в RGB ---
    canvas = Image.new("RGB", (canvas_w, canvas_h), bg_rgb)
    draw = ImageDraw.Draw(canvas)

    # --- 3. Отрисовываем все элементы ---
    for element in template["elements"]:
        await process_element_recursive(
            bot, canvas, draw, order_data, element, scalar=scalar, dpi=dpi
        )

    if output_format == "pdf":
        # --- 4. Конвертация RGB → CMYK + ICC ---
        srgb_profile = ImageCms.getOpenProfile("./statics/sRGB_IEC61966-2-1.icc")
        cmyk_profile = ImageCms.getOpenProfile("./statics/SWOP.icc")
        rgb2cmyk = ImageCms.buildTransformFromOpenProfiles(
            srgb_profile, cmyk_profile, "RGB", "CMYK"
        )
        canvas_cmyk = ImageCms.applyTransform(canvas, rgb2cmyk)

        with open("./statics/JapanColor2002Newspaper.icc", "rb") as f:
            icc_bytes = f.read()

        # сохраняем временно в JPEG (CMYK + ICC)
        img_buffer = BytesIO()
        canvas_cmyk.save(
            img_buffer,
            format="jpeg",
            dpi=(dpi, dpi),
            resolution=dpi,
            icc_profile=icc_bytes,
            quality=100,
        )
        img_buffer.seek(0)

        # оборачиваем в PDF через reportlab
        from reportlab.pdfgen import canvas as rl_canvas
        from reportlab.lib.units import mm
        from reportlab.lib.utils import ImageReader

        img = ImageReader(img_buffer)
        pdf_buffer = BytesIO()
        rl = rl_canvas.Canvas(
            pdf_buffer,
            pagesize=(
                template["canvas"]["width"] * mm,
                template["canvas"]["height"] * mm,
            ),
        )
        rl.drawImage(
            img,
            0,
            0,
            width=template["canvas"]["width"] * mm,
            height=template["canvas"]["height"] * mm,
        )
        rl.showPage()
        rl.save()
        pdf_buffer.seek(0)
        return pdf_buffer

    elif output_format == "png":
        # --- Сохраняем как PNG в sRGB без ICC ---
        png_buffer = BytesIO()
        canvas.save(png_buffer, format="PNG", dpi=(dpi, dpi))
        png_buffer.seek(0)
        return png_buffer

    else:
        raise ValueError(f"Unsupported format: {output_format}")


def apply_filters(image: Image.Image, filters: list):
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
    draw: ImageDraw.ImageDraw,
    text: str,
    font_info: dict,
    pos: dict,
    align: str = "left",
):
    """
    Обработка текста + эмодзи (через Pilmoji).
    Размеры из mm → px заранее пересчитаны в font_info.
    """
    font_path = font_info["file"]
    color = font_info.get("color", "#000000")
    font_size = font_info.get("font_size", 32)
    max_width = font_info.get("max_width", 100)
    stroke_fill = font_info.get("stroke_fill", None)
    stroke_width = font_info.get("stroke_width", 0)

    # подбираем размер шрифта
    font = ImageFont.truetype(font_path, font_size)
    if max_width:
        while font_size > 10:
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

    from pilmoji import Pilmoji

    image = draw._image
    with Pilmoji(image) as pilmoji:
        pilmoji.text(
            (x, y),
            text,
            font=font,
            fill=color,
            stroke_fill=stroke_fill,
            stroke_width=stroke_width,
        )
