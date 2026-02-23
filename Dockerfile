FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 설치 (Playwright 필요)
RUN apt-get update && apt-get install -y \
    libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libxinerama1 libxcursor1 libxtst6 \
    libxi6 libxext6 libx11-6 libpangocairo-1.0-0 libpango-1.0-0 \
    libcairo2 libgdk-pixbuf-2.0-0 libglib2.0-0 libfontconfig1 \
    libfreetype6 libharfbuzz0b libjpeg62-turbo libpng16-16 \
    libwebp7 liblcms2-2 libtiff6 libopenjp2-7 libxpm4 \
    libfribidi0 fonts-noto fonts-noto-cjk fonts-noto-color-emoji \
    wget ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright 브라우저 설치
RUN python -m playwright install chromium

# 애플리케이션 코드 복사
COPY . .

# 포트 설정
EXPOSE 8000

# 앱 실행
CMD ["python", "app.py"]
