# SSCAS - Smart Surveillance and Crowd Analysis System

스마트 감시 및 군중 분석 시스템 - 실시간 인원 감지 및 밀집도 분석

## 📋 프로젝트 개요

SSCAS는 딥러닝 기반 인물 감지와 밀집도 분석을 통해 공공장소의 안전을 관리하는 실시간 감시 시스템입니다.

### 주요 기능

- 🎥 실시간 비디오 스트리밍
- 👤 AI 기반 인원 감지 (Roboflow API)
- 📊 밀집도 히트맵 시각화
- 📈 실시간 통계 대시보드
- 🔄 자동 이미지 폴링 및 업데이트

### 지원 장소

- 🚇 지하철역
- 🎵 콘서트 홀
- 🏘️ 골목 길

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐         ┌──────────────┐
│   ESP32-CAM     │────────▶│   Flask      │
│   (Camera)      │         │   Server     │
└─────────────────┘         └──────┬───────┘
                                   │
                                   ▼
                            ┌──────────────┐
                            │  AI Server   │
                            │  (Roboflow)  │
                            └──────┬───────┘
                                   │
                                   ▼
                            ┌──────────────┐
                            │  Web Client  │
                            │  (Browser)   │
                            └──────────────┘
```

## 📁 프로젝트 구조

```
SSCAS/
├── backend/                    # 백엔드 서버
│   ├── server.py              # Flask 웹 서버
│   ├── ai_server.py           # AI 처리 서버
│   └── config.py              # 설정 파일
├── frontend/                  # 프론트엔드
│   ├── templates/             # HTML 템플릿
│   │   ├── base.html         # 공통 레이아웃
│   │   ├── index.html        # 지하철역 대시보드
│   │   ├── concert.html      # 콘서트홀 대시보드
│   │   ├── path.html         # 골목길 대시보드
│   │   └── pages/            # 추가 페이지
│   └── static/               # 정적 파일
│       ├── assets/           # CSS, JS, 이미지
│       └── media/            # 미디어 파일
├── research_data/             # 연구 데이터
├── docs/                      # 프로젝트 문서
│   ├── web/                  # 웹 관련 문서
│   ├── REFACTORING_GUIDE.md
│   └── REFACTORING_SUMMARY.md
├── backup/                    # 백업 파일
├── requirements.txt           # Python 의존성
├── .env.example              # 환경 변수 템플릿
├── .gitignore                # Git 제외 파일
└── README.md                 # 이 파일
```

## 🚀 빠른 시작

### 1. 필수 요구사항

- Python 3.8+
- ESP32-CAM 또는 웹캠
- Roboflow API 키

### 2. 설치

```bash
# Python 패키지 설치
pip install -r requirements.txt
```

### 3. 환경 설정

```bash
# 환경 변수 파일 생성
cp .env.example .env

# .env 파일 편집
# - SERVER_HOST: AI 서버 IP 주소
# - CAMERA_URL: ESP32-CAM 스트림 URL
# - ROBOFLOW_API_KEY: Roboflow API 키
```

### 4. 서버 실행

#### AI 서버 시작 (터미널 1)
```bash
cd backend
python ai_server.py
```

#### Flask 웹 서버 시작 (터미널 2)
```bash
cd backend
python server.py
```

### 5. 접속

브라우저에서 `http://127.0.0.1:5000` 접속

## 🔧 설정

### config.py

주요 설정을 `backend/config.py`에서 수정:

```python
# Server Configuration
SERVER_HOST = '192.168.144.247'
SERVER_PORT = 9999

# Camera Configuration
CAMERA_URL = "http://192.168.144.241:81/stream"

# Roboflow API
ROBOFLOW_API_KEY = "your_api_key_here"
```

## 📊 API 엔드포인트

| 메서드 | 엔드포인트 | 설명 |
|--------|------------|------|
| GET | `/` | 지하철역 대시보드 |
| GET | `/concert` | 콘서트홀 대시보드 |
| GET | `/path` | 골목길 대시보드 |
| GET | `/video_feed` | 실시간 비디오 스트림 |
| GET | `/get_image/<no>` | 처리된 이미지 |
| GET | `/get_character` | 현재 분석 데이터 |
| GET | `/poll_characters` | 롱 폴링 |

### 응답 예시

```json
{
  "place": "지하철역",
  "time": "2024-12-24 14:30:25",
  "person": "15",
  "density": "23.45"
}
```

## 🛠️ 기술 스택

### 백엔드
- Flask, OpenCV, Roboflow, Seaborn, Matplotlib

### 프론트엔드
- HTML5/CSS3, JavaScript (ES6+), Bootstrap 5

## 🎯 주요 개선사항 (v2.0)

- ✅ 설정 파일 분리
- ✅ 로깅 시스템 추가
- ✅ 스레드 안전성 개선
- ✅ Jinja2 템플릿 상속
- ✅ ES6+ JavaScript 모듈
- ✅ 메모리 누수 방지
- ✅ 코드 중복 80% 감소

## 📖 문서

- **[리팩토링 가이드](docs/REFACTORING_GUIDE.md)** - 상세한 변경사항
- **[리팩토링 요약](docs/REFACTORING_SUMMARY.md)** - 개선사항 요약

## 🐛 문제 해결

### 카메라 연결 실패
- `config.py`에서 `CAMERA_URL` 확인
- ESP32-CAM 실행 상태 확인

### AI 서버 연결 실패
- AI 서버가 먼저 시작되었는지 확인
- 방화벽 설정 확인

### 포트 사용 중
```bash
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

## 📈 향후 계획

- [ ] 데이터베이스 연동
- [ ] 웹소켓 실시간 통신
- [ ] 사용자 인증 시스템
- [ ] Docker 컨테이너화

## 📝 라이센스

MIT License

---

**Made with ❤️ by SSCAS Team**

© 2024-2025 SSCAS - Smart Surveillance and Crowd Analysis System
