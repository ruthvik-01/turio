# Build context is the repository root, not ./backend: SYSTEM_DESIGN.md
# section 6 places alembic/ and alembic.ini at the root, and the container
# startup path runs `alembic upgrade head` before the API.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Requirements first so the dependency layer survives application code edits.
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Mirrors the repository layout so `prepend_sys_path = . backend` resolves in
# both the container and a local checkout.
COPY backend/ ./
COPY alembic/ ./alembic/
COPY alembic.ini ./

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
