DB_CONTAINER := hireme-pixels-db
DB_IMAGE := postgres:17
DB_NAME := hireme_pixels
DB_USER := hireme_pixels
DB_PASSWORD := hireme_pixels
DB_PORT := 5432

.PHONY: db-create db-start db-stop db-remove db-status db-logs db-shell db-migrate run check init test

PYTHON ?= ".venv/bin/python"

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