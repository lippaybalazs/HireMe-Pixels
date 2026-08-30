DB_CONTAINER := hireme-pixels-db
DB_IMAGE := postgres:17
DB_NAME := hireme_pixels
DB_USER := hireme_pixels
DB_PASSWORD := hireme_pixels
DB_PORT := 5432

.PHONY: db-create db-start db-stop db-remove db-status db-logs db-shell db-migrate run check init test docker-build docker-run

PYTHON ?= ".venv/bin/python"
IMAGE_NAME ?= hireme-pixels-backend

db-create:
	docker run \
		--name $(DB_CONTAINER) \
		-e POSTGRES_USER=$(DB_USER) \
		-e POSTGRES_PASSWORD=$(DB_PASSWORD) \
		-e POSTGRES_DB=$(DB_NAME) \
		-p $(DB_PORT):5432 \
		-d $(DB_IMAGE)

db-start:
	docker start $(DB_CONTAINER)

db-stop:
	docker stop $(DB_CONTAINER)

db-remove:
	docker rm $(DB_CONTAINER)

db-status:
	docker ps -a --filter name=$(DB_CONTAINER)

db-logs:
	docker logs $(DB_CONTAINER)

db-shell:
	docker exec -it $(DB_CONTAINER) psql -U $(DB_USER) -d $(DB_NAME)

db-migrate:
	$(PYTHON) manage.py makemigrations
	$(PYTHON) manage.py migrate

run:
	$(PYTHON) manage.py runserver

check:
	$(PYTHON) manage.py check

init:
	$(PYTHON) manage.py initialize_board

test:
	$(PYTHON) manage.py test


docker-build:
	docker build -t $(IMAGE_NAME) .

docker-run:
	docker run --rm \
		-p 8000:8000 \
		--add-host=host.docker.internal:host-gateway \
		-e DB_HOST=host.docker.internal \
		-e DB_NAME=$(DB_NAME) \
		-e DB_USER=$(DB_USER) \
		-e DB_PASSWORD=$(DB_PASSWORD) \
		-e DB_PORT=5432 \
		$(IMAGE_NAME)
	