# Turio — Deployment

## 1. Containers

Use Docker for repeatable environments.

Suggested services:

```text
frontend
backend
worker
postgres
object-storage
```

Browser automation may require a dedicated runtime/container.

## 2. Environments

Maintain:

- development
- evaluation
- production

Never run experiments directly against production user data.

## 3. Environment variables

Example categories:

```text
DATABASE_URL
OBJECT_STORAGE_ENDPOINT
OBJECT_STORAGE_BUCKET
OBJECT_STORAGE_ACCESS_KEY
OBJECT_STORAGE_SECRET_KEY
LLM_API_KEY
BROWSER_RUNTIME_CONFIG
SECRET_KEY
```

Use `.env.example` with placeholders only.

## 4. Worker

Use a background worker for:
- ingestion,
- embedding generation,
- long-running agent tasks,
- evaluations.

## 5. Observability

At minimum:
- structured logs,
- request ids,
- agent run ids,
- application ids,
- error codes,
- basic health endpoint.

## 6. Deployment principle

Ship the smallest validated deployment.

Do not add Kubernetes, service meshes, or other infrastructure unless the real workload requires them.
