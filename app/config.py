import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen = True)
class Settings:
    upstage_api_key: str
    upstage_base_url: str
    upstage_parse_path: str
    upstage_chat_path: str
    upstage_model: str
    request_timeout_sec: float
    cache_ttl_sec: int
    cache_max_entries: int

    @classmethod
    def from_env(cls) -> "Settings":
        api_key = os.getenv("UPSTAGE_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("UPSTAGE_API_KEY가 .env 파일에 설정되지 않았습니다.")
        return cls(
            upstage_api_key=api_key,
            upstage_base_url = os.getenv("UPSTAGE_BASE_URL", "https://api.upstage.ai/v1"),
            upstage_parse_path = os.getenv("UPSTAGE_PARSE_PATH", "/document-ai/document-parse"),
            upstage_chat_path = os.getenv("UPSTAGE_CHAT_PATH", "/chat/completions"),
            upstage_model = os.getenv("UPSTAGE_MODEL", "solar-pro"),
            request_timeout_sec = float(os.getenv("REQUEST_TIMEOUT_SEC", "30.0")),
            cache_ttl_sec = int(os.getenv("CACHE_TTL_SEC", "3600")),
            cache_max_entries = int(os.getenv("CACHE_MAX_ENTRIES", "500")),
        )