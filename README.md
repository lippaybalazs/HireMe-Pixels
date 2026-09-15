# HireMe-Pixels

[hireme.lippay.ro](https://hireme.lippay.ro)

A collaborative pixel board built as a **Cloud & DevOps learning project**.

The application is intentionally simple. The focus is on building, deploying, and managing the infrastructure around it.

## Stack

- **Backend:** Django + Django REST Framework
- **Frontend:** HTML, CSS, JavaScript
- **Database:** PostgreSQL
- **Containers:** Docker
- **Local Kubernetes:** kind
- **CI/CD:** GitHub Actions
- **Infrastructure:** Terraform + Terraform Cloud
- **Cloud:** Microsoft Azure
- **Runtime:** Azure Container Apps
- **Registry:** Azure Container Registry
- **Database:** Azure Database for PostgreSQL
- **DNS / HTTPS:** Azure DNS + managed certificates

## Local Development

The application runs locally in Kubernetes using **kind**.

The root `Makefile` provides the main lifecycle:

```bash
make start
```

Builds the images, creates the kind cluster if necessary, loads the images, deploys the application, and waits for it to become ready.

```bash
make stop
```

Stops the workloads while preserving the cluster and its data.

```bash
make clean
```

Removes the cluster and its data. The next `make start` recreates everything from scratch.

```bash
make logs
```

Shows Kubernetes workload logs.

The backend and frontend can also be developed independently using their own Makefiles and Dockerfiles.

## Infrastructure

Azure infrastructure is managed entirely through **Terraform**, with Terraform Cloud providing remote state and separate environments:

- **CI** — temporary infrastructure created for pull requests and destroyed afterwards
- **Development** — persistent environment deployed from `main`
- **Production** — persistent environment deployed from `production`

The Azure deployment currently consists of Azure Container Apps for the frontend and backend, with PostgreSQL provided as a managed Azure service.

## CI/CD

GitHub Actions handles both validation and deployment.

Pull requests run Terraform, Kubernetes, and backend checks, build and publish the container images, deploy the application to temporary Azure infrastructure, and destroy it afterwards.

Merges to `main` deploy the development environment. The `production` branch is be used for production deployments.

Application images are built by CI/CD and pushed to Azure Container Registry before the Container Apps are deployed.

## Environments

### Development

**Frontend:** https://hiremedev.lippay.ro  
**API:** https://api.hiremedev.lippay.ro/api/

### Production

**Frontend:** https://hireme.lippay.ro  
**API:** https://api.hireme.lippay.ro/api/

## Goal

The goal is to demonstrate practical Cloud & DevOps skills through a small application rather than to build a complex application itself.

The infrastructure will continue to evolve toward areas such as **monitoring, observability, autoscaling, and production hardening** while keeping the application deliberately simple.