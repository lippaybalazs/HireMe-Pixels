PYTHON ?= ".venv/bin/python"

IMAGE_NAME ?= hireme-pixels-frontend

.PHONY: run docker-build docker-run

run:
	$(PYTHON) -m http.server 8080 --directory app

docker-build:
	docker build -t $(IMAGE_NAME) .

docker-run:
	docker run --rm \
		-p 8080:8080 \
		$(IMAGE_NAME)