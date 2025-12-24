from typing import Optional, List

from pydantic import BaseModel


class Button(BaseModel):
    text: str
    callback_data: Optional[str] = None
    url: Optional[str] = None


class NotificationMessage(BaseModel):
    chat_id: int
    message_thread_id: Optional[int] = None
    type: str
    buttons_row_width: int = 1
    buttons: Optional[List[Button]] = None
    content: Optional[str] = None
    text: Optional[str] = None
