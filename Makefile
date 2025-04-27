# Makefile for managing Django project in Docker

.PHONY: help up down restart logs makemigrations migrate shell createsuperuser

help:
	@echo ""
	@echo "Available commands:"
	@echo "  make up                - Start docker containers"
	@echo "  make down              - Stop docker containers"
	@echo "  make restart           - Restart containers"
	@echo "  make logs              - View logs"
	@echo "  make makemigrations    - Run makemigrations inside Django container"
	@echo "  make migrate           - Apply migrations"
	@echo "  make shell             - Open Django shell"
	@echo "  make db_shell		- Open Postgres shell"
	@echo "  make createsuperuser   - Create Django superuser"
	@echo "  make build             - Build docker containers"
	@echo "  make help              - Show this help message"
	@echo ""

build:
	docker compose up --build

up:
	docker compose up

down:
	docker compose down

restart:
	docker compose down && docker compose up

logs:
	docker compose logs -f

makemigrations:
	docker exec -it repcheck_web python3 manage.py makemigrations

migrate:
	docker exec -it repcheck_web python3 manage.py migrate

shell:
	docker exec -it repcheck_web python3 manage.py shell

db_shell:
	docker exec -it repcheck_db psql -U postgres -d repcheck

createsuperuser:
	docker exec -it repcheck_web python3 manage.py createsuperuser

