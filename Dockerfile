# Python 3.11 slim 이미지 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사
COPY requirements.txt .

# Python 패키지 설치
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 파일들 복사
COPY . .

# 정적 파일 및 데이터 파일 권한 설정
RUN chmod -R 755 static/
RUN chmod -R 755 data/
RUN chmod -R 755 templates/

# 포트 8080 노출 (fly.io 기본 포트)
EXPOSE 8080

# 환경변수 설정
ENV PORT=8080
ENV PYTHONPATH=/app


# 애플리케이션 실행
CMD ["python", "main.py"]
