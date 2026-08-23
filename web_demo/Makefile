# Mental Health AI Platform - Makefile
# Single command to run the entire demo

.PHONY: help dev up down build logs clean restart

# Default target
all: up

help:
	@echo "Mental Health AI Platform - Available Commands:"
	@echo ""
	@echo "  make up       - Start with Docker (Recommended)"
	@echo "  make dev      - Start in development mode (npm + python)"
	@echo "  make down     - Stop Docker containers"
	@echo "  make build    - Build Docker images only"
	@echo "  make logs     - View all Docker logs"
	@echo "  make logs-be  - View backend logs only"
	@echo "  make logs-fe  - View frontend logs only"
	@echo "  make clean    - Stop and remove containers + images"
	@echo "  make restart  - Restart Docker containers"
	@echo ""
	@echo "Docker mode:"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend:  http://localhost:8001 (internal)"

# Docker mode (Recommended)
up:
	@echo "Building and starting Docker containers..."
	docker compose up -d --build
	@echo ""
	@echo "Waiting for backend to be ready..."
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		docker compose exec -T backend curl -sf http://localhost:8000/ > /dev/null 2>&1 && echo "Backend ready!" && break || echo "Waiting..." && sleep 5; \
	done
	@echo ""
	@echo "Services started:"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend:  http://localhost:8001 (internal: backend:8000)"

down:
	docker compose down

build:
	docker compose build --no-cache

logs:
	docker compose logs -f

logs-be:
	docker compose logs -f backend

logs-fe:
	docker compose logs -f frontend

clean:
	docker compose down --rmi all -v
	@echo "Cleaned up!"

restart: down up

# Development mode - run without Docker
dev:
	@echo "Starting development servers..."
	@echo "Frontend: http://localhost:3000"
	@echo "Backend:  http://localhost:8001"
	@echo ""
	@echo "Stopping old processes..."
	@pkill -f "uvicorn main:app" 2>/dev/null || true
	@pkill -f "vite" 2>/dev/null || true
	@sleep 1
	@echo "Starting backend..."
	@(cd backend && source venv/bin/activate 2>/dev/null || (python3 -m venv venv && source venv/bin/activate && pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -q -r requirements.txt); JWT_SECRET_KEY="dev-secret-key-12345" uvicorn main:app --host 127.0.0.1 --port 8001) &
	@(npm run dev -- --port 3000) &
	@echo ""
	@echo "Servers started! Access http://localhost:3000"
