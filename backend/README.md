# PushForm AI Backend

FastAPI backend for Android push-up video upload, YOLO Pose analysis, shortform result videos, and PostgreSQL backed feed/social APIs.

## APIs

- `GET /health`
- `POST /api/v1/analyze/pushup`: multipart `file` upload. Optional fields: `userId`, `caption`, `publishToFeed`.
- `GET /api/v1/analyze/{analysisId}`
- `GET /api/v1/analyze/{analysisId}/shortform`
- `GET /api/v1/feed`: legacy Android feed from completed local analyses.
- `GET /api/v1/feeds?currentUserId&limit&offset`
- `GET /api/v1/feeds/{feedId}`
- `POST /api/v1/feeds/{feedId}/like` body `{ "userId": 1 }`
- `POST /api/v1/feeds/{feedId}/save` body `{ "userId": 1 }`
- `GET /api/v1/feeds/saved?userId=1`
- `GET /api/v1/feeds/mine?userId=1`
- `GET /api/v1/feeds/{feedId}/comments`
- `POST /api/v1/feeds/{feedId}/comments` body `{ "userId": 1, "content": "..." }`
- `GET /api/v1/users/{userId}`
- `GET /api/v1/users/{userId}/profile?currentUserId=1`
- `POST /api/v1/users/{userId}/follow` body `{ "currentUserId": 1 }`
- `GET /api/v1/users/{userId}/followers`
- `GET /api/v1/users/{userId}/following`
- `GET /api/v1/users/{userId}/workout-summary`
- `GET /api/v1/messages?userId=1`
- `GET /api/v1/messages/{otherUserId}?userId=1`
- `POST /api/v1/messages` body `{ "senderId": 1, "receiverId": 2, "content": "..." }`
- `GET /api/v1/settings/{userId}`
- `PATCH /api/v1/settings/{userId}`

## Local Run

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
curl -X POST http://localhost:8000/api/v1/analyze/pushup -F "file=@sample_pushup.mp4" -F "userId=1" -F "publishToFeed=true"
```

## Docker And PostgreSQL

```bash
cd backend
cp .env.example .env
docker compose up -d --build
docker compose exec api alembic upgrade head
docker compose exec api python -m app.db.seed
docker compose logs -f api
```

Stop containers without deleting PostgreSQL data:

```bash
docker compose down
```

Do not use `docker compose down -v` unless you intentionally want to delete the database volume.

## Environment

- `DATABASE_URL=postgresql+asyncpg://pushform:pushform_password@db:5432/pushform`
- `POSTGRES_DB=pushform`
- `POSTGRES_USER=pushform`
- `POSTGRES_PASSWORD=pushform_password`
- `CORS_ORIGINS=["*"]`
- `UPLOAD_DIR=uploads`
- `RESULT_DIR=results`
- `SHORTFORM_DIR=shortforms`
- `YOLO_MODEL_PATH=yolov8n-pose.pt`
- `YOLO_CONF=0.6`

`CORS_ORIGINS` supports JSON array format such as `["*"]` and comma-separated strings.

## EC2 Deploy Notes

The repository workflow deploys on push to `main`, then runs:

```bash
cd /home/ubuntu/Ai_project/backend
docker compose down
docker compose up -d --build
docker compose exec -T api alembic upgrade head
```

Open EC2 security group inbound ports:

- SSH: `22`
- FastAPI MVP: `8000`
- Optional Nginx/TLS: `80`, `443`

Android API base URL example:

```text
http://EC2_PUBLIC_IP:8000/
```
