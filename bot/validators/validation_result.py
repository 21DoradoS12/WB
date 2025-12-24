from dataclasses import dataclass


@dataclass
class ValidationResult:
    """
    error_media_type: photo или video
    """

    is_valid: bool
    error_text: str | None = None
    error_media_id: str | None = None
    error_media_type: str | None = None
