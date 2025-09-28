# Recommender System Project

이 프로젝트는 Django 기반의 추천 시스템입니다.

## 🚀 빠른 시작 가이드

### 1. Windows 환경 설정

#### Python 3.12 설치
1. [Python 3.12 공식 사이트](https://www.python.org/downloads/)에서 다운로드
2. 설치 시 **"Add to PATH"** 체크박스 반드시 선택
3. 설치 완료 후 터미널에서 확인:
   ```bash
   python --version
   # Python 3.12.x 출력 확인
   ```

#### 프로젝트 클론 및 설정
```bash
# 레포지토리 클론
git clone <repo-url>
cd <repo-root>

# 가상환경 생성 및 활성화
py -3.12 -m venv .venv
.\.venv\Scripts\activate

# pip 업그레이드 및 패키지 설치
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### 환경 변수 설정
프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가:

```env
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=dev-only

DB_NAME=recommender_db
DB_USER=recommender_user
DB_PASSWORD=recommender_pass
DB_HOST=127.0.0.1
DB_PORT=5432
```

### 2. WSL (Ubuntu) 환경 설정

#### PostgreSQL 16 설치
```bash
# 패키지 업데이트 및 PostgreSQL 설치
sudo apt update
sudo apt install -y postgresql postgresql-contrib
```

#### 데이터베이스 및 사용자 생성
```bash
# PostgreSQL 접속
sudo -u postgres psql

# 데이터베이스 사용자 및 데이터베이스 생성
CREATE ROLE recommender_user WITH LOGIN PASSWORD 'recommender_pass';
CREATE DATABASE recommender_db OWNER recommender_user;

# 데이터베이스 연결 및 pgvector 확장 설치
\c recommender_db
CREATE EXTENSION IF NOT EXISTS vector;

# PostgreSQL 종료
\q
```

#### PostgreSQL 서비스 실행 확인
```bash
sudo service postgresql start
```

#### PostgreSQL 네트워크 설정 (중요!)
Windows에서 WSL의 PostgreSQL에 접속하기 위해 추가 설정이 필요합니다.

**1. postgresql.conf 수정**
```bash
# PostgreSQL 설정 파일 수정
sudo nano /etc/postgresql/16/main/postgresql.conf

# listen_addresses 찾아서 수정
# 기존: listen_addresses = 'localhost'
# 변경: listen_addresses = '*'
```

**2. pg_hba.conf 수정**
```bash
# PostgreSQL 인증 설정 파일 수정
sudo nano /etc/postgresql/16/main/pg_hba.conf

# 파일 끝에 다음 줄 추가
host    all     all     0.0.0.0/0     md5
```

**3. PostgreSQL 재시작**
```bash
sudo service postgresql restart
```

> **⚠️ 중요**: 이 설정 없이는 Windows에서 WSL의 PostgreSQL로 TCP 접속이 막혀서 Django가 데이터베이스에 연결할 수 없습니다.

### 3. Django 애플리케이션 실행

Windows PowerShell에서 다음 명령어를 실행:

```bash
# 가상환경 활성화
.\.venv\Scripts\activate

# 데이터베이스 마이그레이션
python manage.py migrate

# 개발 서버 실행
python manage.py runserver
```

### 4. 실행 확인

브라우저에서 [http://127.0.0.1:8000](http://127.0.0.1:8000)에 접속하여 정상 실행을 확인합니다.

## 📋 요구사항

- **Windows**: Python 3.12
- **WSL**: Ubuntu with PostgreSQL 16
- **데이터베이스**: PostgreSQL with pgvector extension

## 🔧 문제 해결

### 가상환경 활성화가 안 되는 경우
```bash
# PowerShell 실행 정책 변경 (관리자 권한 필요)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### PostgreSQL 연결 오류
- WSL에서 PostgreSQL 서비스가 실행 중인지 확인
- 방화벽 설정 확인
- 데이터베이스 사용자 권한 확인

### 패키지 설치 오류
```bash
# pip 캐시 클리어 후 재설치
pip cache purge
pip install --no-cache-dir -r requirements.txt
```
