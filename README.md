# 서로소식 블로그

Docker, Django, PostgreSQL 기반의 개인 기술 블로그입니다.

## 🚀 빠른 시작

### Docker로 실행
```bash
# 1. 저장소 클론
git clone <repository-url>
cd 20251212

# 2. Docker 컨테이너 실행
docker-compose up --build

# 3. 브라우저에서 접속
http://localhost:8000
```

### 관리자 계정 생성
```bash
docker-compose exec web python manage.py createsuperuser
```

## ⚙️ 주요 기능

- 📝 게시글 작성/수정/삭제
- 💬 댓글 작성/삭제
- 🔐 회원가입/로그인/로그아웃
- 🔒 공개/비공개 게시글 설정
- 🔍 게시글 검색
- 📱 반응형 디자인 (Bootstrap 5)

## 🛠 기술 스택

- **Backend**: Django 4.2, Python 3.11
- **Database**: PostgreSQL 15
- **Frontend**: Bootstrap 5, HTML/CSS/JS
- **DevOps**: Docker, Docker Compose
