#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
cd "$PROJECT_DIR"

MODE="${1:-ui}"
PORT="${PORT:-8000}"

ensure_deps() {
	if ! python3 -c "import httpx,selectolax,pydantic,pandas,tldextract,rich,typer" >/dev/null 2>&1; then
		python3 -m pip install --user --break-system-packages -r requirements-full.txt
	fi
	if [[ "$MODE" == "ui" ]]; then
		if ! command -v streamlit >/dev/null 2>&1; then
			python3 -m pip install --user --break-system-packages streamlit
		fi
	elif [[ "$MODE" == "api" ]]; then
		python3 -c "import fastapi,uvicorn" >/dev/null 2>&1 || python3 -m pip install --user --break-system-packages fastapi "uvicorn[standard]"
	fi
}

run_ui() {
	export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
	streamlit run "$PROJECT_DIR/leadgen/ui.py"
}

run_api() {
	export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
	python3 -m uvicorn leadgen.api:create_app --factory --host 0.0.0.0 --port "$PORT"
}

ensure_deps
case "$MODE" in
	ui) run_ui ;;
	api) run_api ;;
	*) echo "Usage: $0 [ui|api]" >&2; exit 1 ;;
esac
