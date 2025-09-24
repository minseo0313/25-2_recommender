# Python 3.12.5 기반 이미지 사용
FROM python:3.12.5-slim-bookworm

# 유지보수자 정보
LABEL maintainer="Developer"

# 환경 변수 설정
ENV PYTHONUMBUFFERED=1

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY ./requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt

# 애플리케이션 코드 복사
COPY ./app /app
