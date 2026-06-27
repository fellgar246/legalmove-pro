#!/usr/bin/env bash
# Applies ordered SQL migrations against DATABASE_URL inside the private Azure network.
# Tracks applied versions in schema_migrations for safe re-runs.
set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "ERROR: DATABASE_URL is required" >&2
  exit 1
fi

readonly MIGRATION_DIRECTION="${MIGRATION_DIRECTION:-up}"
readonly MIGRATIONS_DIR="${MIGRATIONS_DIR:-/migrations}"

MIGRATIONS=(
  "000001_init"
  "000002_detected_changes_granular"
  "000003_document_storage_provider"
  "000004_allow_azure_storage_provider"
)

psql_cmd() {
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -q "$@"
}

ensure_ledger() {
  psql_cmd <<'SQL'
CREATE TABLE IF NOT EXISTS schema_migrations (
  version TEXT PRIMARY KEY,
  applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
SQL
}

is_applied() {
  local version="$1"
  local count
  count="$(psql_cmd -tAc "SELECT COUNT(*) FROM schema_migrations WHERE version = '${version}'")"
  count="${count//[[:space:]]/}"
  [[ "$count" == "1" ]]
}

apply_up() {
  local version="$1"
  local sql_file="${MIGRATIONS_DIR}/${version}.up.sql"

  if [[ ! -f "$sql_file" ]]; then
    echo "ERROR: missing migration file ${sql_file}" >&2
    exit 1
  fi

  if is_applied "$version"; then
    echo "SKIP: ${version} (already applied)"
    return 0
  fi

  echo "APPLY: ${version}"
  psql_cmd -f "$sql_file"
  psql_cmd -c "INSERT INTO schema_migrations (version) VALUES ('${version}')"
}

apply_down() {
  local version="$1"
  local sql_file="${MIGRATIONS_DIR}/${version}.down.sql"

  if [[ ! -f "$sql_file" ]]; then
    echo "ERROR: missing rollback file ${sql_file}" >&2
    exit 1
  fi

  if ! is_applied "$version"; then
    echo "SKIP: ${version} (not applied)"
    return 0
  fi

  echo "ROLLBACK: ${version}"
  psql_cmd -f "$sql_file"
  psql_cmd -c "DELETE FROM schema_migrations WHERE version = '${version}'"
}

run_up() {
  local version
  for version in "${MIGRATIONS[@]}"; do
    if [[ -n "${MIGRATION_TARGET:-}" && "$version" != "$MIGRATION_TARGET" ]]; then
      continue
    fi
    apply_up "$version"
  done
}

run_down() {
  local version
  local idx

  for (( idx = ${#MIGRATIONS[@]} - 1; idx >= 0; idx-- )); do
    version="${MIGRATIONS[$idx]}"
    if [[ -n "${MIGRATION_TARGET:-}" && "$version" != "$MIGRATION_TARGET" ]]; then
      continue
    fi
    apply_down "$version"
    if [[ -n "${MIGRATION_TARGET:-}" ]]; then
      break
    fi
  done
}

main() {
  echo "Starting migrations (direction=${MIGRATION_DIRECTION})"
  ensure_ledger

  case "$MIGRATION_DIRECTION" in
    up)
      run_up
      ;;
    down)
      run_down
      ;;
    *)
      echo "ERROR: MIGRATION_DIRECTION must be up or down" >&2
      exit 1
      ;;
  esac

  echo "Migrations complete."
}

main
