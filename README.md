# HireMe-Pixels

A collaborative pixel board built as a learning project for **Cloud & DevOps**.

The project is gradually evolving from a simple containerized application into a cloud-deployed system, covering areas such as:

* Docker
* Kubernetes
* CI with GitHub Actions
* Infrastructure as Code
* Azure cloud deployment
* Monitoring and scalability

The goal is to build the infrastructure incrementally while keeping the application itself simple.

## Development

The application runs locally in **Kubernetes using kind**. The root `Makefile` provides the main lifecycle commands:

```bash
make start
```

Builds the backend and frontend Docker images, creates the Kubernetes cluster if needed, loads the images into kind, deploys the application, and waits for all services to become ready.

```bash
make stop
```

Stops the Kubernetes workloads while preserving the local cluster and database data.

```bash
make clean
```

Removes the local Kubernetes cluster and its data. The next `make start` recreates the environment from scratch.

```bash
make logs
```

Shows logs from the Kubernetes workloads.

The `backend/` and `frontend/` directories also have their own Makefiles and Dockerfiles, allowing each component to be developed and run independently.
