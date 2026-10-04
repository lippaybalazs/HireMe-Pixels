# HireMe-Pixels

https://hireme.lippay.ro

A collaborative pixel board built as a **Cloud & DevOps learning project**.

The application is intentionally simple. The focus is on building, deploying, scaling, and managing the infrastructure around it while gradually adding the application features needed to demonstrate those capabilities.

## Stack

* **Backend:** Django + Django REST Framework
* **Frontend:** HTML, CSS, JavaScript
* **Database:** PostgreSQL
* **Real-time updates:** Redis
* **Authentication:** Django accounts + Microsoft Entra ID
* **Containers:** Docker
* **Local Kubernetes:** kind
* **CI/CD:** GitHub Actions
* **Infrastructure:** Terraform + Terraform Cloud
* **Cloud:** Microsoft Azure
* **Runtime:** Azure Container Apps
* **Registry:** Azure Container Registry
* **Database:** Azure Database for PostgreSQL
* **DNS / HTTPS:** Azure DNS + managed certificates

## Application

The application is a **100×100 collaborative pixel board** where users can select and modify pixels.

Users can:

* Create local accounts with a username and password
* Sign in with Microsoft through **Microsoft Entra ID**
* Select and edit individual pixels
* Use the **pencil tool** to draw across multiple pixels
* See pixel changes update in real time
* View information about who changed a pixel
* Persist their selected drawing color and editing mode

Administrative functionality is also integrated into the application. Administrators can ban users, with the affected user's pixels restored from their previous pixel history.

The application remains deliberately simple; the goal is to use it as a platform for demonstrating infrastructure and DevOps concepts.

## Real-Time Updates

Redis is used to support real-time pixel updates between backend instances.

This allows the application to continue working correctly when multiple backend Container App replicas are running. A pixel change can be propagated through Redis so that connected clients receive updates without requiring a page refresh.

This also provides a practical use case for the application's autoscaling configuration: backend instances can scale horizontally while still sharing real-time update information.

## Local Development

The application can be run locally using Docker and Kubernetes with **kind**.

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

Azure infrastructure is managed through **Terraform**, with Terraform Cloud providing remote state and separate environments:

* **CI** — temporary infrastructure created for pull requests and destroyed afterwards
* **Development** — development environment deployed from `main`
* **Production** — production environment deployed from `production`

The Azure deployment uses **Azure Container Apps** for the frontend and backend, with PostgreSQL provided as a managed Azure service.

Terraform also manages the supporting Azure resources, including the Container Apps environment, Azure Container Registry, networking-related resources, DNS, certificates, monitoring, authentication configuration, and application scaling.

## Scaling

The backend is configured to scale horizontally using **Azure Container Apps HTTP-based scaling**.

Multiple backend replicas can run simultaneously, with Azure distributing incoming HTTP traffic between available replicas.

Redis provides the shared real-time update mechanism between those replicas, allowing the application to remain consistent as the backend scales.

This setup provides a practical example of combining:

* Containerized application workloads
* Horizontal scaling
* Load balancing
* Shared application state
* Real-time communication

## Authentication & Administration

Authentication supports two methods:

* Local username/password accounts
* Microsoft Entra ID

Microsoft authentication is integrated using Microsoft's OAuth/OpenID Connect flow, with Entra identities linked to Django users.

The application also has an administrator system with functionality such as user banning. When a user is banned, their pixels can be restored using the application's pixel history.

## CI/CD

GitHub Actions handles validation and deployment.

Pull requests run automated checks for the backend, Kubernetes configuration, and Terraform configuration. CI infrastructure can be deployed temporarily for validation and destroyed afterwards.

Pushes to `main` deploy the development environment, while pushes to `production` deploy the production environment.

Application images are built by CI/CD and pushed to **Azure Container Registry** before the Azure Container Apps are updated.

The infrastructure deployment is separated from the normal application deployment so that existing Azure infrastructure does not need to be recreated on every application deployment.

## Environments

### Development

**Frontend:** https://hiremedev.lippay.ro

**API:** https://api.hiremedev.lippay.ro/api/

### Production

**Frontend:** https://hireme.lippay.ro

**API:** https://api.hireme.lippay.ro/api/

## Goal

The goal is to demonstrate practical **Cloud & DevOps skills through a small application**, rather than to build a complex application itself.

The project currently demonstrates:

* Infrastructure as Code with Terraform
* Remote Terraform state and environment separation
* Azure Container Apps
* Containerized application deployment
* Azure Container Registry
* Managed PostgreSQL
* Horizontal application scaling
* Redis-based real-time communication
* Microsoft Entra ID integration
* Local application authentication
* CI/CD with GitHub Actions
* Kubernetes-based local development
* Application-level administration
* Automated infrastructure testing

The infrastructure will continue to evolve toward areas such as **monitoring, observability, autoscaling, security, and production hardening**, while keeping the application deliberately simple.
