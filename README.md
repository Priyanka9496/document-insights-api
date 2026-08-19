# Document Insights API

Backend service built with **FastAPI, MongoDB, Redis, and Docker Compose**.

It accepts document text, processes it asynchronously using a background worker, and returns a structured summary.

## Run

### Prerequisites

* Docker
* Docker Compose

Start all services:

```bash
docker compose up --build
```

This starts:

* FastAPI API
* Background worker
* MongoDB
* Redis

Swagger:

```text
http://localhost:8000/docs
```

Health check:

```text
http://localhost:8000/health
```

Stop:

```bash
docker compose down
```

## API Endpoints

### Submit Document

```http
POST /documents
```

Request:

```json
{
  "user_id": "user-1",
  "title": "Test Document",
  "content": "Document content"
}
```

A new document is stored with `queued` status and processed asynchronously.

### Get Document Status

```http
GET /documents/{document_id}
```

Possible statuses:

```text
queued -> processing -> completed
                     -> failed
```

A completed document includes the generated summary.

### List User Documents

```http
GET /users/{user_id}/documents
```

Supports:

```text
page
page_size
status
```

Example:

```http
GET /users/user-1/documents?page=1&page_size=20&status=completed
```

### Health Check

```http
GET /health
```

Checks MongoDB and Redis connectivity.

## Processing

The worker atomically claims the oldest queued document using MongoDB `find_one_and_update()`.

Processing is simulated using a random delay of **10–30 seconds**.

Approximately **10% of jobs fail randomly**.

Successful jobs receive a structured summary containing:

```json
{
  "overview": "...",
  "word_count": 10,
  "key_points": [
    "Mock insight generated from document content"
  ]
}
```

## Rate Limiting

Each user can have at most **3 queued or processing documents** at the same time.

Redis tracks active jobs using:

```text
active_jobs:{user_id}
```

A Redis Lua script performs the check and increment atomically to avoid race conditions.

The fourth active submission returns:

```text
429 Too Many Requests
```

If Redis is unavailable and the service cannot enforce the limit, new processing requests return:

```text
503 Service Unavailable
```

## Content Cache

Document content is hashed using SHA-256.

Redis cache key:

```text
summary:{user_id}:{content_hash}
```

The cache TTL defaults to **24 hours**.

If the same user submits identical content after it has already been processed, the cached summary is returned immediately without running the worker again.

## MongoDB Indexes

The following indexes are created during application startup:

```text
(user_id, created_at DESC)
(user_id, status, created_at DESC)
(status, created_at ASC)
(user_id, content_hash, status)
```

They support document listing, filtering, worker queue lookup, and content-hash lookup.

## Configuration

Configuration is loaded using environment variables.

See:

```text
.env.example
```

Important settings include:

```env
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=document_insights
REDIS_URL=redis://localhost:6379

MAX_ACTIVE_JOBS_PER_USER=3
ACTIVE_JOB_TTL_SECONDS=900
SUMMARY_CACHE_TTL_SECONDS=86400

PROCESSING_MIN_SECONDS=10
PROCESSING_MAX_SECONDS=30
PROCESSING_FAILURE_RATE=0.10
```

## Tests

Run:

```bash
python -m pytest -v
```

The tests cover:

* request validation
* `201` document submission
* `404` document lookup
* `422` invalid input
* cache-hit behavior
* rate-limit behavior
* service logic

Current test suite:

```text
9 passed
```

## Design Decisions

* MongoDB is used as the durable job queue to avoid introducing another broker for this assignment.
* The worker is separate from the FastAPI process.
* `find_one_and_update()` prevents multiple workers from claiming the same job.
* Redis cache failures are treated as cache misses.
* Redis rate-limiter failures return `503` because processing capacity cannot be safely enforced.
* UTC-aware timestamps are used throughout.

## With More Time

I would add:

* retry with exponential backoff
* recovery for jobs stuck in `processing`
* protection against concurrent duplicate submissions
* cursor-based pagination for large datasets
* additional metrics and tracing
