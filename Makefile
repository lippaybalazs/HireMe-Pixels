.PHONY: start stop clean logs stop-local lint format format-check

start: stop stop-local
	docker compose up -d --build --wait
	@explorer.exe http://localhost:8080 || true

stop:
	docker compose down

stop-local:
	$(MAKE) -C backend stop
	$(MAKE) -C frontend stop

clean:
	docker compose down -v --rmi local

logs:
	docker compose logs -f
