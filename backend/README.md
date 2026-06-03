# PushForm AI Backend

FastAPI backend for Android push-up video upload, YOLO Pose based analysis, JSON feedback, and shortform result video URLs.

## 주요 API

- `GET /health`: deployment health check
- `POST /api/v1/analyze/pushup`: multipart `file` upload. Returns `analysisId` and starts analysis.
- `GET /api/v1/analyze/{analysisId}`: returns status, progress, metrics, issues, feedback, and `shortformUrl`.
- `GET /api/v1/analyze/{analysisId}/shortform`: returns shortform URL/status.
- `GET /api/v1/feed`: returns completed analyses for the current Android feed screen.

## 로컬 실행

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

Upload test:

```bash
curl -X POST http://localhost:8000/api/v1/analyze/pushup -F "file=@sample_pushup.mp4"
```

## Docker 실행

```bash
cd backend
cp .env.example .env
docker compose up -d --build
docker compose logs -f api
```

Stop:

```bash
docker compose down
```

## AWS EC2 배포

Ubuntu EC2에서 Docker Compose 플러그인을 설치합니다.

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
```

다시 로그인한 뒤 프로젝트를 배포합니다.

```bash
git clone <repository-url>
cd <backend-project>/backend
cp .env.example .env
docker compose up -d --build
docker compose logs -f api
```

EC2 보안 그룹은 MVP 테스트 기준으로 다음 인바운드를 허용합니다.

- SSH: `22`
- FastAPI 테스트: `8000`
- 운영에서 Nginx/TLS를 붙이면 `80`, `443`

Android 앱의 API base URL 예시는 다음과 같습니다.

```text
http://EC2_PUBLIC_IP:8000/
```

## 환경 변수

`.env.example`를 `.env`로 복사해서 사용합니다.

- `ALLOWED_ORIGINS=*`: 개발 중 전체 허용. 운영에서는 Android 클라이언트/도메인으로 제한합니다.
- `UPLOAD_DIR=uploads`
- `RESULT_DIR=results`
- `SHORTFORM_DIR=shortforms`
- `YOLO_MODEL_PATH=yolov8n-pose.pt`
- `YOLO_CONF=0.6`

## 분석 구현 상태

YOLO Pose는 서버 시작 후 첫 분석 요청 때 모델을 lazy-load합니다. 사람 클래스만 `classes=[0]`으로 분석하고, 기본 confidence는 `0.6`입니다. `ultralytics`가 설치되지 않은 환경에서는 API 개발과 테스트가 가능하도록 deterministic dummy pose estimator를 사용합니다.

현재 shortform MVP는 원본 업로드 영상을 `shortforms` 디렉터리로 복사하고 `/media/shortforms/{file}` URL을 반환합니다. 이후 FFmpeg로 9:16 편집, 인트로 카드, 관절선 오버레이, 결과 요약 카드를 추가할 수 있습니다.

## Nginx 운영 구조

현재 MVP는 Android 앱이 `http://EC2_PUBLIC_IP:8000`으로 직접 호출할 수 있습니다. 운영에서는 다음 구조를 권장합니다.

```text
Android App -> Nginx 80/443 -> FastAPI 8000
```
