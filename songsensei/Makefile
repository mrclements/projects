.PHONY: up down build logs clean restart shell-api shell-analysis shell-web

# Start all services
up:
	docker-compose up -d

# Stop all services
down:
	docker-compose down

# Build all services
build:
	docker-compose build

# View logs for all services
logs:
	docker-compose logs -f

# Clean up containers and volumes
clean:
	docker-compose down -v
	docker-compose rm -f

# Restart all services
restart: down up

# Shell into API container
shell-api:
	docker-compose exec api sh

# Shell into Analysis container
shell-analysis:
	docker-compose exec analysis bash

# Shell into Web container
shell-web:
	docker-compose exec web sh

# Install dependencies for all services
install:
	cd api && npm install
	cd web && npm install
	cd analysis && pip install -r requirements.txt

# Run tests
test:
	cd api && npm test
	cd web && npm test
	cd analysis && python -m pytest

# Development mode (with hot reload)
dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Production build
prod:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
