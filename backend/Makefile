DB_CONTAINER := hireme-pixels-db
DB_IMAGE := postgres:17

DB_NAME := hireme_pixels
DB_USER := hireme_pixels
DB_PASSWORD := hireme_pixels
DB_PORT := 5432

IMAGE_NAME := hireme-pixels-backend
BACKEND_CONTAINER := hireme-pixels-backend

.PHONY: start stop clean \
	db-create db-start db-stop db-remove db-status db-logs db-shell \
	migrate init check test \
	docker-build docker-run

# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

start: stop db-start docker-build docker-run
	$(MAKE) migrate
	$(MAKE) init

stop:
	docker stop $(BACKEND_CONTAINER) 2>/dev/null || true
	$(MAKE) db-stop

clean: stop
	docker rmi $(IMAGE_NAME) 2>/dev/null || true
	$(MAKE) db-remove

logs:
	docker logs -f $(CONTAINER_NAME)

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

db-create:
	docker run \
		--name $(DB_CONTAINER) \
		-e POSTGRES_USER=$(DB_USER) \
		-e POSTGRES_PASSWORD=$(DB_PASSWORD) \
		-e POSTGRES_DB=$(DB_NAME) \
		-p $(DB_PORT):5432 \
		-d $(DB_IMAGE)

db-start:
	@if docker ps -a --format '{{.Names}}' | grep -qx '$(DB_CONTAINER)'; then \
		docker start $(DB_CONTAINER); \
	else \
		$(MAKE) db-create; \
	fi

db-stop:
	docker stop $(DB_CONTAINER) 2>/dev/null || true

db-remove:
	docker rm -f $(DB_CONTAINER) 2>/dev/null || true

db-status:
	docker ps -a --filter name=$(DB_CONTAINER)

db-logs:
	docker logs $(DB_CONTAINER)

db-shell:
	docker exec -it $(DB_CONTAINER) psql -U $(DB_USER) -d $(DB_NAME)

# ---------------------------------------------------------------------------
# Django
# ---------------------------------------------------------------------------

migrate:
	docker exec $(BACKEND_CONTAINER) python manage.py migrate

init:
	docker exec $(BACKEND_CONTAINER) python manage.py initialize_board

check:
	docker exec $(BACKEND_CONTAINER) python manage.py check

test:
	docker exec $(BACKEND_CONTAINER) python manage.py test

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------

docker-build:
	docker build -t $(IMAGE_NAME) .

docker-run:
	docker run -d --rm \
		--name $(BACKEND_CONTAINER) \
		-p 8000:8000 \
		--add-host=host.docker.internal:host-gateway \
		-e DB_HOST=host.docker.internal \
		-e DB_NAME=$(DB_NAME) \
		-e DB_USER=$(DB_USER) \
		-e DB_PASSWORD=$(DB_PASSWORD) \
		-e DB_PORT=$(DB_PORT) \
		$(IMAGE_NAME)