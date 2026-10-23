#!/usr/bin/env bash
#
# Asserts the repository layout required by SYSTEM_DESIGN.md section 6.
#
# Run from the repository root, and prefer running it on a fresh clone: git
# does not track empty directories, so a missing .gitkeep shows up here and
# nowhere else. This backs PHASE_PLAN.md Phase 0 exit checklist item (b).

set -u

required_dirs=(
  frontend
  backend
  backend/app
  backend/app/api
  backend/app/services
  backend/app/models
  backend/app/schemas
  backend/app/repositories
  backend/app/ml
  backend/app/agents
  backend/app/adapters
  backend/app/workers
  backend/app/core
  backend/tests
  data
  experiments
  docs
  scripts
  alembic
  alembic/versions
)

required_files=(
  README.md
  .env.example
  .gitignore
  scripts/start-local-stack.ps1
  alembic.ini
)

failures=0

for path in "${required_dirs[@]}"; do
  if [ ! -d "$path" ]; then
    echo "MISSING directory: $path"
    failures=$((failures + 1))
  fi
done

for path in "${required_files[@]}"; do
  if [ ! -f "$path" ]; then
    echo "MISSING file: $path"
    failures=$((failures + 1))
  fi
done

if [ "$failures" -gt 0 ]; then
  echo "FAILED: $failures required path(s) missing."
  exit 1
fi

echo "OK: repository structure matches SYSTEM_DESIGN.md section 6."
