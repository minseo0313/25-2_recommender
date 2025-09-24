# 25-2 Recommender 프로젝트

> 🚀 **Docker 기반 Django + PostgreSQL (pgvector) 개발환경**  
> 이 문서만 따라 하면 팀원 누구든지 동일한 환경에서 바로 실행할 수 있습니다.

---

## 📋 프로젝트 개요

이 프로젝트는 Django와 PostgreSQL의 pgvector 확장을 활용한 추천 시스템입니다. Docker를 사용하여 개발환경을 일관성 있게 구성하고, 벡터 데이터베이스를 통한 고성능 추천 기능을 제공합니다.

### 🛠 기술 스택
- **Backend**: Django 5.1 + Django REST Framework
- **Database**: PostgreSQL 16 + pgvector
- **Containerization**: Docker + Docker Compose
- **Language**: Python 3.12.5

---

## ✅ 1. 필수 설치

다음 소프트웨어가 설치되어 있어야 합니다:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/Mac/Linux)
- [Git](https://git-scm.com/downloads)

> 💡 **Docker Desktop 설치 후 반드시 재시작하세요!**

---

## ✅ 2. 저장소 가져오기

```bash
git clone https://github.com/<YOUR_ID_OR_ORG>/25-2_recommender.git
cd 25-2_recommender
```

---

## ✅ 3. 환경 변수 파일 생성

루트 경로(`25-2_recommender/`)에 `.env` 파일을 생성하고 아래 내용을 넣으세요:

```env
# PostgreSQL
POSTGRES_DB=db_postgres
POSTGRES_USER=user_postgres
POSTGRES_PASSWORD=pwd_postgres
POSTGRES_PORT=5432

# Django
DJANGO_SECRET_KEY=change-me-to-a-long-random-string
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_PORT=8000

# DB Host (docker-compose 서비스명)
POSTGRES_HOST=postgres_service
```

> ⚠️ **중요**: `.env`는 보안상 깃허브에 올리지 않습니다.  
> 팀원은 이 문서를 보고 직접 생성해야 합니다.  
> 참고용으로 `.env.example` 파일도 제공합니다.

---

## ✅ 4. 컨테이너 빌드 & 실행

### 최초 실행 또는 requirements.txt 변경 시:
```bash
docker compose up -d --build
```

### 정상 동작 확인:
```bash
# 컨테이너 상태 확인
docker compose ps

# Django 로그 확인
docker compose logs web --tail=100
# "Watching for file changes with StatReloader" → 정상
```

### 일반적인 재시작:
```bash
docker compose up -d
```

### 컨테이너 중지:
```bash
docker compose down
```

---

## ✅ 5. PostgreSQL 세팅 (최초 1회만)

### DB 확장(pgvector) 활성화:

```bash
docker exec -it postgres_service psql -U user_postgres -d db_postgres
```

psql 내부에서:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
\dx   -- vector 확장 확인
\q
```

---

## ✅ 6. Django 마이그레이션 & 관리자 계정 (최초 1회만)

```bash
docker exec -it django_service bash
```

Django 컨테이너 내부에서:
```bash
# DB 테이블 생성
python manage.py migrate          

# 관리자 계정 생성
python manage.py createsuperuser  
# Username: admin
# Email:    admin@gmail.com
# Password: admin1010

exit
```

---

## ✅ 7. 접속

### 🌐 웹 서비스
- **API 서버**: http://localhost:8000
- **관리자 페이지**: http://localhost:8000/admin

### 🔧 개발 도구
- **PostgreSQL**: localhost:5432
  - Database: `db_postgres`
  - Username: `user_postgres`
  - Password: `pwd_postgres`


---

## 🐛 문제 해결

### 포트 충돌 시
```bash
# 사용 중인 포트 확인
netstat -ano | findstr :8000
netstat -ano | findstr :5432

# Docker 컨테이너 완전 정리
docker compose down -v
docker system prune -f
```

### 컨테이너 재빌드
```bash
# 완전 재빌드
docker compose down
docker compose build --no-cache
docker compose up -d
```

### 로그 확인
```bash
# 모든 서비스 로그
docker compose logs

# 특정 서비스 로그
docker compose logs web
docker compose logs db
```

---

## 📁 프로젝트 구조

```
25-2_recommender/
├── app/                    # Django 애플리케이션
│   ├── config/            # Django 설정
│   │   ├── settings.py    # 설정 파일
│   │   ├── urls.py        # URL 라우팅
│   │   └── ...
│   ├── manage.py          # Django 관리 스크립트
│   └── db.sqlite3         # SQLite DB (개발용)
├── postgres_data/         # PostgreSQL 데이터 (영속 저장)
├── docker-compose.yaml    # Docker Compose 설정
├── Dockerfile            # Django 컨테이너 설정
├── requirements.txt      # Python 패키지 의존성
└── README.md            # 이 파일
```

---

## 🤝 팀 개발 가이드

### Git 워크플로우
1. `main` 브랜치에서 새 브랜치 생성
2. 기능 개발 후 커밋
3. Pull Request 생성
4. 코드 리뷰 후 `main` 브랜치에 머지

### 환경 변수 관리
- `.env` 파일은 절대 커밋하지 마세요
- 새로운 환경 변수가 필요하면 `.env.example`에 추가하고 팀에 공유하세요

---

## 📞 지원

문제가 발생하면 다음을 확인해보세요:

1. Docker Desktop이 실행 중인지 확인
2. 포트 8000, 5432가 사용 가능한지 확인
3. 컨테이너 로그 확인: `docker compose logs`
4. 완전 재시작: `docker compose down -v && docker compose up -d --build`

---
