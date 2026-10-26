# Build context is the repository root, not ./backend: alembic/ and alembic.ini
# live beside backend/, and the startup path runs `alembic upgrade head` first.
#
#   docker build -f backend/Dockerfile .
#
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Requirements first so the dependency layer survives application code edits.
COPY backend/requirements.txt backend/requirements-ml.txt backend/requirements-browser.txt ./

# Optional capability layers. Off by default: they add hundreds of MB and
# neither is needed for the API, worker or matching baselines.
ARG INSTALL_ML=false
ARG INSTALL_BROWSER=false

RUN pip install -r requirements.txt \
 && if [ "$INSTALL_ML" = "true" ]; then pip install -r requirements-ml.txt; fi \
 && if [ "$INSTALL_BROWSER" = "true" ]; then \
      pip install -r requirements-browser.txt \
      && python -m playwright install --with-deps chromium; \
    fi

# Flattened one level: backend/ becomes /app, so the `app` package lands at
# /app/app and alembic.ini sits at /app beside it. That is exactly the layout
# alembic.ini's `prepend_sys_path = . backend` expects, and it keeps the
# working directory identical for uvicorn, alembic and the worker.
COPY backend/ ./
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Run unprivileged. Nothing is written to disk at runtime: resumes go to object
# storage and PostgreSQL holds the metadata.
RUN useradd --create-home --uid 10001 turio \
 && chown -R turio:turio /app
USER turio

EXPOSE 8000

# Overridden by compose for the worker (python -m app.workers.main).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
