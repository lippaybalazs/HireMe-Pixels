K8S_CLUSTER := hireme-pixels
K8S_CONFIG := k8s/kind-config.yaml

BACKEND_IMAGE := hireme-pixels-backend:latest
FRONTEND_IMAGE := hireme-pixels-frontend:latest

K8S_MANIFESTS := \
	k8s/postgres-secret.yaml \
	k8s/postgres.yaml \
	k8s/backend.yaml \
	k8s/frontend.yaml

.PHONY: start stop clean logs \
	k8s-create k8s-build k8s-load k8s-apply k8s-wait k8s-stop k8s-clean \
	stop-local

start: stop stop-local k8s-create k8s-build k8s-load k8s-apply k8s-wait
	@explorer.exe http://localhost:8080 || true

stop:
	$(MAKE) k8s-stop

clean:
	$(MAKE) k8s-clean
	$(MAKE) stop-local

logs:
	kubectl logs -l app=backend --tail=100
	kubectl logs -l app=frontend --tail=100
	kubectl logs postgres-0 --tail=100

k8s-create:
	@if ! kind get clusters | grep -Fxq "$(K8S_CLUSTER)"; then \
		echo "Creating kind cluster: $(K8S_CLUSTER)"; \
		kind create cluster \
			--name $(K8S_CLUSTER) \
			--config $(K8S_CONFIG) \
			--wait 5m; \
	else \
		echo "Kind cluster $(K8S_CLUSTER) already exists"; \
	fi

k8s-build:
	docker build -t $(BACKEND_IMAGE) ./backend
	docker build -t $(FRONTEND_IMAGE) ./frontend

k8s-load:
	kind load docker-image $(BACKEND_IMAGE) --name $(K8S_CLUSTER)
	kind load docker-image $(FRONTEND_IMAGE) --name $(K8S_CLUSTER)

k8s-apply:
	@for manifest in $(K8S_MANIFESTS); do \
		kubectl apply -f $$manifest; \
	done

k8s-wait:
	kubectl wait --for=condition=ready pod/postgres-0 --timeout=120s
	kubectl wait --for=condition=available deployment/backend --timeout=120s
	kubectl wait --for=condition=available deployment/frontend --timeout=120s

k8s-stop:
	-kubectl delete deployment backend frontend --ignore-not-found
	-kubectl delete statefulset postgres --ignore-not-found
	-kubectl delete service backend frontend postgres --ignore-not-found

k8s-clean:
	-kind delete cluster --name $(K8S_CLUSTER)

stop-local:
	$(MAKE) -C backend stop
	$(MAKE) -C frontend stop