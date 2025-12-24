# SSCAS 리팩토링 가이드

## 변경된 파일 목록

### 신규 파일

#### Python
- `python/config.py` - 중앙 집중식 설정 관리
- `python/ai_server_refactored.py` - 개선된 AI 서버 (클래스 기반)

#### 웹
- `web/templates/base.html` - 공통 레이아웃 템플릿
- `web/templates/index_new.html` - 개선된 지하철역 페이지
- `web/templates/concert_new.html` - 개선된 콘서트홀 페이지
- `web/templates/path_new.html` - 개선된 골목길 페이지
- `web/static/assets/js/sscas-dashboard.js` - 모듈화된 JavaScript

#### 설정 및 문서
- `requirements.txt` - Python 의존성
- `.env.example` - 환경 변수 템플릿
- `.gitignore` - Git 제외 파일
- `README_NEW.md` - 업데이트된 프로젝트 문서
- `REFACTORING_GUIDE.md` - 이 파일

### 기존 파일 수정

#### Python
- `python/server.py` - 완전히 리팩토링됨
  - 설정 파일 분리
  - 로깅 추가
  - 스레드 안전성
  - 에러 핸들링

#### 웹
- `web/package.json` - 메타데이터 추가

## 마이그레이션 단계

### 1단계: 백업

기존 파일을 백업하세요:
```bash
# 기존 파일 백업
cp python/server.py python/server.py.backup
cp python/ai_server.py python/ai_server.py.backup
```

### 2단계: 환경 설정

1. `.env.example`을 `.env`로 복사:
```bash
cp .env.example .env
```

2. `.env` 파일 수정 (API 키, IP 주소 등)

3. 의존성 설치:
```bash
pip install -r requirements.txt
```

### 3단계: 새 서버로 전환

#### 옵션 A: 새 AI 서버 사용
```bash
python python/ai_server_refactored.py
```

#### 옵션 B: 기존 AI 서버 사용
```bash
python python/ai_server.py
```

#### 웹 서버 시작 (필수)
```bash
python python/server.py
```

### 4단계: 새 템플릿 사용

새 템플릿을 사용하려면 `python/server.py`에서 다음을 변경:

```python
# 기존
return render_template('index.html')

# 신규
return render_template('index_new.html')
```

또는 기존 파일을 교체:
```bash
# 백업 후
cp web/templates/index.html web/templates/index.html.backup

# 새 파일로 교체
cp web/templates/index_new.html web/templates/index.html
cp web/templates/concert_new.html web/templates/concert.html
cp web/templates/path_new.html web/templates/path.html
```

## 주요 개선 사항

### 코드 품질

#### Before (기존)
```python
ok=0
analysis_data=[]

def recv_data(client_socket):
    global analysis_data,ok
    while True:
        data = client_socket.recv(1024)
        analysis_data=list(data.decode().split(":"))
        if analysis_data[0]=="analysis":
            print("recive : ", repr(data.decode()))
            ok=1
```

#### After (개선)
```python
class ApplicationState:
    def __init__(self):
        self.analysis_data = []
        self.ok = False
        self.lock = Lock()
    
    def update_analysis_data(self, data):
        with self.lock:
            self.analysis_data = data
            self.ok = True

state = ApplicationState()

def recv_data(client_socket):
    """Receive analysis data from AI server"""
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                logger.warning('Connection lost')
                break
            
            decoded_data = data.decode().split(":")
            if decoded_data[0] == "analysis":
                logger.info(f'Received: {decoded_data}')
                state.update_analysis_data(decoded_data)
        except Exception as e:
            logger.error(f'Error: {e}')
            break
```

### JavaScript 개선

#### Before (기존)
```javascript
function pollImage1() {
    fetch('/get_image/1')
        .then(response => response.blob())
        .then(blob => {
            const imageUrl = URL.createObjectURL(blob);
            document.getElementById('image').src = imageUrl;
            setTimeout(pollImage1, 3000);
        })
        .catch(error => {
            console.error('Error:', error);
        });
}
```

#### After (개선)
```javascript
class SSCASClient {
    pollImage(imageId, endpoint, interval) {
        const imageElement = document.getElementById(imageId);
        
        const fetchImage = async () => {
            try {
                const response = await fetch(endpoint);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                
                const blob = await response.blob();
                const imageUrl = URL.createObjectURL(blob);
                
                // Prevent memory leak
                if (imageElement.src.startsWith('blob:')) {
                    URL.revokeObjectURL(imageElement.src);
                }
                
                imageElement.src = imageUrl;
            } catch (error) {
                console.error(`Error polling ${imageId}:`, error);
            } finally {
                setTimeout(fetchImage, interval);
            }
        };
        
        fetchImage();
    }
}
```

### HTML 구조 개선

#### Before (기존)
- 각 페이지마다 전체 HTML 구조 중복
- 인라인 JavaScript 스크립트
- 하드코딩된 경로

#### After (개선)
- Jinja2 템플릿 상속 사용
- 외부 JavaScript 모듈
- `url_for()` 사용한 동적 경로

## 테스트

### 기능 테스트 체크리스트

- [ ] 비디오 스트리밍 정상 작동
- [ ] 이미지 폴링 정상 작동
- [ ] 분석 데이터 업데이트 확인
- [ ] 히트맵 생성 확인
- [ ] 모든 페이지 네비게이션 작동
- [ ] 에러 처리 확인
- [ ] 로그 출력 확인

### 성능 테스트

1. 메모리 사용량 모니터링
2. CPU 사용률 확인
3. 네트워크 트래픽 확인
4. 응답 시간 측정

## 롤백 절차

문제가 발생하면 백업 파일로 복원:

```bash
# Python 서버
cp python/server.py.backup python/server.py
cp python/ai_server.py.backup python/ai_server.py

# HTML 템플릿
cp web/templates/index.html.backup web/templates/index.html
cp web/templates/concert.html.backup web/templates/concert.html
cp web/templates/path.html.backup web/templates/path.html
```

## 문제 해결

### 일반적인 문제

#### 1. 모듈을 찾을 수 없음
```bash
pip install -r requirements.txt
```

#### 2. 포트가 이미 사용 중
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:5000 | xargs kill -9
```

#### 3. 카메라 연결 실패
- `config.py`에서 `CAMERA_URL` 확인
- ESP32-CAM이 실행 중인지 확인
- 네트워크 연결 확인

#### 4. AI 서버 연결 실패
- `config.py`에서 `SERVER_HOST`와 `SERVER_PORT` 확인
- AI 서버가 먼저 시작되었는지 확인
- 방화벽 설정 확인

## 추가 개선 권장사항

### 단기 (1-2주)
- [ ] 환경 변수 로딩 (`python-dotenv` 사용)
- [ ] 유닛 테스트 작성
- [ ] API 문서화 (Swagger/OpenAPI)

### 중기 (1-2개월)
- [ ] 데이터베이스 통합 (SQLite/PostgreSQL)
- [ ] 웹소켓 실시간 통신
- [ ] Docker 컨테이너화

### 장기 (3개월+)
- [ ] 마이크로서비스 아키텍처
- [ ] CI/CD 파이프라인
- [ ] 클라우드 배포 (AWS/GCP/Azure)

## 리소스

- [Flask 문서](https://flask.palletsprojects.com/)
- [OpenCV Python 튜토리얼](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)
- [Roboflow API 문서](https://docs.roboflow.com/)
- [Bootstrap 5 문서](https://getbootstrap.com/docs/5.0/)

## 지원

문제가 발생하면:
1. 로그 파일 확인
2. GitHub Issues 검색
3. 새 이슈 생성

---

**Happy Coding! 🚀**
