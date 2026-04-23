#!/usr/bin/env bash
#
# QR-SaaS Kubernetes Deploy Script
#
# Usage:
#   ./deploy.sh                          # Build + deploy (default registry: local)
#   ./deploy.sh --registry docker.io/myuser   # Push to a remote registry
#   ./deploy.sh --skip-build             # Deploy only (images already pushed)
#   ./deploy.sh --dry-run                # Print manifests without applying
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
K8S_BASE="$SCRIPT_DIR/base"
NAMESPACE="qr-saas"

# ── Defaults ─────────────────────────────────────────
REGISTRY=""
TAG="latest"
SKIP_BUILD=false
DRY_RUN=false

# ── Parse args ───────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --registry)   REGISTRY="$2"; shift 2 ;;
    --tag)        TAG="$2"; shift 2 ;;
    --skip-build) SKIP_BUILD=true; shift ;;
    --dry-run)    DRY_RUN=true; shift ;;
    *)            echo "Unknown flag: $1"; exit 1 ;;
  esac
done

API_IMAGE="qr-saas-api:${TAG}"
WEB_IMAGE="qr-saas-web:${TAG}"

if [[ -n "$REGISTRY" ]]; then
  API_IMAGE="${REGISTRY}/qr-saas-api:${TAG}"
  WEB_IMAGE="${REGISTRY}/qr-saas-web:${TAG}"
fi

echo "============================================"
echo "  QR-SaaS K8s Deployment"
echo "============================================"
echo "  API image : $API_IMAGE"
echo "  Web image : $WEB_IMAGE"
echo "  Namespace : $NAMESPACE"
echo "============================================"

# ── Step 1: Build Docker images ──────────────────────
if [[ "$SKIP_BUILD" == false ]]; then
  echo ""
  echo ">> Building backend image..."
  docker build -t "$API_IMAGE" -f "$PROJECT_ROOT/backend/Dockerfile.prod" "$PROJECT_ROOT/backend"

  echo ""
  echo ">> Building frontend image..."
  docker build -t "$WEB_IMAGE" \
    --build-arg VITE_API_BASE="https://qr.api.santhira.com" \
    -f "$PROJECT_ROOT/frontend/Dockerfile.prod" "$PROJECT_ROOT/frontend"

  # Push to registry if specified
  if [[ -n "$REGISTRY" ]]; then
    echo ""
    echo ">> Pushing images to $REGISTRY..."
    docker push "$API_IMAGE"
    docker push "$WEB_IMAGE"
  fi
else
  echo ""
  echo ">> Skipping build (--skip-build)"
fi

# ── Step 2: Update image references in Kustomization ─
cd "$K8S_BASE"
# Use kustomize edit if available, otherwise sed
if command -v kustomize &> /dev/null; then
  kustomize edit set image "qr-saas-api=$API_IMAGE"
  kustomize edit set image "qr-saas-web=$WEB_IMAGE"
else
  echo ">> kustomize CLI not found, using kubectl kustomize"
fi

# ── Step 3: Apply base manifests ─────────────────────
echo ""
echo ">> Applying K8s manifests..."

if [[ "$DRY_RUN" == true ]]; then
  kubectl kustomize "$K8S_BASE"
  echo ""
  echo ">> Dry-run complete. No changes applied."
  exit 0
fi

# Create namespace first (idempotent)
kubectl apply -f "$K8S_BASE/namespace.yaml"

# Apply all base resources
kubectl apply -k "$K8S_BASE"

# ── Step 4: Create migration ConfigMap from actual SQL file ─
echo ""
echo ">> Creating db-migrations ConfigMap from SQL file..."
kubectl create configmap db-migrations \
  --namespace "$NAMESPACE" \
  --from-file="001_init.sql=$PROJECT_ROOT/backend/migrations/001_init.sql" \
  --dry-run=client -o yaml | kubectl apply -f -

# ── Step 5: Run database migration Job ───────────────
echo ""
echo ">> Running database migration..."
# Delete previous job if it exists (jobs are immutable)
kubectl delete job db-migrate --namespace "$NAMESPACE" --ignore-not-found=true
kubectl apply -f "$K8S_BASE/db-migrate-job.yaml"

echo ""
echo ">> Waiting for migration to complete..."
kubectl wait --for=condition=complete job/db-migrate \
  --namespace "$NAMESPACE" --timeout=120s || {
    echo "!! Migration failed. Check logs:"
    echo "   kubectl logs -n $NAMESPACE job/db-migrate"
    exit 1
  }

# ── Step 6: Verify rollout ───────────────────────────
echo ""
echo ">> Waiting for deployments to roll out..."
kubectl rollout status deployment/api --namespace "$NAMESPACE" --timeout=120s
kubectl rollout status deployment/frontend --namespace "$NAMESPACE" --timeout=120s
kubectl rollout status deployment/redis --namespace "$NAMESPACE" --timeout=60s

echo ""
echo "============================================"
echo "  Deployment complete!"
echo "============================================"
echo ""
echo "  Useful commands:"
echo "    kubectl get all -n $NAMESPACE"
echo "    kubectl logs -n $NAMESPACE -l app.kubernetes.io/name=api -f"
echo "    kubectl port-forward -n $NAMESPACE svc/frontend-svc 8080:80"
echo "    kubectl port-forward -n $NAMESPACE svc/api-svc 8000:8000"
echo ""
