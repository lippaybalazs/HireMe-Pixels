.PHONY: up down logs

up: down
	docker compose up -d --build --wait
	explorer.exe http://localhost:8080

down:
	docker compose down

clean:
	docker compose down -v

logs:
	docker compose logs -f