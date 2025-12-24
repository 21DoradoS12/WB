import logging
import os

import numpy as np
from PIL import Image
from moviepy import VideoClip

log = logging.getLogger(__name__)


class MoviePyVideoService:
    def __init__(
        self,
        output_dir: str = "tmp/videos",
        temp_dir: str = "tmp/temp_images",
        slide_duration: float = 4,
        fade_duration: float = 1,
        target_size: tuple[int, int] = (1080, 1440),
        fps: int = 24,
        cleanup_sources: bool = True,
    ):
        self.output_dir = output_dir
        self.temp_dir = temp_dir
        self.slide_duration = slide_duration
        self.fade_duration = fade_duration
        self.target_size = target_size
        self.fps = fps
        self.cleanup_sources = cleanup_sources

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

    async def _normalize_images(self, image_paths: list[str]) -> list[str]:
        """
        Приводит все изображения к одному размеру target_size с учетом ориентации EXIF
        и сохраняет во временную папку.
        Возвращает пути к нормализованным изображениям.
        """
        from PIL import ExifTags

        normalized_paths = []
        for path in image_paths:
            img = Image.open(path).convert("RGB")

            # Исправляем ориентацию по EXIF
            try:
                for orientation in ExifTags.TAGS.keys():
                    if ExifTags.TAGS[orientation] == "Orientation":
                        break
                exif = img._getexif()
                if exif is not None:
                    orientation_value = exif.get(orientation)
                    if orientation_value == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation_value == 6:
                        img = img.rotate(270, expand=True)
                    elif orientation_value == 8:
                        img = img.rotate(90, expand=True)
            except Exception:
                pass  # если EXIF нет — игнорируем

            # Ресайз
            img_resized = img.resize(self.target_size, Image.Resampling.LANCZOS)

            filename = os.path.basename(path)
            normalized_path = os.path.join(self.temp_dir, f"norm_{filename}")
            img_resized.save(normalized_path, "JPEG", quality=90)
            normalized_paths.append(normalized_path)

        return normalized_paths

    def _make_crossfade_frames(self, images: list[np.ndarray]) -> list[np.ndarray]:
        total_frames = []
        num_frames_show = int((self.slide_duration - self.fade_duration) * self.fps)
        num_frames_fade = int(self.fade_duration * self.fps)

        for i in range(len(images)):
            current_img = images[i]
            next_img = images[i + 1] if i + 1 < len(images) else None

            for _ in range(num_frames_show):
                total_frames.append(current_img)

            if next_img is not None:
                for f in range(num_frames_fade):
                    alpha = f / num_frames_fade
                    frame = (current_img * (1 - alpha) + next_img * alpha).astype(
                        np.uint8
                    )
                    total_frames.append(frame)
        return total_frames

    async def generate(self, image_paths: list[str], output_name: str) -> str:
        try:
            normalized_paths = await self._normalize_images(image_paths)
            images = [np.array(Image.open(p)) for p in sorted(normalized_paths)]

            frames = self._make_crossfade_frames(images)

            def make_frame(t):
                idx = min(int(t * self.fps), len(frames) - 1)
                return frames[idx]

            duration = len(frames) / self.fps
            video = VideoClip(make_frame, duration=duration)

            output_path = f"{self.output_dir}/{output_name}.mp4"
            video.write_videofile(
                output_path,
                fps=self.fps,
                codec="libx264",
                preset="medium",
                bitrate="5000k",
                audio=False,
            )

            if self.cleanup_sources:
                for path in set(image_paths + normalized_paths):
                    try:
                        os.remove(path)
                    except Exception as e:
                        log.error(f"Не удалось удалить файл {path}: {e}", exc_info=True)

            return output_path

        except Exception as e:
            raise RuntimeError(f"Ошибка генерации видео: {e}")
