# HireMe-Pixels

A collaborative pixel board built as a learning project for **Cloud & DevOps**.

The project is gradually evolving from a locally containerized application into a cloud-deployed system, covering areas such as:

* Docker & Docker Compose
* CI with GitHub Actions
* Infrastructure as Code
* Cloud deployment
* Monitoring and scalability

The goal is to build the infrastructure incrementally while keeping the application itself simple.

## Development

The project provides a root `Makefile` for common operations:

```bash
make start
```

Builds and starts the application and database, then runs migrations and initializes the board.

```bash
make stop
```

Stops the application and database containers.

```bash
make clean
```

Stops the application and removes the containers, database volume, and locally built images.

```bash
make logs
```

Shows the Docker Compose logs for the application.
