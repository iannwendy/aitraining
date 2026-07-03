# Mental Health AI Platform - Makefile
# Single command to run the entire demo

.PHONY: help dev up down build logs clean

# Default target
all: up

help:
	@echo "Mental Health AI Platform - Available Commands:"
	@echo ""
	@echo "  make dev      - Run in development mode (npm + python)"
	@echo "  make up       - Run with Docker"
	@echo "  make down     - Stop Docker containers"
	@echo "  make build    - Build Docker images only"
	@echo "  make logs     - View Docker logs"
	@echo "  make clean    - Stop and remove containers + images"
	@echo ""
	@echo "Examples:"
	@echo "  make dev      # Start dev servers on localhost:3000"
	@echo "  make up       # Start Docker containers on localhost:3000"

# Development mode - run without Docker
dev:
	@echo "Starting development servers..."
	@echo "Backend: http://localhost:8001"
	@echo "Frontend: http://localhost:3000"
	@echo ""
	@echo "Stopping old processes..."
	@pkill -f "uvicorn main:app" 2>/dev/null || true
	@pkill -f "vite" 2>/dev/null || true
	@sleep 1
	@echo "Starting backend..."
	@(cd backend && python3 -m venv venv && source venv/bin/activate && pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -q -r requirements.txt 2>/dev/null; uvicorn main:app --host 127.0.0.1 --port 8001) &
	@(cd frontend && npm run dev -- --port 3000) &
	@echo ""
	@echo "✅ Servers started! Access http://localhost:3000"

# Docker mode
up:
	@echo "Starting Docker containers..."
	@docker-compose up -d --build
	@echo ""
	@echo "✅ Services started!"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"

down:
	@echo "Stopping Docker containers..."
	@docker-compose down

build:
	@docker-compose build

logs:
	@docker-compose logs -f

logs-backend:
	@docker-compose logs -f backend

logs-frontend:
	@docker-compose logs -f frontend

clean:
	@echo "Stopping and removing containers..."
	@docker-compose down --rmi all -v
	@echo "✅ Cleaned up!"

restart: down up
