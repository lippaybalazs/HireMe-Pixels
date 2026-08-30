CONTAINER_NAME ?= hireme-pixels-frontend
IMAGE_NAME ?= hireme-pixels-frontend

.PHONY: start stop clean

start: stop
	docker build -t $(IMAGE_NAME) .
	docker run -d --rm \
		--name $(CONTAINER_NAME) \
		-p 8080:8080 \
		$(IMAGE_NAME)

stop:
	docker stop $(CONTAINER_NAME) 2>/dev/null || true

clean: stop
	docker rmi $(IMAGE_NAME) 2>/dev/null || true

logs:
	docker logs -f $(CONTAINER_NAME)