from typing import Optional
from pydantic import BaseModel, Field, field_validator
from urllib.parse import urlparse

class AnalyzeRequest(BaseModel):
    image_url: str = Field(..., min_length = 1, description = "분석할 이미지 주소")
    page_url: Optional[str] = Field(None, description = "원본 상품 페이지 주소")
    @field_validator("image_url", "page_url")
    @classmethod
    def validate_http_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("유효한 http(s) URL이어야 합니다.")
        return value

class AnalyzeResponse(BaseModel):
    alt: str

class HealthResponse(BaseModel):
    status: str
    service: str