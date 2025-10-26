# Cloud File Sharing System (Monolith → Microservices)

Repo structure: see project tree in assignment.

This project demonstrates:
- Monolithic file-sharing app (Flask).
- Microservices split: api-service, auth-service, storage-service.
- Containerization (Dockerfiles for each service).
- Kubernetes manifests for deployments, services, and HPA.
- Prometheus metrics and Grafana dashboards for monitoring.
- Jenkins pipeline skeleton for CI/CD.
- Terraform skeleton for IaC (S3 + placeholders for EKS).

Run locally (quick):
1. Build monolith image and run:
   docker build -t monolith ./services/monolith
   docker run -p 8080:8080 -v $PWD/services/monolith/uploads:/data/uploads monolith

2. Or deploy to Kubernetes using manifests in infra/k8s and k8s/ directory.

Testing:
- Use tests/loadtest.sh or Locust (not included here).

Author: Hrishikesh Kali, Mustafa Vakil, Poojam Dounde, Shravan Kanthewad, Preet Bansal
