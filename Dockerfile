# 1. 백엔드 요구사항인 Python 3.10 버전을 사용합니다.
FROM python:3.10-slim

# 2. 도커 내부의 작업 공간을 /src 로 지정합니다.
WORKDIR /src

# 3. requirements.txt를 복사해서 파이썬 패키지들을 설치합니다.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 백엔드 개발자가 파일을 올릴 app 폴더 전체를 복사해 옵니다.
COPY ./app ./app

# 5. 통신을 위해 8000번 포트를 엽니다.
EXPOSE 8000

# 6. FastAPI 서버를 띄우는 진짜 실행 명령어입니다.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
