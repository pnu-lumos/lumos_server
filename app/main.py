from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import httpx
import mimetypes
from pathlib import Path
from urllib.parse import urlparse
from .config import Settings
from .models import AnalyzeRequest, AnalyzeResponse
from .upstage_client import UpstageClient
#from .cache import TTLAltCache
from .cache import RedisCacheManager
from PIL import Image
import io

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings.from_env()
    app.state.settings = settings
    app.state.upstage = UpstageClient(settings)
    app.state.cache = RedisCacheManager(settings)
    yield
    await app.state.upstage.close()
    await app.state.cache.close()

app = FastAPI(title = "Lumos API", lifespan = lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"], 
    allow_headers=["*"]
)

def preprocess_image(image_bytes: bytes, content_type: str) -> tuple[bytes, str]:
    if content_type == "image/gif":
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                img.seek(0)
                converted_img = img.convert("RGB")
                output = io.BytesIO()
                converted_img.save(output, format = "PNG")
                return output.getvalue(), "image/png"
        except Exception as e:
            print(f"GIF 전환 오류: {e}")
            return image_bytes, content_type
    return image_bytes, content_type

@app.post("/api/analyze", response_model = AnalyzeResponse)
async def analyze_image(request: AnalyzeRequest):
    upstage = app.state.upstage
    cache = app.state.cache
    settings = app.state.settings

    cached = await cache.get(request.image_url)
    if cached:
        print(f"Cache Hit: {request.image_url[:30]}...")
        return AnalyzeResponse(alt = cached)
    try:
        async with httpx.AsyncClient(timeout = settings.request_timeout_sec) as client:
            resp = await client.get(request.image_url, follow_redirects = True)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "").split(";")[0].strip().lower()
            parsed_url = urlparse(request.image_url)
            filename = Path(parsed_url.path).name or "image.bin"
            image_content, final_content_type = preprocess_image(resp.content, content_type)
            if content_type == "image/gif":
                filename = filename.rsplit('.', 1)[0] + ".png"
        markdown_data = await upstage.parse_document(image_bytes = image_content, filename = filename, content_type = final_content_type)
        if hasattr(markdown_data, 'markdown'):
            actual_markdown = markdown_data.markdown
        else:
            actual_markdown = markdown_data
        alt_text = await upstage.generate_alt_text(parsed_markdown = actual_markdown, page_url = request.page_url)
        await cache.set(request.image_url, alt_text)
        return AnalyzeResponse(alt = alt_text)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code = 400, detail = f"이미지를 불러올 수 없습니다: {e.response.status_code}")
    except httpx.TimeoutException:
        raise HTTPException(status_code = 504, detail = "이미지 다운로드 시간이 초과되었습니다.")
    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}") 
        raise HTTPException(status_code = 500, detail = f"서버 내부 오류: {str(e)}")