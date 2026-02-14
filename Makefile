.PHONY: help install dev test lint build deploy clean

# Цвета
GREEN  := \033[0;32m
YELLOW := \033[1;33m
NC     := \033[0m

help: ## Показать справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-15s$(NC) %s\n", $$1, $$2}'

install: ## Установить зависимости
	pip install -e ".[dev]"
	cd frontend && npm install

dev: ## Запустить в режиме разработки
	@echo "$(YELLOW)Запуск Redis...$(NC)"
	docker-compose -f docker-compose.dev.yml up redis -d
	@echo "$(YELLOW)Применение миграций...$(NC)"
	alembic upgrade head
	@echo "$(YELLOW)Запуск приложения...$(NC)"
	python -m src.main

dev-frontend: ## Запустить фронтенд в режиме разработки
	cd frontend && npm run dev

test: ## Запустить тесты
	pytest tests/ -v

lint: ## Проверить код
	ruff check src/
	ruff format --check src/

format: ## Отформатировать код
	ruff format src/

migrate: ## Создать миграцию
	@read -p "Название миграции: " name; \
	alembic revision --autogenerate -m "$$name"

migrate-up: ## Применить миграции
	alembic upgrade head

migrate-down: ## Откатить миграцию
	alembic downgrade -1

build: ## Собрать Docker образ
	docker-compose build

up: ## Запустить в Docker
	docker-compose up -d

down: ## Остановить Docker
	docker-compose down

logs: ## Показать логи
	docker-compose logs -f app

shell: ## Открыть shell в контейнере
	docker-compose exec app /bin/bash

db-shell: ## Открыть psql
	docker-compose exec db psql -U postgres aibot

redis-cli: ## Открыть redis-cli
	docker-compose exec redis redis-cli

backup: ## Создать бэкап
	./deploy/backup.sh

deploy: ## Деплой
	./deploy/deploy.sh

clean: ## Очистить временные файлы
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache htmlcov .coverage
	rm -rf frontend/node_modules frontend/dist