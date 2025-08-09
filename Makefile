SHELL := /bin/bash

# ---- Backend settings ----
VENVDIR := backend/.venv
PYTHON := $(VENVDIR)/bin/python
PIP := $(VENVDIR)/bin/pip
PYTHONPATH := backend
UVICORN_APP := app.main:app
BACKEND_PORT := 8000
FRONTEND_PORT := 5173
UVICORN_OPTS := --reload --app-dir backend/app --host 0.0.0.0 --port $(BACKEND_PORT)

# ---- Frontend settings ----
FRONTEND_DIR := frontend
NPM := npm --prefix $(FRONTEND_DIR)

# Colors (optional)
GREEN=\033[0;32m
YELLOW=\033[1;33m
NC=\033[0m

.PHONY: help backend/install backend/run backend/test backend/clean backend/freeze backend/requirements-update frontend/install frontend/dev frontend/build frontend/preview frontend/clean dev stop test all clean ports kill-ports

help:
	@echo -e "${GREEN}Available targets:${NC}"
	@echo "  backend/install            Create venv & install backend deps"
	@echo "  backend/run                Run FastAPI (reload)"
	@echo "  backend/test               Run backend pytest suite"
	@echo "  backend/freeze             Export exact versions to requirements.txt"
	@echo "  backend/requirements-update Update packages to latest compatible versions"
	@echo "  backend/clean              Remove virtualenv"
	@echo "  frontend/install           Install frontend dependencies (npm)"
	@echo "  frontend/dev               Start Vite dev server"
	@echo "  frontend/build             Production build (Vite)"
	@echo "  frontend/preview           Preview production build"
	@echo "  frontend/clean             Remove node_modules + dist"
	@echo "  dev                        Run backend & frontend (simple concurrent)"
	@echo "  stop                       Stop running dev processes (if started with make dev)"
	@echo "  ports                      Show processes listening on dev ports ($(BACKEND_PORT), $(FRONTEND_PORT))"
	@echo "  kill-ports                 Force kill any processes on dev ports (use if stale)"
	@echo "  test                       Run backend tests (alias)"
	@echo "  clean                      Clean backend venv & frontend artifacts"
	@echo "  all                        Install both backend & frontend"

# ---------------- Backend ----------------
backend/install: $(VENVDIR)/bin/activate
$(VENVDIR)/bin/activate: backend/requirements.txt
	@echo -e "${YELLOW}Creating virtual environment & installing backend deps...${NC}"
	python3 -m venv $(VENVDIR)
	$(PIP) install -q --upgrade pip
	$(PIP) install -r backend/requirements.txt
	@touch $(VENVDIR)/bin/activate
	@echo -e "${GREEN}Backend dependencies installed.${NC}"

backend/run: backend/install
	@echo -e "${GREEN}Starting FastAPI (http://localhost:8000)...${NC}"
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m uvicorn $(UVICORN_APP) $(UVICORN_OPTS)

backend/test: backend/install
	@echo -e "${GREEN}Running backend tests...${NC}"
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest -q backend/tests

backend/freeze: backend/install
	@echo -e "${GREEN}Freezing current dependency versions...${NC}"
	$(PIP) freeze > backend/requirements.txt

backend/requirements-update: backend/install
	@echo -e "${GREEN}Updating backend dependencies (may change versions)...${NC}"
	$(PIP) install -U -r backend/requirements.txt

backend/clean:
	@echo -e "${YELLOW}Removing backend virtual environment...${NC}"
	rm -rf $(VENVDIR)

# ---------------- Frontend ----------------
frontend/install: $(FRONTEND_DIR)/package.json
	@echo -e "${YELLOW}Installing frontend dependencies...${NC}"
	cd $(FRONTEND_DIR) && npm install --no-audit --no-fund
	@echo -e "${GREEN}Frontend dependencies installed.${NC}"

frontend/dev: frontend/install
	@echo -e "${GREEN}Starting Vite dev server (http://localhost:$(FRONTEND_PORT))...${NC}"
	@if lsof -iTCP:$(FRONTEND_PORT) -sTCP:LISTEN -Pn >/dev/null 2>&1; then \
	  echo -e "${YELLOW}Port $(FRONTEND_PORT) already in use. Showing process(es):${NC}"; \
	  lsof -iTCP:$(FRONTEND_PORT) -sTCP:LISTEN -Pn; \
	  echo "Use 'make kill-ports' to free it or choose another port."; \
	  exit 1; \
	fi
	cd $(FRONTEND_DIR) && npm run dev

frontend/build: frontend/install
	@echo -e "${GREEN}Building frontend production bundle...${NC}"
	cd $(FRONTEND_DIR) && npm run build

frontend/preview: frontend/build
	@echo -e "${GREEN}Previewing production build...${NC}"
	cd $(FRONTEND_DIR) && npm run preview

frontend/clean:
	@echo -e "${YELLOW}Removing node_modules and dist...${NC}"
	rm -rf $(FRONTEND_DIR)/node_modules $(FRONTEND_DIR)/dist

# ---------------- Combined / Convenience ----------------
all: backend/install frontend/install
	@echo -e "${GREEN}Backend & frontend installed.${NC}"

test: backend/test

dev: backend/install frontend/install
	@echo -e "${GREEN}Starting backend (port $(BACKEND_PORT)) & frontend (port $(FRONTEND_PORT)) concurrently (Ctrl+C to stop)...${NC}"
	@if lsof -iTCP:$(BACKEND_PORT) -sTCP:LISTEN -Pn >/dev/null 2>&1; then \
	  echo -e "${YELLOW}Backend port $(BACKEND_PORT) already in use. Showing process(es):${NC}"; \
	  lsof -iTCP:$(BACKEND_PORT) -sTCP:LISTEN -Pn; \
	  echo "Use 'make stop' or 'make kill-ports' first."; \
	  exit 1; \
	fi
	@if lsof -iTCP:$(FRONTEND_PORT) -sTCP:LISTEN -Pn >/dev/null 2>&1; then \
	  echo -e "${YELLOW}Frontend port $(FRONTEND_PORT) already in use. Showing process(es):${NC}"; \
	  lsof -iTCP:$(FRONTEND_PORT) -sTCP:LISTEN -Pn; \
	  echo "Use 'make stop' or 'make kill-ports' first."; \
	  exit 1; \
	fi
	# Simple concurrency without extra tooling (uvicorn --reload spawns a watcher + worker)
	( PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m uvicorn $(UVICORN_APP) $(UVICORN_OPTS) & echo $$! > .backend.pid )
	( cd $(FRONTEND_DIR) && npm run dev & echo $$! > .frontend.pid )
	trap 'echo Stopping...; kill $$(cat .backend.pid .frontend.pid) 2>/dev/null || true; rm -f .backend.pid .frontend.pid' INT TERM
	wait || true
	@rm -f .backend.pid .frontend.pid

stop:
	@echo -e "${YELLOW}Stopping dev processes...${NC}"
	@if [ -f .backend.pid ]; then kill $$(cat .backend.pid) 2>/dev/null || true; rm -f .backend.pid; echo "Backend (PID file) stopped."; fi
	@if [ -f .frontend.pid ]; then kill $$(cat .frontend.pid) 2>/dev/null || true; rm -f .frontend.pid; echo "Frontend (PID file) stopped."; fi
	@# Fallback: kill anything still listening on the configured ports (stale processes)
	@if lsof -tiTCP:$(BACKEND_PORT) -sTCP:LISTEN >/dev/null 2>&1; then \
	  echo "Killing stale backend port $(BACKEND_PORT) processes"; \
	  lsof -tiTCP:$(BACKEND_PORT) -sTCP:LISTEN | xargs -r kill; \
	fi
	@if lsof -tiTCP:$(FRONTEND_PORT) -sTCP:LISTEN >/dev/null 2>&1; then \
	  echo "Killing stale frontend port $(FRONTEND_PORT) processes"; \
	  lsof -tiTCP:$(FRONTEND_PORT) -sTCP:LISTEN | xargs -r kill; \
	fi
	@echo -e "${GREEN}Stop command completed.${NC}"

ports:
	@echo -e "${GREEN}Listening processes (if any):${NC}"
	@lsof -iTCP:$(BACKEND_PORT) -sTCP:LISTEN -Pn || echo "No process on $(BACKEND_PORT)"
	@lsof -iTCP:$(FRONTEND_PORT) -sTCP:LISTEN -Pn || echo "No process on $(FRONTEND_PORT)"

kill-ports:
	@echo -e "${YELLOW}Force killing processes on ports $(BACKEND_PORT) & $(FRONTEND_PORT)...${NC}"
	@lsof -tiTCP:$(BACKEND_PORT) -sTCP:LISTEN | xargs -r kill && echo "Backend port cleared." || echo "No backend process."
	@lsof -tiTCP:$(FRONTEND_PORT) -sTCP:LISTEN | xargs -r kill && echo "Frontend port cleared." || echo "No frontend process."
	@rm -f .backend.pid .frontend.pid || true
	@echo -e "${GREEN}kill-ports completed.${NC}"

clean: backend/clean frontend/clean
	@echo -e "${GREEN}Project cleaned.${NC}"
