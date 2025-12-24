import os

from aiogram import Bot


class TelegramMediaService:
    def __init__(self, bot: Bot, download_dir: str = "tmp/downloads"):
        self.bot = bot
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)

    async def download_images(self, file_ids: list[str]) -> list[str]:
        paths = []
        for fid in file_ids:
            file = await self.bot.get_file(fid)
            path = os.path.join(self.download_dir, f"{fid}.jpg")
            await self.bot.download_file(file.file_path, path)
            paths.append(path)
        return paths
