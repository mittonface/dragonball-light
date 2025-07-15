.PHONY: help build up down logs restart clean deploy shell

help:
	@echo "Available commands:"
	@echo "  make build      - Build Docker images"
	@echo "  make up         - Start all services"
	@echo "  make down       - Stop all services"
	@echo "  make logs       - View logs from all services"
	@echo "  make restart    - Restart all services"
	@echo "  make clean      - Remove containers and volumes"
	@echo "  make deploy     - Deploy the application"
	@echo "  make shell      - Open a shell in the running container"

build:
	docker-compose build

up:
	docker network create proxy-network 2>/dev/null || true
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

restart:
	docker-compose restart

clean:
	docker-compose down -v

deploy:
	./deploy.sh

shell:
	docker-compose exec led-server /bin/bash